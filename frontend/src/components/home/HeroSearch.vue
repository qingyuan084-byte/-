<template>
  <header class="home-header">
    <div class="header-inner">
      <a class="logo-wrap" @click.prevent="$emit('scrollToTop')">
        <span class="logo-icon">◆</span>
        <span class="logo-text">随便乱推</span>
      </a>

      <div class="search-wrap">
        <input
          :value="modelValue"
          class="search-input"
          placeholder="搜索电影..."
          @input="$emit('update:modelValue', $event.target.value)"
          @keyup.enter="$emit('search')"
        />
        <button class="search-btn" @click="$emit('search')">
          <span>⌕</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: "" },
});
defineEmits(["update:modelValue", "search", "scrollToTop"]);
</script>

<style scoped>
.home-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-glass, rgba(15, 23, 42, 0.85));
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border-subtle);
  height: 64px;
}
.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 28px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--text-primary);
  cursor: pointer;
  position: absolute;
  left: 28px;
}
.logo-icon {
  font-size: 22px;
  color: var(--gold);
}
.logo-text {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.search-wrap {
  display: flex;
  align-items: center;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.search-wrap:focus-within {
  border-color: var(--gold);
}
.search-input {
  width: 280px;
  padding: 8px 14px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 13px;
  font-family: var(--font-body);
  outline: none;
}
.search-input::placeholder {
  color: var(--text-muted);
}
.search-btn {
  padding: 8px 14px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 18px;
  transition: color 0.2s;
}
.search-btn:hover {
  color: var(--gold);
}
@media (max-width: 768px) {
  .header-inner { padding: 0 16px; }
  .logo-wrap { position: static; }
  .search-input { width: 160px; }
}
</style>
