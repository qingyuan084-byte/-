"""
Redis 缓存层 — 对上层提供 get/set/delete/clear 接口。

特性:
- REDIS_URL 未配置时静默降级，所有读操作返回 None
- 值自动 JSON 序列化/反序列化
- 连接/读写/序列化异常全部静默降级
"""

import json
import hashlib
import os


def _log(msg: str):
    print(f"[缓存] {msg}")


# ── 连接管理 ──────────────────────────────────────────

_redis_client = None
_redis_checked = False


def _get_client():
    """获取 Redis 客户端（懒加载，只尝试一次）。延迟 import 确保 redis 可选。"""
    global _redis_client, _redis_checked

    # 延迟 import，redis 仅在真正使用时才需要
    try:
        import redis
        import redis.exceptions
    except ModuleNotFoundError:
        _redis_checked = True
        _log("redis 包未安装 (pip install redis)，缓存功能已禁用")
        return None

    if _redis_checked:
        return _redis_client

    _redis_checked = True

    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        _log("REDIS_URL 未配置，缓存功能已禁用")
        return None

    try:
        _redis_client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        _redis_client.ping()
        _log(f"Redis 已连接: {redis_url}")
    except Exception as e:
        _log(f"Redis 连接失败 ({e})，缓存功能已禁用")
        _redis_client = None

    return _redis_client


# ── 公共 API ──────────────────────────────────────────


def hash_text(text: str, length: int = 16) -> str:
    """对文本做 sha256 取前 N 位十六进制摘要。用于隐藏敏感搜索词。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def build_cache_key(prefix: str, *parts: str) -> str:
    """构建缓存 key。

    用法:
        build_cache_key("stats", "v1")          → "stats:v1"
        build_cache_key("similar", "1292052", "10")  → "similar:1292052:10"
        build_cache_key("search", hash_text(query), "10")  → "search:<hash>:10"

    调用方负责对敏感参数调用 hash_text()，非敏感参数直接传入原文。
    """
    segments = [prefix]
    for p in parts:
        s = str(p).strip()
        if s:
            segments.append(s)
    return ":".join(segments)


def get_cache(key: str):
    """读取缓存，返回反序列化后的 Python 对象。Redis 不可用时返回 None。"""
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        _log(f"缓存读取失败 key={key}: {e}")
        return None


def set_cache(key: str, value: object, ttl: int | None = None) -> bool:
    """写入缓存，value 会被 JSON 序列化。Redis 不可用时返回 False。"""
    client = _get_client()
    if client is None:
        return False
    if ttl is None:
        ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    try:
        payload = json.dumps(value, ensure_ascii=False, default=str)
        client.setex(key, ttl, payload)
        return True
    except Exception as e:
        _log(f"缓存写入失败 key={key}: {e}")
        return False


def delete_cache(key: str) -> bool:
    """删除单个缓存 key。Redis 不可用时返回 False。"""
    client = _get_client()
    if client is None:
        return False
    try:
        client.delete(key)
        return True
    except Exception as e:
        _log(f"Redis 删除异常 key={key}: {e}")
        return False


def clear_cache_prefix(prefix: str) -> int:
    """按前缀清空缓存，返回删除的 key 数量。Redis 不可用时返回 0。"""
    client = _get_client()
    if client is None:
        return 0
    pattern = f"{prefix}:*"
    try:
        keys = list(client.scan_iter(match=pattern, count=100))
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        _log(f"Redis 前缀扫描异常 prefix={prefix}: {e}")
        return 0


def flush_app_cache() -> int:
    """清空本应用相关的 stats/similar/search/rich 前缀缓存。"""
    deleted = 0
    for prefix in ("stats", "similar", "search", "rich"):
        deleted += clear_cache_prefix(prefix)
    return deleted
