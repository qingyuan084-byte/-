"""
语义检索服务
============
基于向量编码 + 余弦相似度的电影语义搜索。
替代 TF-IDF 文本搜索，解决短查询（"血腥""科幻"）匹配不准确的问题。

单例模式，复用 build_movie_embeddings.py 构建的向量库。
向量文件缺失时降级返回空列表，由调用方回退 TF-IDF。

查询编码自动选择后端（与 RAG 服务一致）：
  - zhipu:  智谱AI embedding-2 API（1024 维，默认）
  - local:  sentence-transformers 本地模型（384 维）
  - dashscope: 阿里云 DashScope text-embedding-v2 API（1536 维，已废弃）
"""

import os
import sys
import time
from pathlib import Path

# Windows 编码修复
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ["PYTHONUTF8"] = "1"
if sys.platform == "win32":
    import io
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env（支持独立导入，不依赖 app.py 的 load_dotenv）
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
APP_ENV = os.getenv("APP_ENV", "development")
env_override = PROJECT_ROOT / f".env.{APP_ENV}"
if env_override.exists():
    load_dotenv(env_override, override=True)

import numpy as np
import pandas as pd

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

ZHIPU_EMBEDDING_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
ZHIPU_EMBEDDING_MODEL = "embedding-2"
ZHIPU_EMBEDDING_DIM = 1024

EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "features" / "movie_embeddings.npy"
METADATA_PATH = PROJECT_ROOT / "data" / "features" / "movie_embeddings_metadata.csv"

