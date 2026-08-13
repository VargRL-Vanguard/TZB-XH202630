"""
WebSocket 客户端消息处理器。

**支持的客户端消息类型**（A-04 验收标准）：
- {"type": "ping"}        → 立即回 {"type": "pong"}，更新心跳
- {"type": "subscribe",   "channel": "agent:xxx"}  → 订阅频道
- {"type": "unsubscribe", "channel": "agent:xxx"}  → 取消订阅
- {"type": "chat",        "targetId": "u002", "content": "..."} → 持久化 + 广播

**不支持 / 异常消息**：服务端忽略 + 日志 warning。
"""
import time
import json

from fastapi import WebSocket

from backend.公共.logger import get_logger
from backend.a_用户与聊天.ws.manager import connection_manager

log = get_logger(__name__)


async def handle_client_message(
    websocket: WebSocket,
    user_id: str,
    raw_text: str,
) -> None:
    """
    处理一条客户端消息。
    """
    try:
        msg = json.loads(raw_text)
    except json.JSONDecodeError:
        log.warning(f"WS 收到非法 JSON: user={user_id} raw={raw_text[:100]}")
        return

    msg_type = msg.get("type")

    if msg_type == "ping":
        await _handle_ping(websocket, user_id, msg)
    elif msg_type == "subscribe":
        await _handle_subscribe(user_id, msg)
    elif msg_type == "unsubscribe":
        await _handle_unsubscribe(user_id, msg)
    elif msg_type == "chat":
        await _handle_chat(user_id, msg)
    else:
        log.warning(f"WS 收到未知消息类型: type={msg_type} user={user_id}")


async def _handle_ping(websocket: WebSocket, user_id: str, msg: dict) -> None:
    """处理 ping：更新心跳 + 回 pong。"""
    await connection_manager.update_ping(websocket)
    await websocket.send_json({
        "type": "pong",
        "timestamp": time.time(),
    })
    log.debug(f"WS pong: user={user_id}")


async def _handle_subscribe(user_id: str, msg: dict) -> None:
    """处理订阅。"""
    channel = msg.get("channel", "")
    if not channel:
        log.warning(f"subscribe 缺少 channel: user={user_id}")
        return
    await connection_manager.subscribe(user_id, channel)


async def _handle_unsubscribe(user_id: str, msg: dict) -> None:
    """处理取消订阅。"""
    channel = msg.get("channel", "")
    if channel:
        await connection_manager.unsubscribe(user_id, channel)


async def _handle_chat(user_id: str, msg: dict) -> None:
    """
    处理聊天消息：持久化（**TBD**, 后续 A-03 实现）+ 广播给 targetId。
    """
    target_id = msg.get("targetId", "")
    content = msg.get("content", "")
    if not target_id or not content:
        log.warning(f"chat 消息字段不全: user={user_id} msg={msg}")
        return

    # 1. 持久化（TODO: A-03 任务实现）
    #    await save_message(from=user_id, to=target_id, content=content)

    # 2. 实时推给 target 在线连接
    event = {
        "type": "chat",
        "fromId": user_id,
        "content": content,
        "timestamp": time.time(),
    }
    delivered = await connection_manager.send_to_user(target_id, event)
    log.info(f"WS chat: {user_id} → {target_id} delivered={delivered}")
