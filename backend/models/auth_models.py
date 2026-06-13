"""
认证相关的 Pydantic 请求/响应模型。
"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=30, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class AuthResponse(BaseModel):
    """认证响应（注册/登录成功时返回 token）"""
    success: bool
    token: str = ""
    username: str = ""
    message: str = ""


class CheckAuthResponse(BaseModel):
    """检查认证状态响应"""
    authenticated: bool
    username: str = ""


class UserProfile(BaseModel):
    """用户信息"""
    username: str
    created_at: str = ""  # ISO 格式
    favorite_count: int = 0


class FavoriteToggleRequest(BaseModel):
    """收藏切换请求"""
    movie_id: str = Field(..., min_length=1, description="豆瓣 movie_id")


class FavoriteToggleResponse(BaseModel):
    """收藏切换响应"""
    movie_id: str
    is_favorited: bool


class FavoriteListResponse(BaseModel):
    """收藏列表响应（仅 ID）"""
    favorites: list[str] = Field(default_factory=list)


class FavoriteMoviesResponse(BaseModel):
    """收藏电影详情列表响应"""
    movies: list[dict] = Field(default_factory=list)
    total: int = 0


# ── 评分模型 ──────────────────────────────────────────

class RatingSetRequest(BaseModel):
    """评分设置请求"""
    movie_id: str = Field(..., min_length=1, description="豆瓣 movie_id")
    rating: float = Field(..., ge=1.0, le=5.0, description="评分 1.0-5.0，支持 0.5 步进")


class RatingSetResponse(BaseModel):
    """评分设置响应"""
    movie_id: str
    rating: float
    is_new: bool
    is_removed: bool = False


class RatingGetResponse(BaseModel):
    """单部电影评分查询响应"""
    movie_id: str
    rating: float | None = None


class RatingListResponse(BaseModel):
    """用户所有评分列表响应"""
    ratings: dict[str, float] = Field(default_factory=dict)
    total: int = 0
