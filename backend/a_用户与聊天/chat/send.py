"""
POST /api/chat/send —— 发送一条聊天消息（A-03）。

**鉴权**：必须登录（用 S-02 统一鉴权 get_current_user）。

**入参校验**：
- userId 必须 == 当前登录用户（防止冒用身份发消息）
- targetId 必须存在于 user 表
- content 非空，type ∈ {text, image, file}

**行为**：
- 写一条 message 记录（user_id→target_id, status="sent"）
- 通过 A-04 WebSocket 推送给 target（如其在线）
- 返回 {id, timestamp, status}
"""
from fastapi import APIRouter, Depends

from backend.公共.errors import BizError, NotFoundError
from backend.公共.response import ok
from backend.公共.logger import get_logger
from backend.公共.auth_middleware import get_current_user

from backend.a_用户与聊天.chat.schemas import (
    SendMessageRequest,
    SendMessageResponse,
)
from backend.a_用户与聊天.db import get_session

log = get_logger(__name__)
router = APIRouter()


@router.post("/send", response_model=None, summary="发送聊天消息")
async def send_message(
    req: SendMessageRequest,
    current: dict = Depends(get_current_user),
) -> dict:
    """
    鉴权 → 校验身份/目标存在 → 写 message 表 → WebSocket 推送 → 返回。
    """
    # 1. 身份一致性：userId 必须等于当前登录用户
    self_id = current["userId"]
    if req.userId != self_id:
        raise BizError(f"userId 必须等于当前登录用户 {self_id}", code=400)

    # 2. 不能给自己发
    if req.targetId == self_id:
        raise BizError("不能给自己发消息", code=400)

    # 3. 写库
    from backend.a_用户与聊天.models.user import User
    from backend.a_用户与聊天.models.message import Message
    from datetime import datetime

    async with get_session() as session:
        # 校验 target 存在
        target = await session.get(User, req.targetId)
        if target is None:
            raise NotFoundError(f"目标用户 {req.targetId} 不存在")

        msg = Message(
            user_id=self_id,
            target_id=req.targetId,
            content=req.content,
            type=req.type,
            status="sent",
        )
        session.add(msg)
        await session.flush()  # 拿到 msg.id 和 server_default 填的 created_at
        await session.refresh(msg)  # 关键：flush 后 refresh 拿 created_at，避免 commit 后 lazy 加载
        msg_id = msg.id
        created_at = msg.created_at

    timestamp_iso = (
        created_at.isoformat() if created_at else datetime.utcnow().isoformat()
    )

    log.info(f"发送消息: {self_id} -> {req.targetId} type={req.type} id={msg_id}")

    # 4. WebSocket 推送（target 在线时）— 失败不影响 HTTP 响应
    try:
        from backend.a_用户与聊天.ws.manager import connection_manager
        await connection_manager.send_to_user(
            req.targetId,
            {
                "type": "chat",
                "from": self_id,
                "data": {
                    "id": msg_id,
                    "content": req.content,
                    "msgType": req.type,
                    "timestamp": timestamp_iso,
                },
            },
        )
    except Exception as e:
        log.warning(f"WS 推送失败（消息已持久化）: {e}")

    resp = SendMessageResponse(
        id=msg_id,
        timestamp=timestamp_iso,
        status="sent",
    )
    return ok(data=resp.model_dump(), message="ok")
