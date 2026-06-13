"""
QA 模块意图识别 — 关键词分类 + 电影名/字段提取。
"""
import re

from backend.services.qa.constants import (
    RECOMMEND_KEYWORDS,
    INFO_KEYWORDS,
    FILTER_KEYWORDS,
    FILTER_RESET_KEYWORDS,
)

# 人物 + 角色关键词模式：匹配 "宫崎骏导演的电影"、"诺兰的作品"、"汤姆汉克斯演的"
# group(1) = 人名, group(2) = 角色词
_PERSON_ROLE_RE = re.compile(
    r'([一-鿿\w·]{1,8}?)(导演|主演|拍的|的电影|的作品|导演的|演的|主演的|执导|作品的|拍摄)'
)


def extract_person_for_search(message: str) -> str | None:
    """从人物查询中提取人名，如 "宫崎骏导演的电影" → "宫崎骏"。

    当用户询问某导演/演员的作品但没有指定具体电影名时，
    提取人名用于搜索推荐。返回 None 表示未检测到人物查询模式。
    """
    msg = message.strip().replace(" ", "")
    m = _PERSON_ROLE_RE.search(msg)
    if not m:
        return None
    person = m.group(1)

    # 去除常见前缀（"推荐"、"找"、"想要" 等）
    _prefixes = ("推荐", "找", "想要", "想看", "有没有", "有没有什么")
    for pfx in sorted(_prefixes, key=len, reverse=True):
        if person.startswith(pfx):
            person = person[len(pfx):]
            break

    person = person.strip("，。,!！?？")
    if len(person) < 2:
        return None
    return person


def keyword_classify(message: str) -> str | None:
    """关键词规则快速分类，返回 intent 或 None（未命中）。"""
    msg = message.strip()

    # 短消息/纯闲聊不抢分类，交给 LLM 自然回复
    if len(msg) <= 3:
        return None

    # 明显的闲聊开头，不抢分类
    chat_starters = ("你好", "嗨", "hi", "hello", "嘿", "哈哈", "谢谢", "辛苦了", "晚安", "早安")
    if any(msg.lower().startswith(s) for s in chat_starters):
        return None

    # 1) 筛选重置 / 查看 → filter
    if any(kw in msg for kw in FILTER_RESET_KEYWORDS):
        return "filter"

    # 2) 电影名 + 查询词 → info
    has_movie_name = bool(re.search(r"《.+?》", msg))
    has_info_kw = any(kw in msg for kw in INFO_KEYWORDS)
    has_recommend_kw = any(kw in msg for kw in RECOMMEND_KEYWORDS)
    has_filter_kw = any(kw in msg for kw in FILTER_KEYWORDS)
    has_person = _PERSON_ROLE_RE.search(msg) and not has_movie_name

    if has_movie_name and has_info_kw:
        return "info"

    # 人物查询（"宫崎骏导演的电影"/"推荐宫崎骏导演的电影"）— 无具体电影名时路由到推荐
    if has_person:
        return "recommend"

    # 3) 筛选关键词 → filter（优先于 recommend）
    if has_filter_kw:
        return "filter"

    # 4) 只有查询词且明确指向某部电影 → info
    if has_info_kw and not has_recommend_kw:
        return "info"

    # 5) 明确推荐意图（含推荐词且消息较长）→ recommend
    if has_recommend_kw and not has_info_kw:
        # 太短的消息（如"好看的"）可能是随口一说，交给 LLM
        if len(msg) < 5:
            return None
        return "recommend"

    return None


def extract_movie_name(message: str) -> str | None:
    """从用户消息中提取电影名。"""
    match = re.search(r"《(.+?)》", message)
    if match:
        return match.group(1).strip()
    match = re.search(r"电影[《\s]*([^《》\s,，。.!！?？\d]+)", message)
    if match and len(match.group(1)) >= 2:
        return match.group(1).strip()
    return None


def extract_field(message: str) -> str:
    """从用户消息中提取查询字段类型。"""
    field_map = {
        "导演": "director", "主演": "actors", "演员": "actors",
        "评分": "rating", "多少分": "rating", "年份": "year",
        "哪一年": "year", "上映": "year", "类型": "genres",
        "剧情": "summary", "简介": "summary", "讲什么": "summary",
        "时长": "runtime", "多久": "runtime", "片长": "runtime",
        "国家": "countries", "哪里": "countries",
    }
    for kw, field in field_map.items():
        if kw in message:
            return field
    return "all"
