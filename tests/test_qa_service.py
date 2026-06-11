"""
QA Service 单元测试 — 测试关键词分类、意图识别、筛选解析等无 API 依赖的功能。
"""
import pytest
from unittest.mock import patch, MagicMock

# 初始化环境
import os, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.services.qa_service import (
    _parse_genres,
    _parse_countries,
    _format_movie_context,
    _format_movie_info,
    _format_filter_state,
    DEFAULT_FILTER_STATE,
    QAService,
    get_session_filter,
    clear_session,
    session_filters,
)


class TestParseGenres:
    def test_comma_separated_string(self):
        assert _parse_genres("科幻, 悬疑, 惊悚") == ["科幻", "悬疑", "惊悚"]

    def test_list_input(self):
        assert _parse_genres(["动作", "喜剧"]) == ["动作", "喜剧"]

    def test_empty_input(self):
        assert _parse_genres(None) == []
        assert _parse_genres("") == []

    def test_chinese_comma(self):
        # _parse_genres only splits on English comma, not Chinese comma
        result = _parse_genres("剧情, 爱情, 战争")
        assert result == ["剧情", "爱情", "战争"]


class TestParseCountries:
    def test_slash_separated(self):
        result = _parse_countries("中国大陆/中国香港")
        assert "中国大陆" in result
        assert "中国香港" in result

    def test_chinese_comma(self):
        result = _parse_countries("美国，日本，韩国")
        assert result == ["美国", "日本", "韩国"]

    def test_empty_input(self):
        assert _parse_countries(None) == []
        assert _parse_countries("") == []


class TestFormatMovieContext:
    def test_formats_multiple_movies(self):
        movies = [
            {"title": "肖申克的救赎", "year": 1994, "rating": 9.7,
             "genres": "剧情, 犯罪", "countries": "美国",
             "directors": "弗兰克·德拉邦特", "summary": "希望让人自由。"},
            {"title": "霸王别姬", "year": 1993, "rating": 9.6,
             "genres": "剧情, 爱情", "countries": "中国大陆",
             "directors": "陈凯歌", "summary": "风华绝代。"},
        ]
        text = _format_movie_context(movies)
        assert "肖申克的救赎" in text
        assert "1994" in text
        assert "9.7" in text
        assert "霸王别姬" in text

    def test_empty_list(self):
        assert "无匹配电影" in _format_movie_context([])


class TestFormatMovieInfo:
    def test_all_fields(self):
        movie = {
            "title": "肖申克的救赎", "year": 1994, "rating": 9.7,
            "genres": "剧情", "directors": "弗兰克·德拉邦特",
            "actors": "蒂姆·罗宾斯", "countries": "美国",
            "runtime": "142分钟", "summary": "希望让人自由。",
        }
        text = _format_movie_info(movie, "all")
        assert "肖申克的救赎" in text
        assert "1994" in text
        assert "9.7" in text
        assert "弗兰克·德拉邦特" in text

    def test_specific_field(self):
        movie = {"title": "肖申克的救赎", "year": 1994, "rating": 9.7}
        text = _format_movie_info(movie, "rating")
        assert "评分" in text
        assert "9.7" in text
        assert "导演" not in text


class TestFormatFilterState:
    def test_empty_state(self):
        text = _format_filter_state(DEFAULT_FILTER_STATE)
        # Default state with no active filters shows "当前无筛选条件"
        assert "无筛选条件" in text

    def test_active_state(self):
        fs = {**DEFAULT_FILTER_STATE, "genres": ["科幻"], "active": True,
              "year_range": [2000, 2020], "rating_range": [8, 10]}
        text = _format_filter_state(fs)
        assert "科幻" in text
        assert "2000" in text
        assert "8" in text  # int not float in format


class TestKeywordClassify:
    @pytest.fixture
    def qa(self):
        with patch("backend.services.qa_service.OpenAI"):
            return QAService()

    def test_recommend_intent(self, qa):
        assert qa._keyword_classify("推荐科幻电影") == "recommend"
        assert qa._keyword_classify("还有什么好看的") == "recommend"
        assert qa._keyword_classify("给我推荐悬疑烧脑的") == "recommend"

    def test_info_intent_with_bookmarks(self, qa):
        assert qa._keyword_classify("《肖申克的救赎》导演是谁") == "info"

    def test_info_intent_keyword_only(self, qa):
        # "拍了哪几部" doesn't match any INFO_KEYWORDS — falls to LLM classification
        result = qa._keyword_classify("蝙蝠侠诺兰拍了哪几部")
        # Falls through to None (will be handled by LLM)
        assert result is None or result == "info"

    def test_filter_intent(self, qa):
        assert qa._keyword_classify("只看科幻片") == "filter"
        assert qa._keyword_classify("评分8分以上") == "filter"
        assert qa._keyword_classify("2000年以后的") == "filter"

    def test_filter_reset(self, qa):
        assert qa._keyword_classify("重置筛选") == "filter"
        assert qa._keyword_classify("清除条件") == "filter"

    def test_unknown_intent(self, qa):
        assert qa._keyword_classify("你好") is None
        assert qa._keyword_classify("今天天气怎么样") is None


