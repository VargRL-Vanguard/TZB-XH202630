"""
A-04 WebSocket 路由：ws://host/ws?token=xxx

**选型说明**（详见 ws/README.md）：
- 选 **FastAPI WebSocket**（不选 websockets 库裸用）
- 理由：与 REST 共进程、共享 JWT 鉴权、共享日志、共享异常处理
- 缺点：高并发需配 uvicorn workers，但比赛演示够用

**握手流程**：
1. 客户端 `ws://host/ws?token=<jwt>` 建立连接
2. 服务端从 query string 拿 token
3. 调 `decode_access_token(token)` 验签
4. 失败 → 立即 close 401
5. 成功 → `connection_manager.connect(ws, user_id)` 接受
6. 进入主循环接收客户端消息（分发给 handlers.py）

**后台任务**：
- 每 60s 调 `cleanup_stale_connections()` 清心跳超时
"""
import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from backend.公共.logger import get_logger
from backend.a_用户与聊天.auth.tokens import decode_access_token
from backend.a_用户与聊天.auth.blacklist import is_blacklisted
from backend.a_用户与聊天.ws.manager import connection_manager
from backend.a_用户与聊天.ws.handlers import handle_client_message

log = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "") -> None:
    """
    WebSocket 端点：ws://host/ws?token=xxx

    **握手失败**：
    - 无 token / 空 token → close 4401（自定义业务码）
    - token 无效 / 过期 → close 4401
    - token 已在黑名单 → close 4401
    """
    # 1. 校验 token
    user_id = None
    try:
        if not token:
            await websocket.close(code=4401, reason="missing token")
            return
        if is_blacklisted(token):
            await websocket.close(code=4401, reason="token blacklisted")
            return
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4401, reason="invalid token payload")
            return
    except Exception as e:
        log.warning(f"WS 握手失败: {e}")
        try:
            await websocket.close(code=4401, reason="auth failed")
        except Exception:
            pass
        return

    # 2. 注册连接
    await connection_manager.connect(websocket, user_id)
    log.info(f"WS 握手成功: user={user_id}")

    # 3. 通知前端：连接就绪（可选，前端也可用 ping 测）
    try:
        await websocket.send_json({
            "type": "connected",
            "userId": user_id,
            "timestamp": time.time(),
        })
    except Exception:
        return

    # 4. 主循环：接收客户端消息
    try:
        while True:
            # 接收文本消息（前端用 JSON）
            text = await websocket.receive_text()
            await handle_client_message(websocket, user_id, text)
    except WebSocketDisconnect:
        log.info(f"WS 客户端断开: user={user_id}")
    except Exception as e:
        log.exception(f"WS 主循环异常: user={user_id} err={e}")
    finally:
        # 5. 清理连接
        await connection_manager.disconnect(websocket, user_id)


# ========== 后台心跳清理任务 ==========


async def heartbeat_cleanup_task(interval: int = 60) -> None:
    """
    后台任务：每 60s 清一次心跳超时连接。
    在 main.py 启动时通过 `asyncio.create_task()` 启动。
    """
    while True:
        try:
            cleaned = await connection_manager.cleanup_stale_connections()
            if cleaned > 0:
                log.info(f"心跳清理: 清除了 {cleaned} 个超时连接")
        except Exception as e:
            log.exception(f"心跳清理异常: {e}")
        await asyncio.sleep(interval)
