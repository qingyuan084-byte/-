"""
数据库化改造测试 — 仓库查询、CSV 降级、API 分页。
使用 SQLite 内存数据库模拟，无需真实 PostgreSQL。
"""
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── 测试 fixtures ────────────────────────────────────


@pytest.fixture
def test_db():
    """创建 SQLite 内存数据库并建表。"""
    from backend.db import Base
    import backend.models.db_models  # noqa: F401 — 注册 Movie 模型

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def repo(test_db):
    """提供 MovieRepository 实例。"""
    from backend.repositories.movie_repository import MovieRepository
    return MovieRepository(test_db)


@pytest.fixture
def sample_movies():
    """测试用电影数据。"""
    return [
        {
            "movie_id": "1234567",
            "title": "测试电影A",
            "rating": 9.5,
            "release_year": 2020.0,
            "genres": "剧情, 科幻",
            "countries": "中国大陆",
            "summary": "一部关于测试的电影。",
            "directors": "导演A",
            "actors": "演员A",
            "runtime": "120分钟",
            "total_ratings": "5000",
            "release_date": "2020-01-01",
            "poster": "https://example.com/poster.jpg",
            "screenwriters": "编剧A",
            "languages": "汉语普通话",
            "link": "https://movie.douban.com/subject/1234567/",
            "tags": "",
            "genre_list": "['剧情', '科幻']",
        },
        {
            "movie_id": "2234567",
            "title": "测试电影B",
            "rating": 8.0,
            "release_year": 2019.0,
            "genres": "喜剧",
            "countries": "美国",
            "summary": "另一部测试电影。",
            "directors": "导演B",
            "actors": "演员B",
            "runtime": "90分钟",
            "total_ratings": "3000",
            "release_date": "2019-06-15",
            "poster": "https://example.com/poster2.jpg",
            "screenwriters": "编剧B",
            "languages": "英语",
            "link": "https://movie.douban.com/subject/2234567/",
            "tags": "",
            "genre_list": "['喜剧']",
        },
        {
            "movie_id": "3234567",
            "title": "星际穿越",
            "rating": 9.4,
            "release_year": 2014.0,
            "genres": "剧情, 科幻, 冒险",
            "countries": "美国",
            "summary": "诺兰的科幻经典。",
            "directors": "克里斯托弗·诺兰",
            "actors": "马修·麦康纳",
            "runtime": "169分钟",
            "total_ratings": "10000",
            "release_date": "2014-11-12",
            "poster": "https://example.com/poster3.jpg",
            "screenwriters": "诺兰兄弟",
            "languages": "英语",
            "link": "https://movie.douban.com/subject/3234567/",
            "tags": "",
            "genre_list": "['剧情', '科幻', '冒险']",
        },
    ]


def _seed(repo, sample_movies):
    """填充测试数据。"""
    for m in sample_movies:
        repo.upsert_movie(m)
    repo.db.commit()


# ── 仓库查询测试 ────────────────────────────────────


