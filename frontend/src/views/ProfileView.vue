<template>
  <div class="profile-view">
    <!-- 用户信息卡片 -->
    <div class="profile-hero glass">
      <div class="hero-avatar">{{ initial }}</div>
      <div class="hero-info">
        <h1 class="hero-name">{{ username }}</h1>
        <p class="hero-meta">
          <span v-if="profile"> {{ formatDate(profile.created_at) }} 加入</span>
        </p>
      </div>
      <button class="logout-btn" @click="handleLogout" title="退出登录">
        <span class="logout-icon">⏻</span>
        <span class="logout-text">退出</span>
      </button>
    </div>

    <!-- Tab 切换栏 -->
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'ratings' }"
        @click="activeTab = 'ratings'"
      >
        <span class="tab-icon">★</span>
        <span class="tab-label">我的评分</span>
        <span class="tab-count">{{ ratedMovies.length }}</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'favorites' }"
        @click="activeTab = 'favorites'"
      >
        <span class="tab-icon">♥</span>
        <span class="tab-label">我的收藏</span>
        <span class="tab-count">{{ favoriteMovies.length }}</span>
      </button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="skeleton-grid">
      <div v-for="i in 6" :key="i" class="skeleton-card" />
    </div>

    <!-- 我的评分 -->
    <section v-else-if="activeTab === 'ratings'">
      <div v-if="ratedMovies.length === 0" class="empty-state">
        <span class="empty-icon">★</span>
        <h3>还没有评分记录</h3>
        <p>在电影详情页给喜欢的电影打分吧</p>
        <router-link to="/explore" class="explore-btn">去发现好电影</router-link>
      </div>
      <div v-else class="movies-grid">
        <MovieCard
          v-for="movie in ratedMovies"
          :key="movie.movie_id"
          :movie="{ ...movie, similarity_score: movie.user_rating / 5 }"
        />
      </div>
    </section>

    <!-- 我的收藏 -->
    <section v-else>
      <div v-if="favoriteMovies.length === 0" class="empty-state">
        <span class="empty-icon">♡</span>
        <h3>还没有收藏电影</h3>
        <p>去发现好电影，点击爱心收藏吧</p>
        <router-link to="/explore" class="explore-btn">去探索</router-link>
      </div>
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
import { getFavoriteMovies, getRatedMovies } from "@/api/auth.js";
import MovieCard from "@/components/MovieCard.vue";

const router = useRouter();
const { currentUser, isAuthenticated, token, logout } = useAuth();

const username = computed(() => currentUser.value || "");
const initial = computed(() => username.value.charAt(0).toUpperCase());

const profile = ref(null);
const favoriteMovies = ref([]);
const ratedMovies = ref([]);
const loading = ref(true);
const activeTab = ref("ratings");

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
    const [favData, ratedData] = await Promise.all([
      getFavoriteMovies(token.value),
      getRatedMovies(token.value),
    ]);
    favoriteMovies.value = favData.movies || [];
    ratedMovies.value = ratedData.movies || [];
    activeTab.value = ratedMovies.value.length > 0 ? "ratings" : "favorites";
  } catch {
    favoriteMovies.value = [];
    ratedMovies.value = [];
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
  margin-bottom: 28px;
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

.logout-icon { font-size: 16px; }

/* ── Tab bar ─────────────────────────── */
.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: 4px;
  border: 1px solid var(--border-subtle);
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s ease;
}

.tab-btn:hover {
  color: var(--text-primary);
  background: var(--bg-surface);
}

.tab-btn.active {
  background: var(--gold-subtle);
  color: var(--gold);
  box-shadow: 0 1px 4px rgba(245, 197, 24, 0.1);
}

.tab-icon {
  font-size: 16px;
}

.tab-label {
  font-weight: 600;
}

.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-display);
}

.tab-btn.active .tab-count {
  background: rgba(245, 197, 24, 0.18);
  color: var(--gold);
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

  .logout-text { display: none; }

  .tab-btn {
    padding: 10px 12px;
    gap: 4px;
    font-size: 13px;
  }

  .movies-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 14px;
  }
}
</style>
