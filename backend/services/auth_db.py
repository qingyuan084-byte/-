"""
用户认证数据库层 — SQLite 存储用户账号和收藏数据。

线程安全（threading.local）+ WAL 模式，与 sessions.py 模式一致。
数据库文件: data/users.db
"""
import uuid
import time
import sqlite3
import threading
from pathlib import Path as _Path

_USER_DB_PATH = _Path(__file__).resolve().parent.parent.parent / "data" / "users.db"
_user_db_local = threading.local()


def _get_auth_db() -> sqlite3.Connection:
    """获取当前线程的 SQLite 连接（线程安全），首次访问自动建表。"""
    if not hasattr(_user_db_local, "conn") or _user_db_local.conn is None:
        _USER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(_USER_DB_PATH))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS favorites (
                user_id TEXT NOT NULL,
                movie_id TEXT NOT NULL,
                added_at REAL NOT NULL,
                PRIMARY KEY (user_id, movie_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )"""
        )
        conn.commit()
        _user_db_local.conn = conn
    return _user_db_local.conn


# ── 用户 CRUD ──────────────────────────────────────────

def create_user(username: str, password_hash: str) -> dict | None:
    """创建用户，返回 {'id', 'username', 'created_at'} 或 None（用户名已存在）。"""
    try:
        conn = _get_auth_db()
        user_id = str(uuid.uuid4())
        now = time.time()
        conn.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, password_hash, now),
        )
        conn.commit()
        return {"id": user_id, "username": username, "created_at": now}
    except sqlite3.IntegrityError:
        return None


def get_user_by_username(username: str) -> dict | None:
    """通过用户名查找用户，返回完整 user 字典或 None。"""
    conn = _get_auth_db()
    row = conn.execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "password_hash": row[2], "created_at": row[3]}


def get_user_by_id(user_id: str) -> dict | None:
    """通过 ID 查找用户。"""
    conn = _get_auth_db()
    row = conn.execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "password_hash": row[2], "created_at": row[3]}


# ── 收藏 CRUD ──────────────────────────────────────────

def add_favorite(user_id: str, movie_id: str) -> bool:
    """添加收藏，已存在则返回 False。"""
    try:
        conn = _get_auth_db()
        conn.execute(
            "INSERT INTO favorites (user_id, movie_id, added_at) VALUES (?, ?, ?)",
            (user_id, movie_id, time.time()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def remove_favorite(user_id: str, movie_id: str) -> bool:
    """移除收藏，返回是否确实删除了记录。"""
    conn = _get_auth_db()
    cur = conn.execute(
        "DELETE FROM favorites WHERE user_id = ? AND movie_id = ?",
        (user_id, movie_id),
    )
    conn.commit()
    return cur.rowcount > 0


def get_favorites(user_id: str) -> list[str]:
    """获取用户收藏的电影 ID 列表（按收藏时间倒序）。"""
    conn = _get_auth_db()
    rows = conn.execute(
        "SELECT movie_id FROM favorites WHERE user_id = ? ORDER BY added_at DESC",
        (user_id,),
    ).fetchall()
    return [r[0] for r in rows]


def is_favorited(user_id: str, movie_id: str) -> bool:
    """检查某电影是否已被用户收藏。"""
    conn = _get_auth_db()
    row = conn.execute(
        "SELECT 1 FROM favorites WHERE user_id = ? AND movie_id = ?",
        (user_id, movie_id),
    ).fetchone()
    return row is not None


def get_favorite_count(user_id: str) -> int:
    """获取用户收藏总数。"""
    conn = _get_auth_db()
    row = conn.execute(
        "SELECT COUNT(*) FROM favorites WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return row[0] if row else 0
