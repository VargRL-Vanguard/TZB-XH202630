"""
B-03 /api/activity/recent 接口：最近 N 条活动（按时间倒序）。

供 B-04 get_recent_activities 直接复用内部函数。
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.activity import Activity
from sqlalchemy import select, and_

router = APIRouter(tags=["activity-recent"])


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


async def _list_recent_activities(
    student_id: str,
    days: int = 7,
    limit: int = 50,
) -> list[dict]:
    """
    模块级内部函数：返回最近 N 天的活动列表（按时间倒序）。
    B-04 get_recent_activities 直接调用这个，保持 HTTP 与 D-03 调用一致。
    """
    from datetime import datetime, timedelta
    start_dt = datetime.now() - timedelta(days=max(0, days - 1))

    async with get_session() as session:
        stmt = (
            select(Activity)
            .where(and_(
                Activity.student_id == student_id,
                Activity.created_at >= start_dt,
            ))
            .order_by(Activity.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        acts = result.scalars().all()
    return [a.to_dict() for a in acts]


@router.get("/api/activity/recent")
async def get_recent_activities_api(
    studentId: str = Query(..., min_length=1),
    days: int = Query(7, ge=1, le=365, description="最近 N 天"),
    limit: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """GET /api/activity/recent?studentId=xxx&days=7 — 最近活动。"""
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看")

    items = await _list_recent_activities(studentId, days=days, limit=limit)
    return ok(data={"count": len(items), "items": items})
