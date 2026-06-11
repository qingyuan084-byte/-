"""
电影数据仓库
===========
封装对 movies 表的 CRUD 查询，供 API 和服务层使用。

所有方法接受 Session 参数（从 get_db 注入），
调用方通过 is_db_available() 决定是否使用仓库。
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.models.db_models import Movie

# sort_by 白名单 → 实际列映射，防止 SQL 注入
_SORT_COLUMNS = {
    "rating": Movie.rating,
    "year": Movie.release_year,
    "total_ratings": Movie.total_ratings,
    "title": Movie.title,
}


class MovieRepository:
    """电影数据访问层。"""

    def __init__(self, db: Session):
        self.db = db

    # ── 查询 ──────────────────────────────────────────

    def list_movies(
        self,
        q: str = "",
        page: int = 1,
        page_size: int = 30,
    ) -> tuple[list[dict], int]:
        """
        分页查询电影基础信息（movie_id, title, rating）。

        Returns:
            (results, total) — results 是 dict 列表，total 是匹配总数。
        """
        query = self.db.query(Movie)
        if q:
            query = query.filter(Movie.title.ilike(f"%{q}%"))

        total = query.count()

        offset = (page - 1) * page_size
        movies = (
            query.order_by(Movie.rating.desc().nullslast())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [m.to_basic_dict() for m in movies], total

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
        分页查询电影完整信息，支持多维度筛选和排序。

        sort_by 仅接受白名单值：rating / year / total_ratings / title。
        其他值不会直接拼入 SQL —— 调用方应在入口处校验。
        """
        query = self.db.query(Movie)

        # 标题搜索
        if q:
            query = query.filter(Movie.title.ilike(f"%{q}%"))

        # 类型筛选
        if genre:
            query = query.filter(Movie.genres.ilike(f"%{genre}%"))

        # 国家筛选
        if country:
            query = query.filter(Movie.countries.ilike(f"%{country}%"))

        # 年份范围
        if year_min is not None:
            query = query.filter(Movie.release_year >= year_min)
        if year_max is not None:
            query = query.filter(Movie.release_year <= year_max)

        # 评分范围
        if rating_min is not None:
            query = query.filter(Movie.rating >= rating_min)
        if rating_max is not None:
            query = query.filter(Movie.rating <= rating_max)

        total = query.count()

        # 白名单映射排序
        sort_col = _SORT_COLUMNS.get(sort_by, _SORT_COLUMNS["rating"])
        if sort_by in ("year",):
            # 年份降序（新→旧），NULL 最后
            query = query.order_by(sort_col.desc().nullslast())
        elif sort_by == "title":
            query = query.order_by(sort_col.asc().nullslast())
        else:
            # rating / total_ratings 降序
            query = query.order_by(sort_col.desc().nullslast())

        offset = (page - 1) * page_size
        movies = query.offset(offset).limit(page_size).all()

        return [m.to_rich_dict() for m in movies], total

    def get_movie_by_id(self, movie_id: str) -> dict | None:
        """根据 movie_id 获取单部电影完整信息。"""
        movie = self.db.query(Movie).filter(Movie.movie_id == str(movie_id)).first()
        if movie is None:
            return None
        return movie.to_rich_dict()

    def get_all_movies(self) -> list[dict]:
        """获取全部电影完整信息（用于推荐服务缓存，不推荐在超大表上使用）。"""
        movies = self.db.query(Movie).all()
        return [m.to_rich_dict() for m in movies]

    def get_stats(self) -> dict:
        """获取数据集统计信息。"""
        total = self.db.query(Movie).count()
        if total == 0:
            return {
                "total_movies": 0,
                "avg_rating": 0.0,
                "top_movie": {"title": "", "rating": 0.0},
                "latest_year": 0,
                "year_span": 0,
            }

        avg_rating = (
            self.db.query(func.avg(Movie.rating))
            .filter(Movie.rating.isnot(None))
            .scalar()
        ) or 0.0

        top = (
            self.db.query(Movie)
            .filter(Movie.rating.isnot(None))
            .order_by(Movie.rating.desc())
            .first()
        )

        latest_year = (
            self.db.query(func.max(Movie.release_year))
            .filter(Movie.release_year.isnot(None))
            .scalar()
        ) or 0

        min_year = (
            self.db.query(func.min(Movie.release_year))
            .filter(Movie.release_year.isnot(None))
            .scalar()
        ) or 0

        return {
            "total_movies": total,
            "avg_rating": round(float(avg_rating), 2),
            "top_movie": {
                "title": top.title if top else "",
                "rating": float(top.rating) if top and top.rating else 0.0,
            },
            "latest_year": int(latest_year),
            "year_span": int(latest_year - min_year) if latest_year and min_year else 0,
        }

    # ── 写入 ──────────────────────────────────────────

    def upsert_movie(self, data: dict):
        """按 movie_id upsert 一条电影记录。"""
        movie_id = str(data.get("movie_id", ""))
        existing = self.db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
        else:
            self.db.add(Movie(**data))

    def delete_all(self):
        """清空 movies 表。"""
        self.db.query(Movie).delete()

    def count(self) -> int:
        """返回 movies 表行数。"""
        return self.db.query(Movie).count()
