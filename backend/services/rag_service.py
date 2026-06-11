"""
RAG 向量检索服务
===============
加载离线构建的电影向量库，提供基于余弦相似度的电影检索。

单例模式，首次初始化时加载 .npy 嵌入和 .csv 元数据。
如果向量文件不存在，降级运行（返回空列表），不阻塞应用启动。

查询编码支持两种后端（由 EMBEDDING_PROVIDER 或自动探测）：
  - zhipu:  智谱AI embedding-2 API（1024 维，推荐）
  - local:  sentence-transformers 本地模型
  - dashscope: 阿里云 DashScope API（已废弃）
"""

import os
import sys
import time
from pathlib import Path

# Windows 编码修复（支持独立导入时正确输出中文）
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ["PYTHONUTF8"] = "1"
if sys.platform == "win32":
    import io
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 确保项目根目录在 sys.path 中
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

class RAGService:
    """向量检索服务 — 单例，延迟加载。"""

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
        self._metadata: pd.DataFrame | None = None
        self._model = None                # sentence-transformers 模型（local 模式）
        self._provider: str = ""          # "zhipu" | "dashscope" | "local"
        self._api_key: str = ""
        self._embedding_dim: int = 0

        self._load_data()

        # 延迟加载 FAISS（不阻塞启动）
        self._faiss = None

        self._resolve_provider()

    # ── 加载 ───────────────────────────────────────────

    def _load_data(self):
        if not EMBEDDINGS_PATH.exists():
            print(f"[RAG] WARN 向量文件不存在: {EMBEDDINGS_PATH}")
            print("[RAG]    请先运行: python scripts/build_movie_embeddings.py")
            print("[RAG]    RAG 功能将降级为纯 LLM 对话模式。")
            return

        if not METADATA_PATH.exists():
            print(f"[RAG] WARNING:元数据文件不存在: {METADATA_PATH}")
            return

        self._embeddings = np.load(EMBEDDINGS_PATH).astype(np.float32)
        self._metadata = pd.read_csv(METADATA_PATH)
        self._embedding_dim = self._embeddings.shape[1]
        print(f"[RAG] [OK] 已加载 {len(self._embeddings)} 部电影向量 ({self._embedding_dim} 维)")

    def _resolve_provider(self):
        """根据环境变量或向量维度自动选择编码后端。"""
        if self._embeddings is None:
            return

        provider = os.getenv("EMBEDDING_PROVIDER", "").strip().lower()

        if provider in ("zhipu", "dashscope", "local"):
            self._provider = provider
        else:
            # 自动探测：1024 维 → zhipu, 1536 维 → dashscope, 384 维 → local
            if self._embedding_dim == 1024:
                self._provider = "zhipu"
            elif self._embedding_dim == 1536:
                self._provider = "dashscope"
            elif self._embedding_dim == 384:
                self._provider = "local"
            else:
                self._provider = "zhipu"

        print(f"[RAG] 编码后端: {self._provider}")

        if self._provider == "zhipu":
            self._api_key = os.getenv("ZHIPU_API_KEY", "")
            if not self._api_key:
                print("[RAG] WARNING:ZHIPU_API_KEY 未设置，编码将失败")
        elif self._provider == "dashscope":
            self._api_key = os.getenv("DASHSCOPE_API_KEY", "")
            if not self._api_key:
                print("[RAG] WARNING:DASHSCOPE_API_KEY 未设置，编码将失败")

    # ── 编码 ───────────────────────────────────────────

    def _encode_query(self, query: str) -> np.ndarray:
        """将查询文本编码为向量。"""
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
                    ZHIPU_EMBEDDING_URL, headers=headers, json=payload, timeout=10,
                )
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    vec = np.array(
                        data["data"][0]["embedding"],
                        dtype=np.float32,
                    )
                    return vec / np.linalg.norm(vec)
                else:
                    if attempt < 2:
                        time.sleep(1)
                    else:
                        print(f"[RAG] ZhipuAI 编码错误: {data}")
                        return np.zeros(self._embedding_dim, dtype=np.float32)
            except Exception as e:
                if attempt < 2:
                    time.sleep(1)
                else:
                    print(f"[RAG] ZhipuAI 编码异常: {e}")
                    return np.zeros(self._embedding_dim, dtype=np.float32)

        return np.zeros(self._embedding_dim, dtype=np.float32)

    def _encode_dashscope(self, query: str) -> np.ndarray:
        import requests

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "text-embedding-v2",
            "input": {"texts": [query]},
        }

        for attempt in range(3):
            try:
                resp = requests.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/embeddings/"
                    "text-embedding/text-embedding",
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                data = resp.json()
                if "output" in data and "embeddings" in data["output"]:
                    vec = np.array(
                        data["output"]["embeddings"][0]["embedding"],
                        dtype=np.float32,
                    )
                    return vec / np.linalg.norm(vec)
                else:
                    if attempt < 2:
                        time.sleep(1)
                    else:
                        print(f"[RAG] DashScope 编码错误: {data.get('message', data)}")
                        return np.zeros(self._embedding_dim, dtype=np.float32)
            except Exception as e:
                if attempt < 2:
                    time.sleep(1)
                else:
                    print(f"[RAG] DashScope 编码异常: {e}")
                    return np.zeros(self._embedding_dim, dtype=np.float32)

        return np.zeros(self._embedding_dim, dtype=np.float32)

    def _encode_local(self, query: str) -> np.ndarray:
        # 设置 HF 镜像
        if not os.getenv("HF_ENDPOINT"):
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

        from sentence_transformers import SentenceTransformer

        if self._model is None:
            print(f"[RAG] ... 加载本地模型: {MODEL_NAME} ...")
            self._model = SentenceTransformer(MODEL_NAME)
            print("[RAG] [OK] 模型就绪")

        return self._model.encode(
            [query],
            normalize_embeddings=True,
        ).astype(np.float32)[0]

    # ── 检索 ───────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        余弦相似度检索。

        返回 list[dict]，每项: movie_id, title, rating, year, genres, similarity
        如果向量未加载，返回空列表。

        优先使用 FAISS IndexFlatIP；不可用时 fallback 到 np.dot。
        """
        if self._embeddings is None or self._metadata is None:
            return []

        query_vec = self._encode_query(query)

        # FAISS 优先
        if self._faiss is None:
            try:
                from backend.services.faiss_index import FaissIndex
                self._faiss = FaissIndex()
            except Exception:
                self._faiss = False

        if self._faiss and self._faiss is not False:
            faiss_result = self._faiss.search(
                query_vec, top_k,
                self._embeddings,
                [str(mid) for mid in self._metadata["movie_id"]],
                [str(t) for t in self._metadata["title"]],
            )
            if faiss_result is not None:
                results = []
                for mid, title, sim in faiss_result:
                    row = self._metadata[self._metadata["movie_id"].astype(str) == mid]
                    if row.empty:
                        continue
                    row = row.iloc[0]
                    results.append({
                        "movie_id": mid,
                        "title": title,
                        "rating": float(row["rating"]),
                        "year": int(row["year"]) if not pd.isna(row["year"]) else None,
                        "genres": str(row["genres"]),
                        "similarity": sim,
                    })
                return results

        # np.dot fallback
        similarities = np.dot(self._embeddings, query_vec)

        if top_k >= len(similarities):
            top_indices = np.argsort(similarities)[::-1]
        else:
            top_indices = np.argpartition(similarities, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

        results = []
        for idx in top_indices:
            row = self._metadata.iloc[idx]
            results.append({
                "movie_id": str(row["movie_id"]),
                "title": str(row["title"]),
                "rating": float(row["rating"]),
                "year": int(row["year"]) if not pd.isna(row["year"]) else None,
                "genres": str(row["genres"]),
                "similarity": round(float(similarities[idx]), 4),
            })

        return results

    def is_ready(self) -> bool:
        return self._embeddings is not None
