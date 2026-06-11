"""
用户认证与收藏 API 路由。

端点:
  POST /api/auth/register      — 注册
  POST /api/auth/login         — 登录
  POST /api/auth/logout        — 登出
  GET  /api/auth/check         — 验证会话
  GET  /api/auth/profile       — 用户信息
  POST /api/favorites/toggle   — 切换收藏
  GET  /api/favorites          — 收藏 ID 列表
  GET  /api/favorites/detail   — 收藏电影详情列表
"""
from fastapi import APIRouter, HTTPException, Header, Depends

from backend.models.auth_models import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    CheckAuthResponse,
    UserProfile,
    FavoriteToggleRequest,
    FavoriteToggleResponse,
    FavoriteListResponse,
    FavoriteMoviesResponse,
)
from backend.services.auth_service import (
    register as _register,
    login as _login,
    logout as _logout,
    validate_session,
    toggle_favorite as _toggle_favorite,
    get_user_favorites,
    get_user_profile,
)

router = APIRouter(tags=["auth"])


# ── 认证依赖 ──────────────────────────────────────────

def get_current_user(authorization: str = Header(None)) -> dict:
    """
    FastAPI 依赖注入：从 Authorization header 提取 Bearer token 并验证。
    返回 {'user_id': str, 'username': str, 'token': str}，认证失败抛出 401。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    token = authorization[7:]
    user = validate_session(token)
    if user is None:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    user["token"] = token
    return user


# ── 认证端点 ──────────────────────────────────────────

@router.post("/api/auth/register", response_model=AuthResponse)
async def register_user(body: RegisterRequest):
    """注册新用户。成功返回 session token。"""
    success, result = _register(body.username, body.password)
    if success:
        return AuthResponse(success=True, token=result, username=body.username)
    return AuthResponse(success=False, message=result)


@router.post("/api/auth/login", response_model=AuthResponse)
async def login_user(body: LoginRequest):
    """用户登录。成功返回 session token。"""
    success, result = _login(body.username, body.password)
    if success:
        return AuthResponse(success=True, token=result, username=body.username)
    return AuthResponse(success=False, message=result)


@router.post("/api/auth/logout")
async def logout_user(user: dict = Depends(get_current_user)):
    """登出，销毁当前会话。"""
    _logout(user["token"])
    return {"success": True, "message": "已退出登录"}


@router.get("/api/auth/check", response_model=CheckAuthResponse)
async def check_auth(user: dict = Depends(get_current_user)):
    """检查当前认证状态。"""
    return CheckAuthResponse(authenticated=True, username=user["username"])


@router.get("/api/auth/profile", response_model=UserProfile)
async def get_profile(user: dict = Depends(get_current_user)):
    """获取当前用户信息。"""
    profile = get_user_profile(user["user_id"])
    if profile is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    from datetime import datetime, timezone
    created_at_dt = datetime.fromtimestamp(profile["created_at"], tz=timezone.utc)
    return UserProfile(
        username=profile["username"],
        created_at=created_at_dt.isoformat(),
        favorite_count=profile["favorite_count"],
    )


# ── 收藏端点 ──────────────────────────────────────────

@router.post("/api/favorites/toggle", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    body: FavoriteToggleRequest,
    user: dict = Depends(get_current_user),
):
    """切换某部电影的收藏状态（收藏↔取消收藏）。"""
    result = _toggle_favorite(user["user_id"], body.movie_id)
    return FavoriteToggleResponse(**result)


@router.get("/api/favorites", response_model=FavoriteListResponse)
async def list_favorites(user: dict = Depends(get_current_user)):
    """获取当前用户的收藏电影 ID 列表。"""
    fav_ids = get_user_favorites(user["user_id"])
    return FavoriteListResponse(favorites=fav_ids)


@router.get("/api/favorites/detail", response_model=FavoriteMoviesResponse)
async def list_favorites_detail(user: dict = Depends(get_current_user)):
    """获取收藏电影的完整详情列表。"""
    fav_ids = get_user_favorites(user["user_id"])
    if not fav_ids:
        return FavoriteMoviesResponse(movies=[], total=0)

    from backend.services.recommender_service import RecommenderService
    service = RecommenderService()
    movies = []
    for mid in fav_ids:
        detail = service.get_movie_detail(mid)
        if detail:
            movies.append(detail)

    return FavoriteMoviesResponse(movies=movies, total=len(movies))
