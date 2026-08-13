"""
B-02 /api/student/knowledge 接口：6 个知识模块进度。

字段名固定（验收标准）：kp_id / kp_name / mastery / status。
mastery ∈ [0,100]，status ∈ mastered / learning / not-started。
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError, NotFoundError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.student import Student

router = APIRouter(tags=["student-knowledge"])

# MVP 阶段默认 6 个知识模块（与 kp_taxonomy.json 根节点对齐）
# 生产环境建议从 kp_taxonomy.json 动态加载一级子节点
_DEFAULT_KNOWLEDGE_MODULES: list[dict] = [
    {"kp_id": "kp01", "kp_name": "工业机器人基础", "mastery": 0, "status": "not-started"},
    {"kp_id": "kp02", "kp_name": "工业机器人坐标系", "mastery": 0, "status": "not-started"},
    {"kp_id": "kp03", "kp_name": "PLC 编程基础", "mastery": 0, "status": "not-started"},
    {"kp_id": "kp04", "kp_name": "传感器与检测技术", "mastery": 0, "status": "not-started"},
    {"kp_id": "kp05", "kp_name": "工业互联网通信", "mastery": 0, "status": "not-started"},
    {"kp_id": "kp06", "kp_name": "智能制造系统集成", "mastery": 0, "status": "not-started"},
]


def _can_view(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


def _status_from_mastery(mastery: float) -> str:
    if mastery >= 80:
        return "mastered"
    if mastery > 0:
        return "learning"
    return "not-started"


async def _get_student_knowledge(student_id: str) -> list[dict]:
    """
    模块级内部函数：返回 6 个知识模块进度列表。
    B-04 快照复用。
    """
    # 从 B 区 activities 聚合每个 kp 的掌握度
    # MVP：如果 Activity 里没有该学生数据，返回默认 + _isMock
    from sqlalchemy import select, func
    from backend.b_学情数据.models.activity import Activity

    async with get_session() as session:
        stmt = (
            select(Activity)
            .where(Activity.student_id == student_id)
        )
        result = await session.execute(stmt)
        acts = result.scalars().all()

    # 统计每个 kp_id 的累计得分 / 参与次数
    kp_stats: dict[str, dict] = {}
    for a in acts:
        for kp in (a.kp_tags or []):
            s = kp_stats.setdefault(kp, {"score_sum": 0.0, "count": 0})
            if a.score is not None:
                s["score_sum"] += a.score
                s["count"] += 1

    # 合并默认模块
    out: list[dict] = []
    all_mock = len(acts) == 0
    for m in _DEFAULT_KNOWLEDGE_MODULES:
        kp_id = m["kp_id"]
        if kp_id in kp_stats and kp_stats[kp_id]["count"] > 0:
            mastery = round(kp_stats[kp_id]["score_sum"] / kp_stats[kp_id]["count"], 1)
            mastery = max(0.0, min(100.0, mastery))
            all_mock = False
        else:
            mastery = m["mastery"]
        out.append({
            "kp_id": kp_id,
            "kp_name": m["kp_name"],
            "mastery": mastery,
            "status": _status_from_mastery(mastery),
        })

    if all_mock:
        for o in out:
            o["_isMock"] = True
    return out


@router.get("/api/student/knowledge")
async def get_student_knowledge(
    studentId: str = Query(..., min_length=1, description="学生ID"),
    user: dict = Depends(get_current_user),
):
    """GET /api/student/knowledge?studentId=xxx — 知识模块掌握度。"""
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看")

    async with get_session() as session:
        stu = await session.get(Student, studentId)
        if stu is None:
            raise NotFoundError(f"学生 {studentId} 不存在")

    klist = await _get_student_knowledge(studentId)
    # 字段名固定校验
    for k in klist:
        assert {"kp_id", "kp_name", "mastery", "status"}.issubset(k.keys()), (
            "knowledge 字段名与契约不一致"
        )
    return ok(data=klist)
