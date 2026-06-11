"""
QA 服务 — 兼容入口（薄封装，实现已拆分到 backend/services/qa/ 子包）。

向后兼容: 所有原有 import 路径继续有效。
"""

# 保持 OpenAI 在模块命名空间中（测试 mock 依赖此路径）
from openai import OpenAI  # noqa: F401

# ── 常量 ──────────────────────────────────────────
from backend.services.qa.constants import DEFAULT_FILTER_STATE  # noqa: F401

# ── 格式化工具 ────────────────────────────────────
from backend.services.qa.formatting import (  # noqa: F401
    _parse_genres,
    _parse_countries,
    _format_movie_context,
    _format_movie_info,
    _format_filter_state,
    _compute_filter_active,
)

# ── 会话管理 ──────────────────────────────────────
from backend.services.qa.sessions import (  # noqa: F401
    user_sessions,
    session_filters,
    _load_sessions_from_db,
    get_session_history,
    append_session_history,
    clear_session,
    get_session_filter,
    save_session_filter,
    clear_session_filter,
)

# ── 筛选解析 ──────────────────────────────────────
from backend.services.qa.filters import (  # noqa: F401
    parse_filter_action,
    apply_tool_args,
    parse_filter_from_message,
    apply_filters,
)

# ── 意图识别 ──────────────────────────────────────
from backend.services.qa.intent import (  # noqa: F401
    keyword_classify,
    extract_movie_name,
    extract_field,
)

# ── QA 服务主类 ───────────────────────────────────
from backend.services.qa.service import QAService  # noqa: F401
