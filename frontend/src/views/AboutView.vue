<template>
  <div class="about-view">
    <!-- 页头 -->
    <section class="page-hero">
      <h1 class="page-title">
        <span class="title-accent">○</span>
        关于随便乱推
      </h1>
      <p class="page-desc">基于豆瓣电影数据的智能推荐平台，融合传统推荐算法与大语言模型</p>
    </section>

    <!-- 项目简介 -->
    <div class="about-grid">
      <div class="about-card glass intro-card">
        <div class="card-icon-wrap">
          <span class="card-icon">◆</span>
        </div>
        <h2>随便乱推 是什么？</h2>
        <p>
          <strong>"随便乱推"</strong>（CinéMatic）是一套完整的<strong>智能电影推荐系统</strong>。
          名字看似随意，实则暗藏巧思 —— 灵感来源于法语 <strong>Ciné</strong>（电影）+ <strong>Automatic</strong>（自动），
          取"不知道看什么的时候，让系统帮你随便一推"之意。
        </p>
        <p>
          项目爬取了<strong>豆瓣电影</strong>上超过 2,100 部高质量影片数据，涵盖从 1930 年代经典到 2026 年最新上映的各类电影。
          系统采用<strong>内容推荐 + 向量语义检索 + AI 智能问答</strong>三大技术路线，
          即使你完全不知道想看什么，也能通过自然语言描述需求、按类型/年代/评分筛选、
          或用一部喜欢的电影找到风格相似的其他作品。
        </p>
        <p>
          内置的 AI 助手<strong>"登小千"</strong>由智谱 GLM 大模型驱动，能理解复杂的推荐需求
          （"推荐几部适合下雨天窝在沙发看的温情电影"），
          回答电影相关问题（"《星际穿越》的导演是谁？"），甚至和你闲聊电影八卦。
        </p>
      </div>

      <!-- 适用场景 -->
      <div class="about-card glass">
        <div class="card-icon-wrap">
          <span class="card-icon">🎯</span>
        </div>
        <h2>适合谁用？</h2>
        <div class="scenarios-list">
          <div class="scenario-item">
            <span class="scenario-icon">🎬</span>
            <div>
              <strong>选择困难症患者</strong>
              <p>打开 Netflix/爱奇艺翻了半小时还是不知道看什么？让随便乱推帮你三秒出结果。</p>
            </div>
          </div>
          <div class="scenario-item">
            <span class="scenario-icon">📚</span>
            <div>
              <strong>电影爱好者</strong>
              <p>通过数据分析页了解电影工业全貌，按评分/年代/类型/国家多维度探索电影世界。</p>
            </div>
          </div>
          <div class="scenario-item">
            <span class="scenario-icon">💻</span>
            <div>
              <strong>开发者 / 学习者</strong>
              <p>完整的全栈项目模板：FastAPI + Vue 3 + FAISS 向量检索 + LLM 集成 + Docker 部署。</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 数据来源 -->
      <div class="about-card glass">
        <div class="card-icon-wrap">
          <span class="card-icon">📊</span>
        </div>
        <h2>数据来源与规模</h2>
        <p>电影数据通过 <strong>豆瓣 JSON API</strong> 爬取，辅以智谱 AI 补充缺失摘要信息，覆盖范围广、信息完整度高。</p>
        <div class="data-stats">
          <div class="data-stat">
            <span class="data-num">2,125</span>
            <span class="data-label">部电影</span>
          </div>
          <div class="data-stat">
            <span class="data-num">1930–2026</span>
            <span class="data-label">年份跨度</span>
          </div>
          <div class="data-stat">
            <span class="data-num">28</span>
            <span class="data-label">种类型标签</span>
          </div>
          <div class="data-stat">
            <span class="data-num">7.46</span>
            <span class="data-label">平均豆瓣评分</span>
          </div>
        </div>
        <p class="data-note">每部电影包含：标题、评分、评价人数、导演、演员、编剧、上映日期、类型、制片国家、语言、片长、剧情简介、海报等完整字段。</p>
      </div>

      <!-- 技术栈 -->
      <div class="about-card glass">
        <div class="card-icon-wrap">
          <span class="card-icon">⚙️</span>
        </div>
        <h2>技术架构</h2>
        <div class="tech-tags">
          <span v-for="cat in techCategories" :key="cat.name" class="tech-category">
            <span class="tech-cat-label">{{ cat.name }}</span>
            <span class="tech-items">
              <span v-for="t in cat.items" :key="t" class="tech-tag">{{ t }}</span>
            </span>
          </span>
        </div>
      </div>

      <!-- 功能特性 -->
      <div class="about-card glass">
        <div class="card-icon-wrap">
          <span class="card-icon">✦</span>
        </div>
        <h2>核心功能</h2>
        <div class="features-list">
          <div v-for="f in features" :key="f.title" class="feature-item">
            <span class="feature-icon">{{ f.icon }}</span>
            <div>
              <strong>{{ f.title }}</strong>
              <p>{{ f.desc }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 部署方式 -->
      <div class="about-card glass">
        <div class="card-icon-wrap">
          <span class="card-icon">☁️</span>
        </div>
        <h2>部署与运行</h2>
        <p>
          系统支持<strong>灵活降级策略</strong>：PostgreSQL 不可用时自动切换到 CSV 文件读取，
          Redis 不可用时跳过缓存直接查询，FAISS 向量索引缺失时降级为 NumPy 暴力计算。
          这意味着你可以在任何环境下快速启动，无需复杂配置。
        </p>
        <div class="deploy-modes">
          <div class="deploy-mode">
            <span class="mode-badge">本地开发</span>
            <p>Python 后端 + Vite 前端，开箱即用</p>
          </div>
          <div class="deploy-mode">
            <span class="mode-badge">Docker 部署</span>
            <p>docker-compose 一键编排 4 个服务（Nginx + FastAPI + PostgreSQL + Redis）</p>
          </div>
          <div class="deploy-mode">
            <span class="mode-badge">局域网共享</span>
            <p>前端绑定 0.0.0.0，同一网络下手机可直接访问</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const techCategories = [
  {
    name: "后端",
    items: ["Python 3.12", "FastAPI", "Uvicorn", "SQLAlchemy"],
  },
  {
    name: "LLM & AI",
    items: ["智谱AI GLM-4-Flash", "embedding-2 (1024维)", "Function Calling", "RAG 检索增强"],
  },
  {
    name: "推荐算法",
    items: ["TF-IDF", "余弦相似度", "FAISS IndexFlatIP", "MultiLabelBinarizer"],
  },
  {
    name: "前端",
    items: ["Vue 3", "Vite", "Element Plus", "ECharts", "axios"],
  },
  {
    name: "数据库/缓存",
    items: ["PostgreSQL 16", "Redis 7", "SQLite", "自动降级策略"],
  },
  {
    name: "部署",
    items: ["Docker", "docker-compose", "Nginx SPA", "多阶段构建"],
  },
  {
    name: "数据处理",
    items: ["pandas", "scikit-learn", "scipy", "jieba 分词"],
  },
  {
    name: "可视化",
    items: ["matplotlib", "seaborn", "plotly", "wordcloud"],
  },
];

const features = [
  {
    icon: "🔍",
    title: "混合推荐引擎",
    desc: "融合 TF-IDF 文本特征 + 多热编码类型标签的余弦相似度推荐。输入一部电影，找到最相似的 N 部作品；输入一段描述，精准匹配符合需求的影片。",
  },
  {
    icon: "🧠",
    title: "AI 智能问答（登小千）",
    desc: "由智谱 GLM-4-Flash 驱动，支持自然语言推荐（\"推荐几部反转结局的悬疑片\"）、电影信息查询（导演/演员/评分）、Function Calling 筛选对话、29 条随机快捷提问池。",
  },
  {
    icon: "⚡",
    title: "语义向量检索",
    desc: "智谱 embedding-2 模型生成 1024 维语义向量，FAISS IndexFlatIP 加速内积检索。RAG 检索增强问答，让 AI 回答基于真实数据库而非幻觉。FAISS 不可用时自动降级 NumPy。",
  },
  {
    icon: "🔐",
    title: "用户系统",
    desc: "完整的注册/登录体系（PBKDF2 密码哈希 + Session Token），支持电影收藏（★星标）、个人主页展示收藏列表，SQLite 持久化存储用户数据。",
  },
  {
    icon: "📈",
    title: "数据分析看板",
    desc: "总览统计、评分分布柱状图、类型饼图、年代趋势折线图、词云、TOP 电影排名表格，多维度可视化电影数据全貌。",
  },
  {
    icon: "🎨",
    title: "深色/浅色主题",
    desc: "支持深色/浅色双主题一键切换，所有页面均适配主题变量，提供一致的视觉体验。",
  },
  {
    icon: "🖼️",
    title: "海报图片代理",
    desc: "内置豆瓣海报代理服务，绕过防盗链限制，自动缓存到本地加速二次加载，预置暖脚本批量下载。",
  },
  {
    icon: "📱",
    title: "响应式布局",
    desc: "全站适配桌面端、平板、手机三种屏幕尺寸，导航栏移动端自动切换为图标模式。",
  },
];
</script>

<style scoped>
.about-view {
  max-width: 960px;
  margin: 0 auto;
}

/* ── 页头 ──────────────────────────────────────── */
.page-hero {
  text-align: center;
  padding: 24px 0 36px;
}
.page-title {
  font-family: var(--font-display);
  font-size: clamp(1.8rem, 5vw, 2.4rem);
  font-weight: 900;
  color: var(--text-primary);
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}
.title-accent {
  color: var(--gold);
}
.page-desc {
  color: var(--text-secondary);
  font-size: 15px;
}

/* ── 卡片网格 ──────────────────────────────────── */
.about-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.about-card {
  border-radius: var(--radius-lg);
  padding: 28px;
  border: 1px solid var(--border-subtle);
}

.intro-card {
  grid-column: 1 / -1;
}

.card-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--gold-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.card-icon {
  font-size: 20px;
}

.about-card h2 {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  letter-spacing: 0.02em;
}

.about-card p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.75;
  margin-bottom: 14px;
}