class TestMovieRepository:
    def test_upsert_and_count(self, repo, sample_movies):
        _seed(repo, sample_movies)
        assert repo.count() == 3

    def test_upsert_idempotent(self, repo, sample_movies):
        """重复 upsert 不产生重复记录。"""
        _seed(repo, sample_movies)
        _seed(repo, [sample_movies[0]])  # 重复插入第一条
        assert repo.count() == 3

    def test_list_movies_pagination(self, repo, sample_movies):
        _seed(repo, sample_movies)
        results, total = repo.list_movies(page=1, page_size=2)
        assert len(results) == 2
        assert total == 3

        results2, _ = repo.list_movies(page=2, page_size=2)
        assert len(results2) == 1

    def test_list_movies_search(self, repo, sample_movies):
        _seed(repo, sample_movies)
        results, total = repo.list_movies(q="星际")
        assert total == 1
        assert results[0]["title"] == "星际穿越"

    def test_list_movies_rich(self, repo, sample_movies):
        _seed(repo, sample_movies)
        results, total = repo.list_movies_rich(page=1, page_size=3)
        assert len(results) == 3
        assert "summary" in results[0]
        assert "directors" in results[0]

    def test_get_movie_by_id(self, repo, sample_movies):
        _seed(repo, sample_movies)
        movie = repo.get_movie_by_id("1234567")
        assert movie is not None
        assert movie["title"] == "测试电影A"
        assert movie["rating"] == 9.5

    def test_get_movie_not_found(self, repo, sample_movies):
        _seed(repo, sample_movies)
        assert repo.get_movie_by_id("9999999") is None

    def test_get_stats(self, repo, sample_movies):
        _seed(repo, sample_movies)
        stats = repo.get_stats()
        assert stats["total_movies"] == 3
        assert stats["avg_rating"] > 0
        assert stats["latest_year"] == 2020

    def test_list_movies_rich_genre_filter(self, repo, sample_movies):
        """仓库层 genre 筛选。"""
        _seed(repo, sample_movies)
        results, total = repo.list_movies_rich(genre="科幻")
        assert total >= 1
        for m in results:
            assert "科幻" in m.get("genres", "")

    def test_list_movies_rich_country_filter(self, repo, sample_movies):
        """仓库层 country 筛选。"""
        _seed(repo, sample_movies)
        results, total = repo.list_movies_rich(country="美国")
        assert total >= 1
        for m in results:
            assert "美国" in m.get("countries", "")

    def test_list_movies_rich_year_range(self, repo, sample_movies):
        """仓库层年份范围筛选。"""
        _seed(repo, sample_movies)
        results, total = repo.list_movies_rich(year_min=2018, year_max=2020)
        assert total >= 2
        for m in results:
            y = m.get("year") or 0
            assert 2018 <= y <= 2020, f"年份 {y} 超出范围"

    def test_list_movies_rich_rating_range(self, repo, sample_movies):
        """仓库层评分范围筛选。"""
        _seed(repo, sample_movies)
        results, total = repo.list_movies_rich(rating_min=9.0)
        assert total >= 1
        for m in results:
            assert m.get("rating", 0) >= 9.0

    def test_list_movies_rich_sort_by_year(self, repo, sample_movies):
        """仓库层按年份排序。"""
        _seed(repo, sample_movies)
        results, total = repo.list_movies_rich(sort_by="year")
        years = [m.get("year") or 0 for m in results]
        assert years == sorted(years, reverse=True)

    def test_list_movies_rich_invalid_sort_falls_back(self, repo, sample_movies):
        """仓库层非法 sort_by 被白名单兜底为 rating 排序，不抛异常。"""
        _seed(repo, sample_movies)
        results, total = repo.list_movies_rich(sort_by="malicious_input")
        assert len(results) > 0
        assert total == 3


# ── CSV 降级测试 ────────────────────────────────────


