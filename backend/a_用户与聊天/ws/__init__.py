"""
A 区 WebSocket 模块：A-04 实时通道（**挑战杯核心**，影响"可视化"15 分）。

**端点**：`ws://host/ws?token=xxx`
**事件协议**（5 类 Agent 协同事件，前端可视化必看）：
- agent.start    Agent 开始
- agent.thinking Agent 思考中
- agent.result   Agent 输出结果
- agent.debate   多 Agent 辩论
- agent.final    协同结束

**B/C/D 接入方式**（后续 Agent 推事件）：
    from backend.a_用户与聊天.ws.manager import connection_manager
    await connection_manager.broadcast_to_channel(
        channel="agent:学情诊断Agent",
        event={...}
    )
"""
from backend.a_用户与聊天.ws.events import (  # noqa: F401
    AgentEventType,
    EVENT_CHANNEL_PREFIX,
)
from backend.a_用户与聊天.ws.manager import (  # noqa: F401
    connection_manager,
    ConnectionManager,
)

__all__ = [
    "AgentEventType", "EVENT_CHANNEL_PREFIX",
    "connection_manager", "ConnectionManager",
]
