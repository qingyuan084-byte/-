"""
智能问答 API 路由

端点:
  POST   /api/chat                      — 智能电影问答（意图识别 + 路由）
  DELETE /api/chat/session/{session_id}  — 清除会话历史

意图路由:
  - recommend: 文本搜索 → LLM 润色推荐
  - info:      电影名提取 → 本地数据库查询
  - chat:      纯 LLM 对话（RAG 增强）
"""

from fastapi import APIRouter, HTTPException

from backend.models.pydantic_models import ChatRequest, ChatResponse
from backend.services.qa_service import QAService, clear_session, get_session_history

router = APIRouter(tags=["chat"])

_service: QAService | None = None


def _get_service() -> QAService:
    global _service
    if _service is None:
        _service = QAService()
    return _service


@router.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """
    智能电影问答接口 — 自动意图识别与路由。

    **意图分类：**
    - 推荐类（"推荐几部科幻片"）→ 文本搜索 + LLM 润色
    - 查询类（"《星际穿越》导演是谁"）→ 本地数据库查询
    - 闲聊类（"你好"）→ 纯 LLM 对话（RAG 增强）

    请求体:
    ```json
    {
        "message": "推荐一部科幻电影",
        "session_id": "sess-abc123"
    }
    ```

    响应:
    ```json
    {
        "reply": "🎬 **《星际穿越》** (2014) — ...",
        "related_movies": ["1889243", "3541415"]
    }
    ```
    """
    service = _get_service()

    if not service.is_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "AI 服务未配置。请在 .env 文件中设置 ZHIPU_API_KEY。"
                "密钥可从 https://open.bigmodel.cn 获取。"
            ),
        )

    try:
        reply, related_ids = service.chat(
            body.message,
            history=body.history,
            session_id=body.session_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 服务调用失败: {e}")

    return ChatResponse(reply=reply, related_movies=related_ids)


@router.delete("/api/chat/session/{session_id}")
async def delete_session(session_id: str):
    """
    清除指定会话的对话历史。
    """
    clear_session(session_id)
    return {"status": "ok", "message": f"会话 {session_id} 已清除"}


@router.get("/api/chat/session/{session_id}")
async def get_session(session_id: str):
    """
    获取指定会话的对话历史（用于前端恢复记忆）。
    """
    history = get_session_history(session_id)
    return {"session_id": session_id, "history": history}
