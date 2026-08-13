"""
B-02 /api/student/behavior 接口：行为数据聚合（周/月/学期）。

支持 period=week|month|semester；
数据缺失时按 0 填充，并加 `_isMock: true` 标注（MVP 阶段允许 mock）。
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError, NotFoundError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.student import Student
from backend.b_学情数据.analytics.aggregator import aggregate_behavior

router = APIRouter(tags=["student-behavior"])


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


@router.get("/api/student/behavior")
async def get_student_behavior(
    studentId: str = Query(..., min_length=1, description="学生ID"),
    period: str = Query("week", pattern="^(week|month|semester)$", description="周期"),
    user: dict = Depends(get_current_user),
):
    """GET /api/student/behavior?studentId=xxx&period=week|month|semester。"""
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看")

    # 先确认学生存在
    async with get_session() as session:
        stu = await session.get(Student, studentId)
        if stu is None:
            raise NotFoundError(f"学生 {studentId} 不存在")

    result = await aggregate_behavior(student_id=studentId, period=period)
    return ok(data=result)
