import { createRouter, createWebHistory } from "vue-router";
import HomeView from "@/views/HomeView.vue";
import AboutView from "@/views/AboutView.vue";
import AnalysisView from "@/views/AnalysisView.vue";
import ChatView from "@/views/ChatView.vue";
import RankingView from "@/views/RankingView.vue";
import CategoryView from "@/views/CategoryView.vue";
import DetailView from "@/views/DetailView.vue";
import ExploreView from "@/views/ExploreView.vue";
import AuthView from "@/views/AuthView.vue";
import ProfileView from "@/views/ProfileView.vue";
import { useAuth } from "@/composables/useAuth.js";

const routes = [
  { path: "/", redirect: "/home" },
  { path: "/home", name: "home", component: HomeView },
  { path: "/explore", name: "explore", component: ExploreView },
  { path: "/ranking", name: "ranking", component: RankingView },
  { path: "/genre/:genre", name: "genre", component: CategoryView },
  { path: "/movie/:id", name: "detail", component: DetailView },
  { path: "/analysis", name: "analysis", component: AnalysisView },
  { path: "/chat", name: "chat", component: ChatView },
  { path: "/about", name: "about", component: AboutView },
  { path: "/auth", name: "auth", component: AuthView },
  { path: "/profile", name: "profile", component: ProfileView, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

// 导航守卫：需要认证的页面未登录时跳转到登录页
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const { isAuthenticated, initialized } = useAuth();
    // 还未初始化完成，先放行（页面会自行处理 loading 和重定向）
    if (!initialized.value) {
      next();
      return;
    }
    if (!isAuthenticated.value) {
      next({ path: "/auth", query: { redirect: to.fullPath } });
      return;
    }
  }
  next();
});

export default router;
