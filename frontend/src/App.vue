<template>
  <div id="app-root">
    <!-- 背景纹理层 -->
    <div class="bg-texture"></div>
    <div class="bg-grain"></div>

    <div class="app-layout">
      <!-- 顶部导航（统一搜索栏） -->
      <header class="app-header glass">
        <div class="header-inner">
          <router-link to="/" class="logo-wrap">
            <span class="logo-icon">◆</span>
            <span class="logo-text">随便乱推</span>
          </router-link>

          <!-- 搜索框（全局） -->
          <div class="search-wrap" :class="{ focused: searchFocused }">
            <span class="search-icon">⌕</span>
            <input
              v-model="searchText"
              class="search-input"
              placeholder="搜索电影、导演、演员..."
              @focus="searchFocused = true"
              @blur="searchFocused = false"
              @keyup.enter="onSearch"
            />
            <button v-if="searchText" class="search-clear" @click="searchText = ''">✕</button>
          </div>

          <!-- 桌面端导航链接 -->
          <nav class="nav-links">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              class="nav-link"
              :class="{ active: isActive(item.path) }"
            >
              <span class="nav-icon">{{ item.icon }}</span>
              <span class="nav-label">{{ item.label }}</span>
              <span class="nav-underline"></span>
            </router-link>
          </nav>

          <!-- 右侧操作区 -->
          <div class="header-right">
            <template v-if="isAuthenticated">
              <router-link to="/profile" class="user-avatar" :title="currentUser">
                {{ currentUser.charAt(0).toUpperCase() }}
              </router-link>
            </template>
            <router-link v-else to="/auth" class="login-link">登录</router-link>

            <button class="theme-toggle" :title="isDark() ? '切换到浅色模式' : '切换到深色模式'" @click="toggleTheme">
              <span class="toggle-icon">{{ isDark() ? '🌙' : '☀️' }}</span>
            </button>

            <!-- 移动端汉堡菜单按钮 -->
            <button class="hamburger-btn" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="菜单">
              <span class="hamburger-line" :class="{ open: mobileMenuOpen }"></span>
            </button>
          </div>
        </div>

        <!-- 移动端下拉菜单 -->
        <transition name="slide-down">
          <div v-if="mobileMenuOpen" class="mobile-menu" @click.self="mobileMenuOpen = false">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              class="mobile-nav-link"
              :class="{ active: isActive(item.path) }"
              @click="mobileMenuOpen = false"
            >
              <span class="nav-icon">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </router-link>
            <div class="mobile-menu-divider"></div>
            <template v-if="isAuthenticated">
              <router-link to="/profile" class="mobile-nav-link" @click="mobileMenuOpen = false">
                <span class="nav-icon">👤</span>
                <span>{{ currentUser }}</span>
              </router-link>
            </template>
            <router-link v-else to="/auth" class="mobile-nav-link" @click="mobileMenuOpen = false">
              <span class="nav-icon">👤</span>
              <span>登录 / 注册</span>
            </router-link>
          </div>
        </transition>
      </header>

      <!-- 主内容区 -->
      <main class="app-main">
        <router-view v-slot="{ Component }">
          <transition :name="transitionName" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>

      <!-- 底部 -->
      <footer class="app-footer">
        <div class="footer-inner">
          <span class="footer-brand">随便乱推</span>
          <span class="footer-divider">·</span>
          <span>Powered by FastAPI + Vue 3</span>
          <span class="footer-divider">·</span>
          <span>&copy; 2026</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useTheme } from "@/composables/useTheme.js";
import { useAuth } from "@/composables/useAuth.js";

const route = useRoute();
const router = useRouter();
const transitionName = ref("fade");
const { isDark, toggle } = useTheme();
const { isAuthenticated, currentUser, checkAuth } = useAuth();

const searchText = ref("");
const searchFocused = ref(false);
const mobileMenuOpen = ref(false);

function toggleTheme() {
  toggle();
}

function onSearch() {
  const q = searchText.value.trim();
  if (!q) return;
  if (route.name !== "home") {
    router.push({ name: "home", query: { q } });
  } else {
    router.replace({ name: "home", query: { q } });
  }
}

// 从 URL 回填搜索框
watch(() => route.query.q, (q) => {
  if (q && typeof q === "string") {
    searchText.value = q;
  }
});

const navItems = [
  { path: "/home", label: "首页", icon: "◇" },
  { path: "/explore", label: "探索", icon: "◆" },
  { path: "/analysis", label: "数据", icon: "◈" },
  { path: "/chat", label: "问答", icon: "◉" },
  { path: "/about", label: "关于", icon: "○" },
];

function isActive(path) {
  return route.path === path || (path === "/home" && route.path === "/");
}

// 路由变化关闭移动菜单
watch(() => route.path, () => { mobileMenuOpen.value = false; });

onMounted(() => {
  checkAuth();
});
</script>

<style>
/* ================================================================
   App.vue — 全局布局样式
   ================================================================ */

/* 背景纹理 */
.bg-texture {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 80% 60% at 50% -10%, rgba(245, 197, 24, 0.04) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 80%, rgba(245, 197, 24, 0.03) 0%, transparent 50%);
}