class SemanticSearchService:
    """语义搜索服务 — 单例，延迟加载。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_ready"):
            return
        self._ready = True

        self._embeddings: np.ndarray | None = None
        self._titles: list[str] = []
        self._movie_ids: list[str] = []
        self._model = None
        self._provider: str = ""
        self._api_key: str = ""
        self._embedding_dim: int = 0

        self._load_data()

        # 延迟加载 FAISS（不阻塞启动）
        self._faiss = None

        self._resolve_provider()

    # -- 加载 -------------------------------------------------

    def _load_data(self):
        if not EMBEDDINGS_PATH.exists():
            print(f"[语义搜索] 向量文件不存在: {EMBEDDINGS_PATH}")
            print("[语义搜索]    请先运行: python scripts/build_movie_embeddings.py")
            print("[语义搜索]    将降级使用 TF-IDF 文本搜索。")
            return

        if not METADATA_PATH.exists():
            print(f"[语义搜索] 元数据文件不存在: {METADATA_PATH}")
            return

        self._embeddings = np.load(EMBEDDINGS_PATH).astype(np.float32)
        metadata = pd.read_csv(METADATA_PATH)
        self._titles = metadata["title"].astype(str).tolist()
        self._movie_ids = metadata["movie_id"].astype(str).tolist()
        self._embedding_dim = self._embeddings.shape[1]
        print(f"[语义搜索] 已加载 {len(self._embeddings)} 部电影向量 ({self._embedding_dim} 维)")

    def _resolve_provider(self):
        if self._embeddings is None:
            return

        provider = os.getenv("EMBEDDING_PROVIDER", "").strip().lower()

        if provider in ("zhipu", "dashscope", "local"):
            self._provider = provider
        else:
            if self._embedding_dim == 1024:
                self._provider = "zhipu"
            elif self._embedding_dim == 1536:
                self._provider = "dashscope"
            elif self._embedding_dim == 384:
                self._provider = "local"
            else:
                self._provider = "zhipu"

        print(f"[语义搜索] 编码后端: {self._provider}")

        if self._provider == "zhipu":
            self._api_key = os.getenv("ZHIPU_API_KEY", "")
        elif self._provider == "dashscope":
            self._api_key = os.getenv("DASHSCOPE_API_KEY", "")

    # -- 编码 -------------------------------------------------

    def _encode_query(self, query: str) -> np.ndarray:
        if self._provider == "zhipu":
            return self._encode_zhipu(query)
        elif self._provider == "dashscope":
            return self._encode_dashscope(query)
        else:
            return self._encode_local(query)

    def _encode_zhipu(self, query: str) -> np.ndarray:
        import requests

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": ZHIPU_EMBEDDING_MODEL, "input": [query]}

        for attempt in range(3):
            try:
                resp = requests.post(
                    ZHIPU_EMBEDDING_URL, headers=headers, json=payload, timeout=10
                )
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    vec = np.array(data["data"][0]["embedding"], dtype=np.float32)
                    return vec / np.linalg.norm(vec)
                else:
                    if attempt < 2:
                        time.sleep(1)
                    else:
                        print(f"[语义搜索] 编码错误: {data}")
                        return np.zeros(self._embedding_dim, dtype=np.float32)
            except Exception as e:
                if attempt < 2:
                    time.sleep(1)
                else:
                    print(f"[语义搜索] 编码异常: {e}")
                    return np.zeros(self._embedding_dim, dtype=np.float32)

        return np.zeros(self._embedding_dim, dtype=np.float32)

    def _encode_dashscope(self, query: str) -> np.ndarray:
        import requests

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": "text-embedding-v2", "input": {"texts": [query]}}

        for attempt in range(3):
            try:
                resp = requests.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/embeddings/"
                    "text-embedding/text-embedding",
                    headers=headers, json=payload, timeout=10
                )
                data = resp.json()
                if "output" in data and "embeddings" in data["output"]:
                    vec = np.array(
                        data["output"]["embeddings"][0]["embedding"], dtype=np.float32
                    )
                    return vec / np.linalg.norm(vec)
                else:
                    if attempt < 2:
                        time.sleep(1)
                    else:
                        print(f"[语义搜索] 编码错误: {data.get('message', data)}")
                        return np.zeros(self._embedding_dim, dtype=np.float32)
            except Exception as e:
                if attempt < 2:
                    time.sleep(1)
                else:
                    print(f"[语义搜索] 编码异常: {e}")
                    return np.zeros(self._embedding_dim, dtype=np.float32)

        return np.zeros(self._embedding_dim, dtype=np.float32)

    def _encode_local(self, query: str) -> np.ndarray:
        if not os.getenv("HF_ENDPOINT"):
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

        from sentence_transformers import SentenceTransformer

        if self._model is None:
            print(f"[语义搜索] 加载本地模型: {MODEL_NAME} ...")
            self._model = SentenceTransformer(MODEL_NAME)
            print("[语义搜索] 模型就绪")

        return self._model.encode(
            [query], normalize_embeddings=True
        ).astype(np.float32)[0]

    # -- 检索 -------------------------------------------------

    def search(self, query: str, top_n: int = 10) -> list[tuple[str, str, float]]:
        """
        返回 [(movie_id, title, similarity_score), ...] 按相似度降序。
        向量未加载时返回空列表。

        优先使用 FAISS IndexFlatIP；不可用时 fallback 到 np.dot。
        """
        if self._embeddings is None:
            return []

        query_vec = self._encode_query(query)

        # FAISS 优先
        if self._faiss is None:
            try:
                from backend.services.faiss_index import FaissIndex
                self._faiss = FaissIndex()
            except Exception:
                self._faiss = False  # 标记已尝试, 不走 FAISS

        if self._faiss and self._faiss is not False:
            result = self._faiss.search(
                query_vec, top_n,
                self._embeddings, self._movie_ids, self._titles,
            )
            if result is not None:
                return result

        # np.dot fallback
        similarities = np.dot(self._embeddings, query_vec)

        n = min(top_n, len(similarities))
        top_indices = np.argpartition(similarities, -n)[-n:]
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

        return [
            (self._movie_ids[i], self._titles[i], round(float(similarities[i]), 4))
            for i in top_indices
        ]

    def is_ready(self) -> bool:
        return self._embeddings is not None
