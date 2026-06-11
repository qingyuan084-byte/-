"""
探索性数据分析 (EDA) — 主入口

读取清洗后的电影数据，输出统计信息，生成所有图表。
运行方式: python -m analysis.eda
"""

import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# 确保项目根目录在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.visualization.charts import (
    plot_genres_pie,
    plot_rating_histogram_interactive,
    plot_year_rating_scatter,
)
from analysis.visualization.wordcloud import (
    generate_summary_wordcloud,
    generate_title_wordcloud,
)

# ── 中文支持 ──────────────────────────────────────
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties

# 强制重建字体缓存
fm._load_fontmanager(try_read_cache=False)

# 查找中文字体文件路径
_CJK_CANDIDATES = ["Noto Sans SC", "SimHei", "Microsoft YaHei", "STXihei", "KaiTi"]
_cjk_font_path = None
_cjk_font_name = None
for f in fm.fontManager.ttflist:
    if f.name in _CJK_CANDIDATES:
        _cjk_font_path = f.fname
        _cjk_font_name = f.name
        break

if _cjk_font_path:
    _CJK_FONT = FontProperties(fname=_cjk_font_path)
    print(f"[字体] 使用: {_cjk_font_name} ({_cjk_font_path})")
else:
    _CJK_FONT = None
    print("[字体] 警告: 未找到中文字体")

matplotlib.rcParams["axes.unicode_minus"] = False

# seaborn 样式（不覆盖字体）
sns.set_style("whitegrid")

# ── 路径 ──────────────────────────────────────────
DATA_PATH = Path("data/processed/douban_movies_cleaned.csv")
FIGURES_DIR = Path("reports/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ======================== 加载数据 ========================

def load_data():
    df = pd.read_csv(DATA_PATH, dtype={"movie_id": str})
    # 确保数值类型正确
    for c in ["rating", "total_ratings", "release_year"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # 解析 genre_list
    import ast
    if "genre_list" in df.columns:
        df["genre_list_parsed"] = df["genre_list"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
        )
    return df


# ======================== 统计信息 ========================

def print_statistics(df):
    print("=" * 60)
    print("豆瓣电影数据 — 探索性数据分析")
    print("=" * 60)

    print(f"\n总电影数: {len(df)}")

    print(f"\n评分分布:")
    print(f"  均值:     {df['rating'].mean():.2f}")
    print(f"  中位数:   {df['rating'].median():.2f}")
    print(f"  标准差:   {df['rating'].std():.2f}")
    print(f"  最低:     {df['rating'].min():.2f}")
    print(f"  最高:     {df['rating'].max():.2f}")

    print(f"\n年份范围:")
    years = df["release_year"].dropna()
    print(f"  最早:     {int(years.min())}")
    print(f"  最新:     {int(years.max())}")
    print(f"  跨度:     {int(years.max()) - int(years.min())} 年")

    print(f"\n评价人数:")
    print(f"  总计:     {df['total_ratings'].sum():,}")
    print(f"  均值:     {df['total_ratings'].mean():,.0f}")
    print(f"  最高:     {df['total_ratings'].max():,}")

    # 类型统计
    if "genre_list_parsed" in df.columns:
        from collections import Counter
        all_genres = []
        for gl in df["genre_list_parsed"]:
            all_genres.extend(gl)
        genre_counter = Counter(all_genres)
        print(f"\n类型数量 (Top 10):")
        for g, c in genre_counter.most_common(10):
            pct = c / len(df) * 100
            print(f"  {g:6s}: {c:4d} ({pct:.1f}%)")

    # 缺失值
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print(f"\n缺失值:")
        for col, cnt in missing.items():
            print(f"  {col}: {cnt} ({cnt/len(df)*100:.1f}%)")

    print("=" * 60)


# ======================== 静态图表 ========================

def plot_rating_histogram(df):
    """评分分布直方图"""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(df["rating"].dropna(), bins=30, color="#409eff", edgecolor="white", alpha=0.85)
    ax.axvline(df["rating"].mean(), color="#e74c3c", linestyle="--", linewidth=2, label=f'均值 {df["rating"].mean():.2f}')
    ax.axvline(df["rating"].median(), color="#f39c12", linestyle="--", linewidth=2, label=f'中位数 {df["rating"].median():.2f}')
    ax.set_title("豆瓣电影评分分布", fontsize=16, fontweight="bold", fontproperties=_CJK_FONT)
    ax.set_xlabel("评分", fontproperties=_CJK_FONT)
    ax.set_ylabel("电影数量", fontproperties=_CJK_FONT)
    ax.legend(prop=_CJK_FONT)
    path = FIGURES_DIR / "rating_histogram.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {path}")


def plot_movies_per_year(df):
    """每年电影产量折线图"""
    year_counts = df["release_year"].value_counts().sort_index()
    year_counts = year_counts[year_counts.index > 1900]  # 过滤异常年份

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(year_counts.index, year_counts.values, color="#409eff", linewidth=2, marker="o", markersize=3)
    ax.fill_between(year_counts.index, year_counts.values, alpha=0.15, color="#409eff")
    ax.set_title("每年电影产量", fontsize=16, fontweight="bold", fontproperties=_CJK_FONT)
    ax.set_xlabel("年份", fontproperties=_CJK_FONT)
    ax.set_ylabel("电影数量", fontproperties=_CJK_FONT)
    path = FIGURES_DIR / "movies_per_year.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {path}")


