<template>
  <div class="welcome-card">
    <div class="welcome-icon">🎥</div>
    <h3>你好，我是登小千</h3>
    <p>我可以根据你的口味推荐电影、分析电影风格、回答电影相关问题。</p>
    <div class="quick-asks">
      <span class="quick-label">试试问我：</span>
      <button
        v-for="q in questions"
        :key="q"
        class="quick-btn"
        @click="$emit('select', q)"
      >
        {{ q }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  questions: { type: Array, default: () => [] },
});
defineEmits(["select"]);
</script>

<style scoped>
.welcome-card {
  text-align: center;
  max-width: 420px;
}
.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.welcome-card h3 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.welcome-card p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 20px;
}
.quick-asks {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.quick-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.quick-btn {
  padding: 8px 18px;
  border-radius: 50px;
  border: 1px solid var(--border-default);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  font-family: var(--font-body);
  max-width: 320px;
  text-align: center;
}
.quick-btn:hover {
  border-color: var(--gold);
  color: var(--gold);
  background: var(--gold-subtle);
  box-shadow: 0 0 12px var(--gold-glow);
}
</style>
