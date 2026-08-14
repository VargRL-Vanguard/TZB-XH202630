"""
D-03：EventEmitter — 协同事件发射器。

职责：
  - 封装对 A 区 WebSocket 的推送
  - 同时写入 agent_log 表
  - 失败降级不阻塞主流程
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

from backend.公共.logger import get_logger
from backend.d_AI集成.db import get_session
from backend.d_AI集成.models.agent_log import AgentLog

log = get_logger(__name__)


class EventEmitter:
    """协同事件发射器。"""

    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.step = 0

    async def emit(
        self,
        event_type: str,
        *,
        agent_name: str,
        content: str = "",
        data: Optional[dict] = None,
    ) -> None:
        """
        发射一个协同事件。

        :param event_type: start / thinking / result / debate / final
        :param agent_name: Agent 名称
        :param content: 事件内容描述
        :param data: 附加数据
        """
        self.step += 1
        event = {
            "type": event_type,
            "agentName": agent_name,
            "step": self.step,
            "content": content,
            "traceId": self.trace_id,
            "timestamp": time.time(),
        }
        if data is not None:
            event["data"] = data

        # 推 WS
        try:
            from backend.a_用户与聊天.ws.manager import connection_manager
            from backend.a_用户与聊天.ws.events import EVENT_CHANNEL_PREFIX
            channel = f"{EVENT_CHANNEL_PREFIX}{agent_name}"
            await connection_manager.broadcast_to_channel(channel=channel, event=event)
        except Exception as e:
            log.warning(f"WS 推送失败（降级）: {e}")

        # 写 agent_log
        try:
            async with get_session() as session:
                log_entry = AgentLog(
                    log_id=f"log-{uuid.uuid4().hex[:12]}",
                    trace_id=self.trace_id,
                    agent_name=agent_name,
                    step=self.step,
                    event_type=event_type,
                    payload=data or {},
                    content=content,
                )
                session.add(log_entry)
        except Exception as e:
            log.warning(f"agent_log 写入失败（降级）: {e}")