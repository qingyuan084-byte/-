<template>
  <!-- 加载骨架屏 -->
  <div v-if="loading" class="loading-grid">
    <div v-for="i in 10" :key="'sk-'+i" class="skeleton-block card-sk"></div>
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
    />
  </div>

  <!-- 空状态 -->
  <div v-else class="empty-state">
    <span class="empty-icon">🎬</span>
    <p>没有找到符合条件的电影</p>
    <a href="#" class="empty-link" @click.prevent="$emit('reset')">清除所有筛选条件</a>
  </div>
</template>

<script setup>
import MovieCard from "@/components/MovieCard.vue";

defineProps({
  movies: { type: Array, default: () => [] },
  loading: { type: Boolean, default: true },
  error: { type: String, default: "" },
});
defineEmits(["reset"]);
</script>

<style scoped>
.movie-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
}
.loading-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
}
.skeleton-block {
  background: linear-gradient(
    110deg, var(--bg-elevated) 30%, var(--bg-surface) 50%, var(--bg-elevated) 70%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 12px;
}
.card-sk { aspect-ratio: 3 / 4; }
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-muted);
}
.empty-icon { font-size: 56px; display: block; margin-bottom: 16px; }
.empty-state p { font-size: 16px; margin-bottom: 16px; }
.empty-link {
  color: var(--gold); text-decoration: none; font-size: 14px; font-weight: 500;
}
.empty-link:hover { text-decoration: underline; }
@media (max-width: 1200px) {
  .movie-grid, .loading-grid { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 900px) {
  .movie-grid, .loading-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 640px) {
  .movie-grid, .loading-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
}
</style>
