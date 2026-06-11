<template>
  <footer class="home-footer">
    <div class="footer-inner">
      <div class="footer-col">
        <h4 class="footer-logo">◆ 随便乱推</h4>
        <p>专注高品质电影发现与推荐</p>
      </div>
      <div class="footer-col">
        <h5>站点导航</h5>
        <a href="#" @click.prevent="$emit('scrollToTop')">首页</a>
        <router-link to="/ranking">排行榜</router-link>
        <router-link to="/chat">AI 问答</router-link>
        <router-link to="/analysis">数据分析</router-link>
      </div>
      <div class="footer-col">
        <h5>关于我们</h5>
        <a href="#">关于随便乱推</a>
        <a href="#">联系方式</a>
        <a href="#">隐私政策</a>
      </div>
      <div class="footer-col">
        <h5>技术栈</h5>
        <p>Python · FastAPI · Vue 3</p>
        <p>智谱AI GLM · SentenceTransformers</p>
        <p class="footer-copy">&copy; 2026 随便乱推</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
defineEmits(["scrollToTop"]);
</script>

<style scoped>
.home-footer {
  background: var(--bg-deep);
  border-top: 1px solid var(--border-subtle);
  padding: 40px 28px 28px;
  margin-top: 20px;
}
.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 40px;
}
.footer-col h4 {
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--gold);
  margin-bottom: 10px;
}
.footer-col h5 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}
.footer-col p {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.7;
}
.footer-col a {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  text-decoration: none;
  line-height: 2.2;
  transition: color 0.2s;
}
.footer-col a:hover {
  color: var(--gold);
}
.footer-copy {
  margin-top: 12px;
  font-size: 12px !important;
  color: var(--text-muted) !important;
}
@media (max-width: 1024px) {
  .footer-inner { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 768px) {
  .footer-inner { grid-template-columns: 1fr; gap: 24px; }
}
</style>
