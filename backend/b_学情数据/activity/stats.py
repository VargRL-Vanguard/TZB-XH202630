"""
B-03 /api/activity/stats 接口：学习活动统计总览。

返回：总活动数、已完成数、平均进度、累计时长、累计得分均值等。
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.activity import Activity
from sqlalchemy import select, and_, func

router = APIRouter(tags=["activity-stats"])


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


@router.get("/api/activity/stats")
async def get_activity_stats(
    studentId: str = Query(..., min_length=1, description="学生ID"),
    user: dict = Depends(get_current_user),
):
    """GET /api/activity/stats?studentId=xxx — 活动统计总览。"""
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看")

    async with get_session() as session:
        # 总数
        total = await session.scalar(
            select(func.count()).select_from(Activity).where(
                Activity.student_id == studentId
            )
        ) or 0
        # 已完成
        completed = await session.scalar(
            select(func.count()).select_from(Activity).where(and_(
                Activity.student_id == studentId,
                Activity.status == "completed",
            ))
        ) or 0
        # 进度均值
        avg_prog = await session.scalar(
            select(func.avg(Activity.progress)).select_from(Activity).where(
                Activity.student_id == studentId
            )
        ) or 0.0
        # 累计时长
        total_minutes = await session.scalar(
            select(func.sum(Activity.duration_minutes)).select_from(Activity).where(
                Activity.student_id == studentId
            )
        ) or 0
        # 得分均值（排除 null）
        avg_score = await session.scalar(
            select(func.avg(Activity.score)).select_from(Activity).where(and_(
                Activity.student_id == studentId,
                Activity.score != None,  # noqa: E711
            ))
        )

    return ok(data={
        "totalActivities": int(total),
        "completedActivities": int(completed),
        "completionRate": round(completed / total, 4) if total else 0.0,
        "avgProgress": round(float(avg_prog), 2),
        "totalStudyMinutes": int(total_minutes or 0),
        "avgScore": round(float(avg_score), 2) if avg_score is not None else None,
    })
