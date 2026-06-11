<template>
  <div class="related-movies">
    <div class="related-label">🎯 相关电影</div>
    <div class="related-grid">
      <MovieCard
        v-for="m in movies"
        :key="m.movie_id"
        :movie="mapFn(m)"
        class="related-card"
      />
    </div>
  </div>
</template>

<script setup>
import MovieCard from "@/components/MovieCard.vue";

defineProps({
  movies: { type: Array, default: () => [] },
  mapFn: { type: Function, required: true },
});
</script>

<style scoped>
.related-movies {
  margin-top: 16px;
}
.related-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.related-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}
@media (max-width: 768px) {
  .related-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 480px) {
  .related-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
