<template>
  <div class="movie-card" :class="{ 'has-score': movie.similarity_score != null }" @click="onCardClick">
    <!-- 金色边框光晕 -->
    <div class="card-glow"></div>

    <div class="poster-wrapper">
      <!-- 海报图片 -->
      <img
        v-if="!imgFailed && posterSrc"
        :src="posterSrc"
        :alt="movie.title"
        class="poster"
        :class="{ 'poster-loaded': imgLoaded }"
        :loading="eager ? 'eager' : 'lazy'"
        decoding="async"
        @load="onPosterLoad"
        @error="onPosterError"
      />

      <!-- 加载失败占位 -->
      <div v-else class="poster-placeholder">
        <div class="placeholder-content">
          <span class="placeholder-icon">🎬</span>
          <span class="placeholder-title">{{ movie.title }}</span>
        </div>
        <!-- 装饰性金色对角线 -->
        <div class="placeholder-accent"></div>
      </div>

      <!-- 海报叠加信息层 -->
      <div class="poster-overlay">
        <span v-if="movie.year" class="overlay-year">{{ movie.year }}</span>
      </div>

      <!-- 相似度评分标签 -->
      <div v-if="movie.similarity_score != null" class="score-badge pulse">
        <span class="score-value">{{ (movie.similarity_score * 100).toFixed(0) }}</span>
        <span class="score-unit">%</span>
      </div>
    </div>

    <!-- 卡片底部信息 -->
    <div class="card-body">
      <h3 class="title" :title="movie.title">{{ movie.title }}</h3>
      <div class="meta">
        <span v-if="movie.rating > 0" class="rating">
          <span class="star">★</span>
          <span>{{ movie.rating }}</span>
        </span>
        <span v-if="movie.year" class="year">{{ movie.year }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const props = defineProps({
  movie: {
    type: Object,
    required: true,
  },
  eager: {
    type: Boolean,
    default: false,
  },
});

const emits = defineEmits(["click"]);

const imgFailed = ref(false);
const imgLoaded = ref(false);

// 豆瓣图床域名 → 走后端代理绕过防盗链
const DOUBAN_HOSTS = [
  "img1.doubanio.com", "img2.doubanio.com", "img3.doubanio.com",
  "img9.doubanio.com", "img.doubanio.com",
];

function isDoubanUrl(url) {
  if (!url) return false;
  try {
    const host = new URL(url).hostname;
    return DOUBAN_HOSTS.some((h) => host === h || host.endsWith("." + h));
  } catch {
    return false;
  }
}

const posterSrc = computed(() => {
  const raw = props.movie?.poster_url;
  if (!raw || imgFailed.value) return "";
  return isDoubanUrl(raw)
    ? `/api/image-proxy?url=${encodeURIComponent(raw)}`
    : raw;
});

function onPosterLoad() {
  imgLoaded.value = true;
}

function onPosterError() {
  imgFailed.value = true;
}

function onCardClick() {
  emits("click");
  if (props.movie?.movie_id) {
    router.push(`/movie/${props.movie.movie_id}`);
  }
}
</script>

<style scoped>
/* ================================================================
   MovieCard — 电影卡片（暗色主题 + 金色点缀 + 毛玻璃悬浮）
   ================================================================ */

.movie-card {
  position: relative;
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition:
    transform 350ms var(--ease-bounce),
    box-shadow 350ms var(--ease-out),
    border-color 350ms var(--ease-out);
}

.movie-card:hover {
  transform: translateY(-8px);
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(245, 197, 24, 0.15);
  border-color: rgba(245, 197, 24, 0.25);
}

/* 金色光晕 */
.card-glow {
  position: absolute;
  inset: -1px;
  border-radius: var(--radius-lg);
  opacity: 0;
  background: linear-gradient(
    135deg,
    rgba(245, 197, 24, 0.12) 0%,
    transparent 50%,
    rgba(245, 197, 24, 0.06) 100%
  );
  transition: opacity 350ms var(--ease-out);
  pointer-events: none;
  z-index: 1;
}
.movie-card:hover .card-glow {
  opacity: 1;
}

/* ── 海报区域 ──────────────────────────────────── */
.poster-wrapper {
  position: relative;
  aspect-ratio: 3 / 4;
  background: var(--bg-surface);
  overflow: hidden;
}

.poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  opacity: 0;
  transition: transform 450ms var(--ease-out), opacity 350ms var(--ease-out);
}
.poster-loaded {
  opacity: 1;
}
.movie-card:hover .poster {
  transform: scale(1.06);
}

/* 海报叠加层 */
.poster-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24px 12px 10px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85) 0%, transparent 100%);
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-out);
}
.movie-card:hover .poster-overlay {
  opacity: 1;
}
.overlay-year {
  font-family: var(--font-display);
  font-size: 13px;
  color: var(--gold);
  font-weight: 600;
  letter-spacing: 0.06em;
}

/* 评分标签 */
.score-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: baseline;
  gap: 1px;
  background: rgba(10, 10, 15, 0.78);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(245, 197, 24, 0.3);
  padding: 4px 10px;
  border-radius: 8px;
  z-index: 2;
  transition: border-color var(--duration-base) var(--ease-out);
}
.movie-card:hover .score-badge {
  border-color: rgba(245, 197, 24, 0.6);
}
.score-value {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--gold);
  line-height: 1;
}
.score-unit {
  font-size: 11px;
  color: var(--gold-dim);
  font-weight: 600;
}

/* 脉冲动画（仅首现） */
.pulse {
  animation: scorePulse 1.8s var(--ease-out) 1;
}
@keyframes scorePulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(245, 197, 24, 0);
  }
  50% {
    box-shadow: 0 0 16px 4px rgba(245, 197, 24, 0.2);
  }
}

/* 占位海报 */
.poster-placeholder {
  width: 100%;
  height: 100%;
  position: relative;
  background: linear-gradient(145deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  z-index: 1;
  padding: 16px;
}
.placeholder-icon {
  font-size: 44px;
  filter: grayscale(0.3);
}
.placeholder-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-weight: 500;
}
.placeholder-accent {
  position: absolute;
  right: -20px;
  top: -20px;
  width: 80px;
  height: 80px;
  background: var(--gold);
  opacity: 0.06;
  transform: rotate(45deg);
  border-radius: 4px;
}

/* ── 卡片底部 ──────────────────────────────────── */
.card-body {
  padding: 14px 14px 16px;
  position: relative;
  z-index: 2;
}

.title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
  transition: color var(--duration-fast) var(--ease-out);
}
.movie-card:hover .title {
  color: var(--gold);
}

.meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.rating {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--gold);
  font-weight: 700;
  font-family: var(--font-display);
}
.star {
  font-size: 14px;
  color: var(--gold);
}

.year {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-display);
}
</style>
