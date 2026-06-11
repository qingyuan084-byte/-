"""
将豆瓣电影数据导入 PostgreSQL
===========================
从 data/processed/douban_movies_cleaned.csv 导入数据到 movies 表。

用法:
    # 按 movie_id upsert（默认，支持重复运行）
    python scripts/import_movies_to_db.py

    # 先清空再全量导入
    python scripts/import_movies_to_db.py --truncate

    # 指定 CSV 路径
    python scripts/import_movies_to_db.py --csv path/to/custom.csv
"""
import sys
import os
import argparse
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
env_file = PROJECT_ROOT / f".env.{os.getenv('APP_ENV', 'development')}"
if env_file.exists():
    load_dotenv(env_file, override=True)

import pandas as pd
from backend.db import get_session, create_tables, dispose_engine
from backend.repositories.movie_repository import MovieRepository
from backend.cache import flush_app_cache, delete_cache, build_cache_key

# ── CSV 列 → DB 列映射 ──────────────────────────────

# CSV 中的列名与 DB 模型字段完全一致（移除了 BOM 前缀）
CSV_COLUMNS = [
    "movie_id", "title", "rating", "total_ratings",
    "directors", "actors", "screenwriters", "release_date",
    "genres", "countries", "languages", "runtime",
    "summary", "link", "poster", "tags",
    "release_year", "genre_list",
]

# 需要在导入时转换类型的列
FLOAT_COLS = {"rating", "release_year"}
STR_COLS = set(CSV_COLUMNS) - FLOAT_COLS


def clean_row(row: dict) -> dict:
    """清洗单行数据：NaN → None，类型转换。"""
    cleaned = {}
    for col in CSV_COLUMNS:
        val = row.get(col)
        if pd.isna(val) or val == "nan" or val == "NaN" or val == "":
            cleaned[col] = None
        elif col in FLOAT_COLS:
            try:
                cleaned[col] = float(val)
            except (ValueError, TypeError):
                cleaned[col] = None
        else:
            cleaned[col] = str(val).strip()
    return cleaned


def main():
    parser = argparse.ArgumentParser(description="导入豆瓣电影数据到 PostgreSQL")
    parser.add_argument(
        "--csv",
        default=str(PROJECT_ROOT / "data" / "processed" / "douban_movies_cleaned.csv"),
        help="CSV 文件路径",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="先清空表再导入（默认按 movie_id upsert）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="每批提交的行数（默认 500）",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[ERROR] CSV 文件不存在: {csv_path}")
        sys.exit(1)

    # ── 连接数据库 ──────────────────────────────────
    create_tables()
    session = get_session()
    if session is None:
        print("[ERROR] 无法连接数据库，请检查 DATABASE_URL 环境变量")
        sys.exit(1)

    repo = MovieRepository(session)

    try:
        # ── 清空模式 ────────────────────────────────
        if args.truncate:
            repo.delete_all()
            session.commit()
            print("[OK] 已清空 movies 表")

        # ── 读 CSV ──────────────────────────────────
        print(f"[INFO] 正在读取 {csv_path} ...")
        # 处理 BOM 前缀
        df = pd.read_csv(csv_path, dtype=str)
        # 移除列名的 BOM
        df.columns = [c.lstrip("﻿").strip() for c in df.columns]
        total_rows = len(df)
        print(f"  CSV 共 {total_rows} 条记录")

        # ── 导入 ────────────────────────────────────
        imported = 0
        batch = []
        for _, row in df.iterrows():
            data = clean_row(row.to_dict())
            batch.append(data)

            if len(batch) >= args.batch_size:
                for item in batch:
                    repo.upsert_movie(item)
                session.commit()
                imported += len(batch)
                print(f"  已导入 {imported}/{total_rows} ... ({imported*100//total_rows}%)")
                batch = []

        # 处理剩余批次
        if batch:
            for item in batch:
                repo.upsert_movie(item)
            session.commit()
            imported += len(batch)

        # ── 验证 ────────────────────────────────────
        count = repo.count()
        print(f"[OK] 导入完成: {imported} 条处理, 表中现存 {count} 条")

        # ── 清理缓存 ────────────────────────────────
        deleted = flush_app_cache()
        if deleted:
            print(f"[OK] 已清理 {deleted} 个缓存键（stats/similar/search/rich）")
        else:
            print("[INFO] 缓存层不可用，跳过清理")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] 导入失败: {e}")
        raise
    finally:
        session.close()
        dispose_engine()


if __name__ == "__main__":
    main()
