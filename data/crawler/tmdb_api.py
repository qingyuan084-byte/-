"""
TMDB API 集成模块

通过 TMDB API 查询电影详情，为豆瓣爬取的电影数据补充海报、预算、票房等信息。
"""

import csv
import os
import time
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

if not TMDB_API_KEY:
    print("[警告] TMDB_API_KEY 未设置，请在 .env 文件中配置。")


def _api_get(endpoint: str, params: dict | None = None, retries: int = 3) -> dict | None:
    """
    封装 TMDB API GET 请求，自动处理限流与重试。

    Args:
        endpoint: API 路径，如 "/search/movie"
        params: 查询参数（不含 api_key，会自动注入）
        retries: 最大重试次数
    """
    if params is None:
        params = {}
    params["api_key"] = TMDB_API_KEY
    params["language"] = params.get("language", "zh-CN")

    url = f"{TMDB_BASE_URL}{endpoint}"

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=15)

            if resp.status_code == 429:
                # 触发限流，等待 Retry-After 或指数退避
                wait = int(resp.headers.get("Retry-After", 2 ** attempt))
                print(f"  [限流] 等待 {wait}s 后重试 (第 {attempt} 次)...")
                time.sleep(wait)
                continue

            if resp.status_code == 401:
                print(f"  [错误] API Key 无效 (401)，请检查 TMDB_API_KEY。")
                return None

            if resp.status_code == 404:
                print(f"  [未找到] {endpoint} {params}")
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            print(f"  [网络异常] {e}，{2 ** attempt}s 后重试...")
            time.sleep(2 ** attempt)

    print(f"  [失败] 已达最大重试次数: {endpoint}")
    return None


def search_movie(title: str, year: str = "") -> dict | None:
    """
    根据标题搜索电影，返回匹配度最高的结果。

    Args:
        title: 电影标题（中文或英文）
        year: 可选，按年份过滤以提高匹配精度

    Returns:
        包含 tmdb_id, title, release_date 等字段的字典，未找到时返回 None
    """
    params: dict[str, Any] = {"query": title}
    if year:
        params["year"] = year

    result = _api_get("/search/movie", params)
    if result and result.get("results"):
        best = result["results"][0]
        return {
            "tmdb_id": best.get("id"),
            "title": best.get("title"),
            "original_title": best.get("original_title"),
            "release_date": best.get("release_date"),
            "overview": best.get("overview"),
            "popularity": best.get("popularity"),
            "vote_average": best.get("vote_average"),
            "vote_count": best.get("vote_count"),
            "poster_path": (
                TMDB_IMAGE_BASE + best["poster_path"]
                if best.get("poster_path")
                else ""
            ),
            "backdrop_path": (
                TMDB_IMAGE_BASE + best["backdrop_path"]
                if best.get("backdrop_path")
                else ""
            ),
            "original_language": best.get("original_language"),
            "genre_ids": best.get("genre_ids", []),
        }

    print(f"  [搜索无结果] {title}")
    return None


def get_movie_details(movie_id: int) -> dict | None:
    """
    获取电影详细信息（海报、预算、票房、IMDb ID 等）。

    Args:
        movie_id: TMDB 电影 ID

    Returns:
        包含 budget, revenue, imdb_id 等字段的字典
    """
    result = _api_get(f"/movie/{movie_id}")
    if not result:
        return None

    return {
        "tmdb_id": result.get("id"),
        "imdb_id": result.get("imdb_id", ""),
        "title": result.get("title"),
        "original_title": result.get("original_title"),
        "original_language": result.get("original_language"),
        "release_date": result.get("release_date"),
        "runtime": result.get("runtime"),
        "budget": result.get("budget"),
        "revenue": result.get("revenue"),
        "poster_path": (
            TMDB_IMAGE_BASE + result["poster_path"]
            if result.get("poster_path")
            else ""
        ),
        "backdrop_path": (
            TMDB_IMAGE_BASE + result["backdrop_path"]
            if result.get("backdrop_path")
            else ""
        ),
        "overview": result.get("overview"),
        "tagline": result.get("tagline", ""),
        "genres": [g["name"] for g in result.get("genres", [])],
        "production_countries": [
            c["name"] for c in result.get("production_countries", [])
        ],
        "spoken_languages": [
            l["name"] for l in result.get("spoken_languages", [])
        ],
        "popularity": result.get("popularity"),
        "vote_average": result.get("vote_average"),
        "vote_count": result.get("vote_count"),
        "status": result.get("status"),
    }


def enrich_movies_with_tmdb(
    input_csv: str = "data/raw/douban_top250.csv",
    output_csv: str = "data/raw/movies_enriched.csv",
    delay: float = 0.5,
):
    """
    读取豆瓣 CSV，通过 TMDB API 为每部电影补充详细信息并保存。

    Args:
        input_csv: 豆瓣爬虫输出的 CSV 路径
        output_csv: 补充后的 CSV 输出路径
        delay: 每次 API 请求之间的延迟（秒），避免触发限流
    """
    if not TMDB_API_KEY or TMDB_API_KEY == "your_key_here":
        raise RuntimeError(
            "请先在 .env 文件中设置有效的 TMDB_API_KEY，"
            "免费注册地址: https://www.themoviedb.org/settings/api"
        )

    df = pd.read_csv(input_csv)
    print(f"已加载 {len(df)} 条豆瓣数据，开始通过 TMDB 补充信息...\n")

    enriched_fields = {
        "tmdb_id": [],
        "imdb_id": [],
        "poster_url": [],
        "backdrop_url": [],
        "tmdb_rating": [],
        "runtime": [],
        "budget": [],
        "revenue": [],
        "original_language": [],
        "tagline": [],
        "overview": [],
    }

    for _, row in df.iterrows():
        title = str(row["title"])
        year = str(row.get("year", ""))
        print(f"[TMDB] 搜索: {title} ({year})")

        # 步骤 1: 搜索匹配
        search_result = search_movie(title, year)

        # 步骤 2: 获取详情
        details = None
        if search_result and search_result.get("tmdb_id"):
            details = get_movie_details(search_result["tmdb_id"])

        # 步骤 3: 汇总结果
        if details:
            enriched_fields["tmdb_id"].append(details.get("tmdb_id", ""))
            enriched_fields["imdb_id"].append(details.get("imdb_id", ""))
            enriched_fields["poster_url"].append(details.get("poster_path", ""))
            enriched_fields["backdrop_url"].append(details.get("backdrop_path", ""))
            enriched_fields["tmdb_rating"].append(details.get("vote_average", ""))
            enriched_fields["runtime"].append(details.get("runtime", ""))
            enriched_fields["budget"].append(details.get("budget", ""))
            enriched_fields["revenue"].append(details.get("revenue", ""))
            enriched_fields["original_language"].append(details.get("original_language", ""))
            enriched_fields["tagline"].append(details.get("tagline", ""))
            enriched_fields["overview"].append(details.get("overview", ""))
        else:
            # 搜索无结果时填充空值
            for field in enriched_fields:
                enriched_fields[field].append("")

        time.sleep(delay)

    # --- 合并并保存 ---
    for field, values in enriched_fields.items():
        df[field] = values

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"\n完成! 已保存 {len(df)} 条记录至 {output_csv}")


if __name__ == "__main__":
    enrich_movies_with_tmdb()
