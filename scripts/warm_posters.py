"""
海报预热脚本 — 预下载所有电影海报到本地缓存目录。

运行方式:
    python scripts/warm_posters.py

首次运行会下载全部 2065 张海报（约 2-5 分钟），之后图片加载全部毫秒级。
"""
import hashlib
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CACHE_DIR = PROJECT_ROOT / "cache" / "images"
CONTENT_TYPE_MAP = {
    "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp",
    "image/png": ".png", "image/gif": ".gif", "image/avif": ".avif",
}
HEADERS = {
    "Referer": "https://movie.douban.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
}
CONCURRENCY = 8
TIMEOUT = 15.0


def cache_key(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def cache_exists(key: str) -> bool:
    for ext in CONTENT_TYPE_MAP.values():
        p = CACHE_DIR / (key + ext)
        if p.exists() and p.stat().st_size > 0:
            return True
    return False


def download_one(url: str) -> tuple[str, bool]:
    """下载单张海报，返回 (url, success)"""
    key = cache_key(url)
    if cache_exists(key):
        return url, True

    try:
        resp = httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "image/webp")
        ext = CONTENT_TYPE_MAP.get(ct.split(";")[0].strip(), ".img")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / (key + ext)).write_bytes(resp.content)
        return url, True
    except Exception as e:
        return url, False


def collect_urls():
    """从 CSV 或数据库收集所有有效海报 URL"""
    urls = set()

    # 尝试 CSV
    csv_path = PROJECT_ROOT / "data" / "processed" / "douban_movies_cleaned.csv"
    if csv_path.exists():
        import pandas as pd
        df = pd.read_csv(csv_path, dtype={"movie_id": str}, usecols=["poster"])
        for raw in df["poster"].dropna():
            s = str(raw).strip()
            if s.startswith("http"):
                urls.add(s)
        print(f"[CSV] 收集到 {len(urls)} 个海报 URL")
        return list(urls)

    # 尝试数据库
    try:
        from backend.db import SessionLocal
        from backend.repositories.movie_repository import MovieRepository
        db = SessionLocal()
        try:
            repo = MovieRepository(db)
            movies = repo.get_all_movies()
            for m in movies:
                u = (m.get("poster_url") or "").strip()
                if u.startswith("http"):
                    urls.add(u)
            print(f"[DB]  收集到 {len(urls)} 个海报 URL")
            return list(urls)
        finally:
            db.close()
    except Exception as e:
        print(f"[WARN] 数据库读取失败: {e}")

    return list(urls)


def main():
    urls = collect_urls()
    if not urls:
        print("[错误] 未找到任何海报 URL，请先确保 data/processed/douban_movies_cleaned.csv 存在")
        return

    already = sum(1 for u in urls if cache_exists(cache_key(u)))
    need = len(urls) - already
    print(f"已有缓存: {already} 张")
    print(f"待下载:   {need} 张")
    if need == 0:
        print("全部已缓存，无需下载")
        return

    print(f"\n开始下载 (并发={CONCURRENCY})...")
    t0 = time.time()
    ok = fail = 0

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {pool.submit(download_one, u): u for u in urls if not cache_exists(cache_key(u))}
        for i, f in enumerate(as_completed(futures), 1):
            _, success = f.result()
            if success:
                ok += 1
            else:
                fail += 1
            if i % 50 == 0 or i == len(futures):
                print(f"  进度: {i}/{len(futures)}  (成功 {ok}, 失败 {fail})")

    elapsed = time.time() - t0
    print(f"\n完成! 耗时 {elapsed:.1f}s | 成功 {ok} | 失败 {fail}")
    print(f"缓存目录: {CACHE_DIR}")


if __name__ == "__main__":
    main()