.bg-grain {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

/* 应用容器 */
.app-layout {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ── 导航栏 ──────────────────────────────────────── */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid var(--border-subtle);
  height: 64px;
  transition: background-color 0.35s ease, border-color 0.35s ease;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Logo */
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text-primary);
  flex-shrink: 0;
}
.logo-icon {
  font-size: 22px;
  color: var(--gold);
  filter: drop-shadow(0 0 6px var(--gold-glow));
}
.logo-text {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--text-primary);
}

/* 搜索框 */
.search-wrap {
  display: flex;
  align-items: center;
  flex: 1;
  max-width: 360px;
  height: 40px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 20px;
  padding: 0 6px;
  transition: border-color 0.25s, box-shadow 0.25s, background 0.25s;
}
.search-wrap:hover {
  border-color: var(--text-muted);
}
.search-wrap.focused {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px var(--gold-glow);
}
.search-icon {
  font-size: 18px;
  color: var(--text-muted);
  margin: 0 6px 0 10px;
  flex-shrink: 0;
}
.search-input {
  flex: 1;
  height: 100%;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 14px;
  font-family: var(--font-body);
  outline: none;
  min-width: 0;
}
.search-input::placeholder {
  color: var(--text-muted);
}
.search-clear {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: var(--bg-elevated);
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 4px;
  flex-shrink: 0;
  transition: color 0.2s;
}
.search-clear:hover { color: var(--text-primary); }

/* 导航链接 */
.nav-links {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}
.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-md);
  transition: all var(--duration-base) var(--ease-out);
  overflow: hidden;
}
.nav-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.04);
}
.nav-link.active {
  color: var(--gold);
  background: var(--gold-subtle);
}
.nav-underline {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 60%;
  height: 2px;
  background: var(--gold);
  border-radius: 1px;
  transition: transform var(--duration-base) var(--ease-bounce);
}
.nav-link.active .nav-underline {
  transform: translateX(-50%) scaleX(1);
}
.nav-icon { font-size: 14px; opacity: 0.7; }
.nav-link.active .nav-icon { opacity: 1; }

/* 右侧操作区 */
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: auto;
}

.login-link {
  text-decoration: none;
  color: var(--gold);
  font-size: 13px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--gold-dim);
  transition: all 0.2s;
  white-space: nowrap;
}
.login-link:hover {
  background: var(--gold-subtle);
  border-color: var(--gold);
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gold) 0%, #e8a817 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-family: var(--font-display);
  transition: all 0.2s;
  flex-shrink: 0;
}
.user-avatar:hover {
  transform: scale(1.08);
  box-shadow: 0 0 14px var(--gold-glow);
}

.theme-toggle {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  font-size: 16px;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
}
.theme-toggle:hover {
  border-color: var(--gold);
  background: var(--gold-subtle);
}

/* 汉堡菜单按钮（仅移动端） */
.hamburger-btn {
  display: none;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  cursor: pointer;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.hamburger-line,
.hamburger-line::before,
.hamburger-line::after {
  display: block;
  width: 18px;
  height: 2px;
  background: var(--text-primary);
  border-radius: 2px;
  transition: all 0.3s ease;
  content: "";
}
.hamburger-line {
  position: relative;
}
.hamburger-line::before {
  position: absolute;
  top: -5px;
}
.hamburger-line::after {
  position: absolute;
  top: 5px;
}
.hamburger-line.open {
  background: transparent;
}
.hamburger-line.open::before {
  top: 0;
  transform: rotate(45deg);
}
.hamburger-line.open::after {
  top: 0;
  transform: rotate(-45deg);
}

/* 移动端下拉菜单 */
.mobile-menu {
  display: none;
  position: absolute;
  top: 64px;
  left: 0;
  right: 0;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-subtle);
  padding: 8px 16px 16px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  z-index: 99;
}
.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  text-decoration: none;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 500;
  border-radius: var(--radius-md);
  transition: background 0.2s;
}
.mobile-nav-link:hover, .mobile-nav-link.active {
  background: var(--gold-subtle);
  color: var(--gold);
}
.mobile-menu-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: 8px 16px;
}

/* ── 主内容 ──────────────────────────────────────── */
.app-main {
  flex: 1;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* ── 底部 ────────────────────────────────────────── */
.app-footer {
  border-top: 1px solid var(--border-subtle);
  padding: 20px 24px;
  transition: border-color 0.35s ease;
}
.footer-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-muted);
}
.footer-brand {
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--gold);
  letter-spacing: 0.04em;
}
.footer-divider { opacity: 0.4; }

/* ── 页面过渡动画 ────────────────────────────────── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out);
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* ── 移动端下拉动画 ──────────────────────────────── */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.25s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── 响应式 ──────────────────────────────────────── */
@media (max-width: 1024px) {
  .logo-text { display: none; }
  .search-wrap { max-width: 240px; }
  .nav-link { padding: 8px 10px; }
}

@media (max-width: 768px) {
  .header-inner { padding: 0 12px; gap: 8px; }
  .logo-text { display: none; }

  /* 搜索框压缩 */
  .search-wrap {
    max-width: none;
    flex: 1;
    height: 36px;
  }
  .search-input { font-size: 13px; }

  /* 隐藏桌面端导航 */
  .nav-links { display: none; }

  /* 隐藏登录按钮（在汉堡菜单中显示） */
  .header-right .login-link { display: none; }

  /* 显示汉堡菜单 */
  .hamburger-btn { display: flex; }
  .mobile-menu { display: block; }

  .app-main { padding: 20px 12px; }
}
</style>
