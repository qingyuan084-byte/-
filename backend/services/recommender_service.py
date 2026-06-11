"""
推荐服务层 — 单例模式封装 ContentBasedRecommender

启动时加载特征和元数据，提供推荐方法供 API 调用。
元数据优先从 PostgreSQL 读取，数据库不可用时自动降级到 CSV。
支持 Redis 缓存 — 不可用时自动降级直查。
"""

import sys
import os
from pathlib import Path

import pandas as pd

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from recommender.content_based import ContentBasedRecommender, load_data
from backend.cache import (
    get_cache,
    set_cache,
    delete_cache,
    build_cache_key,
    hash_text,
    flush_app_cache,
)


def _log(msg: str):
    """统一日志格式。"""
    print(f"[服务] {msg}")


class RecommenderService:
    """推荐服务单例，持有推荐器实例和电影元数据。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        _log("正在初始化 RecommenderService...")

        # 加载特征
        tfidf, movies, genres = load_data()
        self.movie_ids_df = movies

        # ── 尝试从数据库加载元数据，失败则回退 CSV ──────
        self._meta_dict: dict = {}
        self.metadata_df: pd.DataFrame | None = None
        self._db_ok = False
        self._load_metadata()

        # 初始化推荐器
        precompute = os.getenv("RECOMMENDER_PRECOMPUTE", "false").lower() == "true"
        _log(f"预计算相似度矩阵: {'开启' if precompute else '关闭（按需计算）'}")

        try:
            self.recommender = ContentBasedRecommender(
                tfidf_matrix=tfidf,
                movie_ids_df=movies,
                genre_matrix=genres,
                use_genre=True,
                genre_weight=0.3,
                precompute=precompute,
            )
        except MemoryError:
            if precompute:
                _log("[警告] 预计算相似度矩阵时内存不足，自动降级为按需计算")
                self.recommender = ContentBasedRecommender(
                    tfidf_matrix=tfidf,
                    movie_ids_df=movies,
                    genre_matrix=genres,
                    use_genre=True,
                    genre_weight=0.3,
                    precompute=False,
                )
            else:
                raise

        self._initialized = True
        _log("RecommenderService 初始化完成")

    # ── 元数据加载：DB 优先，CSV 降级 ──────────────────

    def _load_metadata(self):
        """尝试从数据库加载元数据缓存，不可用时回退 CSV。"""
        # 1) 尝试 DB
        try:
            from backend.db import is_db_available, get_session
            from backend.repositories.movie_repository import MovieRepository

            if is_db_available():
                session = get_session()
                if session:
                    try:
                        repo = MovieRepository(session)
                        count = repo.count()
                        if count > 0:
                            movies = repo.get_all_movies()
                            self.metadata_df = pd.DataFrame(movies)
                            self.metadata_df["movie_id"] = self.metadata_df["movie_id"].astype(str)
                            self._meta_dict = self.metadata_df.set_index("movie_id").to_dict("index")
                            self._db_ok = True
                            _log(f"元数据(DB): {len(self._meta_dict)} 条")
                            session.close()
                            return
                    finally:
                        session.close()
        except Exception as e:
            _log(f"数据库读取失败: {e}，回退 CSV")

        # 2) 回退 CSV
        self._load_metadata_from_csv()

    def _load_metadata_from_csv(self):
        """从 CSV 文件加载元数据。"""
        cleaned_path = PROJECT_ROOT / "data" / "processed" / "douban_movies_cleaned.csv"
        if cleaned_path.exists():
            self.metadata_df = pd.read_csv(
                cleaned_path,
                dtype={"movie_id": str},
                usecols=[
                    "movie_id", "title", "poster", "rating", "release_year",
                    "genres", "summary", "directors", "actors", "countries",
                    "runtime", "total_ratings", "release_date",
                ],
            )
            self.metadata_df["movie_id"] = self.metadata_df["movie_id"].astype(str)
            self._meta_dict = self.metadata_df.set_index("movie_id").to_dict("index")
            _log(f"元数据(CSV): {len(self._meta_dict)} 条")
        else:
            self._meta_dict = {}
            self.metadata_df = None
            _log("[警告] 未找到清洗后的数据，海报/评分不可用")

    def __len__(self):
        return len(self.movie_ids_df) if self.movie_ids_df is not None else 0

    # 豆瓣图片默认占位图（当 poster 缺失/无效时使用）
    _FALLBACK_POSTER = (
        "data:image/svg+xml,"
        "%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='450'%3E"
        "%3Crect width='300' height='450' fill='%231a1a2e'/%3E"
        "%3Ctext x='150' y='200' text-anchor='middle' font-size='48'%3E🎬%3C/text%3E"
        "%3Ctext x='150' y='240' text-anchor='middle' fill='%23f5c518' font-size='14'%3ENo Poster%3C/text%3E"
        "%3C/svg%3E"
    )

    @staticmethod
    def _valid_poster(raw: str) -> str:
        """校验海报 URL：必须是以 http/https 开头的有效链接，否则返回占位图。"""
        if not raw:
            return RecommenderService._FALLBACK_POSTER
        s = str(raw).strip()
        if s.startswith("http://") or s.startswith("https://"):
            return s
        # NaN / nan / 空字符串等无效值
        if s.lower() in ("nan", "none", "null", ""):
            return RecommenderService._FALLBACK_POSTER
        return RecommenderService._FALLBACK_POSTER

    def _enrich(self, movie_id: str, title: str, score: float) -> dict:
        """用元数据补充海报、评分、年份等信息。"""
        meta = self._meta_dict.get(str(movie_id), {})
        return {
            "movie_id": str(movie_id),
            "title": title,
            "similarity_score": round(float(score), 4),
            "poster_url": self._valid_poster(meta.get("poster") or meta.get("poster_url", "")),
            "rating": float(meta.get("rating", 0) or 0),
            "year": (
                int(meta.get("release_year") or meta.get("year"))
                if (meta.get("release_year") or meta.get("year"))
                   and not pd.isna(meta.get("release_year") or meta.get("year"))
                else None
            ),
        }

    def recommend_by_movie(self, movie_id: str, top_n: int = 10) -> list[dict]:
        """按电影 ID 推荐相似电影（Redis 缓存优先，TTL=6h）。"""
        top_n = min(top_n, 50)  # 防御性上限，API 层也有 le=50 校验
        cache_key = build_cache_key("similar", str(movie_id), str(top_n))

        # 1) 查缓存
        cached = get_cache(cache_key)
        if cached is not None:
            return cached

        # 2) 计算
        raw = self.recommender.recommend_by_movie(str(movie_id), top_n)
        result = [self._enrich(mid, title, score) for mid, title, score in raw]

        # 3) 写缓存（TTL=6h）
        set_cache(cache_key, result, ttl=21600)
        return result

    def recommend_by_text(self, query_text: str, top_n: int = 10) -> list[dict]:
        """按文本搜索推荐电影（Redis 缓存优先，TTL=1h）。query 经 sha256 哈希后用作 key。"""
        top_n = min(top_n, 50)  # 防御性上限，API 层也有 le=50 校验
        cache_key = build_cache_key("search", hash_text(query_text), str(top_n))

        # 1) 查缓存
        cached = get_cache(cache_key)
        if cached is not None:
            return cached

        # 2) 语义搜索优先，TF‑IDF 降级
        from backend.services.semantic_search import SemanticSearchService
        sem = SemanticSearchService()
        raw = sem.search(query_text, top_n)

        if raw:
            print(f"[搜索] 语义检索命中 {len(raw)} 条 → '{query_text}'")
        else:
            print(f"[搜索] 语义检索未命中，降级 TF‑IDF → '{query_text}'")
            raw = self.recommender.recommend_by_text(query_text, top_n)

        result = [self._enrich(mid, title, score) for mid, title, score in raw]

        # 3) 写缓存（TTL=1h）
        set_cache(cache_key, result, ttl=3600)
        return result

    # ── 基础查询（DB 优先，分页）────────────────────

    def _try_db(self):
        """获取 DB 会话，不可用时返回 None。"""
        try:
            from backend.db import get_session
            return get_session()
        except Exception:
            return None

    def list_movies(self, q: str = "", page: int = 1, page_size: int = 30) -> tuple[list[dict], int]:
        """
        按标题筛选电影基础信息（movie_id, title, rating），支持分页。

        Returns:
            (results, total) — results 是 dict 列表，total 是匹配总数。
        """
        # 优先数据库
        session = self._try_db()
        if session:
            try:
                from backend.repositories.movie_repository import MovieRepository
                repo = MovieRepository(session)
                results, total = repo.list_movies(q=q, page=page, page_size=page_size)
                if results:
                    return results, total
            except Exception:
                pass
            finally:
                session.close()

        # 降级 CSV
        return self._list_movies_csv(q=q, page=page, page_size=page_size)

    def _list_movies_csv(self, q: str = "", page: int = 1, page_size: int = 30) -> tuple[list[dict], int]:
        """CSV 降级：基础列表 + 分页。"""
        if self.movie_ids_df is None:
            return [], 0
        df = self.movie_ids_df.copy()
        if q:
            df = df[df["title"].str.contains(q, case=False, na=False)]
        total = len(df)

        start = (page - 1) * page_size
        end = start + page_size
        df = df.iloc[start:end]

        results = []
        for _, row in df.iterrows():
            mid = str(row["movie_id"])
            meta = self._meta_dict.get(mid, {})
            results.append({
                "movie_id": mid,
                "title": str(row["title"]),
                "rating": float(meta.get("rating", 0) or 0),
            })
        return results, total

    def list_movies_rich(
        self,
        q: str = "",
        genre: str | None = None,
        country: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        rating_min: float | None = None,
        rating_max: float | None = None,
        sort_by: str = "rating",
        page: int = 1,
        page_size: int = 30,
    ) -> tuple[list[dict], int]:
        """
        按条件筛选电影完整信息，支持分页和排序。

        Returns:
            (results, total)
        """
        # 优先数据库
        session = self._try_db()
        if session:
            try:
                from backend.repositories.movie_repository import MovieRepository
                repo = MovieRepository(session)
                results, total = repo.list_movies_rich(
                    q=q,
                    genre=genre,
                    country=country,
                    year_min=year_min,
                    year_max=year_max,
                    rating_min=rating_min,
                    rating_max=rating_max,
                    sort_by=sort_by,
                    page=page,
                    page_size=page_size,
                )
                if results or total > 0:
                    return results, total
            except Exception:
                pass
            finally:
                session.close()

        # 降级 CSV
        return self._list_movies_rich_csv(
            q=q,
            genre=genre,
            country=country,
            year_min=year_min,
            year_max=year_max,
            rating_min=rating_min,
            rating_max=rating_max,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )

    def _list_movies_rich_csv(
        self,
        q: str = "",
        genre: str | None = None,
        country: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        rating_min: float | None = None,
        rating_max: float | None = None,
        sort_by: str = "rating",
        page: int = 1,
        page_size: int = 30,
    ) -> tuple[list[dict], int]:
        """CSV 降级：完整列表 + 分页 + 筛选 + 排序。"""
        if self.movie_ids_df is None:
            return [], 0

        df = self.movie_ids_df.copy()

        # 标题搜索
        if q:
            df = df[df["title"].str.contains(q, case=False, na=False)]

        # 合并元数据用于筛选
        meta_df = self.metadata_df.copy() if self.metadata_df is not None else None
        if meta_df is not None:
            meta_df["movie_id"] = meta_df["movie_id"].astype(str)
            df["movie_id"] = df["movie_id"].astype(str)
            # join 元数据列
            keep_cols = ["movie_id", "genres", "countries", "release_year", "rating", "total_ratings"]
            available = [c for c in keep_cols if c in meta_df.columns]
            joined = df.merge(meta_df[available], on="movie_id", how="left")
        else:
            joined = df

        # 类型筛选
        if genre:
            if "genres" in joined.columns:
                joined = joined[joined["genres"].astype(str).str.contains(genre, case=False, na=False)]
            else:
                joined = joined.head(0)

        # 国家筛选
        if country:
            if "countries" in joined.columns:
                joined = joined[joined["countries"].astype(str).str.contains(country, case=False, na=False)]
            else:
                joined = joined.head(0)

        # 年份范围
        year_col = "release_year" if "release_year" in joined.columns else None
        if year_col:
            y_series = pd.to_numeric(joined[year_col], errors="coerce")
            if year_min is not None:
                joined = joined[y_series >= year_min]
                y_series = pd.to_numeric(joined[year_col], errors="coerce")
            if year_max is not None:
                joined = joined[y_series <= year_max]

        # 评分范围
        rating_col = "rating" if "rating" in joined.columns else None
        if rating_col:
            r_series = pd.to_numeric(joined[rating_col], errors="coerce")
            if rating_min is not None:
                joined = joined[r_series >= rating_min]
                r_series = pd.to_numeric(joined[rating_col], errors="coerce")
            if rating_max is not None:
                joined = joined[r_series <= rating_max]

        # 排序
        sort_map = {
            "rating": "rating",
            "year": "release_year",
            "total_ratings": "total_ratings",
            "title": "title",
        }
        col = sort_map.get(sort_by, "rating")
        if col in joined.columns:
            ascending = sort_by == "title"
            if col in ("rating", "release_year", "total_ratings"):
                numeric = pd.to_numeric(joined[col], errors="coerce")
                joined = joined.iloc[(-numeric).fillna(0).argsort()]
            else:
                joined = joined.sort_values(col, ascending=True, na_position="last")
        elif "rating" in joined.columns:
            joined = joined.sort_values("rating", ascending=False, na_position="last")

        total = len(joined)

        start = (page - 1) * page_size
        end = start + page_size
        page_df = joined.iloc[start:end]

        results = []
        for _, row in page_df.iterrows():
            mid = str(row["movie_id"])
            title = str(row.get("title", ""))
            results.append(self._build_detail(mid, title))
        return results, total

    def get_movie_detail(self, movie_id: str) -> dict | None:
        """
        根据 movie_id 获取单部电影详情，不存在返回 None。
        优先查数据库，不可用时查 CSV 元数据。
        """
        mid = str(movie_id)

        # 优先数据库
        session = self._try_db()
        if session:
            try:
                from backend.repositories.movie_repository import MovieRepository
                repo = MovieRepository(session)
                result = repo.get_movie_by_id(mid)
                if result:
                    return result
            except Exception:
                pass
            finally:
                session.close()

        # 降级 CSV
        df = self.movie_ids_df
        if df is None:
            return None
        match = df[df["movie_id"].astype(str) == mid]
        if match.empty:
            return None
        title = str(match.iloc[0]["title"])
        return self._build_detail(mid, title)

    @staticmethod
    def _safe_str(val) -> str:
        """安全转字符串，NaN 返回空字符串。"""
        import numpy as np
        if val is None:
            return ""
        if isinstance(val, float) and np.isnan(val):
            return ""
        return str(val).strip()

    def _build_detail(self, movie_id: str, title: str) -> dict:
        """构建完整的电影详情字典。"""
        import numpy as np
        meta = self._meta_dict.get(str(movie_id), {})
        rating_raw = meta.get("rating", 0)
        year_raw = meta.get("release_year") or meta.get("year")
        return {
            "movie_id": str(movie_id),
            "title": title,
            "rating": float(rating_raw) if rating_raw and not (isinstance(rating_raw, float) and np.isnan(rating_raw)) else 0.0,
            "year": int(year_raw) if year_raw and not (isinstance(year_raw, float) and np.isnan(year_raw)) else None,
            "poster_url": self._valid_poster(meta.get("poster") or meta.get("poster_url", "")),
            "genres": self._safe_str(meta.get("genres", "")),
            "summary": self._safe_str(meta.get("summary", "")),
            "directors": self._safe_str(meta.get("directors", "")),
            "actors": self._safe_str(meta.get("actors", "")),
            "countries": self._safe_str(meta.get("countries", "")),
            "runtime": self._safe_str(meta.get("runtime", "")),
            "total_ratings": self._safe_str(meta.get("total_ratings", "")),
            "release_date": self._safe_str(meta.get("release_date", "")),
        }

    def get_stats(self) -> dict:
        """
        返回数据集统计信息（Redis 缓存优先，TTL=10min）。
        优先查数据库，不可用时用 pandas 计算。
        """
        cache_key = build_cache_key("stats", "v1")

        # 1) 查缓存
        cached = get_cache(cache_key)
        if cached is not None:
            return cached

        # 2) 查 DB / CSV
        stats = self._get_stats_raw()

        # 3) 写缓存（TTL=10min）
        set_cache(cache_key, stats, ttl=600)
        return stats

    def _get_stats_raw(self) -> dict:
        """获取统计信息（DB 优先，CSV 降级）。"""
        # 优先数据库
        session = self._try_db()
        if session:
            try:
                from backend.repositories.movie_repository import MovieRepository
                repo = MovieRepository(session)
                stats = repo.get_stats()
                if stats.get("total_movies", 0) > 0:
                    return stats
            except Exception:
                pass
            finally:
                session.close()

        # 降级 CSV
        return self._get_stats_csv()

    def _get_stats_csv(self) -> dict:
        """CSV 降级：统计信息。兼容 DB 列名 (year) 和 CSV 列名 (release_year)。"""
        import numpy as np
        stats = {
            "total_movies": len(self._meta_dict),
            "avg_rating": 0.0,
            "top_movie": {"title": "", "rating": 0.0},
            "latest_year": 0,
            "year_span": 0,
        }
        if self.metadata_df is not None and not self.metadata_df.empty:
            df = self.metadata_df
            ratings = df["rating"].dropna()
            if not ratings.empty:
                stats["avg_rating"] = round(float(ratings.mean()), 2)
                top_idx = ratings.idxmax()
                stats["top_movie"] = {
                    "title": str(df.loc[top_idx, "title"]),
                    "rating": float(ratings.max()),
                }
            year_col = "year" if "year" in df.columns else "release_year"
            years = df[year_col].dropna()
            if not years.empty:
                stats["latest_year"] = int(years.max())
                stats["year_span"] = int(years.max() - years.min())
        return stats
