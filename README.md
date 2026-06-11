# CinéMatic · 电影推荐系统

基于豆瓣电影数据的智能推荐平台，集成 TF-IDF + FAISS 向量检索 + 智谱AI GLM 问答。

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Python 3.12 + FastAPI + Uvicorn |
| 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 数据库 | PostgreSQL 16 + SQLAlchemy ORM（可选，自动降级 CSV） |
| 缓存 | Redis 7（可选，自动降级） |
| 向量检索 | FAISS IndexFlatIP (1024维) |
| LLM | 智谱AI GLM-4-Flash（兼容 OpenAI SDK） |
| 文本嵌入 | 智谱AI embedding-2 (1024维) |
| 推荐 | TF-IDF + 稀疏矩阵 + MultiLabelBinarizer 类型特征 |

## 项目结构

```
movie-recommendation-system/
├── backend/                       # FastAPI 后端
│   ├── api/                       #   REST API 路由
│   │   ├── recommender_api.py     #     推荐/搜索/列表/统计
│   │   └── qa_api.py              #     智能问答（登小千）
│   ├── models/                    #   Pydantic 模型 + SQLAlchemy ORM
│   │   ├── pydantic_models.py     #     请求/响应 Schema
│   │   └── db_models.py           #     数据库表映射
│   ├── repositories/              #   数据仓库层（DB 查询封装）
│   │   └── movie_repository.py
│   ├── services/                  #   业务逻辑
│   │   ├── recommender_service.py #     推荐服务（DB/CSV 双模式）
│   │   ├── semantic_search.py     #     语义搜索（词向量 + TF-IDF 降级）
│   │   ├── rag_service.py         #     RAG 检索增强
│   │   ├── faiss_index.py         #     FAISS 向量索引封装
│   │   ├── qa_service.py          #     智能问答入口
│   │   └── qa/                    #     问答子模块
│   │       ├── service.py         #       LLM 对话 + function calling
│   │       ├── sessions.py        #       会话管理（内存 + SQLite 持久化）
│   │       ├── constants.py       #       提示词/工具定义/常量
│   │       ├── intent.py          #       意图识别
│   │       ├── filters.py         #       筛选条件处理
│   │       └── formatting.py      #       格式化输出
│   ├── cache.py                   #   Redis 缓存封装（可降级）
│   ├── db.py                      #   数据库连接管理
│   └── app.py                     #   应用入口 + 生命周期
│
├── frontend/                      # Vue 3 前端
│   ├── src/
│   │   ├── api/index.js           #   API 请求封装
│   │   ├── components/            #   通用组件
│   │   │   ├── MovieCard.vue      #     电影卡片
│   │   │   ├── home/              #     首页子组件（Banner/Hero/Section/Ranking/Footer）
│   │   │   ├── explore/           #     探索页子组件（FilterBar/MovieGrid）
│   │   │   ├── detail/            #     详情页子组件（MovieHero/SimilarMovies）
│   │   │   ├── chat/              #     问答页子组件（ChatInput/ChatMessages/QuickPrompts/RelatedMovies）
│   │   │   └── analysis/          #     分析页子组件（StatsOverview/MovieTable）
│   │   ├── composables/           #   可组合逻辑（useMovies/useChat/useSearch/useTheme 等）
│   │   ├── utils/                 #   工具函数（poster/quickQuestions）
│   │   ├── styles/theme.css       #   全局主题样式
│   │   ├── router/index.js        #   路由配置
│   │   └── views/                 #   页面视图（8 个）
│   ├── public/
│   ├── Dockerfile                 #   前端 Nginx 镜像
│   ├── nginx.conf                 #   Nginx SPA + API 代理
│   └── vite.config.js
│
├── data/                          # 数据文件
│   ├── raw/                       #   原始爬虫数据（douban_all_movies.csv）
│   ├── processed/                 #   清洗后 CSV（2125 部）
│   ├── features/                  #   模型特征（TF-IDF / Embeddings / FAISS / Genre）
│   ├── cleaning/                  #   数据清洗脚本（预处理 + 特征工程）
│   ├── crawler/                   #   爬虫（豆瓣 + TMDB API）
│   └── storage/                   #   数据存储抽象层
│
├── recommender/                   # 推荐算法核心
│   └── content_based.py           #   TF-IDF + 类型特征的余弦相似度推荐器
│
├── analysis/                      # 数据分析
│   ├── eda.py                     #   探索性数据分析
│   └── visualization/             #   可视化（图表 + 词云）
│
├── scripts/                       # 工具脚本
│   ├── crawl_2026_movies.py       #   豆瓣新片爬虫（curl_cffi + JSON API）
│   ├── import_movies_to_db.py     #   CSV → PostgreSQL 导入
│   ├── build_movie_embeddings.py  #   离线构建向量索引（zhipu/local）
│   └── warm_posters.py            #   海报预热下载
│
├── tests/                         # 测试（176 条）
├── cache/images/                  # 海报本地缓存
├── .env.example                   # 环境变量模板
├── .env.docker.example            # Docker 环境变量模板
├── .env.development               # 开发环境配置
├── .env.production                # 生产环境配置
├── docker-compose.yml             # 4 服务编排（frontend/backend/postgres/redis）
├── Dockerfile.backend             # 后端多阶段构建
├── requirements.txt               # Python 依赖
└── README.md
```

