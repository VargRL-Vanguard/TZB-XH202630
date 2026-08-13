"""
B-01 /api/student/metrics 接口：核心指标 5 字段。

返回契约（任务清单 B-01 §验收标准）：
  studyHours / completionRate / avgScore / trend / trendValue
字段名与 B-04 快照严格一致。

鉴权：同 info，仅本人 / 教师 / admin 可看。
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError, NotFoundError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.student import Student

router = APIRouter(tags=["student-metrics"])


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


async def _get_student_metrics(student_id: str) -> dict | None:
    """
    模块级内部函数：返回核心指标 dict 或 None。
    B-01 HTTP 接口 + info.py 聚合 + B-04 快照都用这个，避免重复实现。
    """
    async with get_session() as session:
        stu = await session.get(Student, student_id)
        if stu is None:
            return None
        return stu.to_metrics_dict()


@router.get("/api/student/metrics")
async def get_student_metrics(
    studentId: str = Query(..., min_length=1, description="学生ID"),
    user: dict = Depends(get_current_user),
):
    """GET /api/student/metrics?studentId=xxx — 核心指标。"""
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看该学生指标（需要本人/教师/管理员）")

    metrics = await _get_student_metrics(studentId)
    if metrics is None:
        raise NotFoundError(f"学生 {studentId} 不存在")

    return ok(data=metrics)
