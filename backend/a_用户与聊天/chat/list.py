"""
GET /api/chat/list —— 当前用户的会话列表（A-03）。

**鉴权**：必须登录。

**入参**：userId（必须 == 当前登录用户）。

**返回**：按对方 userId 聚合的最近一条消息 + 未读数。
  [
    { targetId, name, lastMessage, lastTime, unread }
  ]

**实现思路**：
1. 找出所有跟 userId 发生过消息的对方 userId（去重）
2. 查 user 表拿 name
3. 对每个 target 拉最新一条消息（user→target 或 target→user）
4. 统计 target→user 且 status="sent" 的未读条数
"""
from fastapi import APIRouter, Depends, Query

from backend.公共.errors import BizError
from backend.公共.response import ok
from backend.公共.logger import get_logger
from backend.公共.auth_middleware import get_current_user

from backend.a_用户与聊天.chat.schemas import ChatListItem
from backend.a_用户与聊天.db import get_session

log = get_logger(__name__)
router = APIRouter()


@router.get("/list", response_model=None, summary="会话列表（按对方聚合最近消息）")
async def chat_list(
    userId: str = Query(..., description="当前用户（必须等于登录用户）"),
    current: dict = Depends(get_current_user),
) -> dict:
    """
    列出当前用户所有会话，按最近消息时间倒序。
    """
    self_id = current["userId"]
    role = current["role"]

    # 越权：学生只能看自己的
    if role not in ("teacher", "admin") and userId != self_id:
        raise BizError(f"userId 必须等于当前登录用户 {self_id}", code=400)

    from backend.a_用户与聊天.models.user import User
    from backend.a_用户与聊天.models.message import Message
    from sqlalchemy import select, func, or_, distinct

    async with get_session() as session:
        # 1. 找到所有"对方 userId"——在 message 表里出现过且不是 self
        target_ids_q = await session.execute(
            select(distinct(Message.target_id)).where(Message.user_id == self_id)
        )
        send_targets = {r[0] for r in target_ids_q.all()}

        sender_ids_q = await session.execute(
            select(distinct(Message.user_id)).where(Message.target_id == self_id)
        )
        recv_targets = {r[0] for r in sender_ids_q.all()}

        target_ids = list(send_targets | recv_targets)
        if not target_ids:
            return ok(data=[], message="ok")

        # 2. 查 user 表拿 name
        users_q = await session.execute(
            select(User).where(User.id.in_(target_ids))
        )
        name_map = {u.id: u.name for u in users_q.scalars().all()}

        # 3. 对每个 target 拉最近一条消息 + 未读数
        result: list[ChatListItem] = []
        for tid in target_ids:
            # 最新一条双向消息
            cond = or_(
                (Message.user_id == self_id) & (Message.target_id == tid),
                (Message.user_id == tid) & (Message.target_id == self_id),
            )
            last_q = await session.execute(
                select(Message)
                .where(cond)
                .order_by(Message.created_at.desc(), Message.id.desc())
                .limit(1)
            )
            last = last_q.scalar_one_or_none()
            if not last:
                continue

            # 未读：target 给我发且 status="sent"
            unread_q = await session.execute(
                select(func.count(Message.id)).where(
                    (Message.user_id == tid)
                    & (Message.target_id == self_id)
                    & (Message.status == "sent")
                )
            )
            unread = int(unread_q.scalar() or 0)

            result.append(
                ChatListItem(
                    targetId=tid,
                    name=name_map.get(tid, tid),
                    lastMessage=last.content,
                    lastTime=last.created_at.isoformat() if last.created_at else "",
                    unread=unread,
                )
            )

        # 4. 按 lastTime 倒序
        result.sort(key=lambda x: x.lastTime, reverse=True)

    return ok(data=[r.model_dump() for r in result], message="ok")
