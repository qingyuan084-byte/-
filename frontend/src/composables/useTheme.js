/**
 * useTheme — 深色/浅色主题切换
 *
 * 逻辑：系统偏好 → 用户手动选择覆盖 → localStorage 持久化
 */
import { ref, watchEffect } from "vue";

const THEME_KEY = "cinematic-theme";

/** 'dark' | 'light' | 'system' */
const stored = localStorage.getItem(THEME_KEY) || "system";

const theme = ref(
  stored === "system" ? _systemPreference() : stored
);

/** 实际生效的主题值（dark 或 light） */
function _systemPreference() {
  if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) return "dark";
  return "light";
}

/** 应用 data-theme 属性到 <html> 根元素 */
function _applyDOM(value) {
  document.documentElement.setAttribute("data-theme", value);
}

/** 持久化用户手动选择 */
function _save(value) {
  localStorage.setItem(THEME_KEY, value);
}

// 初始应用
_applyDOM(theme.value);

// 当 theme 变化时自动同步 DOM
watchEffect(() => {
  _applyDOM(theme.value);
});

// 监听系统主题变化（仅在用户未手动选择时生效）
if (window.matchMedia) {
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    if (localStorage.getItem(THEME_KEY) === "system" || !localStorage.getItem(THEME_KEY)) {
      const next = e.matches ? "dark" : "light";
      theme.value = next;
      _applyDOM(next);
    }
  });
}

export function useTheme() {
  /** 当前生效的主题值 'dark' | 'light' */
  const current = theme;

  /** 是否为深色模式 */
  const isDark = () => theme.value === "dark";

  /** 切换主题 */
  function toggle() {
    theme.value = theme.value === "dark" ? "light" : "dark";
    _save(theme.value);
  }

  /** 设置为深色 */
  function setDark() {
    theme.value = "dark";
    _save("dark");
  }

  /** 设置为浅色 */
  function setLight() {
    theme.value = "light";
    _save("light");
  }

  /** 恢复跟随系统 */
  function useSystem() {
    theme.value = _systemPreference();
    _save("system");
  }

  return { current, isDark, toggle, setDark, setLight, useSystem };
}
