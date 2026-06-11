"""
QA 模块常量 — 配置、提示词、工具定义、关键词列表。
"""
import os

# 智谱AI OpenAI 兼容 API 端点
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# 默认模型
DEFAULT_MODEL = "glm-4-flash"

# RAG / 搜索 检索数量
RETRIEVAL_TOP_K = 5

# 筛选结果最大展示数
FILTER_MAX_DISPLAY = 10

# 每会话最大历史消息数
MAX_HISTORY_MESSAGES = 20

# 默认筛选状态模板
DEFAULT_FILTER_STATE: dict = {
    "genres": [],
    "year_range": [1900, 2030],
    "rating_range": [0, 10],
    "countries": [],
    "sort_by": "rating",
    "active": False,
}

# ── 系统提示词 ──────────────────────────────────────

SYSTEM_PROMPT = (
    "你是登小千，一个热爱电影、知识渊博又亲切幽默的电影伙伴。"
    "你运行在 CinéMatic 电影推荐系统中，拥有一个包含 2125 部电影的数据库。\n\n"

    "【你的性格】\n"
    "- 温暖热情但不啰嗦，像一个对电影了如指掌的老朋友\n"
    "- 偶尔用轻松的调侃或电影梗活跃气氛\n"
    "- 认真对待用户的每个问题，用心推荐，不只是报菜名\n\n"

    "【你的能力】\n"
    "- 根据用户的情绪、场合、口味偏好推荐电影\n"
    "- 解读电影剧情、导演风格、演员表现\n"
    "- 闲聊也行——聊聊最近看的电影、电影节八卦、行业趣事\n"
    "- 用中文回复，口语化但不失专业感\n\n"

    "【推荐规范】\n"
    "- 每次推荐 3-5 部，用格式：🎬 **《电影名》** (年份) ⭐评分\n"
    "- 每部附上 1-2 句走心推荐理由（剧情亮点、情感共鸣点、适合什么心情看）\n"
    "- 优先推荐数据库里真实存在的电影，如果数据库没命中也可以结合你的知识补充\n"
    "- 如果用户说'还有吗''换一批''再来'，表示对上一批不满意，要换不同的推荐\n\n"

    "【对话原则】\n"
    "- 记住对话历史中用户提到的喜好（喜欢的类型、导演、演员），在后续推荐中体现\n"
    "- 用户聊非电影话题时，先正常回应，别第一时间扯回电影。只有话题自然关联到情感/故事/艺术时再引出推荐\n"
    "- 【重要】别硬扯：用户问1+1等于几，你就正常说等于2。别说什么'说到数字让我想起某部电影'\n"
    "- 别每句话都以'你好'开头，别反复自我介绍\n"
    "- 回复控制在 400 字以内"
)

RECOMMEND_POLISH_PROMPT = (
    "你是登小千，一个热爱电影、亲切幽默的电影伙伴。\n"
    "以下是根据用户需求从数据库检索到的电影列表。\n"
    "请用自然、有温度的语言向用户推荐，把推荐当成人际安利而不是机器输出。\n\n"

    "【推荐要求】\n"
    "- 先一句话回应用户的情绪或需求（如'今晚想找点烧脑的？我掏几部压箱底的给你'）\n"
    "- 推荐 3-5 部，格式：🎬 **《电影名》** (年份) ⭐评分 — 推荐理由\n"
    "- 推荐理由要有人情味，别说'该片评分较高'这种废话\n"
    "- 可以在最后问一句引导继续对话（如'有没有哪部让你心动？'）\n"
    "- 【严格禁止】编造不在下方列表中的电影\n"
    "- 如果列表明显不符合用户需求，诚实说'数据库没找到完美匹配的，但我凭记忆推荐几部…'\n"
    "- 控制在 400 字以内\n\n"

    "【用户需求】\n{user_message}\n\n"
    "【数据库检索结果】\n{movie_context}"
)

FILTER_POLISH_PROMPT = (
    "你是登小千。用户正在通过多轮对话筛选电影。\n"
    "当前筛选条件：{filter_summary}\n"
    "按{sort_label}排序，最多匹配 {FILTER_MAX_DISPLAY} 部显示：\n"
    "{movie_context}\n\n"
    "用轻松的语气告知筛选结果，列前 3-5 部。"
    "可以提一句'还有更多，要继续列出来吗？'"
    "控制在 250 字以内。"
)

