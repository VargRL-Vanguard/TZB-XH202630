"""GET /api/learning-path/tasks"""
from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.response import ok

from .service import get_tasks

router = APIRouter()


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


@router.get("/tasks")
def tasks(
    studentId: str = Query(..., alias="studentId", min_length=1),
    user: dict = Depends(get_current_user),
):
    if not _can_view(user, studentId):
        from backend.公共.errors import ForbiddenError
        raise ForbiddenError("无权查看该学生的任务（需要本人/教师/管理员）")
    return ok(data=get_tasks(studentId))
