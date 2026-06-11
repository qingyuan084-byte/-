<template>
  <div class="home-view">
    <HeroSearch
      v-model="searchText"
      @search="onSearch"
      @scroll-to-top="scrollToTop"
    />

    <div class="home-body">
      <main class="main-content">
        <BannerCarousel
          :movies="bannerMovies"
          :loading="loading.banner"
          :visible="!isSearching && !activeTag"
          @select="onBannerClick"
        />

        <!-- 搜索结果 / 标签筛选结果 -->
        <section v-if="isSearching || activeTag" class="movie-section">
          <div class="section-header">
            <h2 class="section-title">
              <span class="title-dot"></span>
              {{ isSearching ? `搜索结果: "${searchQuery}"` : `标签: ${activeTagLabel}` }}
              <span class="section-badge">{{ filteredMovies.length }} 部</span>
            </h2>
            <a href="#" class="section-more clear-link" @click.prevent="clearFilter">
              ✕ 清除{{ isSearching ? '搜索' : '筛选' }}
            </a>
          </div>
          <div class="movie-grid" v-loading="searchLoading">
            <template v-if="filteredMovies.length > 0">
              <MovieCard v-for="m in filteredMovies" :key="m.movie_id" :movie="m" class="grid-card" />
            </template>
            <div v-else class="empty-state">
              <span class="empty-icon">🔍</span>
              <p>没有找到匹配的电影，试试其他关键词</p>
            </div>
          </div>
        </section>

        <!-- 正常分区 -->
        <template v-if="!isSearching && !activeTag">
          <MovieSection
            label="热门推荐"
            :movies="displayHotMovies"
            :loading="loading.hot"
            :expanded="expandedSection === 'hot'"
            @toggle-expand="expandSection('hot')"
          />
          <MovieSection
            label="最新上映"
            :movies="displayNewestMovies"
            :loading="loading.newest"
            :expanded="expandedSection === 'newest'"
            @toggle-expand="expandSection('newest')"
          />
          <MovieSection
            label="高分榜单"
            :movies="displayTopMovies"
            :loading="loading.top"
            :expanded="expandedSection === 'top'"
            badge="≥ 8.5"
            @toggle-expand="expandSection('top')"
          />

          <div ref="categoriesSection">
            <MovieSection
              v-for="cat in categories"
              :key="cat.key"
              :ref="el => setCatRef(cat.key, el)"
              :label="cat.label"
              :movies="getDisplayCatMovies(cat)"
              :loading="loading.categories"
              :expanded="expandedSection === cat.key"
              :dot-class="cat.key"
              :more-link="`/genre/${encodeURIComponent(cat.genreName)}`"
              :skeleton-count="6"
              @toggle-expand="expandSection(cat.key)"
            />
          </div>
        </template>
      </main>

      <SidebarRanking
        :top-rank-movies="topRankMovies"
        :hot-tags="hotTags"
        :active-tag="activeTag"
        :loading="loading.sidebar"
        @select-movie="onRankClick"
        @tag-click="onTagClick"
        @clear-filter="clearFilter"
      />
    </div>

    <HomeFooter @scroll-to-top="scrollToTop" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import MovieCard from "@/components/MovieCard.vue";
import HeroSearch from "@/components/home/HeroSearch.vue";
import BannerCarousel from "@/components/home/BannerCarousel.vue";
import MovieSection from "@/components/home/MovieSection.vue";
import SidebarRanking from "@/components/home/SidebarRanking.vue";
import HomeFooter from "@/components/home/HomeFooter.vue";
import { useMovies, formatGenres } from "@/composables/useMovies.js";
import { useSearch } from "@/composables/useSearch.js";

const router = useRouter();

const categoriesSection = ref(null);
const catRefs = {};
function setCatRef(key, el) {
  if (el) catRefs[key] = el;
}

