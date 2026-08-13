"""
student 包 __init__：暴露 B-04 get_student_snapshot 给 D（AI 集成）调用。

D 区调用方式（协作协议 B_C_D 对接契约）：
    from backend.b_学情数据.student import get_student_snapshot
    snapshot = get_student_snapshot("s001")
    # 返回 info + metrics + dimensions + knowledge 合并结果
"""
from typing import Optional


async def get_student_snapshot(student_id: str) -> Optional[dict]:
    """
    B-04 聚合快照：一次拿到学生画像全量（info+metrics+dimensions+knowledge）。

    纯只读：不写库，不触发 side effect。
    返回 dict 结构：
    {
      "studentId": str,
      "name": str,
      "learnerProfile": { education, major, theoryTestScore, weakKPs[], strongKPs[] },
      "metrics": { studyHours, completionRate, avgScore, trend, trendValue },
      "dimensions": { comprehension, application, analysis, evaluation, creation, collaboration },
      "knowledge": [ { kp_id, kp_name, mastery, status, _isMock? } ... ]
    }
    查不到（studentId 不存在）返回 None。
    """
    from backend.b_学情数据.student.info import _get_student_info_raw
    from backend.b_学情数据.student.knowledge import _get_student_knowledge

    info = await _get_student_info_raw(student_id)
    if info is None:
        return None

    knowledge = await _get_student_knowledge(student_id)

    return {
        "studentId": info["studentId"],
        "name": info["name"],
        "learnerProfile": info["learnerProfile"],
        "metrics": info["metrics"],
        "dimensions": info["_dimensions"],  # 内部字段转正
        "knowledge": knowledge,
    }


__all__ = ["get_student_snapshot"]
