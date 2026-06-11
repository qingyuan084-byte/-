"""
电影推荐系统 — Backend 包
自动加载 .env 环境变量，确保所有子模块独立导入时也能读取配置。
"""
import os
from pathlib import Path

# 项目根目录 (backend 的父目录)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加载 .env（首次导入 backend 包时自动执行）
from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")
_APP_ENV = os.getenv("APP_ENV", "development")
_env_override = _PROJECT_ROOT / f".env.{_APP_ENV}"
if _env_override.exists():
    load_dotenv(_env_override, override=True)
