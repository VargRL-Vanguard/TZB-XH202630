#!/bin/sh
# 后端容器入口：等 MySQL → A 区建表+种子 → B/C 建表+种子 → 启动服务
# 种子脚本均幂等（重复执行清旧重灌），容器每次重启都会刷新演示数据
set -e

echo "[entrypoint] 等待 MySQL 就绪..."
until python -m backend.a_用户与聊天.init_db 2>/dev/null; do
  echo "  MySQL 未就绪，3s 后重试..."
  sleep 3
done
echo "[entrypoint] A 区建表完成（MySQL 就绪）"

echo "[entrypoint] 灌入种子数据..."
python -m backend.a_用户与聊天.seed_data && echo "  A 区账号 OK" || echo "  [警告] A 区种子失败"
python -m backend.b_学情数据.seed_data && echo "  B 区学情 OK" || echo "  [警告] B 区种子失败"
python -c "from backend.c_学习内容.db import init_db; init_db()" && echo "  C 区建表 OK" || true
python -m backend.c_学习内容.seed_data && echo "  C 区路径/建议 OK" || echo "  [警告] C 区种子失败"

echo "[entrypoint] 启动 uvicorn :8000"
# workers 固定 1：WS 连接管理器在进程内存，多 worker 会导致消息路由断裂
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1
