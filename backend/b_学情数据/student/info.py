"""
B-01 /api/student/info 接口：学生基本信息 + learnerProfile。

返回契约（任务清单 B-01 接口契约 + api-doc §2.1）：
{
  "studentId": "s001",
  "name": "张三",
  "learnerProfile": {
    "education": "本科",
    "major": "智能制造",
    "theoryTestScore": 78,
    "weakKPs": ["kp12", "kp15"],
    "strongKPs": ["kp03"]
  },
  "metrics": {...}  # 复用 metrics.py 的结果，方便 B-04 快照直接复用
}

鉴权：仅本人 / 教师 / admin 可看（student 看自己，teacher/admin 看任意）
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError, NotFoundError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.student import Student
from backend.b_学情数据.student.metrics import _get_student_metrics  # 复用

router = APIRouter(tags=["student-info"])


def _can_view(current_user: dict, target_student_id: str) -> bool:
    """
    越权规则（与 A-02 /api/user/info 对齐）：
    - student：只能看自己
    - teacher / admin：可看任意
    """
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


async def _get_student_info_raw(student_id: str) -> Optional[dict]:
    """
    模块级内部函数：查 B 区 Student 表 + A 区 learner_profile 合并。
    返回 info+metrics+learnerProfile 的完整 dict，或 None（studentId 不存在）。

    给 B-04 get_student_snapshot 直接复用，避免重复查库。
    """
    # 1) 查 B 区 Student
    async with get_session() as session:
        stu = await session.get(Student, student_id)
        if stu is None:
            return None
        info = stu.to_info_dict()
        metrics = stu.to_metrics_dict()
        dims = stu.to_dimensions_dict()

    # 2) 查 A 区 learner_profile（可能 None）
    a_profile: Optional[dict] = None
    try:
        from backend.a_用户与聊天 import get_learner_profile as _a_get_lp
        a_profile = await _a_get_lp(student_id)
    except Exception:
        # A 区 DB 不可用时，给空占位，保证 B 区接口单点可用
        a_profile = None

    learner_profile = {
        "education": (a_profile or {}).get("education", ""),
        "major": (a_profile or {}).get("major", ""),
        "theoryTestScore": (a_profile or {}).get("theoryTestScore"),
        "weakKPs": (a_profile or {}).get("weakKPs") or [],
        "strongKPs": (a_profile or {}).get("strongKPs") or [],
    }

    return {
        **info,
        "learnerProfile": learner_profile,
        "metrics": metrics,
        "_dimensions": dims,  # 内部用：B-04 快照需要，HTTP 响应不直接暴露
    }


@router.get("/api/student/info")
async def get_student_info(
    studentId: str = Query(..., min_length=1, description="学生ID"),
    user: dict = Depends(get_current_user),
):
    """GET /api/student/info?studentId=xxx — 学生基本信息 + learnerProfile。"""
    # 1) 越权校验
    if not _can_view(user, studentId):
        raise ForbiddenError("无权查看该学生信息（需要本人/教师/管理员）")

    # 2) 查数据
    raw = await _get_student_info_raw(studentId)
    if raw is None:
        raise NotFoundError(f"学生 {studentId} 不存在")

    # 3) 去掉内部字段，返回契约定义的字段
    resp = {
        "studentId": raw["studentId"],
        "name": raw["name"],
        "learnerProfile": raw["learnerProfile"],
        "metrics": raw["metrics"],
    }
    return ok(data=resp)
