"""
离线构建电影向量库
===================
将 2065 部电影编码为向量，保存到 data/features/ 供 RAG 检索服务使用。

支持三种后端：
  - zhipu (默认): 智谱AI embedding-2 API，1024 维
  - local:        sentence-transformers 本地模型，384 维
  - dashscope:    阿里云 DashScope text-embedding-v2 API，1536 维（已废弃）

用法:
    python scripts/build_movie_embeddings.py              # 默认 zhipu
    python scripts/build_movie_embeddings.py --provider local   # 本地模型
"""

import sys
import os
import time
import argparse
from pathlib import Path

# ═══════════════════════════════════════════════════════
# 修复 Windows GBK 编码问题
# ═══════════════════════════════════════════════════════
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ["PYTHONUTF8"] = "1"
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── 加载 .env ──────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

import numpy as np
import pandas as pd
from tqdm import tqdm

# ── 配置 ──────────────────────────────────────────────

CSV_PATH = PROJECT_ROOT / "data" / "processed" / "douban_movies_cleaned.csv"
OUT_EMBEDDINGS = PROJECT_ROOT / "data" / "features" / "movie_embeddings.npy"
OUT_METADATA = PROJECT_ROOT / "data" / "features" / "movie_embeddings_metadata.csv"
OUT_FAISS_INDEX = PROJECT_ROOT / "data" / "features" / "movie_faiss.index"

# ZhipuAI 配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_EMBEDDING_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
ZHIPU_EMBEDDING_MODEL = "embedding-2"
ZHIPU_BATCH_SIZE = 20


def build_embedding_text(row: pd.Series) -> str:
    title = str(row.get("title", ""))
    summary = str(row.get("summary", ""))
    genres = str(row.get("genres", ""))
    directors = str(row.get("directors", ""))
    actors = str(row.get("actors", ""))
    countries = str(row.get("countries", ""))
    return f"{title} {summary} {genres} 导演:{directors} 主演:{actors} 国家:{countries}"


# ── ZhipuAI 编码 ──────────────────────────────────

