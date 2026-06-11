<template>
  <header class="home-header">
    <div class="header-inner">
      <a class="logo-wrap" @click.prevent="$emit('scrollToTop')">
        <span class="logo-icon">◆</span>
        <span class="logo-text">随便乱推</span>
      </a>

      <nav class="nav-links">
        <a href="#" class="nav-link active" @click.prevent="$emit('scrollToTop')">首页</a>
        <router-link to="/explore" class="nav-link">电影分类</router-link>
        <router-link to="/ranking" class="nav-link">排行榜</router-link>
        <router-link to="/chat" class="nav-link">AI 推荐</router-link>
      </nav>

      <div class="header-right">
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
        <button class="icon-btn" title="收藏">
          <span>♡</span>
        </button>
        <button class="icon-btn" title="登录">
          <span>👤</span>
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
  gap: 40px;
}
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--text-primary);
  flex-shrink: 0;
  cursor: pointer;
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
.nav-links {
  display: flex;
  gap: 2px;
  flex: 1;
}
.nav-link {
  padding: 8px 16px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
}
.nav-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}
.nav-link.active {
  color: var(--gold);
  background: var(--gold-subtle);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
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
  width: 200px;
  padding: 8px 12px;
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
  padding: 8px 12px;
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
.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-btn:hover {
  background: var(--bg-elevated);
  color: var(--gold);
}
@media (max-width: 768px) {
  .header-inner { padding: 0 16px; gap: 16px; }
  .nav-links { display: none; }
  .search-input { width: 140px; }
}
</style>
