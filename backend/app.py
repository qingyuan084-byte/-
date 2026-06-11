"""
电影推荐系统 — FastAPI 主应用

启动命令:
    python backend/app.py
    或
    uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
"""

import sys
import os
from pathlib import Path

# ═══════════════════════════════════════════════════════
# 修复 Windows GBK 编码问题：强制 UTF-8
# openai/httpx 库在输出日志时如果遇到 emoji 会在 GBK 终端崩溃
# ═══════════════════════════════════════════════════════
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ["PYTHONUTF8"] = "1"  # Python 3.12+ 全局 UTF-8 模式
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env 环境变量（必须在其他导入之前）
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# 加载环境专属覆盖（.env.development / .env.production）
APP_ENV = os.getenv("APP_ENV", "development")
env_override = PROJECT_ROOT / f".env.{APP_ENV}"
if env_override.exists():
    load_dotenv(env_override, override=True)
    print(f"[启动] 加载环境配置: .env.{APP_ENV}")
else:
    print(f"[启动] 未找到环境专属配置: .env.{APP_ENV}，使用 .env 默认值")

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx

from backend.api.recommender_api import router as recommender_router
from backend.api.qa_api import router as qa_router
from backend.api.auth_api import router as auth_router
from backend.models.pydantic_models import HealthResponse


# ======================== 生命周期 ========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时预热推荐服务和 RAG 服务（首次请求不再等待加载）。"""
    print("[启动] 预热 RecommenderService...")
    from backend.services.recommender_service import RecommenderService
    RecommenderService()  # 触发单例初始化
    print("[启动] 预热完成，所有特征已加载到内存")

    print("[启动] 恢复持久化会话...")
    try:
        from backend.services.qa_service import _load_sessions_from_db
        _load_sessions_from_db()
    except Exception as e:
        print(f"[启动] 会话恢复失败: {e}")

    print("[启动] 预热 RAGService...")
    try:
        from backend.services.rag_service import RAGService
        rag = RAGService()
        if rag.is_ready():
            print("[启动] RAG 服务就绪")
        else:
            print("[启动] ⚠️ RAG 向量未构建，将降级为纯 LLM 对话模式")
            print("[启动]    运行 python scripts/build_movie_embeddings.py 构建向量库")
    except Exception as e:
        print(f"[启动] ⚠️ RAG 初始化失败: {e}")

    print("[启动] 预热 SemanticSearchService...")
    try:
        from backend.services.semantic_search import SemanticSearchService
        sem = SemanticSearchService()
        if sem.is_ready():
            print("[启动] 语义搜索服务就绪（向量检索 + TF‑IDF 降级）")
        else:
            print("[启动] ⚠️ 语义搜索向量未构建，将降级为 TF‑IDF 搜索")
    except Exception as e:
        print(f"[启动] ⚠️ 语义搜索初始化失败: {e}")

    yield
    print("[关闭] 服务停止")


# ======================== 应用实例 ========================

app = FastAPI(
    title="电影推荐系统 API",
    description="基于内容的电影推荐服务，支持相似电影查询和文本搜索",
    version="0.1.0",
    lifespan=lifespan,
)

CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_STR.split(",")]

# CORS 中间件 — 允许前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(recommender_router)
app.include_router(qa_router)
app.include_router(auth_router)

# 挂载静态文件：图表图片和词云（前端 AnalysisView 使用）
reports_path = PROJECT_ROOT / "reports"
if reports_path.exists():
    app.mount("/api/static", StaticFiles(directory=str(reports_path)), name="static")

# 挂载海报缓存目录 — 已缓存图片由 ASGI 直接返回，不经过 Python 代理处理器
CACHE_DIR = PROJECT_ROOT / "cache" / "images"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=str(CACHE_DIR)), name="images")


# ======================== 图片代理 ========================

DOUBAN_REFERER = "https://movie.douban.com/"
PROXY_TIMEOUT = 12.0

