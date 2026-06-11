<template>
  <div class="profile-view">
    <!-- 用户信息卡片 -->
    <div class="profile-hero glass">
      <div class="hero-avatar">{{ initial }}</div>
      <div class="hero-info">
        <h1 class="hero-name">{{ username }}</h1>
        <p class="hero-meta">
          已收藏 <strong>{{ favorites.length }}</strong> 部电影
          <span v-if="profile"> · {{ formatDate(profile.created_at) }} 加入</span>
        </p>
      </div>
      <button class="logout-btn" @click="handleLogout" title="退出登录">
        <span class="logout-icon">⏻</span>
        <span class="logout-text">退出</span>
      </button>
    </div>

    <!-- 收藏列表 -->
    <section class="favorites-section">
      <h2 class="section-title">
        <span class="title-accent">★</span>
        我的收藏
        <span v-if="!loading && favorites.length > 0" class="count-badge">
          {{ favorites.length }}
        </span>
      </h2>

      <!-- 加载中 -->
      <div v-if="loading" class="skeleton-grid">
        <div v-for="i in 6" :key="i" class="skeleton-card" />
      </div>

      <!-- 空状态 -->
      <div v-else-if="favorites.length === 0" class="empty-state">
        <span class="empty-icon">☆</span>
        <h3>还没有收藏电影</h3>
        <p>去发现好电影，点击星星收藏吧！</p>
        <router-link to="/explore" class="explore-btn">去探索</router-link>
      </div>

      <!-- 电影网格 -->
      <div v-else class="movies-grid">
        <MovieCard
          v-for="movie in favoriteMovies"
          :key="movie.movie_id"
          :movie="movie"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "@/composables/useAuth.js";
import { getFavoriteMovies } from "@/api/auth.js";
import MovieCard from "@/components/MovieCard.vue";

const router = useRouter();
const { currentUser, isAuthenticated, token, favorites, logout } = useAuth();

const username = computed(() => currentUser.value || "");
const initial = computed(() => username.value.charAt(0).toUpperCase());

const profile = ref(null);
const favoriteMovies = ref([]);
const loading = ref(true);

function formatDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
}

async function handleLogout() {
  await logout();
  router.push("/home");
}

onMounted(async () => {
  if (!isAuthenticated.value) {
    router.push("/auth?redirect=/profile");
    return;
  }
  try {
    const data = await getFavoriteMovies(token.value);
    favoriteMovies.value = data.movies || [];
  } catch {
    favoriteMovies.value = [];
  }
  loading.value = false;
});
</script>

<style scoped>
.profile-view {
  max-width: 1100px;
  margin: 0 auto;
}

/* ── Hero ────────────────────────────── */
.profile-hero {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 28px 32px;
  border-radius: var(--radius-xl);
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  margin-bottom: 36px;
}

.hero-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gold) 0%, #e8a817 100%);
  color: #fff;
  font-size: 28px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-family: var(--font-display);
}

.hero-info {
  flex: 1;
  min-width: 0;
}

.hero-name {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.hero-meta {
  font-size: 14px;
  color: var(--text-secondary);
}

.hero-meta strong {
  color: var(--gold);
  font-weight: 700;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.logout-btn:hover {
  border-color: #f87171;
  color: #f87171;
  background: rgba(248, 113, 113, 0.06);
}

.logout-icon {
  font-size: 16px;
}

/* ── Section title ───────────────────── */
.section-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.title-accent {
  color: var(--gold);
  font-size: 22px;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--gold-subtle);
  color: var(--gold);
  font-size: 12px;
  font-weight: 700;
}

/* ── Movies grid ─────────────────────── */
.movies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

/* ── Skeleton ────────────────────────── */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.skeleton-card {
  aspect-ratio: 3 / 4;
  border-radius: var(--radius-lg);
  background: linear-gradient(
    110deg,
    var(--bg-elevated) 30%,
    var(--bg-surface) 50%,
    var(--bg-elevated) 70%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Empty state ─────────────────────── */
.empty-state {
  text-align: center;
  padding: 64px 24px;
}

.empty-icon {
  font-size: 56px;
  color: var(--text-muted);
  display: block;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.explore-btn {
  display: inline-block;
  padding: 10px 28px;
  border-radius: var(--radius-md);
  background: var(--gold);
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
  transition: background 0.2s;
}

.explore-btn:hover {
  background: var(--gold-bright);
}

/* ── Responsive ──────────────────────── */
@media (max-width: 640px) {
  .profile-hero {
    flex-direction: column;
    text-align: center;
    padding: 24px 20px;
  }

  .logout-text {
    display: none;
  }

  .movies-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 14px;
  }
}
</style>
