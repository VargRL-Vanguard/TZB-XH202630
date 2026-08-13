"""
A-03 聊天模块路由统一入口。

**路由清单**（全部挂到 /api/chat 前缀）：
- POST /api/chat/send    → send.py
- GET  /api/chat/history → history.py
- GET  /api/chat/list    → list.py
- POST /api/chat/read    → read.py
"""
from fastapi import APIRouter

from backend.a_用户与聊天.chat.send import router as send_router
from backend.a_用户与聊天.chat.history import router as history_router
from backend.a_用户与聊天.chat.list import router as list_router
from backend.a_用户与聊天.chat.read import router as read_router

router = APIRouter()
router.include_router(send_router)
router.include_router(history_router)
router.include_router(list_router)
router.include_router(read_router)

__all__ = ["router"]
