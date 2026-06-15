<template>
  <div class="analysis-view">
    <template v-if="loading">
      <div class="kpi-row">
        <div v-for="i in 5" :key="'kpisk-'+i" class="skeleton-block kpi-sk"></div>
      </div>
      <div class="charts-grid">
        <div v-for="i in 4" :key="'chsk-'+i" class="skeleton-block chart-sk"></div>
      </div>
    </template>

    <template v-else>
      <header class="page-hero">
        <h1 class="page-title">
          <span class="title-accent">◈</span> 数据分析大屏
        </h1>
        <p class="page-desc">
          共 {{ kpi.totalMovies?.toLocaleString() }} 部影片 · 年份跨度 {{ kpi.yearSpan }} 年 · 多维度可视化
        </p>
      </header>

      <StatsOverview :cards="kpiCards" />

      <section class="charts-section">
        <h2 class="section-title"><span class="title-dot"></span>图表分析</h2>
        <div class="charts-grid">
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">📊 评分分布</span>
              <span class="chart-hint">直方图</span>
            </div>
            <div ref="chartRatingDist" class="chart-body"></div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">📈 电影产量趋势</span>
              <span class="chart-hint">按年份</span>
            </div>
            <div ref="chartYearlyCount" class="chart-body"></div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">📉 平均评分变化</span>
              <span class="chart-hint">按年份</span>
            </div>
            <div ref="chartAvgRating" class="chart-body"></div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">🔥 热门类型 Top 10</span>
              <span class="chart-hint">条形图</span>
            </div>
            <div ref="chartGenres" class="chart-body"></div>
          </div>
        </div>
      </section>

      <MovieTable
        v-model:search="tableSearch"
        v-model:page="tablePage"
        :filtered-data="filteredTableData"
        :paged-data="pagedTableData"
        :page-size="tablePageSize"
        :sort-col="sortCol"
        :sort-dir="sortDir"
        @sort="sortTable"
        @select="goDetail"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from "vue";
import { useRouter } from "vue-router";
import { getMovieListRich } from "@/api/index.js";
import StatsOverview from "@/components/analysis/StatsOverview.vue";
import MovieTable from "@/components/analysis/MovieTable.vue";
import { useCharts } from "@/composables/useCharts.js";
import { useTheme } from "@/composables/useTheme.js";

const {
  buildRatingDistChart, buildYearlyCountChart,
  buildAvgRatingChart, buildGenresChart,
  destroyCharts, resizeCharts, parseGenres,
} = useCharts();

const { isDark } = useTheme();

const loading = ref(true);
const allMovies = ref([]);
const router = useRouter();

const chartRatingDist = ref(null);
const chartYearlyCount = ref(null);
const chartAvgRating = ref(null);
const chartGenres = ref(null);

const tableSearch = ref("");
const tablePage = ref(1);
const tablePageSize = 15;
const sortCol = ref("rating");
const sortDir = ref("desc");

// KPI
const kpi = computed(() => {
  const list = allMovies.value;
  if (!list.length) return {};

  const ratings = list.map((m) => m.rating).filter((r) => r > 0);
  const years = list.map((m) => m.year).filter((y) => y != null && y > 1900);
  const runtimes = list
    .map((m) => {
      const r = m.runtime;
      if (!r) return 0;
      const num = parseInt(String(r).replace(/[^0-9]/g, ""));
      return isNaN(num) ? 0 : num;
    })
    .filter((n) => n > 0 && n < 600);
  const topMovie = [...list].sort((a, b) => b.rating - a.rating)[0];

  return {
    totalMovies: list.length,
    avgRating: ratings.length ? (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1) : "-",
    avgRuntime: runtimes.length ? Math.round(runtimes.reduce((a, b) => a + b, 0) / runtimes.length) + " min" : "-",
    yearSpan: years.length ? Math.max(...years) - Math.min(...years) : "-",
    topMovie: topMovie ? { title: topMovie.title, rating: topMovie.rating?.toFixed(1) } : null,
  };
});

const kpiCards = computed(() => [
  { icon: "🎬", value: (kpi.value.totalMovies || 0).toLocaleString(), label: "电影总数" },
  { icon: "⭐", value: kpi.value.avgRating, label: "平均评分" },
  { icon: "⏱️", value: kpi.value.avgRuntime, label: "平均时长" },
  { icon: "📅", value: kpi.value.yearSpan + " 年", label: "年份跨度" },
  { icon: "🏆", value: kpi.value.topMovie?.title || "-", label: `最高评分 · ${kpi.value.topMovie?.rating || ""}` },
]);

