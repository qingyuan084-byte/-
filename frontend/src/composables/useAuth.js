import { ref, computed } from "vue";
import {
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  checkAuth as apiCheckAuth,
  getProfile as apiGetProfile,
  toggleFavorite as apiToggleFavorite,
  getFavorites as apiGetFavorites,
  setRating as apiSetRating,
  deleteRating as apiDeleteRating,
  getMovieRating as apiGetMovieRating,
  getAllRatings as apiGetAllRatings,
} from "@/api/auth.js";

const TOKEN_KEY = "cinematic_auth_token";

// ── 模块级响应式状态（单例） ──────────────────────────

const token = ref(localStorage.getItem(TOKEN_KEY) || "");
const currentUser = ref(null);
const favorites = ref(new Set());
const ratings = ref({});
const initialized = ref(false);

// ── 导出 composable ────────────────────────────────────

export function useAuth() {
  const isAuthenticated = computed(() => !!token.value && !!currentUser.value);

  async function checkAuth() {
    if (!token.value) {
      initialized.value = true;
      return false;
    }
    try {
      const data = await apiCheckAuth(token.value);
      if (data.authenticated) {
        currentUser.value = data.username;
        await fetchFavorites();
        await fetchRatings();
        initialized.value = true;
        return true;
      }
    } catch {
      clearAuth();
    }
    initialized.value = true;
    return false;
  }

  async function login(username, password) {
    const data = await apiLogin(username, password);
    if (data.success) {
      token.value = data.token;
      localStorage.setItem(TOKEN_KEY, data.token);
      currentUser.value = data.username;
      await fetchFavorites();
      await fetchRatings();
      return { success: true };
    }
    return { success: false, message: data.message };
  }

  async function register(username, password) {
    const data = await apiRegister(username, password);
    if (data.success) {
      token.value = data.token;
      localStorage.setItem(TOKEN_KEY, data.token);
      currentUser.value = data.username;
      await fetchFavorites();
      await fetchRatings();
      return { success: true };
    }
    return { success: false, message: data.message };
  }

  async function logout() {
    if (token.value) {
      try { await apiLogout(token.value); } catch { /* ignore */ }
    }
    clearAuth();
  }

  function clearAuth() {
    token.value = "";
    currentUser.value = null;
    favorites.value = new Set();
    ratings.value = {};
    localStorage.removeItem(TOKEN_KEY);
  }

  async function toggleFavorite(movieId) {
    if (!token.value) return null;
    const result = await apiToggleFavorite(token.value, movieId);
    if (result.is_favorited) {
      favorites.value = new Set([...favorites.value, movieId]);
    } else {
      const next = new Set(favorites.value);
      next.delete(movieId);
      favorites.value = next;
    }
    return result;
  }

  async function fetchFavorites() {
    if (!token.value) return;
    try {
      const data = await apiGetFavorites(token.value);
      favorites.value = new Set(data.favorites || []);
    } catch {
      favorites.value = new Set();
    }
  }

  function isFavorited(movieId) {
    return favorites.value.has(String(movieId));
  }

  // ── 评分操作 ──────────────────────────────────────

  async function setRating(movieId, rating) {
    if (!token.value) return null;
    const result = await apiSetRating(token.value, movieId, rating);
    if (result && !result.is_removed) {
      ratings.value = { ...ratings.value, [movieId]: result.rating };
    }
    return result;
  }

  async function removeRating(movieId) {
    if (!token.value) return null;
    const result = await apiDeleteRating(token.value, movieId);
    if (result && result.is_removed) {
      const next = { ...ratings.value };
      delete next[movieId];
      ratings.value = next;
    }
    return result;
  }

  async function fetchRatings() {
    if (!token.value) return;
    try {
      const data = await apiGetAllRatings(token.value);
      ratings.value = data.ratings || {};
    } catch {
      ratings.value = {};
    }
  }

  function getUserRating(movieId) {
    const r = ratings.value[String(movieId)];
    return r !== undefined ? r : null;
  }

  return {
    token,
    currentUser,
    isAuthenticated,
    favorites,
    ratings,
    initialized,
    login,
    register,
    logout,
    checkAuth,
    toggleFavorite,
    fetchFavorites,
    isFavorited,
    setRating,
    removeRating,
    fetchRatings,
    getUserRating,
  };
}
