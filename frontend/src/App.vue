<template>
  <div id="app-root">
    <!-- 背景纹理层 -->
    <div class="bg-texture"></div>
    <div class="bg-grain"></div>

    <div class="app-layout">
      <!-- 顶部导航 -->
      <header class="app-header glass">
        <div class="header-inner">
          <router-link to="/" class="logo-wrap">
            <span class="logo-icon">◆</span>
            <span class="logo-text">随便乱推</span>
          </router-link>

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

          <!-- 主题切换按钮 -->
          <div class="header-right">
            <!-- 用户认证区 -->
            <template v-if="isAuthenticated">
              <router-link to="/profile" class="user-avatar" :title="currentUser">
                {{ currentUser.charAt(0).toUpperCase() }}
              </router-link>
            </template>
            <router-link v-else to="/auth" class="login-link">登录</router-link>

            <button class="theme-toggle" :title="isDark ? '切换到浅色模式' : '切换到深色模式'" @click="toggleTheme">
              <span class="toggle-icon">{{ isDark ? '☀️' : '🌙' }}</span>
            </button>
          </div>
        </div>
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
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useTheme } from "@/composables/useTheme.js";
import { useAuth } from "@/composables/useAuth.js";

const route = useRoute();
const transitionName = ref("fade");
const { current: theme, isDark, toggle } = useTheme();
const { isAuthenticated, currentUser, checkAuth } = useAuth();

function toggleTheme() {
  toggle();
}

const navItems = [
  { path: "/home", label: "首页", icon: "◇" },
  { path: "/explore", label: "分类", icon: "◆" },
  { path: "/analysis", label: "数据", icon: "◈" },
  { path: "/chat", label: "问答", icon: "◉" },
  { path: "/about", label: "关于", icon: "○" },
];

function isActive(path) {
  return route.path === path || (path === "/home" && route.path === "/");
}

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
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text-primary);
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

/* 导航链接 */
.nav-links {
  display: flex;
  gap: 4px;
}
.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
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
.nav-icon {
  font-size: 14px;
  opacity: 0.7;
}
.nav-link.active .nav-icon {
  opacity: 1;
}

/* ── 主题切换 + 用户区域 ─────────────────── */
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
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
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 18px;
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
  color: var(--gold);
  background: var(--gold-subtle);
}
.toggle-icon {
  display: block;
  line-height: 1;
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
.footer-divider {
  opacity: 0.4;
}

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

/* ── 响应式 ──────────────────────────────────────── */
@media (max-width: 768px) {
  .header-inner {
    padding: 0 16px;
  }
  .logo-text {
    font-size: 16px;
  }
  .nav-label {
    display: none;
  }
  .nav-link {
    padding: 8px 12px;
  }
  .nav-icon {
    font-size: 18px;
    opacity: 1;
  }
  .app-main {
    padding: 20px 16px;
  }
}
</style>