# 允许代理的域名白名单（防止被滥用为开放代理）
ALLOWED_IMAGE_HOSTS = {
    "img1.doubanio.com", "img2.doubanio.com", "img3.doubanio.com",
    "img9.doubanio.com", "img.doubanio.com",
    "img1.doubanio.life", "img2.doubanio.life",
}

# Content-Type → 文件后缀映射
CONTENT_TYPE_MAP = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/avif": ".avif",
}

import hashlib
from fastapi.responses import FileResponse


def _cache_key(url: str) -> str:
    """用 MD5 生成唯一缓存键。"""
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def _cache_path(cache_key: str, content_type: str) -> Path:
    """根据缓存键和 Content-Type 确定文件路径。"""
    ext = CONTENT_TYPE_MAP.get(content_type.split(";")[0].strip(), ".img")
    return CACHE_DIR / (cache_key + ext)


def _find_cached(cache_key: str) -> Path | None:
    """在缓存目录中查找匹配的缓存文件（可能的后缀都试一遍）。"""
    if not CACHE_DIR.exists():
        return None
    for ext in CONTENT_TYPE_MAP.values():
        p = CACHE_DIR / (cache_key + ext)
        if p.exists() and p.stat().st_size > 0:
            return p
    # 也检查无后缀匹配
    for f in CACHE_DIR.glob(f"{cache_key}.*"):
        if f.stat().st_size > 0:
            return f
    return None


@app.get("/api/image-proxy")
async def image_proxy(url: str = Query(..., description="原始图片 URL")):
    """
    图片代理 — 绕过豆瓣 Referer 防盗链 + 本地文件缓存。

    - 首次请求：从豆瓣服务器获取图片，保存到 cache/images/ 目录
    - 后续请求：直接从本地缓存返回，响应在毫秒级
    - 仅允许豆瓣图床域名，其他域名返回 403
    """
    from urllib.parse import urlparse

    host = urlparse(url).hostname or ""
    if host not in ALLOWED_IMAGE_HOSTS:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"detail": f"域名 {host} 不在代理白名单中"},
        )

    key = _cache_key(url)

    # ── 1) 命中缓存：直接返回本地文件 ──────────────
    cached = _find_cached(key)
    if cached is not None:
        content_type = _guess_content_type(cached.suffix)
        return FileResponse(
            cached,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=2592000, immutable",
                "X-Cache": "HIT",
            },
        )

    # ── 2) 未命中：请求豆瓣并落盘 ──────────────────
    headers = {
        "Referer": DOUBAN_REFERER,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    }

    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=e.response.status_code,
                content={"detail": f"上游图片服务器返回 {e.response.status_code}"},
            )
        except httpx.RequestError:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=502,
                content={"detail": "图片服务器连接超时，请稍后重试"},
            )

        body = resp.content
        content_type = resp.headers.get("content-type", "image/webp")

        # 写入缓存
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = _cache_path(key, content_type)
        cache_path.write_bytes(body)

        return StreamingResponse(
            iter([body]),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=2592000, immutable",
                "X-Cache": "MISS",
            },
        )


def _guess_content_type(suffix: str) -> str:
    """根据文件后缀反查 Content-Type。"""
    for ct, ext in CONTENT_TYPE_MAP.items():
        if ext == suffix:
            return ct
    return "image/webp"


# ======================== 基础端点 ========================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查 + 服务状态。"""
    from backend.services.recommender_service import RecommenderService
    service = RecommenderService()
    return HealthResponse(
        status="ok",
        movies_loaded=len(service),
        version=app.version,
    )


@app.get("/")
async def root():
    return {
        "message": "电影推荐系统 API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "similar": "/api/recommend/similar/{movie_id}?top_n=10",
            "search": "/api/recommend/search  (POST, body: {query, top_n})",
        },
    }


# ======================== 启动入口 ========================

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8002"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
    )