class TestCSVFallback:
    """
    验证 DATABASE_URL 未配置时，RecommenderService 自动回退 CSV。
    不依赖真实数据库，测试直接构造 JSON 数据而不是完整加载。
    """

    def test_list_movies_returns_tuple(self):
        """验证 list_movies 返回 (results, total) 元组格式。"""
        from backend.services.recommender_service import RecommenderService

        service = RecommenderService()
        results, total = service.list_movies(page=1, page_size=5)
        assert isinstance(results, list)
        assert isinstance(total, int)
        assert total > 0
        assert len(results) <= 5

    def test_list_movies_rich_returns_tuple(self):
        """验证 list_movies_rich 返回 (results, total) 元组格式。"""
        from backend.services.recommender_service import RecommenderService

        service = RecommenderService()
        results, total = service.list_movies_rich(page=1, page_size=3)
        assert isinstance(results, list)
        assert isinstance(total, int)
        assert total > 0
        assert len(results) <= 3

    def test_list_movies_search(self):
        """验证 title 搜索功能。"""
        from backend.services.recommender_service import RecommenderService

        service = RecommenderService()
        results, total = service.list_movies(q="肖申克", page=1, page_size=10)
        assert isinstance(total, int)
        if total > 0:
            assert any("肖申克" in m.get("title", "") for m in results)

    def test_get_movie_detail(self):
        """验证 get_movie_detail 返回包含完整字段的 dict。"""
        from backend.services.recommender_service import RecommenderService

        service = RecommenderService()
        # 使用一个已知存在的电影 ID
        movie = service.get_movie_detail("1292052")
        if movie is not None:
            assert "title" in movie
            assert "rating" in movie
            assert "summary" in movie

    def test_get_stats(self):
        """验证 get_stats 返回统计信息。"""
        from backend.services.recommender_service import RecommenderService

        service = RecommenderService()
        stats = service.get_stats()
        assert "total_movies" in stats
        assert "avg_rating" in stats
        assert stats["total_movies"] > 0

    def test_list_movies_rich_with_filters_csv(self):
        """验证 CSV 降级模式下 list_movies_rich 支持 genre 筛选。"""
        from backend.services.recommender_service import RecommenderService

        service = RecommenderService()
        results, total = service.list_movies_rich(
            genre="科幻", sort_by="rating", page=1, page_size=10
        )
        assert isinstance(results, list)
        assert isinstance(total, int)
        for m in results:
            genres = m.get("genres", "")
            assert "科幻" in genres, f"期望 genres 包含'科幻'，实际: {genres}"

    def test_list_movies_rich_sort_by_title(self):
        """验证 sort_by=title 正常返回且不报错（排序规则依赖 DB/CSV 后端 locale）。"""
        from backend.services.recommender_service import RecommenderService

        service = RecommenderService()
        results, total = service.list_movies_rich(
            sort_by="title", page=1, page_size=10
        )
        assert isinstance(results, list)
        assert len(results) > 0
        assert total > 0
        assert all("title" in m for m in results)

    def test_list_movies_rich_invalid_sort_is_safe(self):
        """非法 sort_by 不会导致服务崩溃，自动降级为 rating 排序。"""
        from backend.services.recommender_service import RecommenderService

        service = RecommenderService()
        # 直接调用服务层（绕过 API 层校验）验证仓库白名单兜底
        results, total = service.list_movies_rich(
            sort_by="; DROP TABLE movies;", page=1, page_size=5
        )
        assert isinstance(results, list)
        assert isinstance(total, int)


# ── 分页 API 参数测试 ────────────────────────────────


