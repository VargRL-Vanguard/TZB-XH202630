"""
A-01 鉴权路由统一入口。

**路由清单**：
- POST /api/auth/register  → register.py
- POST /api/auth/login     → login.py
- POST /api/auth/logout    → logout.py

**挂载方式**（在 main.py 里）：
    from backend.a_用户与聊天.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
"""
from fastapi import APIRouter

from backend.a_用户与聊天.auth.register import router as register_router
from backend.a_用户与聊天.auth.login import router as login_router
from backend.a_用户与聊天.auth.logout import router as logout_router

# 父路由（不设 prefix，具体 prefix 在 main.py 里 include_router 时给）
router = APIRouter()

# 子路由（每个文件自带 path="/xxx"）
router.include_router(register_router)
router.include_router(login_router)
router.include_router(logout_router)
