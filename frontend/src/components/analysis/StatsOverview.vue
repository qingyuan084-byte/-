<template>
  <section class="kpi-row">
    <div
      v-for="(k, idx) in cards"
      :key="k.label"
      class="kpi-card"
      :style="{ animationDelay: `${idx * 80}ms` }"
    >
      <div class="kpi-icon">{{ k.icon }}</div>
      <div class="kpi-info">
        <span class="kpi-value">{{ k.value }}</span>
        <span class="kpi-label">{{ k.label }}</span>
      </div>
      <div class="kpi-accent"></div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  cards: { type: Array, default: () => [] },
});
</script>

<style scoped>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 36px;
}
.kpi-card {
  position: relative;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg, 16px);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  overflow: hidden;
  animation: fadeInUp 0.5s var(--ease-out) both;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
  border-color: var(--gold-glow);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
.kpi-icon {
  font-size: 28px;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--gold-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}
.kpi-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.kpi-value {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}
.kpi-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}
.kpi-accent {
  position: absolute;
  right: -16px;
  top: -16px;
  width: 64px;
  height: 64px;
  background: var(--gold);
  opacity: 0.04;
  border-radius: 50%;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 1200px) {
  .kpi-row { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .kpi-value { font-size: 18px; }
}
@media (max-width: 480px) {
  .kpi-row { grid-template-columns: 1fr; }
}
</style>
