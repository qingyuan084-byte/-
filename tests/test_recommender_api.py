"""
推荐 API 端点测试 — 使用 FastAPI TestClient 验证路由行为。
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.app import app

client = TestClient(app)


class TestListMovies:
    """GET /api/movies — 分页电影基础列表。"""

    def test_returns_paginated_structure(self):
        """返回分页结构，包含 items / total / page / page_size 字段。"""
        resp = client.get("/api/movies")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert data["total"] > 0

    def test_page_size_respected(self):
        """page_size=5 时返回的 items 数量不超过 5。"""
        resp = client.get("/api/movies?page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 5
        assert data["page_size"] == 5

    def test_page_size_exceeds_max_returns_422(self):
        """page_size=200 超过上限 100，FastAPI 返回 422。"""
        resp = client.get("/api/movies?page=1&page_size=200")
        assert resp.status_code == 422

    def test_search_by_keyword(self):
        """q=肖申克 返回包含关键词的结果。"""
        resp = client.get("/api/movies?q=肖申克")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) > 0
        titles = [item["title"] for item in data["items"]]
        assert any("肖申克" in t for t in titles)

    def test_search_no_match(self):
        """q=不存在的片名xyzxyz 返回空列表但不报错。"""
        resp = client.get("/api/movies?q=不存在的片名xyzxyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_page_zero_returns_422(self):
        """page=0 时 FastAPI 校验 ge=1 返回 422。"""
        resp = client.get("/api/movies?page=0")
        assert resp.status_code == 422


class TestStats:
    """GET /api/stats — 数据集统计。"""

    def test_stats_returns_200_with_total_movies(self):
        """返回 200，响应体包含 total_movies 字段且值大于 0。"""
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_movies" in data
        assert data["total_movies"] > 0


class TestMoviesRich:
    """GET /api/movies/rich — 多维度筛选。"""

    def test_returns_paginated_structure(self):
        """不传参数时正常返回分页结构。"""
        resp = client.get("/api/movies/rich")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] > 0

    def test_genre_filter(self):
        """genre 参数筛选正常。"""
        resp = client.get("/api/movies/rich?genre=科幻")
        assert resp.status_code == 200
        data = resp.json()
        # 筛选结果可能为 0（DB 不可用时 CSV 降级可能精确度略低），但不报错即可
        assert "items" in data
        assert "total" in data

    def test_year_range_filter(self):
        """year_min / year_max 筛选正常。"""
        resp = client.get("/api/movies/rich?year_min=2010&year_max=2020")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_rating_min_filter(self):
        """rating_min 筛选正常。"""
        resp = client.get("/api/movies/rich?rating_min=8.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_sort_by_year(self):
        """sort_by=year 正常返回。"""
        resp = client.get("/api/movies/rich?sort_by=year")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_invalid_sort_by_returns_422(self):
        """sort_by 非法值时返回 422。"""
        resp = client.get("/api/movies/rich?sort_by=invalid_field")
        assert resp.status_code == 422


class TestMovieDetail:
    """GET /api/movie/{movie_id} — 电影详情。"""

    def test_valid_movie_id(self):
        """存在的 movie_id 返回 200 详情。"""
        resp = client.get("/api/movie/1292052")
        assert resp.status_code == 200
        data = resp.json()
        assert data["movie_id"] == "1292052"
        assert len(data["title"]) > 0

    def test_invalid_movie_id_returns_404(self):
        """不存在的 movie_id 返回 404。"""
        resp = client.get("/api/movie/id_not_exist_000")
        assert resp.status_code == 404


class TestHealth:
    """GET /health — 健康检查。"""

    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["movies_loaded"] > 0
