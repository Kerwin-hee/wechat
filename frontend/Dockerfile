# 前端生产镜像（Vue 3 + Vite → Nginx）
FROM node:22-alpine AS builder

WORKDIR /app

# 安装 pnpm（可选，用 npm 也行）
RUN npm install -g pnpm

# 复制依赖配置（利用缓存）
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码
COPY . .

# 构建生产包
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ========== 生产 Nginx 镜像 ==========
FROM nginx:alpine

# 复制 Nginx 配置
COPY frontend/docker/nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 健康检查（BusyBox wget 语法）
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
