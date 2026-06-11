<template>
  <section class="banner-section" v-loading="loading" v-show="visible">
    <el-carousel
      v-if="movies.length > 0"
      :interval="5000"
      arrow="hover"
      indicator-position="none"
      height="420px"
      class="banner-carousel"
    >
      <el-carousel-item v-for="(m, i) in movies" :key="m.movie_id">
        <div class="banner-slide" @click="$emit('select', m)">
          <div class="banner-poster">
            <img
              :src="proxyPoster(m.poster_url) || placeholderPoster"
              :alt="m.title"
              class="banner-img"
              :fetchpriority="i < 2 ? 'high' : 'low'"
              decoding="async"
              @error="onImgError($event)"
            />
          </div>
          <div class="banner-info">
            <h2 class="banner-title">{{ m.title }}</h2>
            <div class="banner-meta">
              <span class="banner-rating">★ {{ m.rating }}</span>
              <span v-if="m.year" class="banner-year">{{ m.year }}</span>
              <span class="banner-genres">{{ formatGenres(m.genres) }}</span>
            </div>
            <p class="banner-summary">{{ m.summary || '暂无简介' }}</p>
            <span class="banner-hint">点击查看详情 →</span>
          </div>
        </div>
      </el-carousel-item>
    </el-carousel>
    <div v-else class="banner-skeleton">
      <div class="skeleton-block banner-sk"></div>
    </div>
  </section>
</template>

<script setup>
import { proxyPoster, placeholderPoster } from "@/utils/poster.js";
import { formatGenres } from "@/composables/useMovies.js";

defineProps({
  movies: { type: Array, default: () => [] },
  loading: { type: Boolean, default: true },
  visible: { type: Boolean, default: true },
});
defineEmits(["select"]);

const placeholderImg = placeholderPoster;

function onImgError(e) {
  e.target.src = placeholderImg;
}
</script>

<style scoped>
.banner-section {
  margin-bottom: 40px;
  border-radius: 16px;
  overflow: hidden;
  background: var(--bg-elevated);
}
.banner-carousel {
  border-radius: 16px;
}
.banner-slide {
  height: 420px;
  display: flex;
  align-items: stretch;
  border-radius: 16px;
  cursor: pointer;
  overflow: hidden;
}
.banner-poster {
  flex: 0 0 280px;
  background: var(--bg-deep);
  display: flex;
  align-items: center;
  justify-content: center;
}
.banner-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
.banner-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px 48px;
  background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-surface) 50%, var(--bg-elevated) 100%);
  min-width: 0;
}
.banner-title {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 12px;
  text-shadow: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.banner-meta {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 16px;
  font-size: 14px;
}
.banner-rating {
  color: var(--gold);
  font-weight: 700;
}
.banner-year {
  color: var(--text-secondary);
}
.banner-genres {
  color: var(--text-muted);
  font-size: 13px;
}
.banner-summary {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0 0 16px;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.banner-hint {
  font-size: 13px;
  color: var(--gold);
  opacity: 0;
  transition: opacity 0.3s;
}
.banner-slide:hover .banner-hint {
  opacity: 0.85;
}
.banner-skeleton { padding: 0; }
.banner-sk { height: 420px; }
.skeleton-block {
  background: linear-gradient(
    110deg, var(--bg-elevated) 30%, var(--bg-surface) 50%, var(--bg-elevated) 70%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 12px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
@media (max-width: 768px) {
  .banner-slide { height: auto; flex-direction: column; }
  .banner-poster { flex: 0 0 220px; }
  .banner-info { padding: 24px; }
  .banner-title { font-size: 22px; }
  .banner-summary { -webkit-line-clamp: 3; }
}
</style>
