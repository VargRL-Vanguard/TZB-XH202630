"""
B-03 /api/activity/calendar 接口：一周内每天活动数/时长日历。

一周内每天一条，无数据补 0。
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.activity import Activity
from sqlalchemy import select, and_, func

router = APIRouter(tags=["activity-calendar"])


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


@router.get("/api/activity/calendar")
async def get_activity_calendar(
    studentId: str = Query(..., min_length=1),
    days: int = Query(7, ge=1, le=31, description="日历天数（默认一周）"),
    user: dict = Depends(get_current_user),
):
    """GET /api/activity/calendar — 每日活动数/时长（无数据补 0）。"""
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看")

    now = datetime.now()
    start_dt = (now - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # 生成天 -> 占位
    daily: dict[str, dict] = {}
    cursor = start_dt
    while cursor.date() <= now.date():
        ds = cursor.date().isoformat()
        daily[ds] = {"date": ds, "count": 0, "minutes": 0}
        cursor += timedelta(days=1)

    # 查这段区间的活动
    async with get_session() as session:
        stmt = select(Activity).where(and_(
            Activity.student_id == studentId,
            Activity.created_at >= start_dt,
        ))
        result = await session.execute(stmt)
        acts = list(result.scalars().all())

    for a in acts:
        ds = a.created_at.date().isoformat()
        if ds in daily:
            daily[ds]["count"] += 1
            daily[ds]["minutes"] += a.duration_minutes or 0

    items = [daily[k] for k in sorted(daily.keys())]
    return ok(data={"days": days, "items": items})
