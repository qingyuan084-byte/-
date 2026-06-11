"""
推荐服务层测试 — 推荐、搜索、top_n 截断、DB 降级到 CSV。
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.services.recommender_service import RecommenderService


@pytest.fixture(scope="module")
def service():
    """共享 RecommenderService 单例（模块级复用，避免重复初始化）。"""
    return RecommenderService()


class TestRecommendByMovie:
    """recommend_by_movie — 按电影 ID 推荐相似电影。"""

    def test_returns_list_within_top_n(self, service):
        """get_similar_movies(存在的movie_id, top_n=10) 返回列表，长度 <= 10。"""
        result = service.recommend_by_movie("1292052", top_n=10)
        assert isinstance(result, list)
        assert len(result) <= 10
        assert len(result) > 0
        assert "movie_id" in result[0]
        assert "title" in result[0]
        assert "similarity_score" in result[0]

    def test_top_n_5_respected(self, service):
        """get_similar_movies(存在的movie_id, top_n=5) 返回列表，长度 <= 5。"""
        result = service.recommend_by_movie("1292052", top_n=5)
        assert len(result) <= 5
        assert len(result) > 0

    def test_unknown_movie_returns_empty(self, service):
        """get_similar_movies("不存在的id_xyz") 返回空列表，不崩溃。"""
        result = service.recommend_by_movie("不存在的id_xyz", top_n=10)
        assert result == []

    def test_top_n_999_capped(self, service):
        """top_n=999 被截断到 50，不崩溃，不返回几百条。"""
        result = service.recommend_by_movie("1292052", top_n=999)
        assert isinstance(result, list)
        assert len(result) <= 50


class TestRecommendByText:
    """recommend_by_text — 按文本搜索推荐电影。"""

    def test_search_returns_nonempty(self, service):
        """search_movies(query="爱情") 返回非空列表。"""
        result = service.recommend_by_text("爱情", top_n=10)
        assert isinstance(result, list)
        assert len(result) > 0
        assert "movie_id" in result[0]
        assert "title" in result[0]

    def test_top_n_5_respected(self, service):
        """recommend_by_text top_n=5 返回不超过 5 条。"""
        result = service.recommend_by_text("科幻", top_n=5)
        assert len(result) <= 5

    def test_top_n_999_capped(self, service):
        """top_n=999 被截断到 50，不崩溃。"""
        result = service.recommend_by_text("喜剧", top_n=999)
        assert isinstance(result, list)
        assert len(result) <= 50

    def test_empty_query_no_crash(self, service):
        """空查询不崩溃，返回 list。"""
        result = service.recommend_by_text("", top_n=5)
        assert isinstance(result, list)


class TestDBFallback:
    """mock 数据库连接失败后，服务自动 fallback 到 CSV，接口仍然返回正常结果。"""

    def test_recommend_by_movie_falls_back_to_csv(self, service):
        """mock _try_db 返回 None 后 recommend_by_movie 仍正常返回。"""
        from backend.services.recommender_service import RecommenderService as RS
        with patch.object(RS, "_try_db", return_value=None):
            result = service.recommend_by_movie("1292052", top_n=10)
            assert isinstance(result, list)
            assert len(result) > 0
            assert "movie_id" in result[0]

    def test_recommend_by_text_falls_back_to_csv(self, service):
        """mock _try_db 返回 None 后 recommend_by_text 仍正常返回。"""
        from backend.services.recommender_service import RecommenderService as RS
        with patch.object(RS, "_try_db", return_value=None):
            result = service.recommend_by_text("爱情", top_n=10)
            assert isinstance(result, list)
            assert len(result) > 0

    def test_list_movies_falls_back_to_csv(self, service):
        """mock _try_db 返回 None 后 list_movies 仍正常返回。"""
        from backend.services.recommender_service import RecommenderService as RS
        with patch.object(RS, "_try_db", return_value=None):
            results, total = service.list_movies(page=1, page_size=5)
            assert isinstance(results, list)
            assert isinstance(total, int)
            assert total > 0

    def test_get_stats_falls_back_to_csv(self, service):
        """mock _try_db 返回 None 后 get_stats 仍正常返回。"""
        from backend.services.recommender_service import RecommenderService as RS
        with patch.object(RS, "_try_db", return_value=None):
            stats = service.get_stats()
            assert "total_movies" in stats
            assert stats["total_movies"] > 0

    def test_get_movie_detail_falls_back_to_csv(self, service):
        """mock _try_db 返回 None 后 get_movie_detail 仍正常返回。"""
        from backend.services.recommender_service import RecommenderService as RS
        with patch.object(RS, "_try_db", return_value=None):
            movie = service.get_movie_detail("1292052")
            assert movie is not None
            assert "title" in movie


class TestMovieDetailAndList:
    """get_movie_detail / list_movies — 基本功能验证。"""

    def test_get_movie_detail_valid(self, service):
        """存在的 movie_id 返回完整详情。"""
        movie = service.get_movie_detail("1292052")
        assert movie is not None
        assert movie["movie_id"] == "1292052"
        assert len(movie["title"]) > 0
        assert "rating" in movie
        assert "summary" in movie
        assert "genres" in movie

    def test_get_movie_detail_not_found(self, service):
        """不存在的 movie_id 返回 None。"""
        result = service.get_movie_detail("id_not_exist_000")
        assert result is None

    def test_list_movies_basic(self, service):
        """list_movies 返回 (results, total) 元组，total > 0。"""
        results, total = service.list_movies(page=1, page_size=10)
        assert isinstance(results, list)
        assert isinstance(total, int)
        assert total > 0
        assert len(results) <= 10
