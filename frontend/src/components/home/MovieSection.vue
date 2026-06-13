<template>
  <section class="movie-section">
    <div class="section-header">
      <h2 class="section-title">
        <span class="title-dot" :class="dotClass"></span>
        {{ expanded ? label + ' · 全部' : label }}
        <span v-if="badge" class="section-badge">{{ badge }}</span>
      </h2>
      <router-link
        v-if="moreLink"
        class="section-more"
        :to="moreLink"
      >
        {{ moreText }}
      </router-link>
      <a v-else href="#" class="section-more" @click.prevent="$emit('toggleExpand')">
        {{ expanded ? '收起 ↑' : moreText }}
      </a>
    </div>
    <div class="movie-grid" v-loading="loading">
      <template v-if="movies.length > 0">
        <MovieCard
          v-for="(m, i) in movies"
          :key="m.movie_id"
          :movie="m"
          :eager="i < 5"
          class="grid-card"
        />
      </template>
      <template v-else>
        <div v-for="i in skeletonCount" :key="'sk-'+i" class="skeleton-block card-sk"></div>
      </template>
    </div>
  </section>
</template>

<script setup>
import MovieCard from "@/components/MovieCard.vue";

defineProps({
  label: { type: String, required: true },
  movies: { type: Array, default: () => [] },
  loading: { type: Boolean, default: true },
  expanded: { type: Boolean, default: false },
  badge: { type: String, default: "" },
  dotClass: { type: String, default: "" },
  moreText: { type: String, default: "查看更多 →" },
  moreLink: { type: String, default: "" },
  skeletonCount: { type: Number, default: 5 },
});
defineEmits(["toggleExpand"]);
</script>

<style scoped>
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
.title-dot.suspense { background: #A855F7; }
.title-dot.comedy { background: #22C55E; }
.title-dot.scifi { background: #3B82F6; }
.title-dot.action { background: #EF4444; }
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
.movie-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.skeleton-block {
  background: linear-gradient(
    110deg, var(--bg-elevated) 30%, var(--bg-surface) 50%, var(--bg-elevated) 70%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 12px;
}
.card-sk {
  aspect-ratio: 3 / 4;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
@media (max-width: 1200px) {
  .movie-grid { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 768px) {
  .movie-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
}
</style>
