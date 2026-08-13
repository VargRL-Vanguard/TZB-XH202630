"""
B 区路由注册入口：把所有 student / activity 子路由汇总。
"""
from fastapi import APIRouter

from backend.b_学情数据.student.info import router as student_info_router
from backend.b_学情数据.student.metrics import router as student_metrics_router
from backend.b_学情数据.student.dimensions import router as student_dimensions_router
from backend.b_学情数据.student.behavior import router as student_behavior_router
from backend.b_学情数据.student.knowledge import router as student_knowledge_router
from backend.b_学情数据.activity.stats import router as activity_stats_router
from backend.b_学情数据.activity.courses import router as activity_courses_router
from backend.b_学情数据.activity.recent import router as activity_recent_router
from backend.b_学情数据.activity.calendar import router as activity_calendar_router
from backend.b_学情数据.activity.record import router as activity_record_router

router = APIRouter()
router.include_router(student_info_router)
router.include_router(student_metrics_router)
router.include_router(student_dimensions_router)
router.include_router(student_behavior_router)
router.include_router(student_knowledge_router)
router.include_router(activity_stats_router)
router.include_router(activity_courses_router)
router.include_router(activity_recent_router)
router.include_router(activity_calendar_router)
router.include_router(activity_record_router)

__all__ = ["router"]
