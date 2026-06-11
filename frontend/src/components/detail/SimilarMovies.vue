<template>
  <section class="similar-section">
    <h2 class="section-title">
      <span class="title-dot"></span>猜你喜欢
    </h2>
    <div v-if="loading" class="loading-grid">
      <div v-for="i in 6" :key="'ssk-'+i" class="skeleton-block card-sk"></div>
    </div>
    <div v-else-if="movies.length > 0" class="movie-grid">
      <MovieCard
        v-for="m in movies"
        :key="m.movie_id"
        :movie="m"
        class="grid-card"
        @click="$emit('select', m.movie_id)"
      />
    </div>
    <div v-else class="no-similar">
      <p>暂无相似推荐</p>
    </div>
  </section>
</template>

<script setup>
import MovieCard from "@/components/MovieCard.vue";

defineProps({
  movies: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});
defineEmits(["select"]);
</script>

<style scoped>
.similar-section {
  margin-top: 60px;
  padding-top: 40px;
  border-top: 1px solid var(--border-subtle);
}
.section-title {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 22px; font-weight: 700; color: var(--text-primary);
  display: flex; align-items: center; gap: 10px; margin-bottom: 24px;
}
.title-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--gold); display: inline-block;
}
.movie-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.loading-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.skeleton-block {
  background: linear-gradient(110deg, var(--bg-elevated) 30%, var(--bg-surface) 50%, var(--bg-elevated) 70%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 12px;
}
.card-sk { aspect-ratio: 3 / 4; }
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.no-similar { text-align: center; padding: 40px; color: var(--text-muted); font-size: 14px; }
@media (max-width: 900px) {
  .movie-grid, .loading-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 640px) {
  .movie-grid, .loading-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
}
</style>
