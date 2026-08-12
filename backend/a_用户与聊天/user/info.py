"""
GET /api/user/info —— 读用户信息（含 LearnerProfile 合并结果）。

**鉴权**：必须登录。

**越权规则**（A-02 验收）：
- 自己 → 200 OK
- 跨学生读他人（student role + target != self）→ 403
- 教师读学生 → 200 OK
- 管理员读任何人 → 200 OK
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.errors import ForbiddenError, NotFoundError
from backend.公共.response import ok
from backend.公共.logger import get_logger

from backend.a_用户与聊天.user.schemas import UserInfoResponse
from backend.a_用户与聊天.user.deps import get_current_user
from backend.a_用户与聊天.db import get_session

log = get_logger(__name__)
router = APIRouter()


def _check_read_permission(current_user: dict, target_user_id: str) -> None:
    """
    检查"读"权限：
    - self → ok
    - teacher / admin → ok
    - 其他人（跨学生）→ 403
    """
    role = current_user.get("role")
    self_id = current_user.get("sub")

    if role in ("teacher", "admin"):
        return
    if self_id == target_user_id:
        return
    raise ForbiddenError("无权访问该用户信息")


@router.get("/info", response_model=None, summary="读用户信息（User + LearnerProfile）")
async def get_user_info(
    userId: str = Query(..., description="目标用户 ID"),
    current: dict = Depends(get_current_user),
) -> dict:
    """
    返回 User + LearnerProfile 合并结构。
    - 鉴权失败 → 401
    - 越权读他人 → 403
    - 用户不存在 → 404
    """
    # 1. 越权检查
    _check_read_permission(current, userId)

    # 2. 查 User
    from backend.a_用户与聊天.models.user import User
    async with get_session() as session:
        user = await session.get(User, userId)
        if user is None:
            raise NotFoundError(f"用户 {userId} 不存在")
        user_data = {
            "userId": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
        }

        # 3. 查 LearnerProfile（可空）
        from backend.a_用户与聊天.models.learner_profile import LearnerProfile
        from sqlalchemy import select
        result = await session.execute(
            select(LearnerProfile).where(LearnerProfile.user_id == userId)
        )
        lp = result.scalar_one_or_none()
        profile_data = {
            "education": lp.education if lp else None,
            "major": lp.major if lp else None,
            "theoryTestScore": lp.theory_test_score if lp else None,
            "weakKPs": lp.weak_kps if lp and lp.weak_kps else [],
            "strongKPs": lp.strong_kps if lp and lp.strong_kps else [],
            "profileUpdatedAt": lp.updated_at.isoformat() if lp and lp.updated_at else None,
        }

    # 4. 合并
    resp = UserInfoResponse(**{**user_data, **profile_data})

    log.info(f"读用户信息: caller={current.get('sub')} target={userId}")
    return ok(data=resp.model_dump(), message="ok")
