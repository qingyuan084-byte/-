"""
交互式图表模块 (Plotly)

生成 HTML 可视化，支持缩放、悬停、筛选。
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def plot_rating_histogram_interactive(df: pd.DataFrame) -> go.Figure:
    """交互式评分分布直方图。"""
    fig = px.histogram(
        df,
        x="rating",
        nbins=40,
        title="豆瓣电影评分分布",
        labels={"rating": "评分"},
        color_discrete_sequence=["#409eff"],
        opacity=0.8,
    )
    fig.add_vline(
        x=df["rating"].mean(),
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f'均值 {df["rating"].mean():.2f}',
    )
    fig.update_layout(
        xaxis_title="评分",
        yaxis_title="电影数量",
        bargap=0.05,
        template="plotly_white",
        title_font_size=20,
    )
    path = REPORTS_DIR / "rating_distribution.html"
    fig.write_html(path)
    print(f"  [OK] {path}")
    return fig


def plot_genres_pie(df: pd.DataFrame) -> go.Figure:
    """类型热度交互饼图（Top 15）。"""
    import ast
    from collections import Counter

    all_genres = []
    genre_col = "genre_list_parsed" if "genre_list_parsed" in df.columns else None
    if genre_col is None and "genre_list" in df.columns:
        for val in df["genre_list"]:
            if isinstance(val, str):
                try:
                    all_genres.extend(ast.literal_eval(val))
                except (ValueError, SyntaxError):
                    pass
            elif isinstance(val, list):
                all_genres.extend(val)
    elif genre_col:
        for gl in df[genre_col]:
            all_genres.extend(gl)

    if not all_genres:
        print("  [警告] 未找到类型数据")
        return None

    top = Counter(all_genres).most_common(15)
    labels, values = zip(*top)

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo="label+percent",
            marker_colors=px.colors.qualitative.Set3,
        )
    )
    fig.update_layout(
        title="电影类型热度分布 (Top 15)",
        template="plotly_white",
        title_font_size=20,
        legend=dict(orientation="v", x=1.02, y=1),
    )
    path = REPORTS_DIR / "genres_pie.html"
    fig.write_html(path)
    print(f"  [OK] {path}")
    return fig


def plot_year_rating_scatter(df: pd.DataFrame) -> go.Figure:
    """年份 vs 评分散点图（气泡大小 = 评价人数）。"""
    plot_df = df.dropna(subset=["release_year", "rating", "total_ratings"]).copy()
    plot_df = plot_df[plot_df["release_year"] > 1900]
    # 评价人数取对数，让气泡更均匀
    plot_df["log_ratings"] = np.log1p(plot_df["total_ratings"])

    fig = px.scatter(
        plot_df,
        x="release_year",
        y="rating",
        size="log_ratings",
        hover_name="title",
        hover_data={
            "rating": ":.1f",
            "total_ratings": True,
            "release_year": True,
            "log_ratings": False,
        },
        title="年份 vs 评分（气泡 = 评价人数）",
        color="rating",
        color_continuous_scale="RdYlGn",
        opacity=0.7,
    )
    fig.update_layout(
        xaxis_title="上映年份",
        yaxis_title="豆瓣评分",
        template="plotly_white",
        title_font_size=20,
    )
    path = REPORTS_DIR / "year_rating_scatter.html"
    fig.write_html(path)
    print(f"  [OK] {path}")
    return fig
