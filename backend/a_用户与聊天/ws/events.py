"""
WebSocket 事件类型常量 + 频道前缀。

**前端订阅约定**：
- 频道名格式：`agent:<agent_name>`，例如 `agent:学情诊断Agent`
- 客户端发 `{"type": "subscribe", "channel": "agent:学情诊断Agent"}` 订阅
"""
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# 频道前缀（统一管理，避免散落字符串）
EVENT_CHANNEL_PREFIX = "agent:"


class AgentEventType(str, Enum):
    """
    5 类 Agent 协同事件类型（**前端必看**，决定可视化 UI 状态机）。

    事件流典型顺序：
        agent.start    →  agent.thinking (N次) → agent.result → agent.debate (可选) → agent.final
    """
    START = "agent.start"
    THINKING = "agent.thinking"
    RESULT = "agent.result"
    DEBATE = "agent.debate"
    FINAL = "agent.final"


# ========== 事件 Payload 模型 ==========


class AgentStartEvent(BaseModel):
    """agent.start: Agent 开始工作"""
    type: str = AgentEventType.START.value
    agentName: str = Field(..., description="Agent 名称，如 '学情诊断Agent'")
    step: int = Field(1, description="步骤编号")
    traceId: str = Field(..., description="协同会话 trace id")
    timestamp: float = Field(..., description="Unix 时间戳（秒）")


class AgentThinkingEvent(BaseModel):
    """agent.thinking: Agent 思考中（可多次发送）"""
    type: str = AgentEventType.THINKING.value
    agentName: str
    step: int
    content: str = Field(..., description="思考过程描述（前端流式显示）")
    traceId: str
    timestamp: float


class AgentResultEvent(BaseModel):
    """agent.result: Agent 输出结果"""
    type: str = AgentEventType.RESULT.value
    agentName: str
    step: int
    content: str = Field(..., description="Agent 输出的最终内容（结构化）")
    data: dict[str, Any] = Field(default_factory=dict, description="结构化数据（前端直接用）")
    traceId: str
    timestamp: float


class AgentDebateEvent(BaseModel):
    """agent.debate: 多个 Agent 辩论"""
    type: str = AgentEventType.DEBATE.value
    agents: list[str] = Field(..., description="参与辩论的 Agent 名列表")
    topic: str = Field(..., description="辩论主题")
    content: str = Field(default="", description="辩论内容（可选）")
    traceId: str
    timestamp: float


class AgentFinalEvent(BaseModel):
    """agent.final: 协同结束（前端关闭 loading + 展示最终结果）"""
    type: str = AgentEventType.FINAL.value
    ok: bool = Field(..., description="是否成功")
    summary: str = Field(default="", description="最终摘要")
    traceId: str
    timestamp: float


# ========== 客户端消息模型 ==========


class ClientPing(BaseModel):
    """客户端 ping：保活"""
    type: str = "ping"
    timestamp: float = 0.0


class ClientSubscribe(BaseModel):
    """客户端订阅频道"""
    type: str = "subscribe"
    channel: str = Field(..., description="频道名，如 'agent:学情诊断Agent'")


class ClientUnsubscribe(BaseModel):
    """客户端取消订阅"""
    type: str = "unsubscribe"
    channel: str


class ClientChat(BaseModel):
    """客户端发聊天消息（持久化 + 广播给 targetId）"""
    type: str = "chat"
    targetId: str = Field(..., description="目标用户 ID")
    content: str = Field(..., description="消息内容")
