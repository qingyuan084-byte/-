"""
数据库 ORM 模型
=============
Movie 模型映射到 movies 表，字段覆盖 douban_movies_cleaned.csv 的全部列。
"""
from sqlalchemy import Column, String, Float, Text
from backend.db import Base


class Movie(Base):
    """豆瓣电影 ORM 模型。"""

    __tablename__ = "movies"

    # 主键
    movie_id = Column(String(32), primary_key=True, comment="豆瓣 movie_id")
    title = Column(String(255), nullable=False, index=True, comment="电影标题")
    rating = Column(Float, nullable=True, comment="豆瓣评分")
    total_ratings = Column(String(32), nullable=True, comment="总评分数（可能包含逗号如 2,028,721）")
    directors = Column(String(512), nullable=True, comment="导演")
    actors = Column(Text, nullable=True, comment="演员（逗号分隔）")
    screenwriters = Column(String(512), nullable=True, comment="编剧")
    release_date = Column(String(32), nullable=True, comment="上映日期（YYYY-MM-DD）")
    genres = Column(String(256), nullable=True, comment="类型（逗号分隔）")
    countries = Column(String(256), nullable=True, comment="国家/地区（斜线分隔）")
    languages = Column(String(256), nullable=True, comment="语言")
    runtime = Column(String(64), nullable=True, comment="片长")
    summary = Column(Text, nullable=True, comment="剧情简介")
    link = Column(String(512), nullable=True, comment="豆瓣链接")
    poster = Column(String(1024), nullable=True, comment="海报 URL")
    tags = Column(Text, nullable=True, comment="标签")
    release_year = Column(Float, nullable=True, comment="上映年份（数值）")
    genre_list = Column(Text, nullable=True, comment="类型列表（Python repr 格式）")

    def to_basic_dict(self) -> dict:
        """返回基础字段（movie_id, title, rating）。"""
        return {
            "movie_id": self.movie_id,
            "title": self.title,
            "rating": float(self.rating) if self.rating else 0.0,
        }

    def to_rich_dict(self) -> dict:
        """返回完整字段。"""
        return {
            "movie_id": self.movie_id,
            "title": self.title,
            "rating": float(self.rating) if self.rating else 0.0,
            "year": int(self.release_year) if self.release_year else None,
            "poster_url": self.poster or "",
            "genres": self.genres or "",
            "summary": self.summary or "",
            "directors": self.directors or "",
            "actors": self.actors or "",
            "countries": self.countries or "",
            "runtime": self.runtime or "",
            "total_ratings": self.total_ratings or "",
            "release_date": self.release_date or "",
        }
