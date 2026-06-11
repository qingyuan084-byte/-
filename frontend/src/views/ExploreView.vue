<template>
  <div class="explore-view">
    <div class="page-container">
      <header class="page-header">
        <h1 class="page-title">
          <span class="title-accent">◉</span> 电影分类 / 筛选
        </h1>
        <p class="page-subtitle">
          共 <strong>{{ totalCount }}</strong> 部电影
        </p>
      </header>

      <FilterBar
        v-model:selected-genres="selectedGenres"
        v-model:selected-countries="selectedCountries"
        v-model:year-range="yearRange"
        v-model:rating-range="ratingRange"
        :all-genres="allGenres"
        :genre-counts="genreCounts"
        :all-countries="allCountries"
        :country-counts="countryCounts"
        :year-bounds="yearBounds"
        :is-filtered="isFiltered"
        :active-filter-count="activeFilterCount"
        :disabled="loading"
        @reset="resetFilters"
      />

      <MovieGrid
        :movies="movies"
        :loading="loading"
        :error="error"
        @reset="resetFilters"
      />

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
import { getMovieListRich } from "@/api/index.js";
import FilterBar from "@/components/explore/FilterBar.vue";
import MovieGrid from "@/components/explore/MovieGrid.vue";

const loading = ref(true);
const error = ref("");
const currentPage = ref(1);
const pageSize = 20;
const movies = ref([]);
const totalCount = ref(0);

const selectedGenres = ref([]);
const selectedCountries = ref([]);
const yearRange = ref([1900, 2026]);
const ratingRange = ref([0, 10]);

const allGenres = ref([]);
const genreCounts = ref({});
const allCountries = ref([]);
const countryCounts = ref({});
const yearBounds = ref({ min: 1900, max: 2026 });

const isFiltered = computed(() => {
  return (
    selectedGenres.value.length > 0 ||
    selectedCountries.value.length > 0 ||
    yearRange.value[0] > yearBounds.value.min ||
    yearRange.value[1] < yearBounds.value.max ||
    ratingRange.value[0] > 0 ||
    ratingRange.value[1] < 10
  );
});

const activeFilterCount = computed(() => {
  let n = 0;
  if (selectedGenres.value.length > 0) n += 1;
  if (selectedCountries.value.length > 0) n += 1;
  if (yearRange.value[0] > yearBounds.value.min || yearRange.value[1] < yearBounds.value.max) n += 1;
  if (ratingRange.value[0] > 0 || ratingRange.value[1] < 10) n += 1;
  return n;
});

async function fetchPage() {
  loading.value = true;
  error.value = "";
  try {
    const params = {
      sortBy: "rating",
      page: currentPage.value,
      pageSize: pageSize,
    };
    if (selectedGenres.value.length === 1) params.genre = selectedGenres.value[0];
    if (selectedCountries.value.length === 1) params.country = selectedCountries.value[0];
    if (yearRange.value[0] > yearBounds.value.min) params.yearMin = yearRange.value[0];
    if (yearRange.value[1] < yearBounds.value.max) params.yearMax = yearRange.value[1];
    if (ratingRange.value[0] > 0) params.ratingMin = ratingRange.value[0];
    if (ratingRange.value[1] < 10) params.ratingMax = ratingRange.value[1];

    const data = await getMovieListRich(params);
    movies.value = (data.items || []).map((m) => ({
      ...m,
      poster_url: m.poster_url || "",
      year: m.year || null,
      rating: m.rating || 0,
    }));
    totalCount.value = data.total || 0;
  } catch (e) {
    error.value = "无法加载电影数据";
    console.warn("[ExploreView]", e);
  }
  loading.value = false;
}

watch(
  [selectedGenres, selectedCountries, yearRange, ratingRange],
  () => { currentPage.value = 1; fetchPage(); },
  { deep: true }
);

function resetFilters() {
  selectedGenres.value = [];
  selectedCountries.value = [];
  yearRange.value = [yearBounds.value.min, yearBounds.value.max];
  ratingRange.value = [0, 10];
}

