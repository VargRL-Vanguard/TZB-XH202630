"""
FastAPI 启动入口：把 A-01 鉴权 + A-04 WebSocket 全部挂上。

**启动命令**：
    cd D:\\TZB\\TZB-XH202630
    python -m backend.main
    # 或
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.公共.config import settings
from backend.公共.errors import BizError, AuthError
from backend.公共.response import fail
from backend.公共.logger import get_logger

# 路由
from backend.a_用户与聊天.auth.router import router as auth_router
from backend.a_用户与聊天.user.router import router as user_router
from backend.a_用户与聊天.chat import router as chat_router
from backend.a_用户与聊天.ws.server import router as ws_router, heartbeat_cleanup_task

# B/C/D 区路由（四区合一启动：前端 8000 端口一次拉通全部接口）
from backend.b_学情数据.routes import router as b_router
from backend.c_学习内容.routes import router as c_router
from backend.d_AI集成.routes import router as d_router
from backend.公共.quality_api import router as quality_router

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期：
    - 启动时启动后台心跳清理任务
    - 关闭时自动取消
    """
    log.info(f"🚀 启动 A 区服务: ENV={settings.ENV} PORT={settings.PORT}")
    cleanup_task = asyncio.create_task(heartbeat_cleanup_task(interval=60))
    log.info("✅ 心跳清理后台任务已启动 (60s 间隔)")

    # B/C/D 区幂等建表（失败不阻塞启动，降级为该区接口报错）
    try:
        from backend.b_学情数据.db import create_all_tables as b_init
        await b_init()
        log.info("✅ B 区建表完成")
    except Exception as e:  # noqa: BLE001
        log.warning(f"B 区建表失败（接口将报错）: {e}")
    try:
        from backend.c_学习内容.db import init_db as c_init
        c_init()
        log.info("✅ C 区建表完成")
    except Exception as e:  # noqa: BLE001
        log.warning(f"C 区建表失败（接口将报错）: {e}")
    try:
        from backend.d_AI集成.db import create_all_tables as d_init
        await d_init()
        log.info("✅ D 区建表完成")
    except Exception as e:  # noqa: BLE001
        log.warning(f"D 区建表失败（接口将报错）: {e}")

    yield
    # 关闭时
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    log.info("🛑 A 区服务已关闭")


# ========== 创建 app ==========

app = FastAPI(
    title="TZB 后端 - A 区（用户与聊天 + WebSocket）",
    description="挑战杯 XH-202630 项目后端 - 成员 A 负责",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 注册路由 ==========

# A-01 鉴权 3 接口（/api/auth/register, /api/auth/login, /api/auth/logout）
app.include_router(auth_router, prefix="/api/auth", tags=["A-01 鉴权"])

# A-02 用户信息 + 学习者画像（/api/user/info, /api/user/profile）
app.include_router(user_router, prefix="/api/user", tags=["A-02 用户/画像"])

# A-03 聊天消息（/api/chat/send, /api/chat/history, /api/chat/list, /api/chat/read）
app.include_router(chat_router, prefix="/api/chat", tags=["A-03 聊天消息"])

# A-04 WebSocket（/ws）
app.include_router(ws_router, tags=["A-04 WebSocket"])

# B 区学情数据（/api/student/* /api/activity/*）
app.include_router(b_router, tags=["B-学情数据"])

# C 区学习内容（/api/learning-path/* /api/suggestions/*）
app.include_router(c_router, tags=["C-学习内容"])

# D 区 AI 集成（/api/ai-chat/* /api/ai/trace/* /api/ai/visualization/*）
app.include_router(d_router, tags=["D-AI集成"])

# 质量看板（/api/quality/latest）
app.include_router(quality_router, tags=["质量看板"])


# ========== 统一异常处理 ==========

@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError) -> JSONResponse:
    """业务异常 → {code, message, data}"""
    log.warning(f"业务异常: {exc.message} (code={exc.code}) path={request.url.path}")
    return JSONResponse(
        status_code=exc.code,
        content=fail(code=exc.code, message=exc.message, data=exc.data),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """未捕获异常 → 500（**不**暴露堆栈到前端）"""
    log.exception(f"未捕获异常: path={request.url.path}")
    return JSONResponse(
        status_code=500,
        content=fail(code=500, message="服务器内部错误", data={}),
    )


# ========== 根路径 / 健康检查 ==========

@app.get("/", summary="根路径")
async def root() -> dict:
    return {
        "code": 200,
        "message": "TZB 后端 A 区运行中",
        "data": {
            "service": "A-用户与聊天",
            "endpoints": [
            "POST /api/auth/register",
            "POST /api/auth/login",
            "POST /api/auth/logout",
            "GET  /api/user/info",
            "PUT  /api/user/profile",
            "POST /api/chat/send",
            "GET  /api/chat/history",
            "GET  /api/chat/list",
            "POST /api/chat/read",
            "WS   /ws?token=xxx",
            "GET  /health",
        ],
        },
    }


@app.get("/health", summary="健康检查")
async def health() -> dict:
    """健康检查：含数据库连接 + WS 连接状态。"""
    from backend.a_用户与聊天.db import engine
    from backend.a_用户与聊天.ws.manager import connection_manager
    from sqlalchemy import text

    # 测 DB
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:
        log.warning(f"健康检查 DB 失败: {e}")

    return {
        "code": 200 if db_ok else 503,
        "message": "ok" if db_ok else "db down",
        "data": {
            "db": "up" if db_ok else "down",
            "ws": connection_manager.stats(),
        },
    }


# ========== 启动 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=(settings.ENV == "dev"),
    )
