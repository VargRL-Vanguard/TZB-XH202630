"""
analytics/aggregator.py：周 / 月 / 学期 行为数据聚合器（B-02）。

核心函数：
  aggregate_behavior(student_id, period) -> dict

行为数据缺失时按 0 填充，并加 `_isMock: true` 标注。
"""
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import select, and_, func

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.activity import Activity

Period = Literal["week", "month", "semester"]


def _period_range(period: Period, now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now or datetime.now()
    if period == "week":
        start = now - timedelta(days=6)
        return start.replace(hour=0, minute=0, second=0, microsecond=0), now
    if period == "month":
        start = now - timedelta(days=29)
        return start.replace(hour=0, minute=0, second=0, microsecond=0), now
    if period == "semester":
        # 学期：按 16 周近似
        start = now - timedelta(days=16 * 7 - 1)
        return start.replace(hour=0, minute=0, second=0, microsecond=0), now
    raise ValueError(f"unknown period: {period}")


async def aggregate_behavior(
    student_id: str,
    period: Period,
    now: datetime | None = None,
) -> dict:
    """
    按周期聚合行为数据。

    返回：
    {
      "period": "week",
      "startDate": "2026-08-07",
      "endDate": "2026-08-13",
      "totalStudyMinutes": 1234,  # 累计学习时长（分钟）
      "activityCount": 15,         # 活动次数
      "completedCount": 8,         # 完成次数
      "avgScore": 76.0,            # 平均得分（可 null）
      "activityTypeBreakdown": {
        "course": 10, "exercise": 3, "test": 2, "discussion": 0
      },
      "dailySeries": [
        {"date": "2026-08-07", "minutes": 120, "count": 2},
        ...
      ],
      "_isMock": true / false      # 数据缺失时 true
    }
    """
    start_dt, end_dt = _period_range(period, now=now)

    async with get_session() as session:
        stmt = select(Activity).where(and_(
            Activity.student_id == student_id,
            Activity.start_time >= start_dt,
            Activity.start_time <= end_dt,
        ))
        result = await session.execute(stmt)
        acts = list(result.scalars().all())

    is_mock = len(acts) == 0

    # 累计指标
    total_minutes = sum(a.duration_minutes or 0 for a in acts)
    activity_count = len(acts)
    completed_count = sum(1 for a in acts if a.status == "completed")
    scores = [a.score for a in acts if a.score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # 按类型分解
    breakdown = {"course": 0, "exercise": 0, "test": 0, "discussion": 0, "other": 0}
    for a in acts:
        t = a.activity_type or "other"
        breakdown[t] = breakdown.get(t, 0) + 1

    # 每天序列
    daily: dict[str, dict] = {}
    # 先把周期内所有天补 0
    cursor = start_dt
    while cursor.date() <= end_dt.date():
        ds = cursor.date().isoformat()
        daily[ds] = {"date": ds, "minutes": 0, "count": 0}
        cursor += timedelta(days=1)
    for a in acts:
        if a.start_time is None:
            continue
        ds = a.start_time.date().isoformat()
        if ds not in daily:
            daily[ds] = {"date": ds, "minutes": 0, "count": 0}
        daily[ds]["minutes"] += a.duration_minutes or 0
        daily[ds]["count"] += 1
    daily_series = [daily[k] for k in sorted(daily.keys())]

    return {
        "period": period,
        "startDate": start_dt.date().isoformat(),
        "endDate": end_dt.date().isoformat(),
        "totalStudyMinutes": total_minutes,
        "activityCount": activity_count,
        "completedCount": completed_count,
        "avgScore": avg_score,
        "activityTypeBreakdown": breakdown,
        "dailySeries": daily_series,
        "_isMock": is_mock,
    }
