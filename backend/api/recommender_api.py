"""
推荐 API 路由

提供端点：
  GET  /api/movies                      — 分页电影列表（支持搜索）
  GET  /api/movies/rich                 — 分页电影完整信息（支持筛选/排序）
  GET  /api/movies/random               — 随机一部高分电影
  GET  /api/movie/{movie_id}            — 单部电影详情（优先数据库）
  GET  /api/recommend/similar/{movie_id} — 按电影 ID 找相似电影
  POST /api/recommend/search             — 按文本搜索电影
  GET  /api/stats                        — 数据集统计（优先数据库）
"""

import math
import random
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from backend.models.pydantic_models import (
    MovieRecommendation,
    MovieDetail,
    RecommendResponse,
    TextQueryRequest,
    StatsResponse,
    PaginatedMovies,
)
from backend.services.recommender_service import RecommenderService

router = APIRouter(tags=["recommend"])

# 懒加载单例
_service: RecommenderService | None = None


def get_service() -> RecommenderService:
    global _service
    if _service is None:
        _service = RecommenderService()
    return _service


class MovieItem(BaseModel):
    movie_id: str
    title: str
    rating: float = 0.0


@router.get("/api/movies", response_model=PaginatedMovies)
async def list_movies(
    q: str = Query(default="", description="搜索电影标题"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=30, ge=1, le=100, description="每页大小"),
):
    """
    分页查询电影基础信息（movie_id, title, rating）。

    - **q**: 可选，按标题模糊搜索
    - **page**: 页码，从 1 开始
    - **page_size**: 每页大小，1-100
    """
    service = get_service()
    movies, total = service.list_movies(q=q, page=page, page_size=page_size)
    return PaginatedMovies(
        items=[MovieDetail(**m) for m in movies],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/api/movies/rich", response_model=PaginatedMovies)
async def list_movies_rich(
    q: str = Query(default="", description="搜索电影标题"),
    genre: str | None = Query(default=None, description="按类型筛选（如：科幻、喜剧）"),
    country: str | None = Query(default=None, description="按国家/地区筛选"),
    year_min: int | None = Query(default=None, description="年份下限"),
    year_max: int | None = Query(default=None, description="年份上限"),
    rating_min: float | None = Query(default=None, ge=0, le=10, description="评分下限"),
    rating_max: float | None = Query(default=None, ge=0, le=10, description="评分上限"),
    sort_by: str = Query(default="rating", description="排序字段：rating、year、total_ratings、title"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=30, ge=1, le=100, description="每页大小"),
):
    """
    分页查询电影完整信息（类型、简介、海报、演职员等），支持多维度筛选和排序。

    - **q**: 可选，按标题模糊搜索
    - **genre**: 可选，按电影类型筛选
    - **country**: 可选，按国家/地区筛选
    - **year_min / year_max**: 可选，年份范围
    - **rating_min / rating_max**: 可选，评分范围
    - **sort_by**: 排序字段，可选 rating / year / total_ratings / title
    - **page**: 页码，从 1 开始
    - **page_size**: 每页大小，1-100
    """
    ALLOWED_SORT = {"rating", "year", "total_ratings", "title"}
    if sort_by not in ALLOWED_SORT:
        raise HTTPException(status_code=422, detail=f"sort_by 只允许: {', '.join(sorted(ALLOWED_SORT))}")

    service = get_service()
    movies, total = service.list_movies_rich(
        q=q,
        genre=genre,
        country=country,
        year_min=year_min,
        year_max=year_max,
        rating_min=rating_min,
        rating_max=rating_max,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return PaginatedMovies(
        items=[MovieDetail(**m) for m in movies],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/api/movie/{movie_id}", response_model=MovieDetail)
async def get_movie_detail(movie_id: str):
    """
    根据 movie_id 获取单部电影详情（优先查数据库）。

    - **movie_id**: 豆瓣 movie_id（如 1292052）
    """
    service = get_service()
    detail = service.get_movie_detail(movie_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"找不到 movie_id={movie_id}")
    return MovieDetail(**detail)


@router.get("/api/recommend/similar/{movie_id}", response_model=RecommendResponse)
async def recommend_similar(
    movie_id: str,
    top_n: int = Query(default=10, ge=1, le=50, description="返回数量"),
):
    """
    根据电影 ID 推荐相似的电影。

    - **movie_id**: 豆瓣 movie_id（如 26752088）
    - **top_n**: 返回结果数量，1-50
    """
    service = get_service()

    try:
        results = service.recommend_by_movie(movie_id, top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐服务内部错误: {e}")

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"找不到 movie_id={movie_id}，请检查 ID 是否正确",
        )

    movies = [MovieRecommendation(**r) for r in results]
    return RecommendResponse(movies=movies, total=len(movies))


@router.post("/api/recommend/search", response_model=RecommendResponse)
async def recommend_by_text(body: TextQueryRequest):
    """
    根据文本描述搜索电影。

    请求体示例:
    ```json
    {"query": "科幻冒险大片 外太空探索", "top_n": 10}
    ```

    - **query**: 搜索文本（1-500 字）
    - **top_n**: 返回结果数量，1-50
    """
    service = get_service()

    try:
        results = service.recommend_by_text(body.query, body.top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐服务内部错误: {e}")

    movies = [MovieRecommendation(**r) for r in results]
    return RecommendResponse(movies=movies, total=len(movies))


@router.get("/api/movies/random")
async def random_movie():
    """
    随机返回一部高分电影（评分 ≥ 8.0），用于 Hero 横幅展示。
    """
    service = get_service()
    movies, _ = service.list_movies()
    high_rated = [m for m in movies if m.get("rating", 0) >= 8.0]
    if not high_rated:
        high_rated = movies
    chosen = random.choice(high_rated)
    return chosen


@router.get("/api/movies/banner")
async def banner_movies(n: int = Query(default=10, ge=1, le=20, description="返回数量")):
    """
    随机返回 N 部高分电影（评分 ≥ 7.5），用于首页轮播。
    每次请求返回不同的随机组合，包含海报 URL 等完整信息。
    """
    service = get_service()
    movies, _ = service.list_movies_rich(rating_min=7.5, sort_by="rating", page_size=500)
    if len(movies) < n:
        movies, _ = service.list_movies_rich(sort_by="rating", page_size=500)
    if len(movies) <= n:
        return movies
    chosen = random.sample(movies, n)
    return chosen


@router.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    返回数据集统计信息：总数、平均评分、最高分电影、年份跨度等。
    优先查数据库，不可用时用 CSV 计算。
    """
    service = get_service()
    try:
        stats = service.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计服务错误: {e}")
