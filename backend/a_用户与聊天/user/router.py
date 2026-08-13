"""
A-02 用户信息 + 画像路由统一入口。

**路由清单**：
- GET  /api/user/info     → info.py
- PUT  /api/user/profile  → profile.py

**挂载方式**（在 main.py 里）：
    from backend.a_用户与聊天.user.router import router as user_router
    app.include_router(user_router, prefix="/api/user", tags=["A-02 用户/画像"])
"""
from fastapi import APIRouter

from backend.a_用户与聊天.user.info import router as info_router
from backend.a_用户与聊天.user.profile import router as profile_router

router = APIRouter()
router.include_router(info_router)
router.include_router(profile_router)