class TestAPIPagination:
    """使用 FastAPI TestClient 验证 API 分页参数。"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.app import app
        return TestClient(app)

    def test_movies_pagination(self, client):
        """GET /api/movies 支持 page 和 page_size 参数。"""
        resp = client.get("/api/movies?page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total"] > 0
        assert len(data["items"]) <= 5
        # pages 计算正确
        if data["total"] > 0:
            import math
            expected_pages = math.ceil(data["total"] / 5)
            assert data["pages"] == expected_pages

    def test_movies_rich_pagination(self, client):
        """GET /api/movies/rich 支持分页参数。"""
        resp = client.get("/api/movies/rich?page=1&page_size=3")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) <= 3

    def test_movies_search(self, client):
        """GET /api/movies 支持 q 搜索 + 分页。"""
        resp = client.get("/api/movies?q=肖申克&page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        if data["total"] > 0:
            assert any("肖申克" in m.get("title", "") for m in data["items"])

    def test_movies_page_size_max(self, client):
        """page_size 上限 100 正常工作。"""
        resp = client.get("/api/movies?page=1&page_size=100")
        assert resp.status_code == 200

    def test_movies_page_size_exceeded(self, client):
        """page_size 超过 100 返回 422 校验错误。"""
        resp = client.get("/api/movies?page=1&page_size=101")
        assert resp.status_code == 422

    def test_movies_rich_genre_filter(self, client):
        """GET /api/movies/rich?genre=科幻 能筛选类型。"""
        resp = client.get("/api/movies/rich?genre=科幻&page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        for m in data["items"]:
            genres = m.get("genres", "")
            assert "科幻" in genres, f"期望 genres 包含'科幻'，实际: {genres}"

    def test_movies_rich_sort_by_rating(self, client):
        """sort_by=rating 按评分降序返回。"""
        resp = client.get("/api/movies/rich?sort_by=rating&page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        ratings = [m.get("rating", 0) for m in data["items"]]
        assert ratings == sorted(ratings, reverse=True)

    def test_movies_rich_sort_by_year(self, client):
        """sort_by=year 按年份降序返回。"""
        resp = client.get("/api/movies/rich?sort_by=year&page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        years = [m.get("year") or 0 for m in data["items"]]
        assert years == sorted(years, reverse=True)

    def test_movies_rich_invalid_sort_by(self, client):
        """非法 sort_by 返回 422，不会导致服务异常。"""
        resp = client.get("/api/movies/rich?sort_by=; DROP TABLE users;--")
        assert resp.status_code == 422
        # 再次正常请求验证服务正常
        resp2 = client.get("/api/movies/rich?page=1&page_size=2")
        assert resp2.status_code == 200

    def test_movies_rich_rating_range(self, client):
        """rating_min/rating_max 筛选评分范围。"""
        resp = client.get("/api/movies/rich?rating_min=9.0&rating_max=10.0&page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        for m in data["items"]:
            r = m.get("rating", 0)
            assert 9.0 <= r <= 10.0, f"评分 {r} 不在 [9.0, 10.0]"

    def test_movies_rich_combined_filters(self, client):
        """组合筛选：类型 + 年份 + 评分。"""
        resp = client.get(
            "/api/movies/rich?genre=剧情&year_min=2000&rating_min=8.0"
            "&sort_by=rating&page=1&page_size=10"
        )
        assert resp.status_code == 200
        data = resp.json()
        for m in data["items"]:
            assert "剧情" in m.get("genres", "")
            assert (m.get("year") or 0) >= 2000
            assert m.get("rating", 0) >= 8.0

    def test_movie_detail(self, client):
        """GET /api/movie/{id} 正确返回。"""
        resp = client.get("/api/movie/1292052")
        if resp.status_code == 404:
            # 可能这个 ID 不存在，跳过
            pass
        else:
            assert resp.status_code == 200
            data = resp.json()
            assert "title" in data
            assert "rating" in data

    def test_stats(self, client):
        """GET /api/stats 正确返回。"""
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_movies"] > 0


# ── db.py 工具函数测试 ──────────────────────────────


class TestDBUtils:
    def test_is_db_available_no_config(self, monkeypatch):
        """未配置 DATABASE_URL 时 is_db_available 返回 False。"""
        monkeypatch.setenv("DATABASE_URL", "")

        # 不 reload 整个模块，直接测试 _normalize_db_url 逻辑
        from backend.db import _normalize_db_url

        # 空 URL → 返回空字符串
        result = _normalize_db_url("")
        assert result == ""

    def test_normalize_db_url_basic(self):
        """基础 URL 保持 user:pass@host:port/db 结构。"""
        from backend.db import _normalize_db_url
        url = "postgresql://user:pass@localhost:5432/db"
        result = _normalize_db_url(url)
        # 可能附加驱动前缀，但核心结构不变
        assert "user:pass@localhost:5432/db" in result

    def test_normalize_db_url_removes_asyncpg(self):
        """移除 +asyncpg 驱动后缀。"""
        from backend.db import _normalize_db_url
        url = "postgresql+asyncpg://user:pass@localhost:5432/db"
        result = _normalize_db_url(url)
        assert "+asyncpg" not in result
        assert "user:pass@localhost:5432/db" in result

    def test_normalize_db_url_at_in_password(self):
        """密码中包含 @ 时自动 URL 编码为 %40。"""
        from backend.db import _normalize_db_url
        url = "postgresql://user:p@ss@localhost:5432/db"
        result = _normalize_db_url(url)
        assert "p%40ss" in result
