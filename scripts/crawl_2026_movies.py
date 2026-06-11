"""
爬取豆瓣指定年份电影
====================
通过豆瓣搜索 API + 摘要 API 获取电影信息，追加到 CSV。

用法:
    python scripts/crawl_douban_movies.py                # 默认 2026
    python scripts/crawl_douban_movies.py --year 2025    # 指定年份
    python scripts/crawl_douban_movies.py --year 2026 --max 100
"""
import csv
import os
import random
import sys
import time
from pathlib import Path

# Windows UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ["PYTHONUTF8"] = "1"
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from curl_cffi import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "douban_all_movies.csv"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
]


def random_delay():
    time.sleep(random.uniform(0.8, 2.0))


def api_headers(referer="https://movie.douban.com/"):
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": referer,
    }


# ── 搜索 API ─────────────────────────────────────────────

def search_by_year(year, max_results=100):
    """通过豆瓣搜索 API 获取指定年份电影，返回 [{id,title,rate,star,directors,casts,cover,url}]。"""
    results = []
    start = 0
    while len(results) < max_results:
        url = (
            f"https://movie.douban.com/j/new_search_subjects"
            f"?sort=U&range=0,10&tags={year}&start={start}&year_range={year},{year}"
        )
        print(f"  [搜索] start={start}")
        try:
            resp = requests.get(url, headers=api_headers(), impersonate="chrome124", timeout=15)
            data = resp.json()
            subjects = data.get("data", [])
            if not subjects:
                break
            for s in subjects:
                if s.get("id"):
                    results.append(s)
            print(f"         本页 {len(subjects)} 条, 累计 {len(results)}")
            if len(subjects) < 20:
                break
            start += 20
            random_delay()
        except Exception as e:
            print(f"  [搜索错误] {e}")
            break
    return results


# ── 摘要 API ─────────────────────────────────────────────

def fetch_subject_abstract(movie_id):
    """获取电影摘要信息：类型、地区、时长。"""
    url = f"https://movie.douban.com/j/subject_abstract?subject_id={movie_id}"
    try:
        resp = requests.get(url, headers=api_headers(), impersonate="chrome124", timeout=10)
        data = resp.json()
        if data.get("r") == 0 and "subject" in data:
            return data["subject"]
    except Exception as e:
        print(f"    [摘要API错误] {e}")
    return {}


# ── CSV 辅助 ─────────────────────────────────────────────

def load_existing_ids():
    """加载已有 movie_id，避免重复。"""
    if not CSV_PATH.exists():
        return set()
    ids = set()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(CSV_PATH, encoding=enc) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mid = row.get("movie_id", "").strip()
                    if mid:
                        ids.add(mid)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    return ids


def build_movie_row(search_item, abstract):
    """将搜索 + 摘要数据组装为标准 CSV 行。"""
    mid = search_item.get("id", "")

    title = search_item.get("title", "")
    # 去掉标题中的年份后缀 "(2026)"
    import re
    title = re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()

    # 评分
    rate_str = search_item.get("rate", "") or ""
    try:
        rating = float(rate_str)
    except (ValueError, TypeError):
        rating = 0.0

    # 类型
    types = abstract.get("types", [])
    genres = ", ".join(types) if types else ""

    # 地区
    region = abstract.get("region", "") or ""

    # 时长
    duration = abstract.get("duration", "") or ""

    # 导演
    directors_list = search_item.get("directors", []) or []
    directors = ", ".join(directors_list)

    # 演员
    casts_list = search_item.get("casts", []) or []
    actors = ", ".join(casts_list[:5])  # 前 5 位

    # 海报
    poster = search_item.get("cover", "") or ""

    # 链接
    link = search_item.get("url", f"https://movie.douban.com/subject/{mid}/")

    # 年份 → 上映日期
    year = abstract.get("release_year", "") or ""
    release_date = f"{year}-01-01" if year else ""

    return {
        "movie_id": mid,
        "title": title,
        "rating": rating,
        "total_ratings": 0,
        "directors": directors,
        "actors": actors,
        "screenwriters": "",
        "release_date": release_date,
        "genres": genres,
        "countries": region,
        "languages": "",
        "runtime": duration,
        "summary": "",
        "link": link,
        "poster": poster,
        "tags": "",
    }


# ── 主流程 ──────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="爬取豆瓣指定年份电影")
    parser.add_argument("--year", type=int, default=2026, help="目标年份，默认 2026")
    parser.add_argument("--max", type=int, default=80, dest="max_results", help="最多数量")
    args = parser.parse_args()

    year = args.year
    print("=" * 56)
    print(f"  豆瓣 {year} 年电影爬虫 (API)")
    print("=" * 56)

    existing = load_existing_ids()
    print(f"\n[INFO] CSV 中已有 {len(existing)} 部电影")

    # Step 1: 搜索
    print(f"\n[Step 1] 搜索 {year} 年电影...")
    search_results = search_by_year(year, args.max_results)
    print(f"  共找到 {len(search_results)} 部")

    new_items = [s for s in search_results if s["id"] not in existing]
    print(f"  其中新电影: {len(new_items)} 部 (跳过已存在: {len(search_results) - len(new_items)})")

    if not new_items:
        print("\n没有新电影，退出。")
        return

    # Step 2: 逐部获取摘要
    print(f"\n[Step 2] 获取 {len(new_items)} 部电影详情...")
    new_movies = []
    for i, item in enumerate(new_items):
        mid = item["id"]
        title_raw = item.get("title", "?")
        print(f"  [{i+1}/{len(new_items)}] {mid} | {title_raw}")

        abstract = fetch_subject_abstract(mid)
        row = build_movie_row(item, abstract)
        new_movies.append(row)

        genres = row["genres"] or "-"
        rating = row["rating"]
        print(f"         {row['title']} | {genres} | {row['countries']} | {row['runtime']} | ★{rating}")

        if i < len(new_items) - 1:
            random_delay()

    # Step 3: 保存
    print(f"\n[Step 3] 保存 {len(new_movies)} 部新电影...")
    fieldnames = [
        "movie_id", "title", "rating", "total_ratings", "directors",
        "actors", "screenwriters", "release_date", "genres", "countries",
        "languages", "runtime", "summary", "link", "poster", "tags",
    ]

    file_exists = CSV_PATH.exists()
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_movies)

    print(f"  已追加到 {CSV_PATH}")
    print(f"\n{'=' * 56}")
    print(f"  完成! 新增 {len(new_movies)} 部 {year} 年电影")
    print(f"  文件: {CSV_PATH}")
    print(f"\n  后续步骤:")
    print(f"    python data/cleaning/data_preprocess.py")
    print(f"    python scripts/import_movies_to_db.py")
    print(f"    python scripts/build_movie_embeddings.py")
    print(f"    python scripts/warm_posters.py")
    print(f"{'=' * 56}")


if __name__ == "__main__":
    main()
