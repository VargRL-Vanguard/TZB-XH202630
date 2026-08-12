"""
PUT /api/user/profile —— 更新学习者画像（**挑战杯核心**，B 学情诊断结果回写入口）。

**鉴权 + 越权规则**（A-02 验收）：
- teacher → 可改任意学生
- admin → 可改任何人
- student → 只能改自己（sub == target）
- 其他 role → 只能改自己

**目标用户判定**：
- 入参含 `userId` 字段 → 改指定用户（仅 teacher/admin 可用）
- 入参不含 `userId` → 默认改自己
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.公共.errors import ForbiddenError, NotFoundError
from backend.公共.response import ok
from backend.公共.logger import get_logger

from backend.a_用户与聊天.user.schemas import UserProfileRequest, UserInfoResponse
from backend.a_用户与聊天.user.deps import get_current_user
from backend.a_用户与聊天.db import get_session, upsert_learner_profile

log = get_logger(__name__)
router = APIRouter()


def _resolve_target_user_id(current: dict, explicit_user_id: Optional[str]) -> str:
    """
    决定要改谁：
    - 显式指定 userId + 当前用户是 teacher/admin → 用显式的
    - 显式指定 userId + 当前用户是 student/其他 → 拒绝（无权改他人）
    - 未指定 userId → 默认改自己
    """
    role = current.get("role")
    self_id = current.get("sub")

    if explicit_user_id is None:
        return self_id

    # 显式指定了 → 必须是 teacher/admin
    if role not in ("teacher", "admin"):
        raise ForbiddenError("无权修改他人画像（仅教师/管理员可指定 userId）")

    return explicit_user_id


@router.put("/profile", response_model=None, summary="更新学习者画像")
async def update_user_profile(
    req: UserProfileRequest,
    userId: Optional[str] = Query(None, description="目标用户 ID（teacher/admin 可指定，student 必须省略）"),
    current: dict = Depends(get_current_user),
) -> dict:
    """
    upsert 画像：不存在则插入，存在则按字段更新（None 字段不动）。

    返回更新后的完整 User + LearnerProfile 合并结果。
    """
    target_user_id = _resolve_target_user_id(current, userId)

    # 1. 确认目标用户存在
    from backend.a_用户与聊天.models.user import User
    async with get_session() as session:
        user = await session.get(User, target_user_id)
        if user is None:
            raise NotFoundError(f"用户 {target_user_id} 不存在")

    # 2. upsert 画像
    result = await upsert_learner_profile(
        target_user_id,
        education=req.education,
        major=req.major,
        theory_test_score=req.theoryTestScore,
        weak_kps=req.weakKPs,
        strong_kps=req.strongKPs,
    )

    # 3. 拼完整响应
    resp = UserInfoResponse(
        userId=target_user_id,
        username=user.username,
        name=user.name,
        role=user.role,
        education=result.get("education"),
        major=result.get("major"),
        theoryTestScore=result.get("theoryTestScore"),
        weakKPs=result.get("weakKPs", []),
        strongKPs=result.get("strongKPs", []),
        profileUpdatedAt=result.get("updatedAt"),
    )

    log.info(
        f"更新画像: caller={current.get('sub')}({current.get('role')}) "
        f"target={target_user_id}"
    )
    return ok(data=resp.model_dump(), message="画像已更新")