def encode_zhipu(texts: list[str]) -> np.ndarray:
    """使用智谱AI embedding-2 API 批量编码。"""
    import requests

    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json",
    }

    all_embeddings = []
    total_batches = (len(texts) + ZHIPU_BATCH_SIZE - 1) // ZHIPU_BATCH_SIZE

    for i in tqdm(range(0, len(texts), ZHIPU_BATCH_SIZE), total=total_batches,
                  desc="    编码中"):
        batch = texts[i : i + ZHIPU_BATCH_SIZE]
        payload = {
            "model": ZHIPU_EMBEDDING_MODEL,
            "input": batch,
        }

        for attempt in range(3):
            try:
                resp = requests.post(
                    ZHIPU_EMBEDDING_URL,
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    emb_list = sorted(data["data"], key=lambda x: x["index"])
                    all_embeddings.extend(
                        [np.array(e["embedding"], dtype=np.float32) for e in emb_list]
                    )
                    break
                else:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                    else:
                        print(f"\n      API 错误: {data}")
                        raise RuntimeError("ZhipuAI API 返回异常")
            except requests.RequestException as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise

    embeddings = np.stack(all_embeddings, axis=0)
    # L2 归一化
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    return embeddings


# ── DashScope 编码（已废弃，保留兼容） ──────────────────

def encode_dashscope(texts: list[str]) -> np.ndarray:
    """使用 DashScope text-embedding-v2 API 批量编码。"""
    import requests

    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    all_embeddings = []
    batch_size = 25
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for i in tqdm(range(0, len(texts), batch_size), total=total_batches,
                  desc="    编码中"):
        batch = texts[i : i + batch_size]
        payload = {
            "model": "text-embedding-v2",
            "input": {"texts": batch},
        }

        for attempt in range(3):
            try:
                resp = requests.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/embeddings/"
                    "text-embedding/text-embedding",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                data = resp.json()
                if "output" in data and "embeddings" in data["output"]:
                    emb_list = data["output"]["embeddings"]
                    emb_list.sort(key=lambda x: x["text_index"])
                    all_embeddings.extend(
                        [np.array(e["embedding"], dtype=np.float32) for e in emb_list]
                    )
                    break
                else:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                    else:
                        print(f"\n      API 错误: {data.get('message', data)}")
                        raise RuntimeError("DashScope API 返回异常")
            except requests.RequestException as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise

    embeddings = np.stack(all_embeddings, axis=0)
    # L2 归一化
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    return embeddings


# ── 本地模型编码 ────────────────────────────────────

def encode_local(texts: list[str]) -> np.ndarray:
    """使用 sentence-transformers 本地模型编码。"""
    HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ["HF_ENDPOINT"] = HF_ENDPOINT
    print(f"      HF_ENDPOINT = {HF_ENDPOINT}")

    from sentence_transformers import SentenceTransformer

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    print(f"      模型: {MODEL_NAME}")
    print("      ⏳ 加载模型（首次需下载约 400MB）...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"      向量维度: {model.get_sentence_embedding_dimension()}")

    return model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).astype(np.float32)


# ── 主流程 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="构建电影向量库")
    parser.add_argument(
        "--provider",
        choices=["zhipu", "dashscope", "local"],
        default="zhipu",
        help="编码后端 (默认: zhipu)",
    )
    args = parser.parse_args()

    # ── 检查数据文件 ──────────────────────────────────
    if not CSV_PATH.exists():
        print(f"[错误] 找不到数据文件: {CSV_PATH}")
        sys.exit(1)

    if args.provider == "zhipu" and not ZHIPU_API_KEY:
        print("[错误] ZHIPU_API_KEY 未设置，请在 .env 中配置")
        print("       或使用 --provider local 选择本地模型")
        sys.exit(1)
    if args.provider == "dashscope" and not os.getenv("DASHSCOPE_API_KEY", ""):
        print("[错误] DASHSCOPE_API_KEY 未设置，请在 .env 中配置")
        print("       或使用 --provider local 选择本地模型")
        sys.exit(1)

    # ── 加载数据 ──────────────────────────────────────
    print(f"[1/4] 加载数据: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    n_movies = len(df)
    print(f"      共 {n_movies} 部电影")

    # ── 构建文本 ──────────────────────────────────────
    print("[2/4] 构建电影文本...")
    texts = [build_embedding_text(row) for _, row in df.iterrows()]

    # ── 编码 ──────────────────────────────────────────
    print(f"[3/4] 编码 ({args.provider}) ...")
    start = time.time()

    if args.provider == "zhipu":
        embeddings = encode_zhipu(texts)
    elif args.provider == "dashscope":
        embeddings = encode_dashscope(texts)
    else:
        embeddings = encode_local(texts)

    elapsed = time.time() - start
    print(f"      耗时: {elapsed:.1f}s, 矩阵形状: {embeddings.shape}")

    # ── 保存 ──────────────────────────────────────────
    print("[4/4] 保存向量和元数据...")

    OUT_EMBEDDINGS.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUT_EMBEDDINGS, embeddings)
    print(f"      → {OUT_EMBEDDINGS} ({embeddings.nbytes / 1024 / 1024:.1f} MB)")

    metadata_cols = ["movie_id", "title", "rating", "release_year", "genres"]
    metadata = df[metadata_cols].copy()
    metadata.rename(columns={"release_year": "year"}, inplace=True)
    metadata.to_csv(OUT_METADATA, index=False)
    print(f"      → {OUT_METADATA}")

    # ── 构建 FAISS 索引 ──────────────────────────────────
    print("\n[5/5] 构建 FAISS 索引 (IndexFlatIP)...")
    try:
        import faiss

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        faiss.write_index(index, str(OUT_FAISS_INDEX))
        print(f"      → {OUT_FAISS_INDEX}")
        print(f"       向量数量: {index.ntotal}, 维度: {index.d}")
        print(f"       索引类型: IndexFlatIP (内积 = 余弦相似度, 向量已 L2 归一化)")
    except ImportError:
        print("      [跳过] faiss 未安装, 请运行: pip install faiss-cpu")
    except Exception as e:
        print(f"      [警告] FAISS 索引构建失败: {e}")

    print(
        f"\n✅ 完成！{n_movies} 部电影 → {embeddings.shape[1]} 维向量。"
        f"\n   provider={args.provider}, 耗时 {elapsed:.1f}s"
    )


if __name__ == "__main__":
    main()
