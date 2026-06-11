<template>
  <div class="filter-panel glass">
    <div class="filter-grid">
      <div class="filter-item">
        <label class="filter-label">电影类型</label>
        <el-select
          :model-value="selectedGenres"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="全部类型"
          clearable
          class="filter-select"
          @update:model-value="$emit('update:selectedGenres', $event)"
        >
          <el-option
            v-for="g in allGenres"
            :key="g"
            :label="`${g} (${genreCounts[g] || 0})`"
            :value="g"
          />
        </el-select>
      </div>

      <div class="filter-item">
        <label class="filter-label">国家/地区</label>
        <el-select
          :model-value="selectedCountries"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="全部地区"
          clearable
          class="filter-select"
          @update:model-value="$emit('update:selectedCountries', $event)"
        >
          <el-option
            v-for="c in allCountries"
            :key="c"
            :label="`${c} (${countryCounts[c] || 0})`"
            :value="c"
          />
        </el-select>
      </div>

      <div class="filter-item filter-item-slider">
        <label class="filter-label">
          年份范围
          <span class="filter-val">{{ yearRange[0] }} – {{ yearRange[1] }}</span>
        </label>
        <el-slider
          :model-value="yearRange"
          range
          :min="yearBounds.min"
          :max="yearBounds.max"
          class="filter-slider"
          @update:model-value="$emit('update:yearRange', $event)"
        />
      </div>

      <div class="filter-item filter-item-slider">
        <label class="filter-label">
          评分范围
          <span class="filter-val">{{ ratingRange[0] }} – {{ ratingRange[1] }} 分</span>
        </label>
        <el-slider
          :model-value="ratingRange"
          range
          :min="0"
          :max="10"
          :step="0.1"
          class="filter-slider"
          @update:model-value="$emit('update:ratingRange', $event)"
        />
      </div>
    </div>

    <div class="filter-actions">
      <el-button @click="$emit('reset')" :disabled="disabled">
        重置筛选
      </el-button>
      <span v-if="isFiltered" class="filter-hint">
        已应用 {{ activeFilterCount }} 项筛选条件
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  selectedGenres: { type: Array, default: () => [] },
  selectedCountries: { type: Array, default: () => [] },
  yearRange: { type: Array, default: () => [1900, 2026] },
  ratingRange: { type: Array, default: () => [0, 10] },
  allGenres: { type: Array, default: () => [] },
  genreCounts: { type: Object, default: () => ({}) },
  allCountries: { type: Array, default: () => [] },
  countryCounts: { type: Object, default: () => ({}) },
  yearBounds: { type: Object, default: () => ({ min: 1900, max: 2026 }) },
  isFiltered: { type: Boolean, default: false },
  activeFilterCount: { type: Number, default: 0 },
  disabled: { type: Boolean, default: false },
});
defineEmits([
  "update:selectedGenres", "update:selectedCountries",
  "update:yearRange", "update:ratingRange",
  "reset",
]);
</script>

<style scoped>
.filter-panel {
  border-radius: var(--radius-xl);
  padding: 24px;
  margin-bottom: 32px;
}
.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}
.filter-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  white-space: nowrap;
}
.filter-val {
  font-size: 12px;
  font-weight: 500;
  color: var(--gold);
  background: var(--gold-subtle);
  padding: 2px 8px;
  border-radius: 10px;
}
.filter-select { width: 100%; }
.filter-slider { margin-top: 4px; }
.filter-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-subtle);
}
.filter-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-left: auto;
}
@media (max-width: 1200px) {
  .filter-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .filter-grid { grid-template-columns: 1fr; }
  .filter-panel { padding: 16px; }
  .filter-actions { flex-wrap: wrap; }
}
</style>
