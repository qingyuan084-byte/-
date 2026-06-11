"""
Redis 缓存层测试 — 连接降级、序列化、key 安全、推荐命中缓存。
"""
import json
import hashlib
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


# ── 模块级别测试 ────────────────────────────────────


class TestCacheKey:
    """缓存 key 构建与安全测试。"""

    def test_hash_text_is_deterministic(self):
        """hash_text 对相同输入产生相同输出。"""
        from backend.cache import hash_text
        a = hash_text("hello world")
        b = hash_text("hello world")
        assert a == b
        assert len(a) == 16
        assert all(c in "0123456789abcdef" for c in a)

    def test_hash_text_different_inputs(self):
        """不同输入产生不同 hash。"""
        from backend.cache import hash_text
        assert hash_text("foo") != hash_text("bar")

    def test_hash_text_does_not_expose_original(self):
        """hash_text 输出不包含原始文本。"""
        from backend.cache import hash_text
        query = "肖申克的救赎"
        result = hash_text(query)
        assert "肖" not in result
        assert result == hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]

    def test_build_cache_key_simple(self):
        """build_cache_key 用 : 连接各段。"""
        from backend.cache import build_cache_key
        key = build_cache_key("stats", "v1")
        assert key == "stats:v1"

    def test_build_cache_key_with_multiple_parts(self):
        """多个 part 正常拼接。"""
        from backend.cache import build_cache_key
        key = build_cache_key("similar", "1292052", "10")
        assert key == "similar:1292052:10"

    def test_build_cache_key_search_uses_hash(self):
        """搜索 key 使用 hash_text 隐藏查询原文。"""
        from backend.cache import build_cache_key, hash_text
        key = build_cache_key("search", hash_text("星际穿越"), "10")
        assert "星际" not in key
        assert key.startswith("search:")
        assert key.endswith(":10")
        assert len(key.split(":")[1]) == 16  # hash 部分 16 位

    def test_build_cache_key_skips_empty_parts(self):
        """空字符串 part 被跳过。"""
        from backend.cache import build_cache_key
        key = build_cache_key("prefix", "", "valid")
        assert key == "prefix:valid"


class TestCacheNoRedis:
    """Redis 未配置时的降级行为。"""

    def test_get_cache_returns_none_without_redis_url(self, monkeypatch):
        """REDIS_URL 未设置时 get_cache 返回 None。"""
        monkeypatch.setenv("REDIS_URL", "")
        # 强制重新加载以清除缓存状态
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        result = cache_mod.get_cache("any_key")
        assert result is None

    def test_set_cache_returns_false_without_redis_url(self, monkeypatch):
        """REDIS_URL 未设置时 set_cache 返回 False。"""
        monkeypatch.setenv("REDIS_URL", "")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        result = cache_mod.set_cache("any_key", {"data": 1})
        assert result is False

    def test_delete_cache_returns_false_without_redis_url(self, monkeypatch):
        """REDIS_URL 未设置时 delete_cache 返回 False。"""
        monkeypatch.setenv("REDIS_URL", "")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        result = cache_mod.delete_cache("any_key")
        assert result is False

    def test_clear_cache_prefix_returns_zero_without_redis_url(self, monkeypatch):
        """REDIS_URL 未设置时 clear_cache_prefix 返回 0。"""
        monkeypatch.setenv("REDIS_URL", "")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        result = cache_mod.clear_cache_prefix("stats")
        assert result == 0

    def test_flush_app_cache_returns_zero_without_redis_url(self, monkeypatch):
        """REDIS_URL 未设置时 flush_app_cache 返回 0。"""
        monkeypatch.setenv("REDIS_URL", "")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        result = cache_mod.flush_app_cache()
        assert result == 0


