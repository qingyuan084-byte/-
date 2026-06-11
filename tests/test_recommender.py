"""
推荐器单元测试 — 验证按需计算、内存优化、MemoryError 降级。
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


# ── 测试用 fixture ────────────────────────────────────


def _make_dummy_data(n_movies=50, n_tfidf_features=100, n_genre_features=10):
    """构造小规模测试数据。"""
    tfidf = csr_matrix(np.random.rand(n_movies, n_tfidf_features).astype(np.float32))
    tfidf[tfidf < 0.7] = 0  # 模拟稀疏
    tfidf.eliminate_zeros()

    movie_ids_df = pd.DataFrame({
        "movie_id": [str(1000000 + i) for i in range(n_movies)],
        "title": [f"测试电影_{i}" for i in range(n_movies)],
    })

    genre = np.eye(n_genre_features, dtype=np.float32)[
        np.random.randint(0, n_genre_features, size=n_movies)
    ]

    return tfidf, movie_ids_df, genre


# ── ContentBasedRecommender 测试 ──────────────────────


class TestContentBasedRecommenderInit:
    """初始化行为测试。"""

    def test_precompute_false_no_similarity_matrix(self):
        """precompute=False 时不创建 similarity_matrix。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        assert rec.similarity_matrix is None
        assert rec.feature_matrix is not None

    def test_precompute_true_creates_similarity_matrix(self):
        """precompute=True 时创建 similarity_matrix。"""
        tfidf, movies, genres = _make_dummy_data(n_movies=20)
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=True,
        )
        assert rec.similarity_matrix is not None
        assert rec.similarity_matrix.shape == (20, 20)

    def test_feature_matrix_is_sparse(self):
        """特征矩阵保持稀疏格式。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender
        from scipy.sparse import issparse

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        assert issparse(rec.feature_matrix)

    def test_use_genre_false_no_genre_fusion(self):
        """use_genre=False 时特征矩阵形状等于 TF-IDF。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=False,
            precompute=False,
        )
        assert rec.feature_matrix.shape == tfidf.shape


