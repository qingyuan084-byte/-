"""
基于内容的推荐器 (Content-Based Recommender)

利用 TF-IDF 文本特征和类型特征计算电影之间的余弦相似度，
支持"相似电影"和"文本搜索"两种推荐方式。
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import load_npz, csr_matrix, hstack, issparse
from sklearn.metrics.pairwise import cosine_similarity

# Windows 终端编码兼容
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ======================== 路径配置 ========================

FEATURES_DIR = Path("data/features")
TFIDF_PATH = FEATURES_DIR / "tfidf_matrix.npz"
VECTORIZER_PATH = FEATURES_DIR / "tfidf_vectorizer.joblib"
MOVIE_IDS_PATH = FEATURES_DIR / "movie_ids.csv"
GENRE_PATH = FEATURES_DIR / "genre_features.csv"


# ======================== 推荐器 ========================

class ContentBasedRecommender:
    """
    基于内容的电影推荐器。

    使用 TF-IDF 文本特征计算余弦相似度，支持按电影 ID 推荐和按文本查询推荐。
    """

    def __init__(
        self,
        tfidf_matrix: np.ndarray | None = None,
        movie_ids_df: pd.DataFrame | None = None,
        genre_matrix: np.ndarray | None = None,
        use_genre: bool = True,
        genre_weight: float = 0.5,
        precompute: bool = False,
    ):
        """
        Args:
            tfidf_matrix: (n_movies, n_features) TF-IDF 特征矩阵（稀疏或密集）
            movie_ids_df: 包含 movie_id, title 的 DataFrame
            genre_matrix: (n_movies, n_genres) 多热编码矩阵，可选
            use_genre: 是否融合类型特征
            genre_weight: 类型特征的权重（0-1），0 表示仅用 TF-IDF
            precompute: 是否预计算完整相似度矩阵（默认关闭，按需计算）
        """
        self.movie_ids_df = movie_ids_df.copy() if movie_ids_df is not None else None
        self.tfidf_matrix = tfidf_matrix
        self.genre_matrix = genre_matrix
        self.use_genre = use_genre and genre_matrix is not None
        self.genre_weight = genre_weight
        self.similarity_matrix = None

        # 构建索引：movie_id -> 矩阵行号
        if self.movie_ids_df is not None:
            self.movie_ids_df["_idx"] = range(len(self.movie_ids_df))
            self._id_to_idx = dict(
                zip(
                    self.movie_ids_df["movie_id"].astype(str),
                    self.movie_ids_df["_idx"],
                )
            )
        else:
            self._id_to_idx = {}

        # 构建最终特征矩阵（保持稀疏）
        self._build_feature_matrix()

        # 预计算相似度（仅在显式开启时）
        if precompute and self.feature_matrix is not None:
            self._precompute_similarity()
        else:
            n_movies = self.feature_matrix.shape[0] if self.feature_matrix is not None else 0
            print(f"[初始化] 特征矩阵形状: {self.feature_matrix.shape}, 未预计算相似度矩阵（按需计算）")

    # ── 内部方法 ──────────────────────────────────────

    def _build_feature_matrix(self):
        """融合 TF-IDF 和类型特征为最终特征矩阵（保持稀疏）。"""
        if self.tfidf_matrix is None:
            self.feature_matrix = None
            return

        # 确保 TF-IDF 为 CSR 稀疏矩阵
        if issparse(self.tfidf_matrix):
            sparse_tfidf = self.tfidf_matrix
        else:
            sparse_tfidf = csr_matrix(self.tfidf_matrix)

        if self.use_genre:
            genre_sparse = csr_matrix(self.genre_matrix.astype(np.float32))
            tfidf_weight = 1.0 - self.genre_weight
            self.feature_matrix = hstack(
                [sparse_tfidf * tfidf_weight, genre_sparse * self.genre_weight],
                format="csr",
            )
        else:
            self.feature_matrix = sparse_tfidf

        print(f"[初始化] 特征矩阵形状: {self.feature_matrix.shape}")

    def _precompute_similarity(self):
        """预计算余弦相似度矩阵（仅 precompute=True 时调用），使用 float32 节省内存。"""
        n = self.feature_matrix.shape[0]
        print(f"[预计算] 正在计算 {n}x{n} 相似度矩阵...")
        self.similarity_matrix = cosine_similarity(self.feature_matrix, dense_output=True)
        self.similarity_matrix = self.similarity_matrix.astype(np.float32)
        # 将对角线（自身相似度）设为 -1，以便排除自身
        np.fill_diagonal(self.similarity_matrix, -1.0)
        mem_mb = self.similarity_matrix.nbytes / (1024 * 1024)
        print(f"[预计算] 完成，相似度矩阵占用 {mem_mb:.1f} MB")

    def _get_idx(self, movie_id: str) -> int | None:
        """将 movie_id 映射到矩阵行号。"""
        return self._id_to_idx.get(str(movie_id))

    def _get_movie_info(self, idx: int) -> tuple[str, str]:
        """根据行号返回 (movie_id, title)。"""
        row = self.movie_ids_df.iloc[idx]
        return str(row["movie_id"]), str(row["title"])

    # ── 公开方法 ──────────────────────────────────────

    def recommend_by_movie(self, movie_id: str, top_n: int = 10) -> list[tuple[str, str, float]]:
        """
        给定电影 ID，返回最相似的 N 部电影。

        优先使用预计算相似度矩阵；若未预计算，则按需计算目标电影与全量特征矩阵的余弦相似度。

        Args:
            movie_id: 豆瓣 movie_id（字符串）
            top_n: 返回数量

        Returns:
            [(movie_id, title, similarity_score), ...]，相似度从高到低排序
        """
        if self.feature_matrix is None:
            return []

        idx = self._get_idx(movie_id)
        if idx is None:
            print(f"[错误] 找不到 movie_id={movie_id}")
            return []

        # 有预计算矩阵时直接查表
        if self.similarity_matrix is not None:
            sim_row = self.similarity_matrix[idx]
            top_indices = np.argpartition(sim_row, -top_n)[-top_n:]
            top_indices = top_indices[np.argsort(sim_row[top_indices])[::-1]]

            results = []
            for i in top_indices:
                mid, title = self._get_movie_info(i)
                results.append((mid, title, float(sim_row[i])))
            return results

        # 按需计算：目标电影向量 vs 全量特征矩阵
        target_vec = self.feature_matrix[idx:idx + 1]
        sims = cosine_similarity(target_vec, self.feature_matrix, dense_output=True)[0]

        # 排除自身
        sims[idx] = -1.0

        top_indices = np.argpartition(sims, -top_n)[-top_n:]
        top_indices = top_indices[np.argsort(sims[top_indices])[::-1]]

        results = []
        for i in top_indices:
            if sims[i] <= -1.0:
                continue
            mid, title = self._get_movie_info(i)
            results.append((mid, title, float(sims[i])))

        return results

    def recommend_by_text(self, query_text: str, top_n: int = 10) -> list[tuple[str, str, float]]:
        """
        给定文本描述，返回最相似的电影。

        优先使用 TF-IDF 余弦相似度；若查询词不在词汇表中（向量全零），
        自动回退到 jieba 分词 + 标题关键词匹配。

        Args:
            query_text: 查询文本，如 "悬疑烧脑的科幻片"
            top_n: 返回数量

        Returns:
            [(movie_id, title, similarity_score), ...]
        """
        if self.tfidf_matrix is None:
            raise RuntimeError("TF-IDF 矩阵未加载")

        # 1) 尝试 TF-IDF 向量化
        tfidf = joblib.load(VECTORIZER_PATH)
        query_vec = tfidf.transform([query_text])

        # 2) 如果查询词不在词汇表中，回退到关键词匹配
        if query_vec.nnz == 0:
            print(f"[文本搜索] 查询词 '{query_text}' 不在 TF-IDF 词汇中，回退到关键词匹配")
            return self._fallback_search(query_text, top_n)

        # 3) 维度不匹配时直接回退（防御性检查）
        if query_vec.shape[1] != self.tfidf_matrix.shape[1]:
            print(f"[文本搜索] 向量维度不匹配 ({query_vec.shape[1]} vs {self.tfidf_matrix.shape[1]})，回退关键词匹配")
            return self._fallback_search(query_text, top_n)

        # 4) 正常 TF-IDF 余弦相似度
        sims = cosine_similarity(query_vec, self.tfidf_matrix, dense_output=True)[0]

        # 5) 最高分过低也回退（query 虽然有特征但匹配太弱）
        if sims.max() < 0.005:
            print(f"[文本搜索] 查询 '{query_text}' TF-IDF 最高分 {sims.max():.6f} 过低，回退关键词匹配")
            return self._fallback_search(query_text, top_n)

        top_indices = np.argpartition(sims, -top_n)[-top_n:]
        top_indices = top_indices[np.argsort(sims[top_indices])[::-1]]

        results = []
        for i in top_indices:
            mid, title = self._get_movie_info(i)
            results.append((mid, title, float(sims[i])))

        return results

    def _fallback_search(self, query_text: str, top_n: int = 10) -> list[tuple[str, str, float]]:
        """
        后备搜索：多策略关键词匹配（标题 + 简介 + 导演 + 演员 + 类型 + 国家）。

        策略（按权重从高到低）：
        0. jieba 关键词精确匹配导演/演员/类型/国家 → +6 分/词
        1. 查询文本整体作为子串匹配标题 → +5 分
        2. jieba 关键词精确匹配标题 → +3 分/词
        3. jieba 关键词拆成单字，全部命中标题 → +2 分/词
        4. jieba 关键词精确匹配简介 → +1 分/词
        5. 查询字符集与标题字符集重叠 → +0.2 分/字
        """
        import jieba

        self._ensure_summaries_loaded()

        keywords = [w.strip() for w in jieba.cut(query_text) if len(w.strip()) > 1]
        if not keywords:
            keywords = [query_text.strip()]

        query_chars = set(query_text.replace(" ", ""))
        query_lower = query_text.lower()

        scores = np.zeros(len(self.movie_ids_df))

        for i in range(len(self.movie_ids_df)):
            row = self.movie_ids_df.iloc[i]
            title = str(row.get("title", ""))
            title_lower = title.lower()
            mid = str(row.get("movie_id", ""))
            summary = self._summaries.get(mid, "")
            score = 0.0

            # 策略 0: 导演/演员/类型/国家匹配（最高权重）
            for kw in keywords:
                for field_name in ["directors", "actors", "genres", "countries"]:
                    field_val = self._metadata_fields.get(field_name, {}).get(mid, "")
                    if field_val and kw in field_val:
                        score += 6.0

            # 策略 1: 完整查询作为标题子串
            if query_lower in title_lower:
                score += 5.0

            # 策略 2: jieba 关键词精确匹配标题
            for kw in keywords:
                if kw in title:
                    score += 3.0

            # 策略 3: 关键词单字全部命中标题
            for kw in keywords:
                kw_chars = set(kw)
                if len(kw_chars) >= 2 and kw_chars.issubset(set(title)):
                    score += 2.0

            # 策略 4: jieba 关键词匹配简介
            if summary:
                for kw in keywords:
                    if kw in summary:
                        score += 1.0

            # 策略 5: 字符重叠
            if query_chars:
                score += len(query_chars & set(title)) * 0.2

            scores[i] = score

        if scores.max() <= 0:
            return []

        top_indices = np.argpartition(scores, -top_n)[-top_n:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        raw_max = float(scores.max())
        results = []
        for i in top_indices:
            if scores[i] > 0:
                mid, title = self._get_movie_info(i)
                max_possible = 6.0 + 5.0 + len(keywords) * 3.0 + len(keywords) * 2.0 + len(keywords) * 1.0 + len(query_chars) * 0.2
                normalized = round(min(float(scores[i]) / max(max_possible, 1.0), 1.0), 4)
                results.append((mid, title, normalized))

        return results

    def _ensure_summaries_loaded(self):
        """按需加载电影元数据（简介、导演、演员、类型、国家 — 用于后备搜索）。"""
        if hasattr(self, "_summaries") and self._summaries:
            return
        self._summaries = {}
        self._metadata_fields = {
            "directors": {},
            "actors": {},
            "genres": {},
            "countries": {},
        }
        cleaned_path = Path("data/processed/douban_movies_cleaned.csv")
        if cleaned_path.exists():
            try:
                usecols = ["movie_id", "summary"]
                for col in ["directors", "actors", "genres", "countries"]:
                    usecols.append(col)
                df = pd.read_csv(
                    cleaned_path,
                    dtype={"movie_id": str},
                    usecols=usecols,
                )
                df["movie_id"] = df["movie_id"].astype(str)
                self._summaries = dict(zip(df["movie_id"], df["summary"].fillna("")))
                for col in ["directors", "actors", "genres", "countries"]:
                    if col in df.columns:
                        self._metadata_fields[col] = dict(
                            zip(df["movie_id"], df[col].fillna(""))
                        )
            except Exception:
                pass


# ======================== 加载函数 ========================

def load_data():
    """从磁盘加载所有特征文件和元数据，返回推荐器所需的数据。"""
    print("=" * 50)
    print("正在加载特征文件...")

    tfidf_matrix = load_npz(TFIDF_PATH)
    print(f"  TF-IDF 矩阵: {tfidf_matrix.shape}")

    movie_ids_df = pd.read_csv(MOVIE_IDS_PATH, dtype={"movie_id": str})
    print(f"  电影元数据: {len(movie_ids_df)} 条")

    genre_matrix = None
    if GENRE_PATH.exists():
        genre_df = pd.read_csv(GENRE_PATH)
        genre_matrix = genre_df.values
        print(f"  类型特征: {genre_matrix.shape}")

    return tfidf_matrix, movie_ids_df, genre_matrix


# ======================== 示例运行 ========================

if __name__ == "__main__":
    # 1. 加载数据
    tfidf, movies, genres = load_data()

    # 2. 初始化推荐器
    recommender = ContentBasedRecommender(
        tfidf_matrix=tfidf,
        movie_ids_df=movies,
        genre_matrix=genres,
        use_genre=True,
        genre_weight=0.3,   # 类型特征权重 30%
        precompute=False,   # 默认按需计算，节省内存
    )

    # 3. 演示：按电影 ID 推荐
    print("\n" + "=" * 50)
    print("【推荐演示 1】与《盗梦空间》相似的电影")

    # 在数据中找一个已知电影 ID
    test_movie = movies.iloc[0]
    test_id = str(test_movie["movie_id"])
    test_title = test_movie["title"]
    print(f"  输入: {test_id} - {test_title}\n")

    results = recommender.recommend_by_movie(test_id, top_n=10)
    for i, (mid, title, score) in enumerate(results, 1):
        bar = "█" * int(score * 20)
        print(f"  {i:2d}. [{score:.4f}] {title}  {bar}")

    # 4. 演示：按文本搜索（长文本效果更好）
    print("\n" + "=" * 50)
    print("【推荐演示 2】文本搜索: '科幻冒险动作大片 外星人入侵地球'")

    results = recommender.recommend_by_text("科幻冒险动作大片 外星人入侵地球", top_n=10)
    for i, (mid, title, score) in enumerate(results, 1):
        bar = "█" * int(score * 30)
        print(f"  {i:2d}. [{score:.4f}] {title}  {bar}")

    # 5. 演示：按文本搜索（短文本也能匹配高频词）
    print("\n" + "=" * 50)
    print("【推荐演示 3】文本搜索: '感人的爱情故事 催泪 虐心'")

    results = recommender.recommend_by_text("感人的爱情故事 催泪 虐心", top_n=10)
    for i, (mid, title, score) in enumerate(results, 1):
        bar = "█" * int(score * 30)
        print(f"  {i:2d}. [{score:.4f}] {title}  {bar}")
