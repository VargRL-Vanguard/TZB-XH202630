"""GET /api/learning-path/timeline?status=completed|current|pending|all"""
from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.response import ok

from .service import get_timeline

router = APIRouter()

ALLOWED_STATUS = {"completed", "current", "pending", "all", ""}


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


@router.get("/timeline")
def timeline(
    studentId: str = Query(..., alias="studentId", min_length=1),
    status: str = Query("all"),
    user: dict = Depends(get_current_user),
):
    if not _can_view(user, studentId):
        from backend.公共.errors import ForbiddenError
        raise ForbiddenError("无权查看该学生的时间线（需要本人/教师/管理员）")
    if status not in ALLOWED_STATUS:
        status = "all"
    return ok(data=get_timeline(studentId, status or None))