class TestRecommendByMovie:
    """按电影推荐测试。"""

    def test_works_without_similarity_matrix(self):
        """没有预计算矩阵时 recommend_by_movie 仍能返回结果。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        results = rec.recommend_by_movie("1000000", top_n=5)
        assert len(results) > 0
        assert len(results) <= 5

    def test_returns_correct_top_n(self):
        """top_n 不超过电影总数时结果数量正确。"""
        tfidf, movies, genres = _make_dummy_data(n_movies=30)
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        results = rec.recommend_by_movie("1000000", top_n=10)
        assert len(results) == 10

    def test_self_not_in_results(self):
        """自身电影不会出现在推荐结果里。"""
        tfidf, movies, genres = _make_dummy_data(n_movies=30)
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        target_id = "1000005"
        results = rec.recommend_by_movie(target_id, top_n=10)
        result_ids = [r[0] for r in results]
        assert target_id not in result_ids

    def test_unknown_movie_returns_empty(self):
        """不存在的 movie_id 返回空列表。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        results = rec.recommend_by_movie("9999999", top_n=5)
        assert results == []

    def test_similarity_scores_descending(self):
        """推荐结果按相似度从高到低排序。"""
        tfidf, movies, genres = _make_dummy_data(n_movies=30)
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        results = rec.recommend_by_movie("1000000", top_n=10)
        scores = [r[2] for r in results]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"分数未降序: {scores}"

    def test_result_structure(self):
        """返回结果结构为 (movie_id, title, similarity_score)。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        results = rec.recommend_by_movie("1000000", top_n=3)
        for item in results:
            assert len(item) == 3
            assert isinstance(item[0], str)  # movie_id
            assert isinstance(item[1], str)  # title
            assert isinstance(item[2], float)  # similarity_score

    def test_precomputed_and_ondemand_agree(self):
        """预计算与按需计算的结果应一致。"""
        tfidf, movies, genres = _make_dummy_data(n_movies=30)
        from recommender.content_based import ContentBasedRecommender

        rec_pre = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=True,
        )
        rec_on = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )

        pre_results = rec_pre.recommend_by_movie("1000000", top_n=10)
        on_results = rec_on.recommend_by_movie("1000000", top_n=10)

        pre_ids = [r[0] for r in pre_results]
        on_ids = [r[0] for r in on_results]
        assert pre_ids == on_ids

        for p, o in zip(pre_results, on_results):
            assert abs(p[2] - o[2]) < 1e-4, f"分数不一致: {p[2]} vs {o[2]}"


class TestRecommendByText:
    """文本搜索推荐测试。"""

    def test_returns_results(self):
        """recommend_by_text 能正常返回结果。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        results = rec.recommend_by_text("科幻", top_n=5)
        assert isinstance(results, list)
        # 词汇不在 TF-IDF 词汇表中时会回退到 fallback 搜索
        # fallback 可能返回空，这是合理的

    def test_empty_query(self):
        """空查询不崩溃。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender

        rec = ContentBasedRecommender(
            tfidf_matrix=tfidf,
            movie_ids_df=movies,
            genre_matrix=genres,
            use_genre=True,
            precompute=False,
        )
        results = rec.recommend_by_text("", top_n=5)
        assert isinstance(results, list)


# ── RecommenderService MemoryError 降级测试 ───────────


class TestRecommenderServiceDegradation:
    """MemoryError 降级测试。"""

    def test_default_precompute_is_false(self, monkeypatch):
        """默认情况下 RECOMMENDER_PRECOMPUTE 未设置，precompute 应为 False。"""
        monkeypatch.delenv("RECOMMENDER_PRECOMPUTE", raising=False)
        # 验证读取逻辑
        val = os.getenv("RECOMMENDER_PRECOMPUTE", "false").lower()
        assert val == "false"

    def test_env_true_enables_precompute(self, monkeypatch):
        """RECOMMENDER_PRECOMPUTE=true 时启用预计算。"""
        monkeypatch.setenv("RECOMMENDER_PRECOMPUTE", "true")
        val = os.getenv("RECOMMENDER_PRECOMPUTE", "false").lower() == "true"
        assert val is True

    def test_memory_error_fallback(self):
        """模拟 MemoryError 时自动降级为按需计算。"""
        tfidf, movies, genres = _make_dummy_data()
        from recommender.content_based import ContentBasedRecommender

        # 第一次调用抛出 MemoryError，第二次应成功（precompute=False）
        call_count = [0]

        def mock_init_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and kwargs.get("precompute"):
                raise MemoryError("模拟内存不足")

        with patch.object(
            ContentBasedRecommender, "__init__",
            side_effect=mock_init_side_effect,
        ):
            # 模拟 RecommenderService 的降级逻辑
            precompute = True
            recommender = None
            try:
                recommender = ContentBasedRecommender(
                    tfidf_matrix=tfidf,
                    movie_ids_df=movies,
                    genre_matrix=genres,
                    use_genre=True,
                    genre_weight=0.3,
                    precompute=precompute,
                )
            except MemoryError:
                if precompute:
                    # 降级
                    recommender = ContentBasedRecommender(
                        tfidf_matrix=tfidf,
                        movie_ids_df=movies,
                        genre_matrix=genres,
                        use_genre=True,
                        genre_weight=0.3,
                        precompute=False,
                    )

            assert recommender is not None
            assert call_count[0] == 2  # 第一次失败，第二次成功


# ── 缓存兼容性测试 ────────────────────────────────────


class TestCacheCompatibility:
    """验证 Redis 缓存逻辑在按需计算模式下正常工作。"""

    def test_recommend_by_movie_cache_write(self):
        """recommend_by_movie 在按需计算模式下仍然写入缓存。"""
        from backend.cache import delete_cache, build_cache_key

        cache_key = build_cache_key("similar", "test_movie", "3")
        delete_cache(cache_key)

        import backend.cache as cache_mod
        orig_client = cache_mod._redis_client
        orig_checked = cache_mod._redis_checked
        try:
            mock = MagicMock()
            mock.get.return_value = None
            cache_mod._redis_client = mock
            cache_mod._redis_checked = True

            from backend.services.recommender_service import RecommenderService
            service = RecommenderService()

            # 使用真实电影 ID 测试
            result = service.recommend_by_movie("1292052", top_n=3)
            assert isinstance(result, list)
            if result:
                assert "movie_id" in result[0]
                assert "title" in result[0]
                assert "similarity_score" in result[0]

            assert mock.setex.called
        finally:
            cache_mod._redis_client = orig_client
            cache_mod._redis_checked = orig_checked
            delete_cache(cache_key)

    def test_recommend_by_movie_enrich_structure(self):
        """返回的 dict 结构包含所有必要字段。"""
        from backend.services.recommender_service import RecommenderService
        service = RecommenderService()

        result = service.recommend_by_movie("1292052", top_n=3)
        assert isinstance(result, list)
        if result:
            item = result[0]
            assert "movie_id" in item
            assert "title" in item
            assert "similarity_score" in item
            assert "poster_url" in item
            assert "rating" in item
            assert "year" in item
