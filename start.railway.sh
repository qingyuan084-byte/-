#!/bin/bash
# ========================================================
# CinéMatic Railway 启动脚本
# ========================================================
set -e

echo "[Railway] 启动 CinéMatic..."

# 首次部署：将初始数据从镜像复制到持久化卷
if [ ! -f /app/data/.persisted ]; then
    echo "[Railway] 首次部署 — 初始化数据到持久化卷..."
    cp -rn /app/data-init/* /app/data/
    touch /app/data/.persisted
    echo "[Railway] 数据初始化完成"
else
    echo "[Railway] 检测到已有持久化数据，跳过初始化"
fi

# 确保必要的目录存在
mkdir -p /var/log/nginx /var/lib/nginx /run/nginx
echo "[Railway] Nginx 目录已创建"

# 用 envsubst 替换 nginx 配置中的 $PORT
if [ -z "$PORT" ]; then
    PORT=80
fi
echo "[Railway] PORT=$PORT"

envsubst '$PORT' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
echo "[Railway] Nginx 配置已生成:"
head -5 /etc/nginx/conf.d/default.conf

# 测试 nginx 配置
nginx -t

# 启动后端 (Uvicorn, 后台运行)
echo "[Railway] 启动后端..."
cd /app
python backend/app.py &
BACKEND_PID=$!

# Nginx 前台运行 (exec 替换当前进程，容器由 nginx 保活)
echo "[Railway] 启动 Nginx (前台)..."
exec nginx -g "daemon off;"