def plot_avg_rating_by_year(df):
    """平均评分随年份变化"""
    yearly = df.dropna(subset=["release_year", "rating"])
    yearly = yearly[yearly["release_year"] > 1900]
    avg = yearly.groupby("release_year")["rating"].agg(["mean", "count"])
    avg = avg[avg["count"] >= 3]  # 至少 3 部电影的年份

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax1.bar(avg.index, avg["count"], color="#e0e0e0", label="电影数量", alpha=0.8)
    ax1.set_ylabel("电影数量", color="#999", fontproperties=_CJK_FONT)
    ax2 = ax1.twinx()
    ax2.plot(avg.index, avg["mean"], color="#e74c3c", linewidth=2.5, marker="o", markersize=3, label="平均评分")
    ax2.set_ylabel("平均评分", color="#e74c3c", fontproperties=_CJK_FONT)
    ax2.set_ylim(0, 10)
    ax1.set_title("平均评分随年份变化趋势", fontsize=16, fontweight="bold", fontproperties=_CJK_FONT)
    ax1.set_xlabel("年份", fontproperties=_CJK_FONT)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", prop=_CJK_FONT)
    path = FIGURES_DIR / "avg_rating_by_year.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {path}")


def plot_top_genres(df):
    """Top 10 类型条形图"""
    if "genre_list_parsed" not in df.columns:
        print("  [跳过] genre_list_parsed 列不存在")
        return
    from collections import Counter
    all_genres = []
    for gl in df["genre_list_parsed"]:
        all_genres.extend(gl)
    top = Counter(all_genres).most_common(10)
    labels, values = zip(*top)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("viridis", len(labels))
    bars = ax.barh(list(reversed(labels)), list(reversed(values)), color=list(reversed(colors)))
    ax.set_title("电影类型 Top 10", fontsize=16, fontweight="bold", fontproperties=_CJK_FONT)
    ax.set_xlabel("出现次数", fontproperties=_CJK_FONT)
    for label in ax.get_yticklabels():
        label.set_fontproperties(_CJK_FONT)
    for bar, val in zip(bars, list(reversed(values))):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=10)
    path = FIGURES_DIR / "top_genres.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {path}")


# ======================== 主函数 ========================

def run_all():
    print("[加载] 读取数据...")
    df = load_data()

    print("\n[统计] 基本信息")
    print_statistics(df)

    print("\n[生成] 静态图表 (matplotlib/seaborn)")
    plot_rating_histogram(df)
    plot_movies_per_year(df)
    plot_avg_rating_by_year(df)
    plot_top_genres(df)

    print("\n[生成] 交互式图表 (plotly)")
    plot_rating_histogram_interactive(df)
    plot_genres_pie(df)
    plot_year_rating_scatter(df)

    print("\n[生成] 词云")
    generate_title_wordcloud(df)
    generate_summary_wordcloud(df)

    print(f"\n{'='*60}")
    print("全部完成! 输出目录:")
    print(f"  图表: {FIGURES_DIR.resolve()}")
    print(f"  交互: {Path('reports').resolve()}")
    print(f"  词云: {Path('reports').resolve()}")


if __name__ == "__main__":
    run_all()
