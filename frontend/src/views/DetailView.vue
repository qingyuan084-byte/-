<template>
  <div class="detail-view">
    <div class="page-container">
      <button class="back-btn" @click="$router.back()">← 返回</button>

      <!-- 骨架屏 -->
      <template v-if="loading">
        <div class="detail-layout">
          <div class="skeleton-block poster-sk"></div>
          <div class="detail-info">
            <div class="skeleton-block title-sk"></div>
            <div class="skeleton-block meta-sk"></div>
            <div class="skeleton-block text-sk"></div>
            <div class="skeleton-block text-sk short"></div>
          </div>
        </div>
      </template>

      <!-- 404 -->
      <div v-else-if="!movie" class="not-found">
        <span class="nf-icon">🔍</span>
        <h2>电影未找到</h2>
        <p>ID: {{ route.params.id }} 不存在</p>
        <router-link to="/" class="nf-link">返回首页</router-link>
      </div>

      <!-- 详情内容 -->
      <template v-else>
        <MovieHero
          :movie="movie"
          :poster-src="posterSrc"
          @go-category="goCategory"
        />

        <SimilarMovies
          :movies="similarMovies"
          :loading="loadingSimilar"
          @select="goDetail"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getMovieDetail, getSimilarMovies } from "@/api/index.js";
import { proxyPoster } from "@/utils/poster.js";
import MovieHero from "@/components/detail/MovieHero.vue";
import SimilarMovies from "@/components/detail/SimilarMovies.vue";

const route = useRoute();
const router = useRouter();

const movie = ref(null);
const similarMovies = ref([]);
const loading = ref(true);
const loadingSimilar = ref(false);

const posterSrc = computed(() => proxyPoster(movie.value?.poster_url || ""));

function goDetail(id) { router.push(`/movie/${id}`); }
function goCategory(genre) { router.push(`/genre/${encodeURIComponent(genre)}`); }

async function fetchMovieDetail(id) {
  loading.value = true;
  movie.value = null;
  try {
    const data = await getMovieDetail(id);
    if (data) {
      movie.value = { ...data, poster_url: data.poster_url || "" };
    }
  } catch (e) {
    console.warn("[DetailView] 电影详情获取失败", e);
    movie.value = null;
  }
  loading.value = false;
}

async function fetchSimilarMovies(id) {
  loadingSimilar.value = true;
  try {
    const data = await getSimilarMovies(id, 10);
    if (data && data.movies) {
      similarMovies.value = data.movies.map((m) => ({
        ...m,
        poster_url: m.poster_url || "",
      }));
    } else {
      similarMovies.value = [];
    }
  } catch (e) {
    console.warn("[DetailView] 相似电影获取失败", e);
    similarMovies.value = [];
  }
  loadingSimilar.value = false;
}

onMounted(() => {
  const id = route.params.id;
  if (id) { fetchMovieDetail(id); fetchSimilarMovies(id); }
});

watch(() => route.params.id, (newId) => {
  if (newId) { fetchMovieDetail(newId); fetchSimilarMovies(newId); }
});
</script>

<style scoped>
.detail-view {
  min-height: 100vh;
  background: var(--bg-deep);
  color: var(--text-primary);
  transition: background-color 0.35s ease, color 0.35s ease;
}
.page-container { max-width: 1200px; margin: 0 auto; padding: 32px 28px; }

.back-btn {
  display: inline-block;
  padding: 8px 18px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: 28px;
  transition: all 0.2s;
  font-family: inherit;
}
.back-btn:hover {
  border-color: var(--gold-glow);
  color: var(--gold);
  background: var(--gold-subtle);
}

/* skeleton */
.detail-layout { display: flex; gap: 40px; }
.detail-info { flex: 1; min-width: 0; }
.skeleton-block {
  background: linear-gradient(110deg, var(--bg-elevated) 30%, var(--bg-surface) 50%, var(--bg-elevated) 70%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 12px;
}
.poster-sk { width: 300px; height: 400px; flex-shrink: 0; }
.title-sk { height: 42px; width: 70%; margin-bottom: 16px; }
.meta-sk { height: 80px; width: 100%; margin-bottom: 16px; }
.text-sk { height: 16px; width: 100%; margin-bottom: 10px; }
.text-sk.short { width: 60%; }
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 404 */
.not-found { text-align: center; padding: 100px 20px; }
.nf-icon { font-size: 64px; display: block; margin-bottom: 16px; }
.not-found h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.not-found p { font-size: 14px; color: var(--text-secondary); margin-bottom: 24px; }
.nf-link {
  display: inline-block; padding: 10px 24px; border-radius: 8px;
  background: var(--gold); color: #fff; text-decoration: none;
  font-weight: 600; font-size: 14px; transition: background 0.2s;
}
.nf-link:hover { background: var(--gold-bright); }

@media (max-width: 640px) {
  .page-container { padding: 20px 16px; }
}
</style>
