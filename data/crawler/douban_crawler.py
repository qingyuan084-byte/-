"""
豆瓣电影 Top 250 爬虫

使用 curl_cffi 模拟浏览器指纹绕过反爬，爬取 Top 250 电影信息并保存为 CSV。
"""

import csv
import os
import random
import time
from datetime import datetime

from curl_cffi import requests
from lxml import html

# ======================== 反爬策略 ========================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

DOUBAN_TOP250_URL = "https://movie.douban.com/top250"


def _random_delay():
    """随机等待 1-3 秒，降低请求频率。"""
    time.sleep(random.uniform(1, 3))


def _build_headers():
    """生成随机请求头，包含 Referer 伪装。"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Referer": "https://movie.douban.com/",
    }


def _parse_movie_item(item) -> dict | None:
    """
    解析单个电影条目，返回字段字典。
    item: lxml Element，对应一个电影块。
    """
    try:
        # --- 标题 ---
        title_el = item.xpath('.//span[@class="title"]/text()')
        title = title_el[0].strip() if title_el else ""

        # --- 豆瓣评分 ---
        rating_el = item.xpath('.//span[@class="rating_num"]/text()')
        rating = float(rating_el[0].strip()) if rating_el else 0.0

        # --- 评价人数 ---
        rating_count_el = item.xpath('.//div[@class="star"]//span[last()]/text()')
        rating_count = 0
        if rating_count_el:
            raw = rating_count_el[0].strip()
            rating_count = int("".join(c for c in raw if c.isdigit()))

        # --- 一句话简介 ---
        quote_el = item.xpath('.//span[@class="inq"]/text()')
        quote = quote_el[0].strip() if quote_el else ""

        # --- 导演 / 主演 / 年份 / 国家 / 类型 ---
        info_el = item.xpath('.//div[@class="bd"]/p[1]/text()')
        info_text = "".join(info_el).replace("\n", " ").replace("\xa0", " ").strip()
        # info_text 格式类似:
        # "导演: 弗兰克·德拉邦特 Frank Darabont &nbsp 主演: 蒂姆·罗宾斯 / ... &nbsp 1994&nbsp/&nbsp美国&nbsp/&nbsp犯罪 剧情"
        # 实际 HTML 中以 \xa0 和 / 分割各字段

        # 按 &nbsp; 等价符号分割（lxml 已转为空格）
        # 更好的做法：拆出导演、主演部分，再拆年份/国家/类型
        parts = [p.strip() for p in info_text.split("  ") if p.strip()]
        # parts 通常为 ["导演: xxx  主演: xxx", "1994 / 美国 / 犯罪 剧情"]
        # 但分隔符不稳定，使用正则方式拆分

        # --- 另一种更稳健的方式：直接解析文本 ---
        director = ""
        actors = ""
        year = ""
        country = ""
        genre = ""

        # 去掉多余空白
        clean_info = " ".join(info_text.split())

        # 年份
        import re

        year_match = re.search(r"(\d{4})", clean_info)
        if year_match:
            year = year_match.group(1)

        # 导演
        director_match = re.search(r"导演:\s*(.+?)(?:\s{2,}|主\s*演)", clean_info)
        if director_match:
            director = director_match.group(1).strip()

        # 主演
        actor_match = re.search(r"主演:\s*(.+?)(?:\s{2,}|\d{4})", clean_info)
        if actor_match:
            actors = actor_match.group(1).strip()

        # 国家/地区和类型出现在年份之后: "1994 / 美国 / 犯罪 剧情"
        after_year = clean_info.split(str(year))[-1] if year else clean_info
        segments = [s.strip() for s in after_year.split("/")]
        if len(segments) >= 2:
            country = segments[1]
        if len(segments) >= 3:
            genre = segments[2]

        return {
            "title": title,
            "rating": rating,
            "rating_count": rating_count,
            "director": director,
            "actors": actors,
            "year": year,
            "country": country,
            "genre": genre,
            "quote": quote,
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        print(f"  [警告] 解析条目失败: {e}")
        return None


def crawl_douban_top250(output_path: str = "data/raw/douban_top250.csv"):
    """
    爬取豆瓣电影 Top 250，保存为 CSV。

    Args:
        output_path: CSV 输出路径，默认为 data/raw/douban_top250.csv
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    all_movies = []

    for page in range(10):
        start = page * 25
        url = f"{DOUBAN_TOP250_URL}?start={start}&filter="

        print(f"[{page + 1}/10] 正在请求: {url}")

        headers = _build_headers()
        try:
            resp = requests.get(
                url,
                headers=headers,
                impersonate="chrome124",  # curl_cffi: 模拟 Chrome 124 指纹
                timeout=15,
            )
            resp.encoding = "utf-8"

            if resp.status_code != 200:
                print(f"  [错误] HTTP {resp.status_code}, 跳过本页")
                _random_delay()
                continue

            tree = html.fromstring(resp.text)
            items = tree.xpath('//div[@class="item"]')

            if not items:
                # 备选：尝试 ol.grid_view 下的 li
                items = tree.xpath('//ol[@class="grid_view"]/li')

            print(f"  获取到 {len(items)} 条记录")

            for item in items:
                movie = _parse_movie_item(item)
                if movie:
                    movie["rank"] = start + len(all_movies) + 1
                    all_movies.append(movie)

        except Exception as e:
            print(f"  [异常] {e}")
            _random_delay()
            continue

        _random_delay()

    # --- 写入 CSV ---
    if not all_movies:
        print("未获取到任何数据，请检查网络或反爬策略。")
        return []

    fieldnames = [
        "rank", "title", "rating", "rating_count", "director",
        "actors", "year", "country", "genre", "quote", "crawl_time",
    ]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_movies)

    print(f"\n完成! 共 {len(all_movies)} 部电影已保存至 {output_path}")
    return all_movies


if __name__ == "__main__":
    crawl_douban_top250()
