<template>
  <div class="category-view">
    <div class="page-container">
      <!-- 页面标题 -->
      <header class="page-header">
        <router-link to="/" class="back-link">← 返回首页</router-link>
        <h1 class="page-title">
          <span class="title-accent">{{ genreName }}</span>
          电影
        </h1>
        <p class="page-subtitle">共 {{ totalCount }} 部</p>
      </header>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-grid">
        <div v-for="i in 8" :key="'sk-'+i" class="skeleton-block card-sk"></div>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="empty-state">
        <span class="empty-icon">⚠️</span>
        <p>{{ error }}</p>
      </div>

      <!-- 电影网格 -->
      <div v-else-if="movies.length > 0" class="movie-grid">
        <MovieCard
          v-for="m in movies"
          :key="m.movie_id"
          :movie="m"
          class="grid-card"
          @click="goDetail(m.movie_id)"
        />
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <span class="empty-icon">🎬</span>
        <p>该分类暂无电影数据</p>
        <router-link to="/" class="empty-link">浏览全部电影</router-link>
      </div>

      <!-- 分页 -->
      <div v-if="totalCount > pageSize" class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalCount"
          layout="prev, pager, next, total"
          background
          @current-change="onPageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getMovieListRich } from "@/api/index.js";
import MovieCard from "@/components/MovieCard.vue";

const route = useRoute();
const router = useRouter();

// ── 状态 ──────────────────────────────────────────────
const genreName = computed(() => {
  try {
    return decodeURIComponent(route.params.genre || "");
  } catch {
    return route.params.genre || "";
  }
});

const loading = ref(true);
const error = ref("");
const currentPage = ref(1);
const pageSize = 20;
const movies = ref([]);
const totalCount = ref(0);

// ── 数据获取 ──────────────────────────────────────────
async function fetchPage() {
  loading.value = true;
  error.value = "";
  try {
    const data = await getMovieListRich({
      genre: genreName.value,
      sortBy: "rating",
      page: currentPage.value,
      pageSize: pageSize,
    });
    movies.value = (data.items || []).map((m) => ({
      ...m,
      poster_url: m.poster_url || "",
    }));
    totalCount.value = data.total || 0;
  } catch (e) {
    error.value = "无法加载分类数据";
    console.warn("[CategoryView]", e);
  }
  loading.value = false;
}

function onPageChange(page) {
  currentPage.value = page;
  window.scrollTo({ top: 200, behavior: "smooth" });
  fetchPage();
}

function goDetail(id) {
  router.push(`/movie/${id}`);
}

// 路由参数变化时重置并重新加载
watch(() => route.params.genre, () => {
  currentPage.value = 1;
  fetchPage();
});

onMounted(() => {
  fetchPage();
});
</script>

<style scoped>
.category-view {
  min-height: 100vh;
  background: var(--bg-deep);
  color: var(--text-primary);
  transition: background-color 0.35s ease, color 0.35s ease;
}

.page-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 28px;
}

/* 页面标题 */
.page-header {
  margin-bottom: 36px;
}
.back-link {
  display: inline-block;
  font-size: 13px;
  color: var(--text-secondary);
  text-decoration: none;
  margin-bottom: 12px;
  transition: color 0.2s;
}
.back-link:hover {
  color: var(--gold);
}
.page-title {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 32px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.title-accent {
  color: var(--gold);
}
.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 网格 */
.movie-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
}

/* 分页 */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 40px;
}

/* 加载 & 空状态 */
.loading-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
}
.skeleton-block {
  background: linear-gradient(110deg, var(--bg-elevated) 30%, var(--bg-surface) 50%, var(--bg-elevated) 70%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 12px;
}
.card-sk {
  aspect-ratio: 3 / 4;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 56px;
  display: block;
  margin-bottom: 16px;
}
.empty-state p {
  font-size: 16px;
  margin-bottom: 16px;
}
.empty-link {
  color: var(--gold);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}
.empty-link:hover {
  text-decoration: underline;
}

/* 响应式 */
@media (max-width: 1200px) {
  .movie-grid, .loading-grid { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 900px) {
  .movie-grid, .loading-grid { grid-template-columns: repeat(3, 1fr); }
  .page-title { font-size: 26px; }
}
@media (max-width: 640px) {
  .movie-grid, .loading-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .page-container { padding: 24px 16px; }
  .page-title { font-size: 22px; }
}
</style>
