"""
MovieRepository 单元测试 — 使用 SQLite 内存数据库，无需真实 PostgreSQL。
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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


_SEED_FIXTURES = [
    {
        "movie_id": "1234567",
        "title": "测试电影A - 科幻巨制",
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
        "title": "测试电影B - 喜剧之王",
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
        "title": "测试电影C - 星际穿越",
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


def _seed(repo, movies):
    for m in movies:
        repo.upsert_movie(m)
    repo.db.commit()


class TestMovieRepository:
    """MovieRepository 核心方法测试。"""

    def test_list_movies_returns_nonempty(self, repo):
        """list_movies(q="", ...) 返回非空列表。"""
        _seed(repo, _SEED_FIXTURES)
        results, total = repo.list_movies(q="", page=1, page_size=10)
        assert isinstance(results, list)
        assert len(results) > 0
        assert total >= 3

    def test_list_movies_no_match_returns_empty(self, repo):
        """list_movies(q="不存在的片名xyzxyz") 返回空列表。"""
        _seed(repo, _SEED_FIXTURES)
        results, total = repo.list_movies(q="不存在的片名xyzxyz", page=1, page_size=10)
        assert results == []
        assert total == 0

    def test_get_movie_by_id_returns_correct_object(self, repo):
        """get_movie_by_id(真实存在的movie_id) 返回正确电影对象，字段不为空。"""
        _seed(repo, _SEED_FIXTURES)
        movie = repo.get_movie_by_id("1234567")
        assert movie is not None
        assert movie["movie_id"] == "1234567"
        assert movie["title"] == "测试电影A - 科幻巨制"
        assert movie["rating"] == 9.5
        assert len(movie["title"]) > 0
        assert len(movie.get("directors", "")) > 0

    def test_get_movie_by_id_not_found_returns_none(self, repo):
        """get_movie_by_id("id_not_exist_000") 返回 None。"""
        _seed(repo, _SEED_FIXTURES)
        result = repo.get_movie_by_id("id_not_exist_000")
        assert result is None

    def test_get_stats_has_total_movies(self, repo):
        """get_stats() 返回包含 total_movies 字段的字典，值大于 0。"""
        _seed(repo, _SEED_FIXTURES)
        stats = repo.get_stats()
        assert "total_movies" in stats
        assert stats["total_movies"] >= 3
        assert stats["total_movies"] > 0
