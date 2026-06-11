"""
豆瓣电影数据 — 特征工程

从清洗后的数据构造三类特征：
  1. 类型多热编码（MultiLabelBinarizer）
  2. 文本 TF-IDF（TfidfVectorizer, max_features=300）
  3. 数值特征（评分、评价人数、年份）

所有特征矩阵和辅助文件保存到 data/features/ 目录。
"""

import ast
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import save_npz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer

# Windows 终端编码兼容
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ======================== 路径配置 ========================

INPUT_PATH = Path("data/processed/douban_movies_cleaned.csv")
FEATURES_DIR = Path("data/features")

GENRE_OUTPUT = FEATURES_DIR / "genre_features.csv"
TFIDF_OUTPUT = FEATURES_DIR / "tfidf_matrix.npz"
VECTORIZER_OUTPUT = FEATURES_DIR / "tfidf_vectorizer.joblib"
MOVIE_IDS_OUTPUT = FEATURES_DIR / "movie_ids.csv"


# ======================== 工具函数 ========================

def parse_genre_list(val) -> list[str]:
    """
    将 CSV 中的字符串 "['剧情', '喜剧']" 还原为 Python list。
    兼容 NaN、空字符串、已经是 list 的情况。
    """
    if isinstance(val, list):
        return val
    if pd.isna(val) or str(val).strip() == "" or str(val).strip() == "[]":
        return []
    try:
        return ast.literal_eval(str(val))
    except (ValueError, SyntaxError):
        # 兜底：按逗号拆分
        return [g.strip().strip("'\"") for g in str(val).strip("[]").split(",") if g.strip()]


# ======================== 主流程 ========================

def build_features(input_path: Path = INPUT_PATH, output_dir: Path = FEATURES_DIR):
    """读取数据 → 构造特征 → 保存到磁盘。"""

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. 读取数据 ──────────────────────────────────
    df = pd.read_csv(input_path, dtype={"movie_id": str})
    print(f"[读取] {len(df)} 条记录")
    print(f"  列名: {list(df.columns)}")

    # ── 2. 类型多热编码 ──────────────────────────────
    print("\n" + "=" * 50)
    print("1. 类型多热编码 (MultiLabelBinarizer)")

    df["genre_list_parsed"] = df["genre_list"].apply(parse_genre_list)
    mlb = MultiLabelBinarizer()
    genre_matrix = mlb.fit_transform(df["genre_list_parsed"])
    genre_names = [f"genre_{g}" for g in mlb.classes_]

    print(f"  电影数量: {genre_matrix.shape[0]}")
    print(f"  类型数量: {genre_matrix.shape[1]}")
    print(f"  类型列表: {mlb.classes_.tolist()}")

    # 保存（带列名，便于后续分析）
    genre_df = pd.DataFrame(genre_matrix, columns=genre_names, index=df.index)
    genre_df.to_csv(GENRE_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"  已保存: {GENRE_OUTPUT}")

    # ── 3. TF-IDF 文本特征 ───────────────────────────
    print("\n" + "=" * 50)
    print("2. TF-IDF 文本特征 (TfidfVectorizer)")

    # 拼接 title + summary
    df["text"] = df["title"].fillna("") + " " + df["summary"].fillna("暂无简介")

    tfidf = TfidfVectorizer(
        max_features=300,
        analyzer="char_wb",          # 字符级 n-gram，对中文更友好
        ngram_range=(2, 4),          # 2-4 字组合
        min_df=2,                    # 至少在 2 部电影中出现
    )
    tfidf_matrix = tfidf.fit_transform(df["text"])

    print(f"  TF-IDF 矩阵形状: {tfidf_matrix.shape}")
    print(f"  特征词示例: {tfidf.get_feature_names_out()[:20].tolist()}")

    # 保存稀疏矩阵
    save_npz(TFIDF_OUTPUT, tfidf_matrix)
    print(f"  已保存: {TFIDF_OUTPUT}")

    # 保存 vectorizer（用于后续 transform 新数据）
    joblib.dump(tfidf, VECTORIZER_OUTPUT)
    print(f"  已保存: {VECTORIZER_OUTPUT}")

    # ── 4. 数值特征 ──────────────────────────────────
    print("\n" + "=" * 50)
    print("3. 数值特征")

    num_cols = ["rating", "total_ratings", "release_year"]
    existing = [c for c in num_cols if c in df.columns]
    missing = [c for c in num_cols if c not in df.columns]
    if missing:
        print(f"  [警告] 以下列不存在: {missing}")

    # 确保类型正确
    for c in existing:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    print(f"  数值特征列: {existing}")

    # ── 5. 保存电影 ID / 标题对照表 ──────────────────
    print("\n" + "=" * 50)
    print("4. 电影 ID 对照表")

    ids_df = df[["movie_id", "title"]].copy()
    ids_df.to_csv(MOVIE_IDS_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"  已保存: {MOVIE_IDS_OUTPUT}")
    print(f"  记录数: {len(ids_df)}")

    # ── 6. 汇总 ──────────────────────────────────────
    print("\n" + "=" * 50)
    print("特征工程完成！汇总:")
    print(f"  电影数量:       {len(df)}")
    print(f"  类型特征维度:   {genre_matrix.shape[1]}")
    print(f"  TF-IDF 维度:   {tfidf_matrix.shape[1]}")
    print(f"  数值特征维度:   {len(existing)}")
    print(f"  输出目录:       {output_dir.resolve()}")


if __name__ == "__main__":
    build_features()
