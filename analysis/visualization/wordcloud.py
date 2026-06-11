"""
词云生成模块

从电影标题和简介生成词云图，使用 jieba 分词处理中文文本。
"""

import re
from collections import Counter
from pathlib import Path

import jieba
import numpy as np
import pandas as pd
from PIL import Image
from wordcloud import WordCloud

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── 中文字体查找 ──────────────────────────────────
def _find_cjk_font() -> str | None:
    """在系统中查找可用的中文字体文件路径。"""
    import matplotlib.font_manager as fm
    candidates = ["Noto Sans SC", "SimHei", "Microsoft YaHei", "STXihei", "KaiTi"]
    for f in fm.fontManager.ttflist:
        if f.name in candidates:
            return f.fname
    # 兜底：直接搜索系统字体目录
    import glob as _glob
    for pattern in [
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
    ]:
        if Path(pattern).exists():
            return pattern
    return None

_CJK_FONT_PATH = _find_cjk_font()

# ======================== 中文停用词表 ========================

STOP_WORDS = set([
    # 常用停用词
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "所", "为", "所以", "因为", "但是", "然而", "虽然", "如果", "可以",
    "这个", "那个", "什么", "怎么", "怎样", "如何", "为什么", "哪", "吗",
    "啊", "呢", "吧", "哦", "嗯", "哈", "呀", "哇", "嘛", "被", "把",
    "从", "对", "与", "向", "将", "让", "给", "由", "当", "以", "之",
    "更", "还", "已经", "又", "再", "才", "并", "或", "但", "而", "只",
    "且", "能", "会", "可以", "可", "该", "应", "应该", "可能", "需要",
    "开始", "开始", "结束", "最后", "然后", "接着", "之后", "之前",
    "真的", "比较", "非常", "太", "很", "一点", "一下", "一直", "一样",
    "一种", "一个", "一部", "一位", "一名", "一些", "一片", "一场",
    "一部", "电影", "本片", "故事", "讲述", "改编", "影片",
    # 豆瓣高频但无意义的词
    "饰", "主演", "导演", "饰演", "扮演", "出演",
    "分钟", "上映", "简介", "暂无", "暂无简介",
    "饰)", "饰）", "本片", "本片根据", "根据",
    # 多余字符
    " ", "\n", "\r", "\t", "、", "。", "，", "！", "？", "；", "：",
    "（", "）", "《", "》", "【", "】", "“", "”", "'", "\"",
    "/", "\\", "-", "_", "+", "=", "&", "%", "#", "@", "!", "*",
])

# 额外从文本中自动过滤的短词
MIN_WORD_LEN = 1  # 单字也保留（中文单字有意义）


def _segment(text: str) -> list[str]:
    """对文本进行 jieba 分词并去停用词。"""
    if pd.isna(text) or not str(text).strip():
        return []
    # 清理括号内演员名：去掉（xxx 饰）模式中的内容
    text = re.sub(r"[（(][^)）]*?饰[)）]", "", str(text))
    text = re.sub(r"[（(][^)）]*?飾[)）]", "", str(text))
    words = jieba.cut(text)
    return [
        w.strip() for w in words
        if w.strip()
        and len(w.strip()) > MIN_WORD_LEN
        and w.strip() not in STOP_WORDS
        and not w.strip().isdigit()
        and not all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for c in w.strip())
    ]


def generate_title_wordcloud(df: pd.DataFrame) -> WordCloud:
    """从电影标题生成词云。"""
    print("  [词云] 处理标题...")
    titles = df["title"].dropna().tolist()
    text = " ".join(titles)
    # 标题不用分词，直接整体作为词组
    words = jieba.cut(text)
    filtered = [w.strip() for w in words if w.strip() and len(w.strip()) > 1 and w.strip() not in STOP_WORDS]

    if not filtered:
        print("  [警告] 标题分词后为空")
        return None

    word_freq = Counter(filtered)
    wc = WordCloud(
        font_path=_CJK_FONT_PATH,
        width=1200,
        height=600,
        background_color="white",
        max_words=200,
        colormap="viridis",
        collocations=False,
        prefer_horizontal=0.7,
    ).generate_from_frequencies(word_freq)

    path = REPORTS_DIR / "wordcloud_title.png"
    wc.to_file(str(path))
    print(f"  [OK] {path}")
    return wc


def generate_summary_wordcloud(df: pd.DataFrame) -> WordCloud:
    """从电影简介生成词云。"""
    print("  [词云] 处理简介...")
    summaries = df["summary"].dropna().tolist()
    all_words = []
    for s in summaries:
        all_words.extend(_segment(s))

    if not all_words:
        print("  [警告] 简介分词后为空")
        return None

    word_freq = Counter(all_words)
    wc = WordCloud(
        font_path=_CJK_FONT_PATH,
        width=1200,
        height=600,
        background_color="white",
        max_words=200,
        colormap="plasma",
        collocations=False,
        prefer_horizontal=0.7,
    ).generate_from_frequencies(word_freq)

    path = REPORTS_DIR / "wordcloud_summary.png"
    wc.to_file(str(path))
    print(f"  [OK] {path}")
    return wc