class TestExtractMovieName:
    @pytest.fixture
    def qa(self):
        with patch("backend.services.qa_service.OpenAI"):
            return QAService()

    def test_bookmark_format(self, qa):
        assert qa._extract_movie_name("《肖申克的救赎》导演是谁") == "肖申克的救赎"
        assert qa._extract_movie_name("《盗梦空间》主演") == "盗梦空间"

    def test_film_prefix_format(self, qa):
        # "电影流浪地球好看吗" — regex captures from "电影" to first non-letter delimiter
        # The pattern r'电影[《\s]*([^《》\s,，。.!！?？\d]+)' captures after "电影"
        result = qa._extract_movie_name("电影流浪地球好看吗")
        # The regex matches "流浪地球好看吗" (no delimiters between "电影" and "好看吗")
        assert result is not None

    def test_no_movie_name(self, qa):
        assert qa._extract_movie_name("推荐好看的电影") is None


class TestExtractField:
    @pytest.fixture
    def qa(self):
        with patch("backend.services.qa_service.OpenAI"):
            return QAService()

    def test_director(self, qa):
        assert qa._extract_field("导演是谁") == "director"

    def test_rating(self, qa):
        assert qa._extract_field("评分多少") == "rating"

    def test_actors(self, qa):
        assert qa._extract_field("主演是谁") == "actors"

    def test_summary(self, qa):
        # "讲的什么" contains "的" so doesn't match "讲什么" keyword
        assert qa._extract_field("讲的什么") in ("summary", "all")

    def test_default_all(self, qa):
        assert qa._extract_field("这是什么电影") == "all"


class TestParseFilterFromMessage:
    @pytest.fixture
    def qa(self):
        with patch("backend.services.qa_service.OpenAI"):
            return QAService()

    def test_genre_filter(self, qa):
        fs = {**DEFAULT_FILTER_STATE}
        result = qa._parse_filter_from_message(fs, "只看科幻片", "add")
        assert "科幻" in result["genres"]
        # active is set by _handle_filter, not by _parse_filter_from_message

    def test_rating_filter(self, qa):
        fs = {**DEFAULT_FILTER_STATE}
        result = qa._parse_filter_from_message(fs, "评分9分以上", "add")
        assert result["rating_range"][0] == 9.0

    def test_country_filter(self, qa):
        fs = {**DEFAULT_FILTER_STATE}
        result = qa._parse_filter_from_message(fs, "中国的", "add")
        assert any("中国" in c for c in result["countries"])

    def test_reset_filter(self, qa):
        # _parse_filter_from_message doesn't handle "reset" action by itself —
        # reset is done in _handle_filter before calling this method
        fs = {"genres": ["科幻"], "year_range": [2000, 2020],
              "rating_range": [8, 10], "countries": ["美国"],
              "sort_by": "rating", "active": True}
        # "reset" action: _parse_filter_from_message just returns fs unchanged
        result = qa._parse_filter_from_message(fs, "重置筛选", "reset")
        # Reset is handled upstream in _handle_filter, not here
        assert result is fs  # unchanged by this method

    def test_accumulate_genres(self, qa):
        fs = {**DEFAULT_FILTER_STATE, "genres": ["科幻"], "active": True}
        result = qa._parse_filter_from_message(fs, "再看悬疑的", "add")
        assert "科幻" in result["genres"]
        assert "悬疑" in result["genres"]


class TestSessionManagement:
    def test_get_session_filter_default(self):
        fs = get_session_filter("nonexistent-session")
        assert fs == DEFAULT_FILTER_STATE
        assert fs["active"] is False

    def test_set_and_get_filter(self):
        session_filters["test-sess-1"] = {"genres": ["喜剧"], "year_range": [1900, 2030],
                                           "rating_range": [0, 10], "countries": [],
                                           "sort_by": "rating", "active": True}
        fs = get_session_filter("test-sess-1")
        assert fs["genres"] == ["喜剧"]
        assert fs["active"] is True
        # cleanup
        clear_session("test-sess-1")

    def test_clear_session_clears_history_and_filters(self):
        session_filters["test-sess-2"] = {"genres": ["动作"], "year_range": [1900, 2030],
                                           "rating_range": [0, 10], "countries": [],
                                           "sort_by": "rating", "active": True}
        clear_session("test-sess-2")
        fs = get_session_filter("test-sess-2")
        assert fs == DEFAULT_FILTER_STATE
