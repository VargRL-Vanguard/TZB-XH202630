"""
GET /api/chat/history —— 拉取某对用户的聊天历史（A-03）。

**鉴权**：必须登录。

**入参**：
- userId:   当前用户（**必填**，与 token 一致；防止拉他人消息）
- targetId: 对方用户
- limit:    每页条数（默认 50，上限 200）
- offset:   跳过条数（默认 0）

**返回**：
- list:     消息数组（按 created_at 升序：旧→新）
- total:    满足条件的总条数
- hasMore:  offset + len(list) < total

**越权规则**：
- 学生只能查自己 ↔ 对方的会话（userId 必须 == sub）
- 教师/管理员可查任意两人（userId 任意但仍需提供）
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.errors import BizError
from backend.公共.response import ok
from backend.公共.logger import get_logger
from backend.公共.auth_middleware import get_current_user

from backend.a_用户与聊天.chat.schemas import (
    HistoryResponse,
    MessageItem,
)
from backend.a_用户与聊天.db import get_session

log = get_logger(__name__)
router = APIRouter()


@router.get("/history", response_model=None, summary="聊天历史（分页）")
async def chat_history(
    userId: str = Query(..., description="当前用户（必须等于登录用户）"),
    targetId: str = Query(..., description="对方用户 ID"),
    limit: int = Query(50, ge=1, le=200, description="每页条数"),
    offset: int = Query(0, ge=0, description="跳过条数"),
    current: dict = Depends(get_current_user),
) -> dict:
    """
    拉取 userId ↔ targetId 之间的双向消息。
    - 鉴权失败 → 401
    - userId != 当前用户（且非 teacher/admin）→ 400
    """
    self_id = current["userId"]
    role = current["role"]

    # 越权：学生只能查自己的
    if role not in ("teacher", "admin") and userId != self_id:
        raise BizError(f"userId 必须等于当前登录用户 {self_id}", code=400)

    if userId == targetId:
        raise BizError("userId 和 targetId 不能相同", code=400)

    from backend.a_用户与聊天.models.message import Message
    from sqlalchemy import select, func, or_

    async with get_session() as session:
        # 双向条件：(我→他) OR (他→我)
        cond = or_(
            (Message.user_id == userId) & (Message.target_id == targetId),
            (Message.user_id == targetId) & (Message.target_id == userId),
        )

        # 1. 总数
        total_q = await session.execute(select(func.count(Message.id)).where(cond))
        total = int(total_q.scalar() or 0)

        # 2. 分页（按 created_at 升序）
        rows_q = await session.execute(
            select(Message)
            .where(cond)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .offset(offset)
            .limit(limit)
        )
        rows = rows_q.scalars().all()

        items = [
            MessageItem(
                id=r.id,
                userId=r.user_id,
                targetId=r.target_id,
                content=r.content,
                type=r.type,
                timestamp=r.created_at.isoformat() if r.created_at else "",
                status=r.status,
            )
            for r in rows
        ]

    has_more = (offset + len(items)) < total
    resp = HistoryResponse(list=items, total=total, hasMore=has_more)
    return ok(data=resp.model_dump(), message="ok")
