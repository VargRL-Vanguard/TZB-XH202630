"""
B-03 /api/activity/courses 接口：课程类活动列表。

支持 filter=all|in-progress|completed|not-started（4 种单测覆盖）。
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.activity import Activity
from sqlalchemy import select, and_, func

router = APIRouter(tags=["activity-courses"])

_VALID_FILTERS = {"all", "in-progress", "completed", "not-started"}


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


@router.get("/api/activity/courses")
async def list_activity_courses(
    studentId: str = Query(..., min_length=1),
    filter: str = Query("all", description="all|in-progress|completed|not-started"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """GET /api/activity/courses — 课程类活动列表（按进度/状态过滤）。"""
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看")
    if filter not in _VALID_FILTERS:
        from backend.公共.errors import BizError
        raise BizError(f"filter 非法，需为 {sorted(_VALID_FILTERS)}", code=400)

    clauses = [
        Activity.student_id == studentId,
        Activity.activity_type == "course",
    ]
    if filter != "all":
        clauses.append(Activity.status == filter)

    async with get_session() as session:
        stmt = (
            select(Activity)
            .where(and_(*clauses))
            .order_by(Activity.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        acts = result.scalars().all()

        total = await session.scalar(
            select(func.count()).select_from(Activity).where(and_(*clauses))
        ) or 0

    return ok(data={
        "total": int(total),
        "items": [a.to_dict() for a in acts],
    })
