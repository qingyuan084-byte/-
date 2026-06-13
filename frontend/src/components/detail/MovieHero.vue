<template>
  <div class="detail-layout">
    <!-- 左：海报 -->
    <div class="poster-col">
      <img
        v-if="posterSrc"
        :src="posterSrc"
        :alt="movie.title"
        class="detail-poster"
      />
      <div v-else class="detail-poster placeholder">
        <div class="placeholder-inner">
          <span class="ph-icon">🎬</span>
          <span class="ph-text">{{ movie.title }}</span>
        </div>
      </div>
    </div>

    <!-- 右：信息 -->
    <div class="info-col">
      <h1 class="movie-title">{{ movie.title }}</h1>
      <p v-if="movie.title_en" class="title-en">{{ movie.title_en }}</p>

      <div class="rating-row">
        <span v-if="movie.rating > 0" class="rating-big">
          <span class="star">★</span>
          <span class="score">{{ movie.rating }}</span>
          <span class="score-unit">/ 10</span>
        </span>
        <span v-if="movie.total_ratings" class="total-ratings">
          {{ formatNumber(movie.total_ratings) }} 人评价
        </span>
        <button
          class="fav-btn"
          :class="{ active: favorited }"
          :title="favorited ? '取消收藏' : '收藏电影'"
          @click="handleFavorite"
        >
          {{ favorited ? '♥' : '♡' }}
        </button>
      </div>

      <div class="user-rating-row">
        <span class="user-rate-label">我的评分</span>
        <StarRating
          :model-value="userRating"
          show-label
          @rate="handleRate"
        />
        <button
          v-if="userRating > 0"
          class="clear-rate-btn"
          title="清除评分"
          @click="handleClearRating"
        >✕</button>
      </div>

      <div class="meta-grid">
        <div v-if="movie.year" class="meta-item">
          <span class="meta-label">上映年份</span>
          <span class="meta-value">{{ movie.year }}</span>
        </div>
        <div v-if="movie.countries" class="meta-item">
          <span class="meta-label">制片国家</span>
          <span class="meta-value">{{ movie.countries }}</span>
        </div>
        <div v-if="movie.runtime" class="meta-item">
          <span class="meta-label">片长</span>
          <span class="meta-value">{{ movie.runtime }}</span>
        </div>
        <div v-if="movie.release_date" class="meta-item">
          <span class="meta-label">上映日期</span>
          <span class="meta-value">{{ movie.release_date }}</span>
        </div>
      </div>

      <div v-if="genreTags.length > 0" class="genre-row">
        <span
          v-for="g in genreTags"
          :key="g"
          class="genre-tag"
          @click="$emit('goCategory', g)"
        >
          {{ g }}
        </span>
      </div>

      <div v-if="movie.directors" class="info-line">
        <span class="info-label">导演：</span>
        <span>{{ movie.directors }}</span>
      </div>
      <div v-if="movie.actors" class="info-line">
        <span class="info-label">主演：</span>
        <span>{{ movie.actors }}</span>
      </div>

      <div v-if="movie.summary" class="summary-block">
        <h3 class="section-label">剧情简介</h3>
        <p class="summary-text">{{ movie.summary }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "@/composables/useAuth.js";
import StarRating from "@/components/StarRating.vue";

const props = defineProps({
  movie: { type: Object, required: true },
  posterSrc: { type: String, default: "" },
});
defineEmits(["goCategory"]);

const router = useRouter();
const { isAuthenticated, toggleFavorite, isFavorited, setRating, removeRating, getUserRating } = useAuth();

const favorited = computed(() => isFavorited(props.movie.movie_id));
const userRating = ref(0);

watch(() => props.movie.movie_id, (mid) => {
  userRating.value = getUserRating(mid) || 0;
}, { immediate: true });

async function handleFavorite() {
  if (!isAuthenticated.value) {
    router.push("/auth?redirect=" + encodeURIComponent(`/movie/${props.movie.movie_id}`));
    return;
  }
  await toggleFavorite(props.movie.movie_id);
}

async function handleRate(val) {
  if (!isAuthenticated.value) {
    router.push("/auth?redirect=" + encodeURIComponent(`/movie/${props.movie.movie_id}`));
    return;
  }
  await setRating(props.movie.movie_id, val);
  userRating.value = getUserRating(props.movie.movie_id) || 0;
}

async function handleClearRating() {
  await removeRating(props.movie.movie_id);
  userRating.value = 0;
}

function formatNumber(val) {
  if (!val) return "0";
  const n = parseInt(val);
  if (isNaN(n)) return String(val);
  if (n >= 10000) return (n / 10000).toFixed(1) + "万";
  return n.toLocaleString();
}

const genreTags = computed(() => {
  const g = props.movie?.genres;
  if (!g) return [];
  if (Array.isArray(g)) return g.filter(Boolean);
  return String(g).split(/[,，]/).map((x) => x.trim()).filter(Boolean);
});
</script>

<style scoped>
.detail-layout {
  display: flex;
  gap: 40px;
}
.poster-col {
  flex-shrink: 0;
  width: 300px;
}
.detail-poster {
  width: 100%;
  border-radius: 16px;
  display: block;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4);
}
.detail-poster.placeholder {
  background: linear-gradient(145deg, var(--bg-elevated) 0%, var(--bg-surface) 50%, var(--bg-deep) 100%);
  aspect-ratio: 3 / 4;
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-inner { text-align: center; }
.ph-icon { font-size: 56px; display: block; margin-bottom: 12px; }
.ph-text { font-size: 15px; color: rgba(255, 255, 255, 0.7); }
.info-col { flex: 1; min-width: 0; }
.movie-title {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 32px; font-weight: 800; color: var(--text-primary);
  margin-bottom: 6px; line-height: 1.2;
}
.title-en { font-size: 15px; color: var(--text-secondary); margin-bottom: 16px; }
.rating-row { display: flex; align-items: baseline; gap: 16px; margin-bottom: 24px; }
.rating-big { display: flex; align-items: baseline; gap: 6px; }
.rating-big .star { font-size: 22px; color: var(--gold); }
.rating-big .score {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 36px; font-weight: 800; color: var(--gold); line-height: 1;
}
.rating-big .score-unit { font-size: 14px; color: var(--text-secondary); }
.total-ratings { font-size: 13px; color: var(--text-muted); }
.fav-btn {
  margin-left: 12px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid var(--border-subtle);
  background: transparent;
  font-size: 24px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  color: var(--text-muted);
  padding: 0;
  flex-shrink: 0;
}
.fav-btn:hover {
  border-color: var(--gold);
  color: var(--gold);
  transform: scale(1.1);
}
.fav-btn.active {
  border-color: var(--gold);
  background: var(--gold-subtle);
  color: var(--gold);
  box-shadow: 0 0 12px var(--gold-glow);
}
.user-rating-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding: 10px 14px;
  background: var(--bg-elevated);
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
}
.user-rate-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.clear-rate-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
  margin-left: 4px;
}
.clear-rate-btn:hover {
  border-color: #f87171;
  color: #f87171;
}
.meta-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px;
}
.meta-item {
  display: flex; flex-direction: column; gap: 2px; padding: 10px 14px;
  background: var(--bg-elevated); border-radius: 10px; border: 1px solid var(--border-subtle);
}
.meta-label {
  font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em;
}
.meta-value { font-size: 14px; color: var(--text-primary); font-weight: 500; }
.genre-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.genre-tag {
  display: inline-block; padding: 5px 14px; border-radius: 20px;
  background: var(--gold-subtle); border: 1px solid var(--gold-glow);
  color: var(--gold); font-size: 12px; font-weight: 500; cursor: pointer;
  transition: all 0.2s;
}
.genre-tag:hover { border-color: rgba(249, 115, 22, 0.4); }
.info-line { font-size: 14px; color: var(--text-primary); margin-bottom: 8px; line-height: 1.6; }
.info-label { color: var(--text-muted); }
.summary-block { margin-top: 20px; }
.section-label {
  font-size: 13px; font-weight: 600; color: var(--text-secondary);
  margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.04em;
}
.summary-text { font-size: 14px; color: var(--text-primary); line-height: 1.8; }
@media (max-width: 900px) {
  .detail-layout { flex-direction: column; gap: 24px; }
  .poster-col { width: 220px; margin: 0 auto; }
  .movie-title { font-size: 26px; }
}
@media (max-width: 640px) {
  .poster-col { width: 180px; }
  .movie-title { font-size: 22px; }
  .meta-grid { grid-template-columns: 1fr; }
}
</style>
