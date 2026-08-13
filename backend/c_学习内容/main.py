"""C 区 FastAPI 应用入口（可独立启动；也可被主应用 include_router）。

启动：
    cd backend
    uvicorn c_学习内容.main:app --reload --port 8003
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.公共.errors import BizError
from backend.公共.response import fail

from .db import init_db
from .routes import router

# 公共/logger 兼容兜底（loguru 未装时降级到标准 logging）
try:
    from backend.公共.logger import get_logger as _public_get_logger
    log = _public_get_logger(__name__)
except Exception:  # pragma: no cover
    log = logging.getLogger(__name__)

# 公共/config 兼容兜底
try:
    from backend.公共.config import settings
except Exception:  # pragma: no cover
    class _Cfg:
        CORS_ORIGINS: list[str] = ["*"]
    settings = _Cfg()


def create_app() -> FastAPI:
    app = FastAPI(
        title="c_学习内容 (C 区)",
        version="0.1.0",
        description="学习路径 + 学习建议 + 领域专家 Agent + 3 种形态资源 + 动态迭代",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.on_event("startup")
    def _startup():
        try:
            init_db()
            log.info("C 区 init_db 完成")
        except Exception as e:  # pragma: no cover
            log.warning(f"C 区 init_db 失败（演示模式继续）: {e}")

    # ---- 全局异常处理（S-01 + 公共/errors 契约）----

    @app.exception_handler(BizError)
    async def biz_error_handler(request: Request, exc: BizError) -> JSONResponse:
        """业务异常 → {code, message, data}（HTTP 状态码对齐 exc.code）"""
        log.warning(f"C 区业务异常: {exc.message} (code={exc.code}) path={request.url.path}")
        return JSONResponse(
            status_code=exc.code,
            content=fail(code=exc.code, message=exc.message, data=exc.data),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """未捕获异常 → 500（**不**暴露堆栈到前端）"""
        log.exception(f"C 区未捕获异常: path={request.url.path}")
        return JSONResponse(
            status_code=500,
            content=fail(code=500, message="服务器内部错误", data={}),
        )

    @app.get("/")
    def root():
        return {
            "code": 200,
            "data": {
                "area": "C",
                "module": "c_学习内容",
                "version": "0.1.0",
                "endpoints": [
                    "/api/learning-path/overview",
                    "/api/learning-path/timeline",
                    "/api/learning-path/modules",
                    "/api/learning-path/tasks",
                    "/api/learning-path/feedback",
                    "/api/suggestions/list",
                    "/api/suggestions/read",
                ],
            },
        }

    return app


app = create_app()