## 本地开发

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 ZHIPU_API_KEY（智谱AI 开放平台免费申请）
```

### 3. 启动基础设施（可选）

```bash
# PostgreSQL（Windows 本地）
& "D:\soft\postgresql\bin\pg_ctl.exe" start -D "D:\soft\postgresql\data"

# Redis（Docker）
docker compose up -d redis
```

未配置 PostgreSQL 或 Redis 时，系统自动降级到 CSV 文件 + 无缓存模式。

### 4. 导入数据（可选）

```bash
python scripts/import_movies_to_db.py   # CSV → PostgreSQL
```

### 5. 构建向量索引（首次或数据更新后）

```bash
python scripts/build_movie_embeddings.py --provider zhipu
python scripts/warm_posters.py           # 预热海报缓存
```

### 6. 启动服务

```bash
# 后端 (port 8002)
python backend/app.py

# 前端（新开终端，port 3000）
cd frontend && npm run dev
```

### 7. 运行测试

```bash
python -m pytest -q   # 176 passed
```

## Docker 部署

### 前置条件

- Docker 24+
- Docker Compose v2

### 快速启动

```bash
# 1. 创建 Docker 环境变量文件
cp .env.docker.example .env.docker

# 2. 编辑 .env.docker，填入 ZHIPU_API_KEY

# 3. 启动 PostgreSQL + Redis
docker compose up -d postgres redis

# 4. 构建后端和前端镜像
docker compose build backend frontend

# 5. 导入电影数据到 PostgreSQL（仅首次）
docker compose run --rm backend python scripts/import_movies_to_db.py

# 6. 启动全部服务
docker compose up -d
```

### 验证

```bash
curl http://localhost:8002/health              # {"status":"ok","movies_loaded":2125}
curl http://localhost:8002/docs                # API 文档
# 浏览器打开 http://localhost:3000              # 前端页面
```

### 常用命令

```bash
docker compose logs -f backend                 # 查看日志
docker compose restart backend                 # 重启后端
docker compose down                            # 停止全部
docker compose down -v                         # 停止并删除数据卷（重置数据库）
docker compose build --no-cache backend        # 重新构建
```

### 端口说明

| 服务 | 容器端口 | 宿主机端口 |
|------|---------|-----------|
| 前端 (Nginx) | 80 | 3000 |
| 后端 (FastAPI) | 8002 | 8002 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |

### 构建注意事项

- **faiss-cpu / scipy 编译**: Dockerfile 使用 `python:3.11-slim-bookworm`，安装 `build-essential` + `libopenblas-dev` + `gfortran`。首次构建约 5-15 分钟。
- **镜像大小**: 约 1.5-2.5 GB（含全部 Python 科学计算包）。
- **数据挂载**: `data/features/` 和 `data/processed/` 以只读卷挂载，修改宿主数据后需重启容器。

## 环境变量参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_ENV` | 运行环境（development / production / docker） | `development` |
| `API_PORT` | 后端端口 | `8002` |
| `DATABASE_URL` | PostgreSQL 连接串 | — |
| `REDIS_URL` | Redis 连接串 | — |
| `CACHE_TTL_SECONDS` | 缓存过期秒数 | `3600` |
| `ZHIPU_API_KEY` | 智谱AI API Key（必填） | — |
| `ZHIPU_MODEL` | LLM 模型 | `glm-4-flash` |
| `EMBEDDING_PROVIDER` | 嵌入后端（zhipu / local） | `zhipu` |
| `RECOMMENDER_PRECOMPUTE` | 预计算相似度矩阵 | `false` |
| `USE_FAISS_INDEX` | 启用 FAISS 向量索引 | `true` |
| `FAISS_INDEX_PATH` | FAISS 索引文件路径 | `data/features/movie_faiss.index` |
| `HF_ENDPOINT` | HuggingFace 镜像（国内网络） | — |
| `CORS_ORIGINS` | 允许的跨域来源 | `*`（开发）/ 限定域名（生产） |

## 降级策略

| 组件 | 降级条件 | Fallback |
|------|---------|----------|
| PostgreSQL | 连接失败 / 空表 | CSV 文件（`data/processed/`） |
| Redis | 未安装 / 连接失败 | 无缓存直查 |
| FAISS | 未安装 / 文件缺失 / 维度不匹配 | `np.dot` 暴力计算 |
| Recommender | MemoryError | `precompute=False` 按需计算 |
| ZhipuAI API | 网络 / 配额错误 | 错误信息返回前端 |

## License

MIT
