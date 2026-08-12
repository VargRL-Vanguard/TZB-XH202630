"""
POST /api/chat/read —— 把某 user 发给我的所有未读消息标为已读（A-03）。

**鉴权**：必须登录。

**入参**：{ userId, targetId }（userId 必须 == 当前登录用户）

**行为**：
- 把所有 target→user 且 status="sent" 的消息改成 "read"
- 返回 { success, markedCount }
"""
from fastapi import APIRouter, Depends

from backend.公共.errors import BizError
from backend.公共.response import ok
from backend.公共.logger import get_logger
from backend.公共.auth_middleware import get_current_user

from backend.a_用户与聊天.chat.schemas import (
    MarkReadRequest,
    MarkReadResponse,
)
from backend.a_用户与聊天.db import get_session

log = get_logger(__name__)
router = APIRouter()


@router.post("/read", response_model=None, summary="标记消息已读")
async def mark_read(
    req: MarkReadRequest,
    current: dict = Depends(get_current_user),
) -> dict:
    """
    把 user 给我发的所有未读消息标为已读。
    """
    self_id = current["userId"]
    if req.userId != self_id:
        raise BizError(f"userId 必须等于当前登录用户 {self_id}", code=400)

    if req.userId == req.targetId:
        raise BizError("userId 和 targetId 不能相同", code=400)

    from backend.a_用户与聊天.models.message import Message
    from sqlalchemy import select, update

    async with get_session() as session:
        # 先查数量（用于返回）
        cnt_q = await session.execute(
            select(Message).where(
                (Message.user_id == req.targetId)
                & (Message.target_id == req.userId)
                & (Message.status == "sent")
            )
        )
        rows = cnt_q.scalars().all()
        marked = len(rows)

        if marked > 0:
            # 批量更新
            await session.execute(
                update(Message)
                .where(
                    (Message.user_id == req.targetId)
                    & (Message.target_id == req.userId)
                    & (Message.status == "sent")
                )
                .values(status="read")
            )

    log.info(
        f"标已读: {req.userId} <- {req.targetId} 数量={marked}"
    )
    resp = MarkReadResponse(success=True, markedCount=marked)
    return ok(data=resp.model_dump(), message="ok")