function onPageChange(page) {
  currentPage.value = page;
  window.scrollTo({ top: 200, behavior: "smooth" });
  fetchPage();
}

const COMMON_GENRES = [
  "剧情", "喜剧", "科幻", "动作", "悬疑", "爱情", "恐怖",
  "动画", "犯罪", "战争", "奇幻", "冒险", "纪录片", "历史", "古装", "武侠",
];
const COMMON_COUNTRIES = [
  "中国大陆", "美国", "日本", "韩国", "英国", "法国", "德国",
  "中国香港", "中国台湾", "意大利", "印度", "加拿大", "澳大利亚",
];

onMounted(async () => {
  yearBounds.value = { min: 1900, max: 2026 };
  yearRange.value = [1900, 2026];
  allGenres.value = COMMON_GENRES;
  genreCounts.value = Object.fromEntries(COMMON_GENRES.map((g) => [g, 0]));
  allCountries.value = COMMON_COUNTRIES;
  countryCounts.value = Object.fromEntries(COMMON_COUNTRIES.map((c) => [c, 0]));
  await fetchPage();
});
</script>

<style scoped>
.explore-view {
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
.page-header { margin-bottom: 28px; }
.page-title {
  font-family: var(--font-display);
  font-size: clamp(1.6rem, 4vw, 2rem);
  font-weight: 800;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.title-accent { color: var(--gold); }
.page-subtitle { font-size: 14px; color: var(--text-secondary); }
.page-subtitle strong { color: var(--gold); font-weight: 700; }

.pagination-wrap { display: flex; justify-content: center; margin-top: 40px; }

/* Element Plus 深色覆盖 */
:deep(.el-select) {
  --el-fill-color-blank: var(--bg-surface);
  --el-border-color: var(--border-subtle);
  --el-text-color-regular: var(--text-primary);
  --el-text-color-placeholder: var(--text-muted);
}
:deep(.el-select .el-input__wrapper) {
  background: var(--bg-surface); border-color: var(--border-subtle); box-shadow: none;
}
:deep(.el-select .el-input__wrapper:hover) { border-color: var(--gold-dim); }
:deep(.el-select.is-focus .el-input__wrapper) {
  border-color: var(--gold); box-shadow: 0 0 0 1px var(--gold) inset;
}
:deep(.el-select-dropdown) { background: var(--bg-elevated); border: 1px solid var(--border-subtle); }
:deep(.el-select-dropdown__item) { color: var(--text-primary); }
:deep(.el-select-dropdown__item:hover) { background: var(--gold-subtle); }
:deep(.el-select-dropdown__item.selected) { color: var(--gold); font-weight: 600; }
:deep(.el-select .el-tag) {
  background: var(--gold-subtle); border-color: var(--gold-dim); color: var(--gold);
}
:deep(.el-slider) {
  --el-slider-main-bg-color: var(--gold);
  --el-slider-runway-bg-color: var(--bg-surface);
  --el-slider-stop-bg-color: var(--text-muted);
}
:deep(.el-slider__bar) { background: var(--gold); }
:deep(.el-slider__button) {
  border-color: var(--gold); background: var(--bg-elevated); width: 14px; height: 14px;
}
:deep(.el-button) {
  --el-button-bg-color: var(--bg-surface);
  --el-button-border-color: var(--border-subtle);
  --el-button-text-color: var(--text-secondary);
  --el-button-hover-text-color: var(--text-primary);
  --el-button-hover-border-color: var(--text-muted);
}
:deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: var(--text-secondary);
  --el-pagination-button-bg-color: var(--bg-surface);
  --el-pagination-button-color: var(--text-secondary);
  --el-pagination-hover-color: var(--gold);
}
:deep(.el-pagination .el-pager li) { background: var(--bg-surface); color: var(--text-secondary); }
:deep(.el-pagination .el-pager li:hover) { color: var(--gold); }
:deep(.el-pagination .el-pager li.is-active) { background: var(--gold); color: #1a1a2e; }

@media (max-width: 640px) {
  .page-container { padding: 24px 16px; }
}
</style>
