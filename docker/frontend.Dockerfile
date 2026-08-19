# 前端镜像：node 构建 → nginx 托管（同源反代 API/WS，浏览器只看到一个域名，无 CORS）
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# VITE_API_BASE=/ → 构建期注入同源相对路径；ws/client.ts 对空 base 有 location.origin 兜底
ARG VITE_API_BASE=/
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# ---- 运行阶段 ----
FROM nginx:alpine
# 注意：nginx.conf 必须在 frontend/ context 内（frontend/nginx.conf），COPY 不能跨 context
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