class TestCacheWithMockRedis:
    """使用 mock Redis 验证序列化/反序列化和缓存逻辑。"""

    @pytest.fixture
    def mock_redis_client(self):
        """提供内存级别的 mock Redis，模拟真实 get/setex/delete 行为。"""
        mock = MagicMock()
        store = {}

        def _get(key):
            return store.get(key)

        def _setex(key, ttl, value):
            store[key] = value
            return True

        def _delete(*keys):
            removed = 0
            for k in keys:
                if k in store:
                    del store[k]
                    removed += 1
            return removed

        def _scan_iter(match=None, count=100):
            import fnmatch
            for k in list(store.keys()):
                if fnmatch.fnmatch(k, match or "*"):
                    yield k

        def _ping():
            return True

        mock.get.side_effect = _get
        mock.setex.side_effect = _setex
        mock.delete.side_effect = _delete
        mock.scan_iter.side_effect = _scan_iter
        mock.ping.side_effect = _ping
        mock._store = store
        return mock

    def test_set_and_get_roundtrip(self, monkeypatch, mock_redis_client):
        """set_cache 写入后 get_cache 能正确读回。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        import backend.cache as cache_mod
        cache_mod._redis_client = mock_redis_client
        cache_mod._redis_checked = True

        data = {"movies": ["肖申克的救赎", "霸王别姬"], "count": 2}
        ok = cache_mod.set_cache("test:key", data, ttl=60)
        assert ok is True

        result = cache_mod.get_cache("test:key")
        assert result == data

    def test_set_and_get_list(self, monkeypatch, mock_redis_client):
        """list 类型也能正常序列化/反序列化。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        import backend.cache as cache_mod
        cache_mod._redis_client = mock_redis_client
        cache_mod._redis_checked = True

        data = [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]
        cache_mod.set_cache("test:list", data, ttl=60)
        result = cache_mod.get_cache("test:list")
        assert result == data

    def test_get_cache_miss(self, monkeypatch, mock_redis_client):
        """缓存未命中时 get_cache 返回 None。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        import backend.cache as cache_mod
        cache_mod._redis_client = mock_redis_client
        cache_mod._redis_checked = True

        result = cache_mod.get_cache("nonexistent")
        assert result is None

    def test_delete_cache(self, monkeypatch, mock_redis_client):
        """delete_cache 删除后 get_cache 返回 None。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        import backend.cache as cache_mod
        cache_mod._redis_client = mock_redis_client
        cache_mod._redis_checked = True

        cache_mod.set_cache("test:del", {"x": 1}, ttl=60)
        assert cache_mod.get_cache("test:del") is not None

        cache_mod.delete_cache("test:del")
        assert cache_mod.get_cache("test:del") is None

    def test_clear_cache_prefix(self, monkeypatch, mock_redis_client):
        """clear_cache_prefix 按前缀清除。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        import backend.cache as cache_mod
        cache_mod._redis_client = mock_redis_client
        cache_mod._redis_checked = True

        cache_mod.set_cache("stats:v1", {"total": 100}, ttl=60)
        cache_mod.set_cache("stats:other", {"count": 50}, ttl=60)
        cache_mod.set_cache("similar:123:10", ["a", "b"], ttl=60)

        deleted = cache_mod.clear_cache_prefix("stats")
        assert deleted == 2
        assert cache_mod.get_cache("stats:v1") is None
        assert cache_mod.get_cache("stats:other") is None
        assert cache_mod.get_cache("similar:123:10") is not None

    def test_flush_app_cache_clears_all_prefixes(self, monkeypatch, mock_redis_client):
        """flush_app_cache 清除 stats/similar/search/rich 四类前缀。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        import backend.cache as cache_mod
        cache_mod._redis_client = mock_redis_client
        cache_mod._redis_checked = True

        cache_mod.set_cache("stats:v1", {}, ttl=60)
        cache_mod.set_cache("similar:x:1", [], ttl=60)
        cache_mod.set_cache("search:abc:10", [], ttl=60)
        cache_mod.set_cache("rich:def:1", [], ttl=60)
        cache_mod.set_cache("other:key", "keep me", ttl=60)

        deleted = cache_mod.flush_app_cache()
        assert deleted == 4
        assert cache_mod.get_cache("other:key") == "keep me"

    def test_json_decode_error_is_handled(self, monkeypatch, mock_redis_client):
        """Redis 中有损坏的 JSON 数据时 get_cache 返回 None 不崩溃。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        mock_redis_client._store["bad:key"] = "{ not valid json"
        import backend.cache as cache_mod
        cache_mod._redis_client = mock_redis_client
        cache_mod._redis_checked = True

        result = cache_mod.get_cache("bad:key")
        assert result is None


class TestRedisConnectionFailure:
    """Redis 连接异常时的降级行为。"""

    def test_get_cache_returns_none_on_connection_error(self, monkeypatch):
        """Redis 连接失败时 get_cache 返回 None。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        with patch.object(cache_mod, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.side_effect = Exception("connection refused")
            mock_get_client.return_value = mock_client

            result = cache_mod.get_cache("any_key")
            assert result is None

    def test_set_cache_returns_false_on_connection_error(self, monkeypatch):
        """Redis 连接失败时 set_cache 返回 False。"""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        with patch.object(cache_mod, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.setex.side_effect = Exception("connection refused")
            mock_get_client.return_value = mock_client

            result = cache_mod.set_cache("key", {"x": 1})
            assert result is False


class TestRecommendCache:
    """推荐服务缓存集成测试。"""

    def test_recommend_by_movie_caches_result(self):
        """recommend_by_movie 第二次调用命中缓存（不重复计算）。"""
        from backend.cache import delete_cache, build_cache_key

        # 准备：先清空对应缓存
        cache_key = build_cache_key("similar", "1292052", "5")
        delete_cache(cache_key)

        # 用 mock Redis 验证 set_cache 被调用
        import backend.cache as cache_mod
        orig_client = cache_mod._redis_client
        orig_checked = cache_mod._redis_checked
        try:
            mock = MagicMock()
            mock.get.return_value = None  # 第一次未命中
            cache_mod._redis_client = mock
            cache_mod._redis_checked = True

            from backend.services.recommender_service import RecommenderService
            service = RecommenderService()

            result = service.recommend_by_movie("1292052", top_n=5)
            assert isinstance(result, list)
            assert len(result) <= 5
            assert len(result) > 0

            # 验证 setex 被调用（写缓存）
            assert mock.setex.called
            # 验证 TTL 为 21600（6h）
            call_args = mock.setex.call_args
            assert call_args[0][1] == 21600
        finally:
            cache_mod._redis_client = orig_client
            cache_mod._redis_checked = orig_checked

    def test_recommend_by_movie_cache_hit(self):
        """缓存命中时直接返回，不调用底层推荐器。"""
        import backend.cache as cache_mod

        # 准备预置缓存
        from backend.cache import build_cache_key, set_cache, delete_cache
        cache_key = build_cache_key("similar", "1292052", "3")
        set_cache(cache_key, [{"movie_id": "1", "title": "Cached"}], ttl=21600)

        orig_client = cache_mod._redis_client
        orig_checked = cache_mod._redis_checked
        try:
            mock = MagicMock()
            mock.get.return_value = json.dumps(
                [{"movie_id": "1", "title": "Cached"}], ensure_ascii=False
            )
            cache_mod._redis_client = mock
            cache_mod._redis_checked = True

            from backend.services.recommender_service import RecommenderService
            service = RecommenderService()

            result = service.recommend_by_movie("1292052", top_n=3)
            assert len(result) == 1
            assert result[0]["title"] == "Cached"
            # 不应调用 setex（缓存命中直接返回）
            assert not mock.setex.called
        finally:
            cache_mod._redis_client = orig_client
            cache_mod._redis_checked = orig_checked
            delete_cache(cache_key)

    def test_recommend_by_text_cache_key_hides_query(self):
        """recommend_by_text 的 cache key 不直接暴露原始搜索词。"""
        from backend.cache import hash_text, build_cache_key

        query = "科幻冒险电影"
        key = build_cache_key("search", hash_text(query), "10")

        assert "科幻" not in key
        assert "冒险" not in key
        assert "电影" not in key
        assert key.startswith("search:")

    def test_recommend_by_text_works_without_redis(self, monkeypatch):
        """Redis 不可用时 recommend_by_text 仍然正常返回结果。"""
        monkeypatch.setenv("REDIS_URL", "")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        from backend.services.recommender_service import RecommenderService
        service = RecommenderService()

        result = service.recommend_by_text("科幻", top_n=3)
        assert isinstance(result, list)
        assert len(result) <= 3

    def test_get_stats_works_without_redis(self, monkeypatch):
        """Redis 不可用时 get_stats 仍然正常返回。"""
        monkeypatch.setenv("REDIS_URL", "")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        from backend.services.recommender_service import RecommenderService
        service = RecommenderService()

        stats = service.get_stats()
        assert "total_movies" in stats
        assert stats["total_movies"] > 0

    def test_get_stats_caches_result(self):
        """get_stats 第二次调用命中缓存。"""
        import backend.cache as cache_mod
        from backend.cache import delete_cache, build_cache_key

        cache_key = build_cache_key("stats", "v1")
        delete_cache(cache_key)

        import json as _json
        cached_stats = _json.dumps(
            {"total_movies": 9999, "avg_rating": 9.9}, ensure_ascii=False
        )

        orig_client = cache_mod._redis_client
        orig_checked = cache_mod._redis_checked
        try:
            mock = MagicMock()
            mock.get.return_value = None  # 第一次未命中
            cache_mod._redis_client = mock
            cache_mod._redis_checked = True

            from backend.services.recommender_service import RecommenderService
            service = RecommenderService()

            stats = service.get_stats()
            assert isinstance(stats, dict)

            # 验证 setex 被调用
            assert mock.setex.called
            call_args = mock.setex.call_args
            assert call_args[0][1] == 600  # 10min TTL
        finally:
            cache_mod._redis_client = orig_client
            cache_mod._redis_checked = orig_checked
            delete_cache(cache_key)

    def test_recommend_by_movie_works_without_redis(self, monkeypatch):
        """Redis 不可用时 recommend_by_movie 仍然正常返回。"""
        monkeypatch.setenv("REDIS_URL", "")
        import backend.cache as cache_mod
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

        from backend.services.recommender_service import RecommenderService
        service = RecommenderService()

        result = service.recommend_by_movie("1292052", top_n=3)
        assert isinstance(result, list)
        assert len(result) <= 3
        if result:
            assert "movie_id" in result[0]
            assert "title" in result[0]
            assert "similarity_score" in result[0]
