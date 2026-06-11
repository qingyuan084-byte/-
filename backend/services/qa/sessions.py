"""
QA 模块会话管理 — 内存存储 + SQLite 持久化 + 筛选状态。
"""
import json
import time
import sqlite3
import threading
from copy import deepcopy
from pathlib import Path as _Path

from backend.services.qa.constants import DEFAULT_FILTER_STATE, MAX_HISTORY_MESSAGES

# 服务端会话存储
user_sessions: dict[str, list[dict]] = {}

# 服务端筛选状态存储
session_filters: dict[str, dict] = {}

# SQLite 持久化
_SESSION_DB_PATH = _Path(__file__).resolve().parent.parent.parent.parent / "data" / "sessions.db"
_session_db_local = threading.local()


def _get_session_db() -> sqlite3.Connection:
    """获取当前线程的 SQLite 连接（线程安全）。"""
    if not hasattr(_session_db_local, "conn") or _session_db_local.conn is None:
        _SESSION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(_SESSION_DB_PATH))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chat_history (
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                seq INTEGER NOT NULL,
                PRIMARY KEY (session_id, seq)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS session_filters_db (
                session_id TEXT PRIMARY KEY,
                filter_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )"""
        )
        conn.commit()
        _session_db_local.conn = conn
    return _session_db_local.conn


def _load_sessions_from_db():
    """启动时从 SQLite 恢复会话数据到内存。"""
    try:
        conn = _get_session_db()

        # 恢复聊天历史
        rows = conn.execute(
            "SELECT session_id, role, content FROM chat_history ORDER BY session_id, seq"
        ).fetchall()
        for sess_id, role, content in rows:
            if sess_id not in user_sessions:
                user_sessions[sess_id] = []
            user_sessions[sess_id].append({"role": role, "content": content})
            # 应用 MAX_HISTORY_MESSAGES 限制
            if len(user_sessions[sess_id]) > MAX_HISTORY_MESSAGES:
                user_sessions[sess_id] = user_sessions[sess_id][-MAX_HISTORY_MESSAGES:]

        # 恢复筛选状态
        filter_rows = conn.execute(
            "SELECT session_id, filter_json FROM session_filters_db"
        ).fetchall()
        for sess_id, filter_json in filter_rows:
            try:
                session_filters[sess_id] = json.loads(filter_json)
            except (json.JSONDecodeError, TypeError):
                pass

        if rows or filter_rows:
            print(f"[会话] 已从 SQLite 恢复 {len(user_sessions)} 个会话, "
                  f"{len(session_filters)} 个筛选状态")
    except Exception as e:
        print(f"[会话] SQLite 恢复失败: {e}")


def _persist_chat_message(session_id: str, role: str, content: str):
    """持久化一条聊天消息到 SQLite。"""
    try:
        conn = _get_session_db()
        seq = len(user_sessions.get(session_id, []))
        conn.execute(
            "INSERT OR REPLACE INTO chat_history (session_id, role, content, seq) VALUES (?, ?, ?, ?)",
            (session_id, role, content, seq),
        )
        conn.commit()
    except Exception:
        pass  # 持久化失败不影响正常使用


def _persist_filter_state(session_id: str, fs: dict):
    """持久化筛选状态到 SQLite。"""
    try:
        conn = _get_session_db()
        conn.execute(
            "INSERT OR REPLACE INTO session_filters_db (session_id, filter_json, updated_at) VALUES (?, ?, ?)",
            (session_id, json.dumps(fs, ensure_ascii=False), time.time()),
        )
        conn.commit()
    except Exception:
        pass


def _delete_session_from_db(session_id: str):
    """从 SQLite 删除会话的所有数据。"""
    try:
        conn = _get_session_db()
        conn.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM session_filters_db WHERE session_id = ?", (session_id,))
        conn.commit()
    except Exception:
        pass


def get_session_history(session_id: str) -> list[dict]:
    if session_id not in user_sessions:
        user_sessions[session_id] = []
    return list(user_sessions[session_id])


def append_session_history(session_id: str, role: str, content: str):
    if session_id not in user_sessions:
        user_sessions[session_id] = []
    user_sessions[session_id].append({"role": role, "content": content})
    if len(user_sessions[session_id]) > MAX_HISTORY_MESSAGES:
        user_sessions[session_id] = user_sessions[session_id][-MAX_HISTORY_MESSAGES:]
    _persist_chat_message(session_id, role, content)


def clear_session(session_id: str):
    user_sessions.pop(session_id, None)
    session_filters.pop(session_id, None)
    _delete_session_from_db(session_id)


def get_session_filter(session_id: str) -> dict:
    """获取会话的筛选状态（返回副本）。"""
    if session_id not in session_filters:
        session_filters[session_id] = deepcopy(DEFAULT_FILTER_STATE)
    return deepcopy(session_filters[session_id])


def save_session_filter(session_id: str, fs: dict):
    """保存筛选状态。"""
    session_filters[session_id] = deepcopy(fs)
    _persist_filter_state(session_id, fs)


def clear_session_filter(session_id: str):
    """重置筛选状态为默认值。"""
    session_filters[session_id] = deepcopy(DEFAULT_FILTER_STATE)
    _persist_filter_state(session_id, DEFAULT_FILTER_STATE)