RAG_INSTRUCTION = (
    "以下是从数据库检索到的电影。\n"
    "如果用户话题跟电影/故事/情感/艺术自然相关，就融入推荐。\n"
    "如果用户话题完全不相关（纯数学、编程、天气……），直接忽略，正常聊天。\n"
    "用你的语气推荐，别报搜索结果。\n\n"
    "【数据库检索结果】\n"
)

# ── LLM function calling 工具定义 ──────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "recommend_movies",
            "description": "用户希望获得电影推荐。根据用户描述的需求（类型、风格、主题等）搜索并推荐电影。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "用户的推荐需求描述，如'科幻冒险大片'、'类似星际穿越的电影'、'冷门悬疑片'",
                    },
                },
                "required": ["query_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_movie_info",
            "description": "用户想查询某部特定电影的详细信息（导演、主演、评分、年份、剧情简介等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_title": {
                        "type": "string",
                        "description": "电影名称，去除书名号等装饰符号",
                    },
                    "field": {
                        "type": "string",
                        "enum": ["director", "actors", "rating", "year", "genres", "summary", "runtime", "countries", "all"],
                        "description": "要查询的具体字段，'all' 表示全部信息。默认为 'all'。",
                    },
                },
                "required": ["movie_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_filters",
            "description": (
                "用户通过多轮对话逐步添加电影筛选条件。支持累积添加类型、年份范围、评分范围、"
                "国家地区、排序方式。也支持移除条件、重置全部条件、查看当前条件。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "set", "remove", "reset", "show"],
                        "description": "操作类型。add=追加到现有条件；set=替换某类条件；remove=移除某类条件；reset=清除所有条件；show=仅展示当前条件",
                    },
                    "genres": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "电影类型，如 ['科幻', '悬疑', '喜剧']",
                    },
                    "year_min": {
                        "type": "integer",
                        "description": "起始年份，如 2000",
                    },
                    "year_max": {
                        "type": "integer",
                        "description": "结束年份，如 2024",
                    },
                    "rating_min": {
                        "type": "number",
                        "description": "最低评分，如 8.0",
                    },
                    "rating_max": {
                        "type": "number",
                        "description": "最高评分，如 10.0",
                    },
                    "countries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "国家/地区，如 ['中国大陆', '美国', '日本']",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["rating", "year", "title"],
                        "description": "排序方式：rating=按评分降序，year=按年份降序，title=按标题排序",
                    },
                },
                "required": ["action"],
            },
        },
    },
]

# ── 关键词列表 ─────────────────────────────────────

RECOMMEND_KEYWORDS = [
    "推荐", "找一部", "找几部", "有什么", "有哪些", "好看的",
    "类似", "相似的", "差不多", "同类型", "同款",
    "介绍几部", "推荐几部", "安利", "求推荐",
    "适合", "值得一看", "经典", "冷门", "热门", "高分",
    "最近有什么", "有没有", "能不能推荐", "想看",
    "还有什么", "之类的",
]

INFO_KEYWORDS = [
    "导演", "主演", "演员", "上映时间", "什么时候上映",
    "评分", "多少分", "讲什么", "剧情", "简介",
    "时长", "多久", "哪个国家", "哪里拍的",
    "是谁", "谁演的", "谁导演", "出品",
    "哪一年", "什么时候的", "片长", "介绍",
    "详细信息", "具体情况", "资料",
]

FILTER_KEYWORDS = [
    "只看", "只要", "筛选", "过滤", "仅显示",
    "不要", "排除", "除了",
    "以上", "以下", "之间", "以内",
    "评分大于", "评分高于", "评分低于",
    "年以前", "年以后", "年代", "之后", "之前",
    "中国的", "国产", "美国的", "好莱坞", "日本的", "韩国的",
    "限制", "缩小", "范围",
]

FILTER_RESET_KEYWORDS = [
    "重置筛选", "清除筛选", "清除条件", "清空条件",
    "取消筛选", "去掉条件", "重来", "重新筛选",
    "显示条件", "查看条件", "当前条件", "我的筛选",
]
