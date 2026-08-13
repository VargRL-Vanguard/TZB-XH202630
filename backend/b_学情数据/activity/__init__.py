"""
activity 包 __init__：暴露 B-04 get_recent_activities 给 D（AI 集成）调用。

D 区调用方式：
    from backend.b_学情数据.activity import get_recent_activities
    activities = get_recent_activities("s001", days=7)
    # 返回：最近 N 天活动，按时间倒序
"""
from typing import Optional

from backend.b_学情数据.activity.recent import _list_recent_activities


async def get_recent_activities(
    student_id: str,
    days: int = 7,
    limit: int = 50,
) -> list[dict]:
    """
    B-04 聚合：最近 N 天学习活动列表（按时间倒序）。

    纯只读。
    :param student_id: 学生 ID
    :param days: 最近 N 天（默认 7）
    :param limit: 返回条数上限（默认 50）
    :return: list[activity_dict]，按 created_at DESC；无数据返回 []
    """
    return await _list_recent_activities(student_id, days=days, limit=limit)


__all__ = ["get_recent_activities"]
