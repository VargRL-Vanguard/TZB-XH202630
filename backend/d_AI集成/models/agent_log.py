"""
AgentLog 表：多 Agent 协同日志（D-00 挑战杯新增 ⭐）。

D-00 验收标准强制字段：
  log_id (PK) / trace_id / agent_name / step / event_type / payload (JSON) / ts
"""
from sqlalchemy import String, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.d_AI集成.models.base import Base, TimestampMixin


class AgentLog(Base, TimestampMixin):
    """多 Agent 协同日志表。"""

    __tablename__ = "agent_log"

    log_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="日志ID（PK）"
    )
    trace_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True, comment="协同追踪ID"
    )
    agent_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", comment="Agent名称"
    )
    step: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="步骤序号"
    )
    event_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="", comment="事件类型：start/thinking/result/debate/final"
    )
    payload: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="事件载荷（JSON）"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="事件内容摘要"
    )

    def to_dict(self) -> dict:
        return {
            "logId": self.log_id,
            "traceId": self.trace_id,
            "agentName": self.agent_name,
            "step": self.step,
            "eventType": self.event_type,
            "payload": self.payload or {},
            "content": self.content,
            "ts": self.created_at.isoformat() if self.created_at else "",
        }