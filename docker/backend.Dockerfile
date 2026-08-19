# 后端镜像（build context = 项目根，因运行时按 `python -m backend.main` 包结构导入）
# 基础镜像选 3.11-slim：bcrypt==3.2.2 无 cp312 wheel，3.12 需源码编译装 gcc
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先装依赖（独立层，requirements 不变时命中缓存）
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷代码（backend/ 包 + main 入口）
COPY backend/ ./backend/

# 质量看板数据源：quality_api.py 读 ../docs/quality_reports/（相对 backend/ 的上级）
COPY docs/quality_reports/ ./docs/quality_reports/

# 入口脚本：等 MySQL 就绪 → 建表 → 灌种子 → 起 uvicorn
COPY docker/backend-entrypoint.sh /entrypoint.sh
# 防 git autocrlf 把脚本检出成 CRLF 导致 /bin/sh^M 报错
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
