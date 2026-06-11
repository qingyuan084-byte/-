"""
QA 模块筛选解析 — 从用户消息/LLM tool_args 提取筛选参数并应用到数据集。
"""
import re

from backend.services.qa.formatting import _parse_genres, _parse_countries


def parse_filter_action(message: str) -> str:
    """从用户消息中解析筛选操作类型。"""
    if any(kw in message for kw in ["重置", "清除", "清空", "重来", "取消"]):
        return "reset"
    if any(kw in message for kw in ["查看", "显示条件", "当前条件", "我的筛选"]):
        return "show"
    if any(kw in message for kw in ["去掉", "不要", "排除", "移除", "除了"]):
        return "remove"
    return "add"


def apply_tool_args(fs: dict, args: dict, action: str) -> dict:
    """将 LLM 提取的工具参数应用到筛选状态。"""
    if action == "set" or action == "add":
        if args.get("genres"):
            if action == "set":
                fs["genres"] = list(args["genres"])
            else:
                for g in args["genres"]:
                    if g not in fs["genres"]:
                        fs["genres"].append(g)

        if args.get("countries"):
            if action == "set":
                fs["countries"] = list(args["countries"])
            else:
                for c in args["countries"]:
                    if c not in fs["countries"]:
                        fs["countries"].append(c)

        if args.get("year_min") is not None or args.get("year_max") is not None:
            if args.get("year_min") is not None:
                fs["year_range"][0] = args["year_min"]
            if args.get("year_max") is not None:
                fs["year_range"][1] = args["year_max"]

        if args.get("rating_min") is not None or args.get("rating_max") is not None:
            if args.get("rating_min") is not None:
                fs["rating_range"][0] = args["rating_min"]
            if args.get("rating_max") is not None:
                fs["rating_range"][1] = args["rating_max"]

        if args.get("sort_by"):
            fs["sort_by"] = args["sort_by"]

    elif action == "remove":
        if args.get("genres"):
            for g in args["genres"]:
                if g in fs["genres"]:
                    fs["genres"].remove(g)
        if args.get("countries"):
            for c in args["countries"]:
                if c in fs["countries"]:
                    fs["countries"].remove(c)
        # 年份/评分 remove → 重置为默认范围
        if args.get("year_min") is not None or args.get("year_max") is not None:
            fs["year_range"] = [1900, 2030]
        if args.get("rating_min") is not None or args.get("rating_max") is not None:
            fs["rating_range"] = [0, 10]

    return fs


def parse_filter_from_message(fs: dict, message: str, action: str) -> dict:
    """从用户消息中提取筛选参数（关键词/正则方式，无 LLM 参与）。"""
    if action == "remove":
        return fs  # 复杂移除交给 LLM

    # 类型筛选
    genre_set = {
        "科幻", "悬疑", "喜剧", "动作", "爱情", "恐怖", "动画",
        "犯罪", "战争", "奇幻", "冒险", "剧情", "历史", "古装",
        "武侠", "纪录片", "惊悚", "音乐", "歌舞", "家庭",
    }
    for genre in genre_set:
        if genre in message:
            if genre not in fs["genres"]:
                fs["genres"].append(genre)

    # 国家/地区
    country_map = {
        "中国": "中国大陆", "国产": "中国大陆", "大陆": "中国大陆",
        "美国": "美国", "好莱坞": "美国",
        "日本": "日本", "韩国": "韩国", "英国": "英国",
        "法国": "法国", "德国": "德国", "印度": "印度",
        "香港": "中国香港", "台湾": "中国台湾",
    }
    for kw, country in country_map.items():
        if kw in message:
            if country not in fs["countries"]:
                fs["countries"].append(country)

    # 年份
    year_match = re.search(r"(\d{4})\s*年\s*以\s*后", message)
    if year_match:
        fs["year_range"][0] = int(year_match.group(1))
    year_match = re.search(r"(\d{4})\s*年\s*以\s*前", message)
    if year_match:
        fs["year_range"][1] = int(year_match.group(1))
    year_match = re.search(r"(\d{4})\s*-\s*(\d{4})", message)
    if year_match:
        fs["year_range"][0] = int(year_match.group(1))
        fs["year_range"][1] = int(year_match.group(2))
    decade_match = re.search(r"(\d{2})\s*年代", message)
    if decade_match:
        d = int(decade_match.group(1))
        fs["year_range"] = [1900 + d, 1900 + d + 9]

    # 评分
    rating_match = re.search(r"(\d+(?:\.\d+)?)\s*分?\s*以\s*上", message)
    if rating_match:
        fs["rating_range"][0] = float(rating_match.group(1))
    rating_match = re.search(r"(\d+(?:\.\d+)?)\s*分?\s*以\s*下", message)
    if rating_match:
        fs["rating_range"][1] = float(rating_match.group(1))

    return fs


def apply_filters(fs: dict, movies: list[dict]) -> list[dict]:
    """根据筛选状态过滤电影列表。"""
    if not movies:
        return []

    # 类型筛选
    if fs.get("genres"):
        movies = [
            m for m in movies
            if any(g in _parse_genres(m.get("genres", "")) for g in fs["genres"])
        ]

    # 国家筛选
    if fs.get("countries"):
        movies = [
            m for m in movies
            if any(c in _parse_countries(m.get("countries", "")) for c in fs["countries"])
        ]

    # 年份筛选
    yr = fs.get("year_range", [1900, 2030])
    movies = [
        m for m in movies
        if m.get("year") and yr[0] <= m["year"] <= yr[1]
    ]

    # 评分筛选
    rr = fs.get("rating_range", [0, 10])
    movies = [
        m for m in movies
        if rr[0] <= (m.get("rating") or 0) <= rr[1]
    ]

    # 排序
    sort_by = fs.get("sort_by", "rating")
    if sort_by == "rating":
        movies.sort(key=lambda m: m.get("rating") or 0, reverse=True)
    elif sort_by == "year":
        movies.sort(key=lambda m: m.get("year") or 0, reverse=True)
    elif sort_by == "title":
        movies.sort(key=lambda m: m.get("title", ""))

    return movies
