"""
QA 模块格式化工具 — 纯函数，无外部依赖。
"""
import re


def _parse_genres(g) -> list[str]:
    """解析 genres 字段为字符串列表。"""
    if not g:
        return []
    if isinstance(g, list):
        return [x.strip() for x in g if x and str(x).strip()]
    return [x.strip() for x in str(g).split(",") if x.strip()]


def _parse_countries(c) -> list[str]:
    """解析 countries 字段为字符串列表。"""
    if not c:
        return []
    if isinstance(c, list):
        return [x.strip() for x in c if x and str(x).strip()]
    return [x.strip() for x in re.split(r"[,，/]", str(c)) if x.strip()]


def _format_movie_context(movies: list[dict]) -> str:
    """将检索到的电影列表格式化为 LLM 可读的上下文文本。"""
    if not movies:
        return "（无匹配电影）"
    lines = []
    for i, m in enumerate(movies, 1):
        year_str = f" ({m['year']})" if m.get("year") else ""
        rating = m.get("rating", 0)
        genres = m.get("genres", "")
        summary = m.get("summary", "")
        directors = m.get("directors", "")
        countries = m.get("countries", "")
        lines.append(
            f"{i}. 《{m['title']}》{year_str}\n"
            f"   评分: {rating:.1f} | 类型: {genres} | 地区: {countries}\n"
            f"   导演: {directors}\n"
            f"   简介: {summary[:100]}"
        )
    return "\n\n".join(lines)


def _format_movie_info(movie: dict, field: str = "all") -> str:
    """将单部电影详情格式化为可读文本。"""
    lines = [f"🎬 **《{movie['title']}》** ({movie.get('year', '未知')})"]

    if field in ("rating", "all"):
        lines.append(f"⭐ 豆瓣评分: {movie.get('rating', 0)}")
    if field in ("genres", "all"):
        genres = movie.get("genres", "")
        if genres:
            lines.append(f"🎭 类型: {genres}")
    if field in ("director", "all"):
        directors = movie.get("directors", "")
        if directors:
            lines.append(f"🎬 导演: {directors}")
    if field in ("actors", "all"):
        actors = movie.get("actors", "")
        if actors:
            lines.append(f"👥 主演: {actors}")
    if field in ("countries", "all"):
        countries = movie.get("countries", "")
        if countries:
            lines.append(f"🌍 国家/地区: {countries}")
    if field in ("runtime", "all"):
        runtime = movie.get("runtime", "")
        if runtime:
            lines.append(f"⏱️ 片长: {runtime}")
    if field in ("summary", "all"):
        summary = movie.get("summary", "")
        if summary:
            lines.append(f"📝 简介: {summary}")

    return "\n".join(lines)


def _format_filter_state(fs: dict) -> str:
    """格式化当前筛选状态为可读摘要。"""
    parts = []
    if fs.get("genres"):
        parts.append(f"类型: {'、'.join(fs['genres'])}")
    if fs.get("countries"):
        parts.append(f"地区: {'、'.join(fs['countries'])}")
    yr = fs.get("year_range", [1900, 2030])
    if yr[0] > 1900 or yr[1] < 2030:
        parts.append(f"年份: {yr[0]}–{yr[1]}")
    rr = fs.get("rating_range", [0, 10])
    if rr[0] > 0 or rr[1] < 10:
        parts.append(f"评分: {rr[0]}–{rr[1]} 分")
    sort_label = {"rating": "评分降序", "year": "年份降序", "title": "标题"}.get(
        fs.get("sort_by", "rating"), "评分降序"
    )
    parts.append(f"排序: {sort_label}")

    if not parts or (len(parts) == 1 and parts[0].startswith("排序")):
        return "当前无筛选条件"
    return "当前筛选条件：" + " | ".join(parts)


def _compute_filter_active(fs: dict) -> bool:
    """判断筛选状态是否有活跃条件。"""
    return bool(
        fs.get("genres")
        or fs.get("countries")
        or fs.get("year_range", [1900, 2030])[0] > 1900
        or fs.get("year_range", [1900, 2030])[1] < 2030
        or fs.get("rating_range", [0, 10])[0] > 0
        or fs.get("rating_range", [0, 10])[1] < 10
    )
