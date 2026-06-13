"""
认证业务逻辑 — 密码哈希、会话管理、收藏操作。

会话存储在内存字典中（7 天 TTL），服务重启后需重新登录。
"""
import hashlib
import secrets
import time

from backend.services.auth_db import (
    create_user as _db_create_user,
    get_user_by_username,
    get_user_by_id,
    add_favorite as _db_add_favorite,
    remove_favorite as _db_remove_favorite,
    get_favorites as _db_get_favorites,
    is_favorited as _db_is_favorited,
    get_favorite_count,
    set_rating as _db_set_rating,
    remove_rating as _db_remove_rating,
    get_user_rating as _db_get_user_rating,
    get_all_ratings as _db_get_all_ratings,
    get_rating_count,
)

# ── 密码哈希 (pbkdf2_hmac, stdlib, 零依赖) ─────────────

_PBKDF2_ITERATIONS = 600_000
_PBKDF2_HASH_NAME = "sha256"
_SALT_BYTES = 32


def hash_password(password: str) -> str:
    """对密码进行 PBKDF2 哈希，返回存储格式: $iterations$salt_hex$hash_hex"""
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        _PBKDF2_HASH_NAME,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return f"${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """验证密码是否匹配存储的哈希值。"""
    try:
        parts = stored.split("$")
        if len(parts) != 4 or parts[0] != "":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hex = parts[3]
        dk = hashlib.pbkdf2_hmac(
            _PBKDF2_HASH_NAME,
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return secrets.compare_digest(dk.hex(), expected_hex)
    except (ValueError, AttributeError):
        return False


# ── 会话管理（内存存储） ──────────────────────────────

_auth_sessions: dict[str, dict] = {}
SESSION_TTL_SECONDS = 7 * 24 * 3600  # 7 天


def _generate_token() -> str:
    """生成 64 字符 hex 令牌。"""
    return secrets.token_hex(32)


def _cleanup_expired_sessions():
    """清理过期的会话。"""
    now = time.time()
    expired = [
        t for t, s in _auth_sessions.items()
        if now - s.get("created_at", 0) > SESSION_TTL_SECONDS
    ]
    for t in expired:
        del _auth_sessions[t]


def validate_session(token: str) -> dict | None:
    """验证会话 token，返回 {'user_id', 'username'} 或 None。"""
    if not token:
        return None
    session = _auth_sessions.get(token)
    if session is None:
        return None
    if time.time() - session.get("created_at", 0) > SESSION_TTL_SECONDS:
        del _auth_sessions[token]
        return None
    return {"user_id": session["user_id"], "username": session["username"]}


# ── 注册 / 登录 / 登出 ────────────────────────────────

def register(username: str, password: str) -> tuple[bool, str]:
    """
    注册新用户。
    返回 (success, message_or_token)。
    """
    username = username.strip()
    if len(username) < 3 or len(username) > 30:
        return False, "用户名需 3-30 个字符"
    if len(password) < 6:
        return False, "密码至少 6 个字符"

    pwd_hash = hash_password(password)
    user = _db_create_user(username, pwd_hash)
    if user is None:
        return False, "用户名已存在"

    token = _generate_token()
    _auth_sessions[token] = {
        "user_id": user["id"],
        "username": user["username"],
        "created_at": time.time(),
    }
    _cleanup_expired_sessions()
    return True, token


def login(username: str, password: str) -> tuple[bool, str]:
    """
    用户登录。
    返回 (success, message_or_token)。
    """
    username = username.strip()
    user = get_user_by_username(username)
    if user is None:
        return False, "用户名或密码错误"

    if not verify_password(password, user["password_hash"]):
        return False, "用户名或密码错误"

    token = _generate_token()
    _auth_sessions[token] = {
        "user_id": user["id"],
        "username": user["username"],
        "created_at": time.time(),
    }
    _cleanup_expired_sessions()
    return True, token


def logout(token: str) -> None:
    """销毁会话 token。"""
    _auth_sessions.pop(token, None)


# ── 收藏操作 ──────────────────────────────────────────

def toggle_favorite(user_id: str, movie_id: str) -> dict:
    """
    切换收藏状态。
    返回 {'movie_id': str, 'is_favorited': bool}
    """
    if _db_is_favorited(user_id, movie_id):
        _db_remove_favorite(user_id, movie_id)
        return {"movie_id": movie_id, "is_favorited": False}
    else:
        _db_add_favorite(user_id, movie_id)
        return {"movie_id": movie_id, "is_favorited": True}


def get_user_favorites(user_id: str) -> list[str]:
    """获取用户收藏的电影 ID 列表。"""
    return _db_get_favorites(user_id)


def get_user_profile(user_id: str) -> dict | None:
    """获取用户信息（不包含密码哈希）。"""
    user = get_user_by_id(user_id)
    if user is None:
        return None
    return {
        "username": user["username"],
        "created_at": user["created_at"],
        "favorite_count": get_favorite_count(user_id),
        "rating_count": get_rating_count(user_id),
    }


# ── 评分操作 ──────────────────────────────────────────

def set_rating(user_id: str, movie_id: str, rating: float) -> dict:
    """
    设置或更新用户对电影的评分（1.0-5.0，支持 0.5 步进）。
    返回 {'movie_id': str, 'rating': float, 'is_new': bool}
    """
    rating = round(max(1.0, min(5.0, float(rating))) * 2) / 2
    is_new = _db_set_rating(user_id, movie_id, rating)
    return {"movie_id": movie_id, "rating": rating, "is_new": is_new}


def remove_rating(user_id: str, movie_id: str) -> bool:
    """删除评分，返回是否确实删除了记录。"""
    return _db_remove_rating(user_id, movie_id)


def get_user_rating(user_id: str, movie_id: str) -> float | None:
    """获取用户对某部电影的评分，未评返回 None。"""
    return _db_get_user_rating(user_id, movie_id)


def get_all_ratings(user_id: str) -> dict[str, float]:
    """获取用户所有评分，返回 {movie_id: rating, ...}。"""
    return _db_get_all_ratings(user_id)
