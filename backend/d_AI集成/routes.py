"""
D 区路由聚合入口：供 backend/main.py 统一挂载（四区合一启动）。
"""
from fastapi import APIRouter

from backend.d_AI集成.api.ai_chat import router as ai_chat_router
from backend.d_AI集成.api.trace import router as trace_router
from backend.d_AI集成.api.visualization import router as visualization_router

router = APIRouter()
router.include_router(ai_chat_router)
router.include_router(trace_router)
router.include_router(visualization_router)

__all__ = ["router"]
