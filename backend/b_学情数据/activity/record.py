"""
B-03 /api/activity/record 接口：写入一条学习活动记录。

接收完整 payload，写入 Activity 表，返回新 activity_id。
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import ForbiddenError
from backend.公共.response import ok

from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.activity import Activity

router = APIRouter(tags=["activity-record"])


class ActivityRecordReq(BaseModel):
    """record 入参契约。"""
    studentId: str = Field(..., min_length=1)
    activityType: str = Field(default="other", pattern="^(course|exercise|test|discussion|other)$")
    resourceId: str = Field(default="")
    resourceName: str = Field(default="")
    resourceType: str = Field(default="")
    status: str = Field(default="not-started", pattern="^(not-started|in-progress|completed)$")
    progress: float = Field(default=0.0, ge=0, le=100)
    score: Optional[float] = Field(default=None, ge=0, le=100)
    startTime: Optional[str] = Field(default=None, description="ISO8601 字符串")
    endTime: Optional[str] = Field(default=None)
    durationMinutes: int = Field(default=0, ge=0)
    kpTags: list[str] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)


def _can_write(current_user: dict, target_student_id: str) -> bool:
    """
    写入规则：
    - student：只能写自己
    - teacher / admin：可写任意（代录）
    """
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


@router.post("/api/activity/record")
async def record_activity(
    req: ActivityRecordReq,
    user: dict = Depends(get_current_user),
):
    """POST /api/activity/record — 写入学习活动记录。"""
    if not _can_write(user, req.studentId):
        raise ForbiddenError("无权写入该学生的活动记录")

    aid = f"a-{uuid.uuid4().hex[:12]}"
    act = Activity(
        activity_id=aid,
        student_id=req.studentId,
        activity_type=req.activityType,
        resource_id=req.resourceId,
        resource_name=req.resourceName,
        resource_type=req.resourceType,
        status=req.status,
        progress=req.progress,
        score=req.score,
        start_time=_parse_iso(req.startTime),
        end_time=_parse_iso(req.endTime),
        duration_minutes=req.durationMinutes,
        kp_tags=req.kpTags or [],
        extra=req.extra or {},
    )
    async with get_session() as session:
        session.add(act)

    return ok(data={"activityId": aid}, message="活动记录已写入")
