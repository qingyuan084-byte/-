"""
共享 FAISS 向量索引
==================
为 semantic_search 和 rag_service 提供统一的 FAISS 检索能力。

优先级: FAISS IndexFlatIP > np.dot fallback
- USE_FAISS_INDEX=false 时跳过 FAISS 加载
- FAISS 未安装 / index 文件缺失 / 维度不匹配时自动降级 np.dot
- 不影响后端启动
"""

import os
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


class FaissIndex:
    """
    FAISS 向量索引 — 进程级单例, 延迟加载。

    用法:
        index = FaissIndex()
        distances, indices = index.search(query_vec, top_k)  # 返回 (distances, indices) 或 (None, None)
        index.is_ready  # bool — FAISS 是否可用

    若 FAISS 不可用, 调用方应 fallback 到 np.dot(self._embeddings, query_vec)。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._index = None
        self._dim = 0
        self._ntotal = 0

        self._index_path: Path | None = None
        self._enabled = False
        self._load_error: str | None = None

        self._resolve()

    def _resolve(self):
        """解析配置并尝试加载 FAISS index。"""
        use_faiss = os.getenv("USE_FAISS_INDEX", "true").lower() == "true"
        if not use_faiss:
            print("[FAISS] USE_FAISS_INDEX=false, 跳过 FAISS，将使用 np.dot fallback")
            return

        index_path = os.getenv("FAISS_INDEX_PATH", "data/features/movie_faiss.index")
        path = Path(index_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        self._index_path = path

        try:
            import faiss
            self._faiss = faiss
        except ImportError as e:
            self._load_error = f"faiss 未安装: {e}"
            print(f"[FAISS] {self._load_error}, 降级 np.dot")
            return

        if not path.exists():
            self._load_error = f"索引文件不存在: {path}"
            print(f"[FAISS] {self._load_error}, 请运行 build_movie_embeddings.py 生成")
            print("[FAISS]    将使用 np.dot fallback")
            return

        try:
            self._index = faiss.read_index(str(path))
            self._dim = self._index.d
            self._ntotal = self._index.ntotal
            self._enabled = True
            print(f"[FAISS] 已加载索引: {path} ({self._ntotal} 向量, {self._dim} 维)")
        except Exception as e:
            self._load_error = f"加载失败: {e}"
            print(f"[FAISS] {self._load_error}, 降级 np.dot")

    @property
    def is_ready(self) -> bool:
        return self._enabled and self._index is not None

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def ntotal(self) -> int:
        return self._ntotal

    def validate(self, embeddings: np.ndarray) -> bool:
        """验证 FAISS index 维度是否与 embeddings 匹配。"""
        if not self.is_ready:
            return False
        if embeddings.shape[1] != self._dim:
            print(f"[FAISS] 维度不匹配: index={self._dim}, embeddings={embeddings.shape[1]}, 降级 np.dot")
            return False
        if embeddings.shape[0] != self._ntotal:
            print(f"[FAISS] 向量数量不匹配: index={self._ntotal}, embeddings={embeddings.shape[0]}, 降级 np.dot")
            return False
        return True

    def search(
        self,
        query_vec: np.ndarray,
        top_k: int,
        embeddings: np.ndarray,
        movie_ids: list[str],
        titles: list[str],
    ) -> list[tuple[str, str, float]] | None:
        """
        使用 FAISS 检索 top_k 最相似向量。

        Args:
            query_vec: (D,) 已 L2 归一化的查询向量
            top_k: 返回数量
            embeddings: (N, D) numpy 数组（fallback 用）
            movie_ids: movie_id 列表
            titles: 标题列表

        Returns:
            [(movie_id, title, score), ...] 或 None（表示应 fallback 到 np.dot）
        """
        if not self.is_ready or not self.validate(embeddings):
            return None

        try:
            vec = query_vec.astype(np.float32).reshape(1, -1)
            distances, indices = self._index.search(vec, top_k)

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(movie_ids):
                    continue
                results.append((
                    movie_ids[idx],
                    titles[idx],
                    round(float(dist), 4),
                ))
            return results
        except Exception as e:
            print(f"[FAISS] 检索异常: {e}, 降级 np.dot")
            return None
