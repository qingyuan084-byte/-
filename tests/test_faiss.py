"""
FAISS 向量索引测试 — 加载、验证、检索、fallback。
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


# ── 测试用 fixture ────────────────────────────────────


def _make_dummy_embeddings(n=50, dim=384):
    """创建小规模 L2 归一化向量和元数据。"""
    rng = np.random.RandomState(42)
    emb = rng.randn(n, dim).astype(np.float32)
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    import pandas as pd
    meta = pd.DataFrame({
        "movie_id": [str(1000000 + i) for i in range(n)],
        "title": [f"测试电影_{i}" for i in range(n)],
        "rating": [round(float(rng.uniform(5, 10)), 1) for _ in range(n)],
        "year": [int(rng.randint(1990, 2025)) for _ in range(n)],
        "genres": ["剧情" for _ in range(n)],
    })
    return emb, meta


# ── FaissIndex 测试 ───────────────────────────────────


class TestFaissIndexLifecycle:
    """FaissIndex 加载、验证、禁用测试。"""

    def test_disabled_by_env(self, monkeypatch):
        """USE_FAISS_INDEX=false 时 is_ready=False。"""
        monkeypatch.setenv("USE_FAISS_INDEX", "false")
        from backend.services.faiss_index import FaissIndex

        # 强制重建实例
        FaissIndex._instance = None
        idx = FaissIndex()
        assert idx.is_ready is False

    def test_enabled_by_default(self, monkeypatch):
        """未设置环境变量时默认启用 FAISS。"""
        monkeypatch.delenv("USE_FAISS_INDEX", raising=False)
        from backend.services.faiss_index import FaissIndex

        FaissIndex._instance = None
        idx = FaissIndex()
        print(f"FAISS enabled: {idx.is_ready}")

    def test_validate_dimension_match(self):
        """validate 在维度匹配时返回 True。"""
        import faiss
        emb, _ = _make_dummy_embeddings(n=30, dim=128)
        index = faiss.IndexFlatIP(128)
        index.add(emb)

        from backend.services.faiss_index import FaissIndex
        FaissIndex._instance = None
        idx = FaissIndex()

        # 注入 mock index
        idx._index = index
        idx._dim = 128
        idx._ntotal = 30
        idx._enabled = True

        assert idx.validate(emb) is True

    def test_validate_dimension_mismatch_fails(self):
        """validate 在维度不匹配时返回 False。"""
        import faiss
        emb, _ = _make_dummy_embeddings(n=30, dim=128)
        other_emb = np.random.randn(20, 64).astype(np.float32)
        other_emb = other_emb / np.linalg.norm(other_emb, axis=1, keepdims=True)

        index = faiss.IndexFlatIP(128)
        index.add(emb)

        from backend.services.faiss_index import FaissIndex
        FaissIndex._instance = None
        idx = FaissIndex()
        idx._index = index
        idx._dim = 128
        idx._ntotal = 30
        idx._enabled = True

        assert idx.validate(other_emb) is False

    def test_validate_count_mismatch_fails(self):
        """validate 在向量数量不匹配时返回 False。"""
        import faiss
        emb, _ = _make_dummy_embeddings(n=30, dim=128)
        other_emb, _ = _make_dummy_embeddings(n=50, dim=128)

        index = faiss.IndexFlatIP(128)
        index.add(emb)

        from backend.services.faiss_index import FaissIndex
        FaissIndex._instance = None
        idx = FaissIndex()
        idx._index = index
        idx._dim = 128
        idx._ntotal = 30
        idx._enabled = True

        assert idx.validate(other_emb) is False

    def test_search_works(self):
        """search 能返回正确数量的结果。"""
        import faiss
        emb, _ = _make_dummy_embeddings(n=30, dim=128)
        index = faiss.IndexFlatIP(128)
        index.add(emb)

        from backend.services.faiss_index import FaissIndex
        FaissIndex._instance = None
        idx = FaissIndex()
        idx._index = index
        idx._dim = 128
        idx._ntotal = 30
        idx._enabled = True

        query = emb[0]
        movie_ids = [str(1000000 + i) for i in range(30)]
        titles = [f"测试电影_{i}" for i in range(30)]

        result = idx.search(query, 5, emb, movie_ids, titles)
        assert result is not None
        assert len(result) == 5
        assert result[0][0] == movie_ids[0]  # query is emb[0], so self should be top-1
        assert abs(result[0][2] - 1.0) < 1e-4  # self-similarity ~= 1.0

    def test_search_returns_none_when_not_ready(self):
        """FAISS 未就绪时 search 返回 None。"""
        emb, _ = _make_dummy_embeddings(n=30, dim=128)
        from backend.services.faiss_index import FaissIndex

        FaissIndex._instance = None
        idx = FaissIndex()
        result = idx.search(np.zeros(128), 5, emb, [], [])
        assert result is None

    def test_search_returns_none_on_dim_mismatch(self):
        """维度不匹配时 search 返回 None。"""
        import faiss
        emb, _ = _make_dummy_embeddings(n=30, dim=128)
        idx_faiss = faiss.IndexFlatIP(128)
        idx_faiss.add(emb)

        from backend.services.faiss_index import FaissIndex
        FaissIndex._instance = None
        fi = FaissIndex()
        fi._index = idx_faiss
        fi._dim = 128
        fi._ntotal = 30
        fi._enabled = True

        other_emb, _ = _make_dummy_embeddings(n=30, dim=64)
        result = fi.search(np.zeros(128), 5, other_emb, [], [])
        assert result is None


# ── SemanticSearch FAISS fallback 测试 ────────────────


class TestSemanticSearchFallback:
    """SemanticSearchService 的 FAISS 降级行为。"""

    def test_faiss_not_available_does_not_block_service(self):
        """embedding 存在时，即使 FAISS 不可用，SemanticSearchService 也能正常初始化。"""
        from backend.services.semantic_search import SemanticSearchService
        SemanticSearchService._instance = None
        svc = SemanticSearchService()
        assert svc.is_ready() is True

    @patch("backend.services.semantic_search.SemanticSearchService._encode_query")
    def test_fallback_to_npdot_when_faiss_disabled(self, mock_encode, monkeypatch):
        """USE_FAISS_INDEX=false 时走 np.dot fallback。"""
        monkeypatch.setenv("USE_FAISS_INDEX", "false")
        from backend.services.semantic_search import SemanticSearchService

        SemanticSearchService._instance = None
        svc = SemanticSearchService()

        if not svc.is_ready():
            pytest.skip("向量文件未就绪")

        mock_encode.return_value = svc._embeddings[0].copy()
        results = svc.search("测试查询", top_n=5)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_faiss_import_error_does_not_crash(self, monkeypatch):
        """FAISS import 失败时不影响服务启动和检索。"""
        import builtins
        orig_import = builtins.__import__

        def block_faiss(name, *args, **kwargs):
            if name == "faiss" or name.startswith("faiss."):
                raise ImportError("模拟 faiss 未安装")
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=block_faiss):
            from backend.services.semantic_search import SemanticSearchService
            SemanticSearchService._instance = None
            svc = SemanticSearchService()

            if svc.is_ready() and svc._embeddings is not None:
                query_vec = svc._embeddings[0].copy()
                with patch.object(svc, "_encode_query", return_value=query_vec):
                    results = svc.search("测试", top_n=5)
                    assert isinstance(results, list)

    def test_result_structure_is_consistent(self):
        """返回结构始终为 (movie_id, title, similarity_score)。"""
        from backend.services.semantic_search import SemanticSearchService
        SemanticSearchService._instance = None
        svc = SemanticSearchService()

        if not svc.is_ready():
            pytest.skip("向量文件未就绪")

        query_vec = svc._embeddings[0].copy()
        with patch.object(svc, "_encode_query", return_value=query_vec):
            results = svc.search("测试", top_n=5)
        for item in results:
            assert len(item) == 3
            assert isinstance(item[0], str)
            assert isinstance(item[1], str)
            assert isinstance(item[2], float)


# ── RAGService FAISS fallback 测试 ────────────────────


class TestRAGServiceFallback:
    """RAGService 的 FAISS 降级行为。"""

    def test_faiss_not_available_does_not_block_service(self):
        """embedding 存在时，即使 FAISS 不可用，RAGService 也能正常初始化。"""
        from backend.services.rag_service import RAGService
        RAGService._instance = None
        svc = RAGService()
        assert svc.is_ready() is True

    @patch("backend.services.rag_service.RAGService._encode_query")
    def test_retrieve_fallback_when_faiss_disabled(self, mock_encode, monkeypatch):
        """USE_FAISS_INDEX=false 时走 np.dot fallback。"""
        monkeypatch.setenv("USE_FAISS_INDEX", "false")
        from backend.services.rag_service import RAGService

        RAGService._instance = None
        svc = RAGService()

        if not svc.is_ready():
            pytest.skip("向量文件未就绪")

        mock_encode.return_value = svc._embeddings[0].copy()
        results = svc.retrieve("测试查询", top_k=5)
        assert isinstance(results, list)
        assert len(results) > 0
        assert "movie_id" in results[0]
        assert "title" in results[0]
        assert "similarity" in results[0]

    def test_retrieve_result_structure(self):
        """返回结构包含 movie_id, title, rating, year, genres, similarity。"""
        from backend.services.rag_service import RAGService
        RAGService._instance = None
        svc = RAGService()

        if not svc.is_ready():
            pytest.skip("向量文件未就绪")

        query_vec = svc._embeddings[0].copy()
        with patch.object(svc, "_encode_query", return_value=query_vec):
            results = svc.retrieve("测试", top_k=5)

        for item in results:
            for key in ("movie_id", "title", "rating", "year", "genres", "similarity"):
                assert key in item


# ── API 端到端测试 ────────────────────────────────────


class TestAPIWithFAISS:
    """API 层与 FAISS 集成测试。"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.app import app
        return TestClient(app)

    def test_stats_endpoint(self, client):
        """GET /api/stats 仍然正常。"""
        resp = client.get("/api/stats")
        assert resp.status_code == 200

    def test_movies_endpoint(self, client):
        """GET /api/movies 仍然正常。"""
        resp = client.get("/api/movies?page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_recommend_by_movie(self, client):
        """GET /api/recommend/similar/{movie_id} 仍然正常。"""
        resp = client.get("/api/recommend/similar/1292052?top_n=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data.get("movies"), list)

    def test_recommend_by_text(self, client):
        """POST /api/recommend/search 仍然正常。"""
        resp = client.post("/api/recommend/search", json={
            "query": "科幻冒险电影",
            "top_n": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data.get("movies"), list)
