"""
AIConversation 表：AI 对话历史（D-00 / D-05 共用 ⭐）。

D-00 验收标准强制字段：
  conv_id (PK) / student_id / ai_type / messages (JSON) / summary / ts
"""
from sqlalchemy import String, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.d_AI集成.models.base import Base, TimestampMixin


class AIConversation(Base, TimestampMixin):
    """AI 对话历史表。"""

    __tablename__ = "ai_conversation"

    conv_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="对话ID（PK）"
    )
    student_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="学生ID"
    )
    ai_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="chat", comment="AI类型：chat / path / suggest"
    )
    messages: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="对话消息列表（JSON）"
    )
    summary: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="对话摘要"
    )
    msg_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="消息条数"
    )

    def to_dict(self) -> dict:
        return {
            "convId": self.conv_id,
            "studentId": self.student_id,
            "aiType": self.ai_type,
            "messages": self.messages or [],
            "summary": self.summary,
            "msgCount": self.msg_count,
            "createdAt": self.created_at.isoformat() if self.created_at else "",
            "updatedAt": self.updated_at.isoformat() if self.updated_at else "",
        }