import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8002",
        changeOrigin: true,
        timeout: 120000,        // AI 问答响应可能需 5-30 秒
        proxyTimeout: 120000,
      },
    },
  },
});
