"""
QA 服务主类 — 意图识别 + 智能路由 + LLM 对话 + 多轮筛选。
"""

import os
import re
import json
import sys
from pathlib import Path

# Windows 编码修复
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ["PYTHONUTF8"] = "1"
if sys.platform == "win32":
    import io
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 加载 .env（支持独立导入，不依赖 app.py 的 load_dotenv）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
APP_ENV = os.getenv("APP_ENV", "development")
env_override = PROJECT_ROOT / f".env.{APP_ENV}"
if env_override.exists():
    load_dotenv(env_override, override=True)

from backend.services.rag_service import RAGService

from backend.services.qa.constants import (
    ZHIPU_BASE_URL,
    DEFAULT_MODEL,
    RETRIEVAL_TOP_K,
    FILTER_MAX_DISPLAY,
    SYSTEM_PROMPT,
    RECOMMEND_POLISH_PROMPT,
    FILTER_POLISH_PROMPT,
    RAG_INSTRUCTION,
    TOOLS,
)
from backend.services.qa.formatting import (
    _format_movie_context,
    _format_movie_info,
    _format_filter_state,
    _compute_filter_active,
)
from backend.services.qa.sessions import (
    get_session_history,
    append_session_history,
    get_session_filter,
    save_session_filter,
    clear_session_filter,
)
from backend.services.qa.filters import (
    parse_filter_action,
    apply_tool_args,
    parse_filter_from_message,
    apply_filters,
)
from backend.services.qa.intent import (
    keyword_classify,
    extract_movie_name,
    extract_field,
    extract_person_for_search,
)


