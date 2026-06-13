<template>
  <div class="profile-view">
    <!-- 用户信息卡片 -->
    <div class="profile-hero glass">
      <div class="hero-avatar">{{ initial }}</div>
      <div class="hero-info">
        <h1 class="hero-name">{{ username }}</h1>
        <p class="hero-meta">
          已收藏 <strong>{{ favorites.length }}</strong> 部电影
          <span v-if="ratingCount > 0"> · 已评分 <strong>{{ ratingCount }}</strong> 部</span>
          <span v-if="profile"> · {{ formatDate(profile.created_at) }} 加入</span>
        </p>
      </div>
      <button class="logout-btn" @click="handleLogout" title="退出登录">
        <span class="logout-icon">⏻</span>
        <span class="logout-text">退出</span>
      </button>
    </div>

    <!-- 评分列表 -->
    <section v-if="ratedMovies.length > 0" class="favorites-section">
      <h2 class="section-title">
        <span class="title-accent">★</span>
        我的评分
        <span class="count-badge">{{ ratedMovies.length }}</span>
      </h2>
      <div class="movies-grid">
        <div
          v-for="movie in ratedMovies"
          :key="movie.movie_id"
          class="rated-card"
          @click="$router.push(`/movie/${movie.movie_id}`)"
        >
          <div class="rated-poster">
            <img
              v-if="movie.poster_url"
              :src="movie.poster_url"
              :alt="movie.title"
              class="rated-img"
            />
            <div v-else class="rated-ph">
              <span>🎬</span>
            </div>
            <div class="rated-score-badge">
              <StarRating :model-value="movie.user_rating" readonly />
            </div>
          </div>
          <div class="rated-info">
            <h3 class="rated-title">{{ movie.title }}</h3>
            <span v-if="movie.rating > 0" class="rated-douban">豆瓣 {{ movie.rating }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 收藏列表 -->
    <section class="favorites-section">
      <h2 class="section-title">
        <span class="title-accent">♥</span>
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
        <span class="empty-icon">♡</span>
        <h3>还没有收藏电影</h3>
        <p>去发现好电影，点击爱心收藏吧！</p>
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
import { getRatedMovies } from "@/api/auth.js";
import MovieCard from "@/components/MovieCard.vue";
import StarRating from "@/components/StarRating.vue";

const router = useRouter();
const { currentUser, isAuthenticated, token, favorites, ratings, logout } = useAuth();

const username = computed(() => currentUser.value || "");
const initial = computed(() => username.value.charAt(0).toUpperCase());
const ratingCount = computed(() => Object.keys(ratings.value).length);

const profile = ref(null);
const favoriteMovies = ref([]);
const ratedMovies = ref([]);
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
    const [favData, ratedData] = await Promise.all([
      getFavoriteMovies(token.value),
      getRatedMovies(token.value),
    ]);
    favoriteMovies.value = favData.movies || [];
    ratedMovies.value = ratedData.movies || [];
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

/* ── Rated cards ────────────────────── */
.rated-card {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.rated-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(245, 197, 24, 0.12);
}
.rated-poster {
  position: relative;
  aspect-ratio: 3 / 4;
  background: var(--bg-surface);
  overflow: hidden;
}
.rated-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.rated-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #1a1a2e, #16213e);
  font-size: 40px;
}
.rated-score-badge {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px 8px 8px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.88) 0%, transparent 100%);
  display: flex;
  justify-content: center;
}
.rated-info {
  padding: 10px 12px 12px;
}
.rated-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}
.rated-douban {
  font-size: 12px;
  color: var(--gold);
  font-weight: 700;
  font-family: var(--font-display);
}
</style>
