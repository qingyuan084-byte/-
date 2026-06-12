#!/bin/bash
# ========================================================
# CinéMatic Railway 启动脚本
# ========================================================
set -e

echo "[Railway] 启动 CinéMatic..."

# 1) 用 envsubst 替换 nginx 配置中的 ${PORT}
if [ -z "$PORT" ]; then
    PORT=80
fi
echo "[Railway] PORT=$PORT"

envsubst '$PORT' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# 2) 启动后端 (Uvicorn, 内部 8002)
echo "[Railway] 启动后端..."
cd /app
python backend/app.py &
BACKEND_PID=$!

# 3) 启动 Nginx (前台运行)
echo "[Railway] 启动 Nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

# 等待任一进程退出
wait -n $BACKEND_PID $NGINX_PID