.about-card p:last-child {
  margin-bottom: 0;
}

.about-card strong {
  color: var(--gold);
  font-weight: 600;
}

/* 项目简介 */
.about-card ul {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.about-card li {
  font-size: 14px;
  color: var(--text-secondary);
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.5;
}
.list-marker {
  color: var(--gold);
  flex-shrink: 0;
  margin-top: 2px;
}

/* 适用场景 */
.scenarios-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.scenario-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.scenario-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 1px;
}
.scenario-item strong {
  display: block;
  font-size: 14px;
  margin-bottom: 3px;
}
.scenario-item p {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 0;
  line-height: 1.55;
}

/* 技术栈 */
.tech-tags {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.tech-category {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.tech-cat-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  flex-shrink: 0;
  width: 72px;
  padding-top: 3px;
}
.tech-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.tech-tag {
  padding: 3px 10px;
  border-radius: 6px;
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  border: 1px solid var(--border-default);
}

/* 数据统计 */
.data-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
}
.data-stat {
  text-align: center;
  padding: 14px 8px;
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}
.data-num {
  display: block;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 0.02em;
}
.data-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}
.data-note {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.6;
}

/* 功能特性 */
.features-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.feature-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.feature-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 1px;
}
.feature-item strong {
  display: block;
  font-size: 14px;
  margin-bottom: 2px;
}
.feature-item p {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 0;
  line-height: 1.5;
}

/* 部署方式 */
.deploy-modes {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}
.deploy-mode {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.mode-badge {
  flex-shrink: 0;
  padding: 3px 10px;
  border-radius: 6px;
  background: var(--gold-subtle);
  color: var(--gold);
  font-size: 12px;
  font-weight: 600;
}
.deploy-mode p {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 0;
  line-height: 1.5;
}

/* ── 响应式 ────────────────────────────────────── */
@media (max-width: 768px) {
  .about-grid {
    grid-template-columns: 1fr;
  }
  .about-card {
    padding: 20px;
  }
}
</style>