// Table
const filteredTableData = computed(() => {
  let list = [...allMovies.value];
  const q = tableSearch.value.trim().toLowerCase();
  if (q) list = list.filter((m) => m.title?.toLowerCase().includes(q));
  list.sort((a, b) => {
    let va, vb;
    if (sortCol.value === "rating") { va = a.rating || 0; vb = b.rating || 0; }
    else if (sortCol.value === "year") { va = a.year || 0; vb = b.year || 0; }
    else {
      va = (a.title || "").toLowerCase(); vb = (b.title || "").toLowerCase();
      return sortDir.value === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    }
    return sortDir.value === "asc" ? va - vb : vb - va;
  });
  return list;
});

const pagedTableData = computed(() => {
  const start = (tablePage.value - 1) * tablePageSize;
  return filteredTableData.value.slice(start, start + tablePageSize);
});

function sortTable(col) {
  if (sortCol.value === col) { sortDir.value = sortDir.value === "asc" ? "desc" : "asc"; }
  else { sortCol.value = col; sortDir.value = "desc"; }
  tablePage.value = 1;
}

function goDetail(movieId) {
  router.push(`/movie/${movieId}`);
}

watch(tableSearch, () => { tablePage.value = 1; });

async function fetchData() {
  loading.value = true;
  try {
    const MAX_SIZE = 100;
    const data = await getMovieListRich({ page: 1, pageSize: MAX_SIZE });
    const items = data.items || [];
    const total = data.total || 0;

    if (total > MAX_SIZE) {
      const pages = Math.ceil(total / MAX_SIZE);
      const promises = [];
      for (let p = 2; p <= pages; p++) {
        promises.push(getMovieListRich({ page: p, pageSize: MAX_SIZE }));
      }
      const rest = await Promise.all(promises);
      rest.forEach((r) => items.push(...(r.items || [])));
    }

    if (items.length) allMovies.value = items;
  } catch (e) {
    console.warn("[AnalysisView] API 不可用", e);
    allMovies.value = [];
  }
  loading.value = false;
  await nextTick();
  renderAllCharts();
}

function renderAllCharts() {
  destroyCharts();
  if (allMovies.value.length === 0) return;
  buildRatingDistChart(chartRatingDist, allMovies.value);
  buildYearlyCountChart(chartYearlyCount, allMovies.value);
  buildAvgRatingChart(chartAvgRating, allMovies.value);
  buildGenresChart(chartGenres, allMovies.value);
}

onMounted(async () => {
  await fetchData();
  window.addEventListener("resize", resizeCharts);
});

// 主题切换时重建图表
watch(() => isDark(), () => {
  if (allMovies.value.length > 0) {
    nextTick(() => renderAllCharts());
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  destroyCharts();
});
</script>

<style scoped>
.analysis-view {
  min-height: 100vh;
  background: var(--bg-deep);
  color: var(--text-primary);
  transition: background-color 0.35s ease, color 0.35s ease;
}

.page-hero {
  text-align: center;
  padding: 32px 0 28px;
}
.page-title {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.title-accent { color: var(--gold); margin-right: 6px; }
.page-desc { font-size: 13px; color: var(--text-muted); }

.charts-section { margin-bottom: 40px; }
.section-title {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 20px; font-weight: 700; color: var(--text-primary);
  display: flex; align-items: center; gap: 10px; margin-bottom: 20px;
}
.title-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--gold); display: inline-block;
}
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}
.chart-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg, 16px);
  padding: 20px;
  transition: border-color 0.2s;
}
.chart-card:hover { border-color: var(--gold-glow); }
.chart-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
}
.chart-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.chart-hint {
  font-size: 11px; color: var(--text-muted); background: var(--bg-surface);
  padding: 2px 10px; border-radius: 10px;
}
.chart-body { height: 360px; width: 100%; }

.skeleton-block {
  background: linear-gradient(110deg, var(--bg-elevated) 30%, var(--bg-surface) 50%, var(--bg-elevated) 70%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-lg, 16px);
}
.kpi-sk { height: 88px; }
.chart-sk { height: 400px; }
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (max-width: 1200px) {
  .charts-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .page-title { font-size: 22px; }
  .chart-body { height: 280px; }
}
</style>