const {
  allMovies, loading, baseMovies,
  bannerMovies, hotMoviesAll, newestMoviesAll, topMoviesAll,
  getCatMoviesAll, topRankMovies, hotTags,
  fetchMovies, fetchBannerMovies, fetchNewestMovies, markLoaded, categoryKeywords,
} = useMovies();

const {
  searchText, searchQuery, isSearching, searchResults,
  activeTag, activeTagLabel, expandedSection, searchLoading,
  filteredMovies, onSearch, clearFilter, expandSection,
} = useSearch(baseMovies);

const categories = ref([
  { key: "suspense", label: "悬疑烧脑", genreName: "悬疑", movies: [] },
  { key: "comedy", label: "轻松喜剧", genreName: "喜剧", movies: [] },
  { key: "scifi", label: "科幻世界", genreName: "科幻", movies: [] },
  { key: "action", label: "动作大片", genreName: "动作", movies: [] },
]);

const displayHotMovies = computed(() =>
  expandedSection.value === "hot" ? hotMoviesAll.value : hotMoviesAll.value.slice(0, 10)
);
const displayNewestMovies = computed(() =>
  expandedSection.value === "newest" ? newestMoviesAll.value : newestMoviesAll.value.slice(0, 10)
);
const displayTopMovies = computed(() =>
  expandedSection.value === "top" ? topMoviesAll.value : topMoviesAll.value.slice(0, 10)
);

function getDisplayCatMovies(cat) {
  const all = getCatMoviesAll(cat.key);
  return expandedSection.value === cat.key ? all : all.slice(0, 10);
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function onBannerClick(m) {
  router.push(`/movie/${m.movie_id}`);
}
function onRankClick(m) {
  router.push(`/movie/${m.movie_id}`);
}
function onTagClick(tag) {
  router.push(`/genre/${encodeURIComponent(tag)}`);
}

function updateCategoryMovies() {
  categories.value.forEach((cat) => {
    cat.movies = getCatMoviesAll(cat.key).slice(0, 6);
  });
}

onMounted(async () => {
  await Promise.all([fetchMovies(), fetchBannerMovies(), fetchNewestMovies()]);
  updateCategoryMovies();
  markLoaded();
});
</script>

<style scoped>
.home-view {
  --home-bg: var(--bg-deep);
  --home-card: var(--bg-elevated);
  --home-card-hover: var(--bg-surface);
  --home-surface: var(--bg-surface);
  --home-border: var(--border-subtle);
  --home-text: var(--text-primary);
  --home-text-secondary: var(--text-secondary);
  --home-text-muted: var(--text-muted);
  --home-accent: var(--gold);
  --home-accent-bright: var(--gold-bright);
  --home-accent-dim: var(--gold-dim);
  --home-accent-glow: var(--gold-glow);
  --home-accent-subtle: var(--gold-subtle);

  font-family: var(--font-body);
  background: var(--home-bg);
  color: var(--home-text);
  min-height: 100vh;
  transition: background-color 0.35s ease, color 0.35s ease;
}

.home-body {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  gap: 32px;
  padding: 32px 28px;
}
.main-content {
  flex: 1;
  min-width: 0;
}

.movie-section {
  margin-bottom: 40px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.section-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}
.title-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--gold);
  display: inline-block;
}
.section-badge {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  background: var(--gold-subtle);
  color: var(--gold);
  padding: 3px 10px;
  border-radius: 20px;
}
.section-more {
  font-size: 13px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.2s;
  cursor: pointer;
}
.section-more:hover {
  color: var(--gold);
}
.clear-link {
  color: var(--gold);
}
.clear-link:hover {
  color: var(--gold-bright);
}
.movie-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}
.empty-state p {
  font-size: 14px;
}

@media (max-width: 1200px) {
  .movie-grid { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 1024px) {
  .home-body { flex-direction: column; }
}
@media (max-width: 768px) {
  .home-body { padding: 20px 16px; }
  .movie-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
}
</style>
