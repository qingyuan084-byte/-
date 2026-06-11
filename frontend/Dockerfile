# ========================================================
# CinéMatic 前端 Dockerfile — 多阶段构建
# ========================================================
# Stage 1: Node 构建 Vue 应用
# Stage 2: Nginx 提供静态文件 + API 代理
# ========================================================

# ── Stage 1: 构建 ────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# 利用 Docker 层缓存：先复制依赖文件
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码并构建
COPY . .
RUN npm run build

# ── Stage 2: 运行时 ──────────────────────────────────
FROM nginx:alpine

# 替换默认 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
