<template>
  <div class="ranking-view">
    <div class="page-container">
      <!-- 页面标题 -->
      <header class="page-header">
        <h1 class="page-title">
          <span class="title-icon">🏆</span>
          电影排行榜
        </h1>
        <p class="page-subtitle">共 {{ totalCount }} 部电影</p>
      </header>

      <!-- 排序标签 -->
      <div class="sort-tabs">
        <button
          v-for="tab in sortTabs"
          :key="tab.key"
          class="sort-tab"
          :class="{ active: sortBy === tab.key }"
          @click="switchSort(tab.key)"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>
      </div>

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
        <span class="empty-icon">📭</span>
        <p>暂无电影数据</p>
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
import { useRouter } from "vue-router";
import { getMovieListRich } from "@/api/index.js";
import MovieCard from "@/components/MovieCard.vue";

const router = useRouter();

// ── 排序 ──────────────────────────────────────────────
const SORT_KEY_MAP = { rating: "rating", year: "year", total_ratings: "total_ratings" };
const sortTabs = [
  { key: "rating", label: "按评分排序", icon: "⭐" },
  { key: "year", label: "按年份排序", icon: "📅" },
  { key: "total_ratings", label: "按评价人数", icon: "👥" },
];
const sortBy = ref("rating");
const currentPage = ref(1);
const pageSize = 20;
const loading = ref(true);
const error = ref("");

const movies = ref([]);
const totalCount = ref(0);

// ── 数据获取 ──────────────────────────────────────────
async function fetchPage() {
  loading.value = true;
  error.value = "";
  try {
    const data = await getMovieListRich({
      sortBy: sortBy.value,
      page: currentPage.value,
      pageSize: pageSize,
    });
    movies.value = (data.items || []).map((m) => ({
      ...m,
      poster_url: m.poster_url || "",
    }));
    totalCount.value = data.total || 0;
  } catch (e) {
    error.value = "无法加载排行榜数据";
    console.warn("[RankingView]", e);
  }
  loading.value = false;
}

function switchSort(key) {
  if (sortBy.value === key) return;
  sortBy.value = key;
  currentPage.value = 1;
  fetchPage();
}

function onPageChange(page) {
  currentPage.value = page;
  window.scrollTo({ top: 200, behavior: "smooth" });
  fetchPage();
}

function goDetail(id) {
  router.push(`/movie/${id}`);
}

// 监听排序和页数变化
watch([sortBy, currentPage], () => {
  // 已在 switchSort/onPageChange 中触发 fetchPage
});

onMounted(() => {
  fetchPage();
});
</script>

<style scoped>
.ranking-view {
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
  text-align: center;
  margin-bottom: 36px;
}
.page-title {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 32px;
  font-weight: 800;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}
.title-icon {
  font-size: 36px;
}
.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 排序标签 */
.sort-tabs {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 36px;
  flex-wrap: wrap;
}
.sort-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
}
.sort-tab:hover {
  border-color: var(--gold-glow);
  color: var(--text-primary);
  background: var(--bg-surface);
}
.sort-tab.active {
  border-color: var(--gold);
  background: var(--gold-subtle);
  color: var(--gold);
  font-weight: 600;
}
.tab-icon {
  font-size: 15px;
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
  grid-column: 1 / -1;
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
  .sort-tab { padding: 8px 14px; font-size: 12px; }
}
</style>
