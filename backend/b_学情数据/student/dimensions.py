"""
B-02 /api/student/dimensions 接口：6 维能力雷达。

字段名固定（验收标准）：
  comprehension / application / analysis / evaluation / creation / collaboration
每个 0-100 整数。
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError, NotFoundError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.student import Student

router = APIRouter(tags=["student-dimensions"])


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


async def _get_student_dimensions(student_id: str) -> dict | None:
    """
    模块级内部函数：返回 6 维雷达 dict 或 None。
    B-04 快照复用。
    """
    async with get_session() as session:
        stu = await session.get(Student, student_id)
        if stu is None:
            return None
        return stu.to_dimensions_dict()


@router.get("/api/student/dimensions")
async def get_student_dimensions(
    studentId: str = Query(..., min_length=1, description="学生ID"),
    user: dict = Depends(get_current_user),
):
    """GET /api/student/dimensions?studentId=xxx — 6 维能力雷达。"""
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看")

    dims = await _get_student_dimensions(studentId)
    if dims is None:
        raise NotFoundError(f"学生 {studentId} 不存在")

    # 字段名固定校验
    expected = {"comprehension", "application", "analysis",
                "evaluation", "creation", "collaboration"}
    assert set(dims.keys()) == expected, "6 维字段名与契约不一致"
    return ok(data=dims)
