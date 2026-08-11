"""
WebSocket 连接管理器（**单例**，全进程共享）。

**核心能力**：
1. 维护 (user_id → WebSocket) 映射，支持多设备同账号
2. 维护 (channel → set[user_id]) 订阅关系
3. **最近 50 条事件环形缓冲**：新连接重放（断线重连不丢可视化进度）
4. 心跳超时清理（5min 无活动 → 关闭）
5. 线程/异步安全（asyncio.Lock 保护）
"""
import asyncio
import time
from collections import deque
from typing import Optional

from fastapi import WebSocket

from backend.公共.logger import get_logger

log = get_logger(__name__)


# 最近 50 条事件环形缓冲（断线重连重放用）
EVENT_BUFFER_SIZE = 50
# 心跳超时（秒）
HEARTBEAT_TIMEOUT = 300  # 5 分钟


class ConnectionManager:
    """
    WebSocket 连接管理器（单例模式见 connection_manager）。
    """

    def __init__(self):
        # user_id → set[WebSocket]（一个用户可能多设备）
        self._connections: dict[str, set[WebSocket]] = {}
        # channel → set[user_id]
        self._subscriptions: dict[str, set[str]] = {}
        # 全局事件环形缓冲（断线重连重放）
        self._event_buffer: deque = deque(maxlen=EVENT_BUFFER_SIZE)
        # websocket → last_ping_ts（心跳检测）
        self._last_ping: dict[WebSocket, float] = {}
        # 异步锁
        self._lock = asyncio.Lock()

    # ============== 连接生命周期 ==============

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        注册新连接。
        1. 接受握手
        2. 加入 user_id 索引
        3. 重放最近 50 条事件（让前端刷新后能补回进度）
        """
        await websocket.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)
            self._last_ping[websocket] = time.time()
        log.info(f"WS 连接: user={user_id} 当前连接数={self._connection_count()}")

        # 重放缓冲（注意：要在锁外 send，否则长时间持锁）
        for event in list(self._event_buffer):
            try:
                await websocket.send_json(event)
            except Exception as e:
                log.warning(f"重放事件失败: {e}")
                break

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        清理连接。
        1. 从 _connections 移除
        2. 从 _last_ping 移除
        3. 清理空订阅
        """
        async with self._lock:
            conns = self._connections.get(user_id)
            if conns:
                conns.discard(websocket)
                if not conns:
                    del self._connections[user_id]
            self._last_ping.pop(websocket, None)
            # 清理该 user 的所有订阅
            for channel, users in list(self._subscriptions.items()):
                users.discard(user_id)
                if not users:
                    del self._subscriptions[channel]
        log.info(f"WS 断开: user={user_id} 当前连接数={self._connection_count()}")

    # ============== 订阅 ==============

    async def subscribe(self, user_id: str, channel: str) -> None:
        """用户订阅频道。"""
        async with self._lock:
            if channel not in self._subscriptions:
                self._subscriptions[channel] = set()
            self._subscriptions[channel].add(user_id)
        log.info(f"WS 订阅: user={user_id} channel={channel}")

    async def unsubscribe(self, user_id: str, channel: str) -> None:
        async with self._lock:
            users = self._subscriptions.get(channel)
            if users:
                users.discard(user_id)
                if not users:
                    del self._subscriptions[channel]

    # ============== 发送 ==============

    async def send_to_user(self, user_id: str, event: dict) -> int:
        """
        给指定用户的所有连接发事件。
        :return: 成功发送的连接数
        """
        async with self._lock:
            conns = list(self._connections.get(user_id, set()))
        if not conns:
            return 0
        sent = 0
        for ws in conns:
            try:
                await ws.send_json(event)
                sent += 1
            except Exception as e:
                log.warning(f"send_to_user 失败 user={user_id}: {e}")
        return sent

    async def broadcast_to_channel(self, channel: str, event: dict) -> int:
        """
        广播给频道所有订阅者。
        :return: 收到事件的用户数
        """
        async with self._lock:
            user_ids = list(self._subscriptions.get(channel, set()))
        if not user_ids:
            log.debug(f"broadcast_to_channel: 频道 {channel} 暂无订阅者")
            return 0
        sent_users = 0
        for uid in user_ids:
            if await self.send_to_user(uid, event) > 0:
                sent_users += 1
        return sent_users

    async def broadcast_all(self, event: dict) -> int:
        """广播给所有在线用户。"""
        async with self._lock:
            user_ids = list(self._connections.keys())
        sent = 0
        for uid in user_ids:
            if await self.send_to_user(uid, event) > 0:
                sent += 1
        return sent

    # ============== 事件缓冲（重放） ==============

    async def record_event(self, event: dict) -> None:
        """记录事件到环形缓冲（每个事件都会自动入队）。"""
        async with self._lock:
            self._event_buffer.append(event)

    # ============== 心跳 ==============

    async def update_ping(self, websocket: WebSocket) -> None:
        """更新最后 ping 时间。"""
        async with self._lock:
            self._last_ping[websocket] = time.time()

    async def cleanup_stale_connections(self) -> int:
        """
        清理超时连接（5min 无 ping）。
        由后台任务每 60s 调用一次。
        """
        now = time.time()
        stale: list[tuple[WebSocket, str]] = []
        async with self._lock:
            for ws, last in list(self._last_ping.items()):
                if now - last > HEARTBEAT_TIMEOUT:
                    # 找到这个 ws 对应的 user_id
                    for uid, conns in self._connections.items():
                        if ws in conns:
                            stale.append((ws, uid))
                            break
        for ws, uid in stale:
            try:
                await ws.close(code=1000, reason="heartbeat timeout")
            except Exception:
                pass
            await self.disconnect(ws, uid)
            log.info(f"WS 心跳超时清理: user={uid}")
        return len(stale)

    # ============== 状态查询 ==============

    def _connection_count(self) -> int:
        return sum(len(c) for c in self._connections.values())

    def stats(self) -> dict:
        return {
            "online_users": len(self._connections),
            "total_connections": self._connection_count(),
            "channels": len(self._subscriptions),
            "buffered_events": len(self._event_buffer),
        }


# ========== 进程级单例 ==========
connection_manager = ConnectionManager()