class QAService:
    """QA 服务 — 单例，意图识别 + 智能路由 + LLM 对话 + 多轮筛选。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_ready"):
            return
        self._ready = True
        self._client = None  # type: ignore
        self._rag = RAGService()
        self._recommender = None
        self._all_movies_cache: list[dict] | None = None

    # ── 内部：客户端管理 ─────────────────────────────

    def _get_api_key(self) -> str:
        return os.getenv("ZHIPU_API_KEY", "").strip()

    def _get_model(self) -> str:
        return os.getenv("ZHIPU_MODEL", DEFAULT_MODEL).strip()

    def _ensure_client(self):
        if self._client is not None:
            return
        api_key = self._get_api_key()
        if not api_key:
            raise RuntimeError(
                "未找到 ZHIPU_API_KEY 环境变量。\n"
                "请在项目根目录 .env 文件中添加:\n"
                "  ZHIPU_API_KEY=你的智谱AI密钥"
            )
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key, base_url=ZHIPU_BASE_URL)

    def _get_recommender(self):
        if self._recommender is None:
            from backend.services.recommender_service import RecommenderService
            self._recommender = RecommenderService()
        return self._recommender

    def _load_all_movies(self) -> list[dict]:
        """加载全部电影数据（带缓存），供筛选使用。"""
        if self._all_movies_cache is not None:
            return self._all_movies_cache
        recommender = self._get_recommender()
        try:
            movies, _ = recommender.list_movies_rich()
            self._all_movies_cache = movies
        except Exception:
            self._all_movies_cache = []
        return self._all_movies_cache

    # ── 内部：电影数据格式化 ─────────────────────────

    @staticmethod
    def _to_related(results: list[dict]) -> list[dict]:
        """将电影 dict 列表转为前端 MovieRecommendation 格式。"""
        recommender = None
        out = []
        for m in results:
            poster = m.get("poster_url", "")
            if not poster:
                # RAG 结果没有海报，从推荐器元数据中捞取
                try:
                    if recommender is None:
                        from backend.services.recommender_service import RecommenderService
                        recommender = RecommenderService()
                    mid = str(m.get("movie_id", ""))
                    poster = recommender._valid_poster(
                        recommender._meta_dict.get(mid, {}).get("poster", "")
                    )
                except Exception:
                    poster = ""

            sim = m.get("similarity_score") or m.get("similarity") or 0
            year_raw = m.get("year")
            if year_raw is not None and str(year_raw) in ("nan", "None", ""):
                year_raw = None

            out.append({
                "movie_id": str(m.get("movie_id", "")),
                "title": str(m.get("title", "")),
                "similarity_score": float(sim),
                "poster_url": str(poster),
                "rating": float(m.get("rating", 0) or 0),
                "year": int(year_raw) if year_raw is not None else None,
            })
        return out

    # ── 内部：LLM 调用 ──────────────────────────────

    def _call_llm(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 600,
        tools: list[dict] | None = None,
    ) -> tuple[str | None, list[dict] | None]:
        kwargs = dict(
            model=self._get_model(),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        text = choice.content
        tool_calls_raw = getattr(choice, "tool_calls", None)

        tool_calls = None
        if tool_calls_raw:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in tool_calls_raw
            ]

        return text, tool_calls

    def _safe_llm_reply(
        self, messages: list[dict], fallback: str = "AI 服务暂时不可用，请稍后重试。",
        max_tokens: int = 600,
    ) -> str:
        try:
            text, _ = self._call_llm(messages, max_tokens=max_tokens)
            return text or fallback
        except UnicodeEncodeError:
            return fallback
        except Exception as exc:
            err = str(exc).lower()
            if "401" in err or "unauthorized" in err:
                return "API Key 无效，请检查 .env 中 ZHIPU_API_KEY 的值。"
            elif "429" in err or "rate" in err:
                return "请求过于频繁，请稍后再试。"
            elif "timeout" in err:
                return "AI 服务响应超时，请稍后重试。"
            return fallback

    # ── 意图分类：关键词规则 ─────────────────────────

    def _keyword_classify(self, message: str) -> str | None:
        return keyword_classify(message)

    # ── 意图分类：LLM function calling ───────────────

    def _llm_classify(
        self, user_message: str, session_id: str | None = None
    ) -> tuple[str | None, dict | None]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 如果有活跃的筛选条件，注入上下文帮助 LLM 理解
        if session_id:
            fs = get_session_filter(session_id)
            if fs.get("active"):
                messages.append({
                    "role": "system",
                    "content": (
                        f"当前会话已有筛选条件：{_format_filter_state(fs)}。"
                        "用户可能在基于这些条件继续筛选。如果用户说'再加''还要'等，"
                        "应使用 update_filters 工具的 add 操作追加条件。"
                    ),
                })
            messages.extend(get_session_history(session_id))

        messages.append({"role": "user", "content": user_message})

        try:
            text, tool_calls = self._call_llm(messages, temperature=0.3, tools=TOOLS)
        except Exception:
            return None, None

        if not tool_calls:
            return None, None

        tc = tool_calls[0]
        try:
            args = json.loads(tc["arguments"]) if isinstance(tc["arguments"], str) else tc["arguments"]
        except (json.JSONDecodeError, TypeError):
            return None, None

        intent_map = {
            "recommend_movies": "recommend",
            "get_movie_info": "info",
            "update_filters": "filter",
        }
        return intent_map.get(tc["name"]), args

    # ── Handler: 推荐 ─────────────────────────────────

    def _handle_recommend(
        self, user_message: str, session_id: str | None = None
    ) -> tuple[str, list[str]]:
        recommender = self._get_recommender()

        try:
            results = recommender.recommend_by_text(user_message, top_n=RETRIEVAL_TOP_K)
        except Exception:
            results = []

        if not results:
            return self._handle_chat(user_message, session_id)

        context = _format_movie_context(results)
        system = RECOMMEND_POLISH_PROMPT.format(
            user_message=user_message,
            movie_context=context,
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"请根据以上检索结果，为用户推荐电影。用户需求：{user_message}"},
        ]
        reply = self._safe_llm_reply(messages, fallback=self._format_fallback_recommend(results))

        return reply, self._to_related(results)

    def _format_fallback_recommend(self, movies: list[dict]) -> str:
        lines = ["根据你的需求，为你找到以下电影：\n"]
        for i, m in enumerate(movies, 1):
            year = f" ({m['year']})" if m.get("year") else ""
            rating = m.get("rating", 0)
            lines.append(f"{i}. 🎬 **《{m['title']}》**{year} ⭐{rating:.1f}")
        return "\n".join(lines)

    # ── Handler: 信息查询 ─────────────────────────────

    def _handle_info(
        self, user_message: str, session_id: str | None = None
    ) -> tuple[str, list[str]]:
        movie_name = self._extract_movie_name(user_message)
        field = self._extract_field(user_message)

        if not movie_name:
            return self._handle_chat(user_message, session_id)

        movie = self._lookup_movie(movie_name)

        if movie:
            reply = _format_movie_info(movie, field)
            return reply, self._to_related([movie])

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        messages.insert(
            1,
            {
                "role": "system",
                "content": f"（注意：在本地电影数据库中未找到名为《{movie_name}》的电影。请基于你的知识回答，并说明这不是数据库中的信息。）",
            },
        )
        reply = self._safe_llm_reply(messages)
        return reply, []

    # ── 意图辅助方法（委托给子模块） ─────────────────

    def _extract_movie_name(self, message: str) -> str | None:
        return extract_movie_name(message)

    def _extract_field(self, message: str) -> str:
        return extract_field(message)

    def _lookup_movie(self, name: str) -> dict | None:
        recommender = self._get_recommender()
        try:
            movies, _ = recommender.list_movies_rich(name)
        except Exception:
            return None
        if not movies:
            return None
        name_lower = name.lower().strip()
        for m in movies:
            if m["title"].lower().strip() == name_lower:
                return m
        for m in movies:
            if name_lower in m["title"].lower():
                return m
        return movies[0] if movies else None

    # ── Handler: 多轮筛选 ─────────────────────────────

    def _handle_filter(
        self, user_message: str, session_id: str | None = None, tool_args: dict | None = None
    ) -> tuple[str, list[str]]:
        if not session_id:
            return self._handle_chat(user_message, session_id)

        fs = get_session_filter(session_id)

        # ── 解析操作 ─────────────────────────────────
        if tool_args:
            action = tool_args.get("action", "add")
        else:
            action = self._parse_filter_action(user_message)

        # ── 重置 ─────────────────────────────────────
        if action == "reset":
            clear_session_filter(session_id)
            return "✅ 筛选条件已重置。现在显示全部电影，你可以随时添加新的筛选条件。", []

        # ── 查看当前条件 ────────────────────────────
        if action == "show":
            if not fs.get("active"):
                return "📋 当前没有设置任何筛选条件。你可以说'只看科幻片''评分8分以上'来添加条件。", []
            return f"📋 {_format_filter_state(fs)}", []

        # ── 更新条件 ─────────────────────────────────
        if tool_args:
            fs = self._apply_tool_args(fs, tool_args, action)
        else:
            fs = self._parse_filter_from_message(fs, user_message, action)

        fs["active"] = _compute_filter_active(fs)
        save_session_filter(session_id, fs)

        # ── 应用筛选 + 返回结果 ─────────────────────
        if not fs.get("active"):
            return "✅ 筛选条件已更新。当前没有活跃的筛选条件，显示全部电影。", []

        movies = self._apply_filters(fs)
        if not movies:
            return (
                f"😕 根据当前条件（{_format_filter_state(fs)}）没有找到匹配的电影。"
                "试试放宽条件，或说'重置筛选'重新开始。"
            ), []

        related_ids = [m["movie_id"] for m in movies[:FILTER_MAX_DISPLAY]]
        display_movies = movies[:FILTER_MAX_DISPLAY]
        total_count = len(movies)

        # 筛选结果摘要 + LLM 润色
        sort_label = {"rating": "评分降序", "year": "年份降序", "title": "标题"}.get(
            fs.get("sort_by", "rating"), "评分降序"
        )
        context = _format_movie_context(display_movies)
        system = FILTER_POLISH_PROMPT.format(
            filter_summary=_format_filter_state(fs),
            sort_label=sort_label,
            movie_context=context,
            FILTER_MAX_DISPLAY=FILTER_MAX_DISPLAY,
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "请告知用户筛选结果。"},
        ]
        reply = self._safe_llm_reply(
            messages,
            fallback=self._format_fallback_filter(movies, fs, total_count),
        )

        # 补充总数信息
        if total_count > FILTER_MAX_DISPLAY:
            reply += f"\n\n（共 {total_count} 部匹配，以上为前 {FILTER_MAX_DISPLAY} 部）"

        return reply, self._to_related(display_movies)

    # ── 筛选辅助方法（委托给子模块） ─────────────────

    def _parse_filter_action(self, message: str) -> str:
        return parse_filter_action(message)

    def _apply_tool_args(self, fs: dict, args: dict, action: str) -> dict:
        return apply_tool_args(fs, args, action)

    def _parse_filter_from_message(self, fs: dict, message: str, action: str) -> dict:
        return parse_filter_from_message(fs, message, action)

    def _apply_filters(self, fs: dict) -> list[dict]:
        movies = self._load_all_movies()
        return apply_filters(fs, movies)

    def _format_fallback_filter(self, movies: list[dict], fs: dict, total: int) -> str:
        """LLM 不可用时的降级筛选结果文本。"""
        lines = [f"📋 {_format_filter_state(fs)}\n"]
        lines.append(f"共找到 {total} 部匹配电影：\n")
        for i, m in enumerate(movies[:FILTER_MAX_DISPLAY], 1):
            year = f" ({m['year']})" if m.get("year") else ""
            rating = m.get("rating", 0)
            lines.append(f"{i}. 🎬 **《{m['title']}》**{year} ⭐{rating:.1f}")
        if total > FILTER_MAX_DISPLAY:
            lines.append(f"\n... 还有 {total - FILTER_MAX_DISPLAY} 部，可以继续筛选缩小范围。")
        return "\n".join(lines)

    # ── Handler: 纯对话（RAG 增强 + 自然闲聊） ────────

    # RAG 相似度阈值：低于此值说明用户话题与电影无关，跳过 RAG
    _RAG_RELEVANCE_THRESHOLD = 0.28

    @staticmethod
    def _mentioned_movies(reply: str, candidates: list[dict]) -> list[dict]:
        """只保留 LLM 回复中真正提到的电影，避免闲聊时硬塞无关卡片。"""
        if not reply or not candidates:
            return []
        mentioned = []
        for m in candidates:
            title = str(m.get("title", ""))
            if title and title in reply:
                mentioned.append(m)
        return mentioned

    def _handle_chat(
        self, user_message: str, session_id: str | None = None
    ) -> tuple[str, list[str]]:
        # 检索 RAG
        retrieved = self._rag.retrieve(user_message, top_k=RETRIEVAL_TOP_K)

        # 根据相似度判断话题是否真的与电影相关
        top_score = max((m.get("similarity", 0) for m in retrieved), default=0)
        is_movie_related = top_score >= self._RAG_RELEVANCE_THRESHOLD

        if is_movie_related and retrieved:
            context_text = _format_movie_context(retrieved)
            system_content = RAG_INSTRUCTION + context_text
        else:
            # 话题与电影无关 — 不传 RAG，纯聊天
            system_content = SYSTEM_PROMPT
            retrieved = []

        messages = [{"role": "system", "content": system_content}]

        # 注入筛选状态
        if session_id:
            fs = get_session_filter(session_id)
            if fs.get("active"):
                messages.append({
                    "role": "system",
                    "content": (
                        f"（用户有活跃筛选条件：{_format_filter_state(fs)}。"
                        "如果用户说'还有吗'，在筛选条件下推荐。）"
                    ),
                })

        # 注入历史上下文
        if session_id:
            history = get_session_history(session_id)
            if history:
                messages.append({
                    "role": "system",
                    "content": (
                        "以下是你们之前的对话历史，注意用户提到过的偏好和上下文，"
                        "自然地在回复中体现你记住了这些信息。"
                    ),
                })
                messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        reply = self._safe_llm_reply(messages, max_tokens=800)

        # 只在 RAG 判定为电影相关时才展示卡片
        if is_movie_related and retrieved:
            related = self._mentioned_movies(reply, retrieved)
            return reply, self._to_related(related)
        return reply, []

    # ── 主入口 ───────────────────────────────────────

    def chat(
        self,
        user_message: str,
        history: list[dict] | None = None,
        session_id: str | None = None,
    ) -> tuple[str, list[str]]:
        """
        智能电影问答 — 意图识别 + 路由 + 多轮筛选。

        流程:
          1. 关键词快速分类 → recommend / info / filter
          2. 未命中 → LLM function calling 分类
          3. 无工具调用 → 纯 LLM 对话（RAG 增强）

        多轮筛选:
          - 用户说"只看科幻片" → 添加 genre 筛选
          - 用户说"评分8分以上" → 追加 rating 筛选
          - 用户说"中国的" → 追加 country 筛选
          - 用户说"重置筛选" → 清除所有条件
          - 条件累积生效，每次返回当前筛选结果
        """
        self._ensure_client()

        # ── Step 1: 关键词分类 ──────────────────────
        intent = self._keyword_classify(user_message)

        if intent == "recommend":
            search_query = extract_person_for_search(user_message) or user_message
            reply, related_ids = self._handle_recommend(search_query, session_id)
        elif intent == "info":
            reply, related_ids = self._handle_info(user_message, session_id)
        elif intent == "filter":
            reply, related_ids = self._handle_filter(user_message, session_id)
        else:
            # ── Step 2: LLM function calling ──────────
            llm_intent, tool_args = self._llm_classify(user_message, session_id)

            if llm_intent == "recommend":
                query_text = (tool_args or {}).get("query_text", user_message)
                reply, related_ids = self._handle_recommend(query_text, session_id)
            elif llm_intent == "info":
                movie_title = (tool_args or {}).get("movie_title", "")
                field = (tool_args or {}).get("field", "all")
                movie = self._lookup_movie(movie_title) if movie_title else None
                if movie:
                    reply = _format_movie_info(movie, field)
                    related_ids = self._to_related([movie])
                else:
                    reply, related_ids = self._handle_info(user_message, session_id)
            elif llm_intent == "filter":
                reply, related_ids = self._handle_filter(user_message, session_id, tool_args)
            else:
                # ── Step 3: 纯对话 ────────────────────
                reply, related_ids = self._handle_chat(user_message, session_id)

        # ── 保存会话 ──────────────────────────────
        if session_id:
            append_session_history(session_id, "user", user_message)
            append_session_history(session_id, "assistant", reply)

        return reply, related_ids

    def is_configured(self) -> bool:
        return bool(self._get_api_key())
