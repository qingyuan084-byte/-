<template>
  <aside class="sidebar">
    <div class="side-panel">
      <h3 class="side-title">
        🏆 电影排行榜
        <router-link to="/ranking" class="side-title-link">全部 →</router-link>
      </h3>
      <ul class="rank-list" v-loading="loading">
        <li
          v-for="(m, idx) in topRankMovies"
          :key="m.movie_id"
          class="rank-item"
          @click="$emit('selectMovie', m)"
        >
          <span class="rank-num" :class="'top-' + (idx + 1)">
            {{ idx + 1 }}
          </span>
          <div class="rank-info">
            <span class="rank-title">{{ m.title }}</span>
            <span class="rank-rating">★ {{ m.rating }}</span>
          </div>
        </li>
      </ul>
      <div v-if="topRankMovies.length === 0" class="rank-skeleton">
        <div v-for="i in 8" :key="'sk-rank-'+i" class="skeleton-block rank-sk"></div>
      </div>
    </div>

    <div class="side-panel">
      <h3 class="side-title">🔥 热门标签</h3>
      <div class="tag-cloud" v-loading="loading">
        <template v-if="hotTags.length > 0">
          <span
            v-for="t in hotTags"
            :key="t.name"
            class="tag-chip"
            :class="{ active: activeTag === t.name }"
            :style="{ '--tag-hue': t.hue }"
            @click="$emit('tagClick', t.name)"
          >
            {{ t.name }}
            <sup class="tag-count">{{ t.count }}</sup>
          </span>
        </template>
        <template v-else>
          <span v-for="i in 10" :key="'sk-tag-'+i" class="skeleton-block tag-sk"></span>
        </template>
      </div>
      <div v-if="activeTag" class="tag-clear">
        <a href="#" @click.prevent="$emit('clearFilter')">✕ 清除标签筛选</a>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  topRankMovies: { type: Array, default: () => [] },
  hotTags: { type: Array, default: () => [] },
  activeTag: { type: String, default: "" },
  loading: { type: Boolean, default: true },
});
defineEmits(["selectMovie", "tagClick", "clearFilter"]);
</script>

<style scoped>
.sidebar {
  width: 280px;
  flex-shrink: 0;
}
.side-panel {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
}
.side-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.side-title-link {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.2s;
}
.side-title-link:hover {
  color: var(--gold);
}
.rank-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 8px;
  transition: background 0.2s;
  cursor: pointer;
}
.rank-item:hover {
  background: rgba(255, 255, 255, 0.05);
}
.rank-num {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-display);
  background: var(--bg-surface);
  color: var(--text-muted);
  flex-shrink: 0;
}
.rank-num.top-1,
.rank-num.top-2,
.rank-num.top-3 {
  background: var(--gold);
  color: #fff;
}
.rank-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.rank-title {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rank-rating {
  font-size: 12px;
  color: var(--gold);
  font-weight: 600;
}
.rank-skeleton {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.rank-sk {
  height: 36px;
  border-radius: 8px;
}
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 6px 12px;
  border-radius: 20px;
  background: hsl(var(--tag-hue), 30%, 18%);
  color: hsl(var(--tag-hue), 60%, 70%);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.tag-chip:hover {
  border-color: hsl(var(--tag-hue), 50%, 50%);
  transform: translateY(-1px);
}
.tag-chip.active {
  border-color: var(--gold);
  background: var(--gold-subtle);
  color: var(--gold);
}
.tag-count {
  font-size: 10px;
  opacity: 0.6;
}
.tag-sk {
  width: 60px;
  height: 28px;
  border-radius: 20px;
}
.tag-clear {
  margin-top: 12px;
  text-align: center;
}
.tag-clear a {
  font-size: 12px;
  color: var(--gold);
  text-decoration: none;
}
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
@media (max-width: 1024px) {
  .sidebar {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  .side-panel { margin-bottom: 0; }
}
@media (max-width: 768px) {
  .sidebar { grid-template-columns: 1fr; }
}
</style>
