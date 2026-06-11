"""
Pydantic 数据模型 — 推荐系统的请求/响应定义
"""

from pydantic import BaseModel, Field


class MovieRecommendation(BaseModel):
    """单条推荐结果"""
    movie_id: str = Field(..., description="豆瓣 movie_id")
    title: str = Field(..., description="电影标题")
    similarity_score: float = Field(..., description="相似度分数 (0-1)")
    poster_url: str = Field(default="", description="海报图片 URL")
    rating: float = Field(default=0.0, description="豆瓣评分")
    year: int | None = Field(default=None, description="上映年份")


class MovieDetail(BaseModel):
    """电影详情"""
    movie_id: str
    title: str
    rating: float = 0.0
    year: int | None = None
    poster_url: str = ""
    genres: str = ""
    summary: str = ""
    directors: str = ""
    actors: str = ""
    countries: str = ""
    runtime: str = ""
    total_ratings: str = ""
    release_date: str = ""


class RecommendResponse(BaseModel):
    """推荐响应"""
    movies: list[MovieRecommendation] = Field(default_factory=list, description="推荐电影列表")
    total: int = Field(default=0, description="结果总数")


class TextQueryRequest(BaseModel):
    """文本搜索请求"""
    query: str = Field(..., min_length=1, max_length=500, description="搜索文本")
    top_n: int = Field(default=10, ge=1, le=50, description="返回数量")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="ok")
    movies_loaded: int = Field(default=0)
    version: str = Field(default="0.1.0")


class StatsResponse(BaseModel):
    """数据分析统计响应"""
    total_movies: int = 0
    avg_rating: float = 0.0
    top_movie: dict = Field(default_factory=lambda: {"title": "", "rating": 0.0})
    latest_year: int = 0
    year_span: int = 0


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, max_length=1000, description="用户消息")
    history: list[dict] = Field(default_factory=list, description="历史消息（兼容旧版）")
    session_id: str | None = Field(default=None, description="会话 ID，用于服务端记忆")


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str = Field(..., description="AI 回复")
    related_movies: list[MovieRecommendation] = Field(default_factory=list, description="相关电影列表")


# ── 分页模型 ──────────────────────────────────────────

class PaginatedMovies(BaseModel):
    """分页电影基础信息响应"""
    items: list[MovieDetail] = Field(default_factory=list, description="当前页电影列表")
    total: int = Field(default=0, description="匹配总数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=30, description="每页大小")
    pages: int = Field(default=0, description="总页数")
