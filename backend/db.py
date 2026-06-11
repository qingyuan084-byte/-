"""
数据库连接模块
============
封装 SQLAlchemy engine、Session、Base、get_db 依赖注入。

- 从 DATABASE_URL 读取连接信息
- 未配置时返回 None（所有组件自动降级到 CSV）
- 支持密码中的特殊字符自动转义
"""
import os
import re
from urllib.parse import quote

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session


def _normalize_db_url(raw: str) -> str:
    """
    规范化 DATABASE_URL，处理密码中的 @ 等特殊字符。

    策略：找到 user:pass@host 中最后一个 @，将之前的部分中的密码段 URL-encode。
    自动选择可用驱动：psycopg2 > pg8000 (如果都不可用则使用默认)。
    """
    if not raw:
        return raw

    # 统一去除驱动后缀
    for suffix in ("+asyncpg", "+psycopg2", "+psycopg", "+pg8000"):
        raw = raw.replace(suffix, "")

    # 自动选择可用驱动
    driver = _detect_driver()

    prefix = f"postgresql+{driver}://" if driver else "postgresql://"
    old_prefix = "postgresql://"
    if not raw.startswith(old_prefix):
        return raw

    rest = raw[len(old_prefix):]
    if "@" not in rest:
        return raw

    # 最后一个 @ 分隔 user:password 和 host
    last_at = rest.rindex("@")
    user_pass = rest[:last_at]
    host_db = rest[last_at + 1:]

    if ":" in user_pass:
        user, password = user_pass.split(":", 1)
        password = quote(password, safe="")
        return f"{prefix}{user}:{password}@{host_db}"

    return f"{prefix}{user_pass}@{host_db}"


def _detect_driver() -> str:
    """检测可用的 PostgreSQL 驱动。"""
    try:
        import psycopg2  # noqa: F401
        return "psycopg2"
    except ImportError:
        pass
    try:
        import pg8000  # noqa: F401
        return "pg8000"
    except ImportError:
        pass
    return ""


# ── 引擎 ──────────────────────────────────────────────

_engine = None
_SessionLocal: sessionmaker | None = None
Base = declarative_base()


def _init_engine():
    """延迟初始化引擎（首次调用 get_db 时）。"""
    global _engine, _SessionLocal
    if _engine is not None:
        return

    # 每次初始化时重新读取并规范化 URL（支持运行时安装驱动）
    raw = os.getenv("DATABASE_URL", "")
    db_url = _normalize_db_url(raw)
    if not db_url:
        return  # 无数据库配置，保持 None

    try:
        _engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        # 验证连接
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[DB] PostgreSQL 连接成功 ({db_url.split('://')[0]})")
    except Exception as e:
        print(f"[DB] 数据库连接失败: {e}")
        print(f"[DB] 将使用 CSV 文件作为数据源")
        _engine = None
        _SessionLocal = None


def get_db() -> Session | None:
    """
    FastAPI 依赖注入：获取数据库会话。

    用法:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    if _SessionLocal is None:
        _init_engine()
    if _SessionLocal is None:
        return None  # 无数据库，调用方需自行降级

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Session | None:
    """
    非 FastAPI 上下文（脚本、服务层）使用：直接获取一个 Session。

    返回 None 表示数据库不可用。
    """
    if _SessionLocal is None:
        _init_engine()
    if _SessionLocal is None:
        return None
    return _SessionLocal()


def is_db_available() -> bool:
    """检查数据库是否可用。"""
    if _SessionLocal is None:
        _init_engine()
    return _SessionLocal is not None


def dispose_engine():
    """关闭连接池（用于测试清理）。"""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
        _engine = None
        _SessionLocal = None


def create_tables():
    """创建所有 ORM 映射表（幂等，仅建不存在的表）。"""
    if _engine is None:
        _init_engine()
    if _engine is None:
        raise RuntimeError("数据库不可用，无法创建表")
    # 导入所有模型以注册到 Base.metadata
    import backend.models.db_models  # noqa: F401
    try:
        Base.metadata.create_all(bind=_engine)
        print("[DB] 表结构检查/创建完成")
    except Exception as e:
        print(f"[DB] 表创建失败: {e}")
        print("[DB] 请确认数据库用户有 CREATE TABLE 权限:")
        print("[DB]   GRANT CREATE ON SCHEMA public TO 你的用户名;")
        raise
