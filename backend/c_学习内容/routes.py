"""C 区 FastAPI 路由汇总。"""
from __future__ import annotations

from fastapi import APIRouter

from .learning_path import (
    feedback as lp_feedback,
    modules as lp_modules,
    overview as lp_overview,
    tasks as lp_tasks,
    timeline as lp_timeline,
)
from .suggestions import list as sg_list, read as sg_read

router = APIRouter()

# 学习路径（5 个非 AI + feedback）
router.include_router(lp_overview.router, prefix="/api/learning-path", tags=["learning-path"])
router.include_router(lp_timeline.router, prefix="/api/learning-path", tags=["learning-path"])
router.include_router(lp_modules.router, prefix="/api/learning-path", tags=["learning-path"])
router.include_router(lp_tasks.router, prefix="/api/learning-path", tags=["learning-path"])
router.include_router(lp_feedback.router, prefix="/api/learning-path", tags=["learning-path"])

# 学习建议（2 个）
router.include_router(sg_list.router, prefix="/api/suggestions", tags=["suggestions"])
router.include_router(sg_read.router, prefix="/api/suggestions", tags=["suggestions"])
