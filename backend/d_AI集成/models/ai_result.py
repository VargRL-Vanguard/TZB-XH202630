"""
AIResult 表：AI 生成结果（D-00 / D-05 共用 ⭐）。

D-00 验收标准强制字段：
  result_id (PK) / student_id / ai_type / input_snapshot / output / metrics (JSON) / ts
"""
from sqlalchemy import String, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column

from backend.d_AI集成.models.base import Base, TimestampMixin


class AIResult(Base, TimestampMixin):
    """AI 生成结果表。"""

    __tablename__ = "ai_result"

    result_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="结果ID（PK）"
    )
    student_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="学生ID"
    )
    ai_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="chat", comment="AI类型：chat / path / suggest"
    )
    input_snapshot: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="输入快照"
    )
    output: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="AI 输出内容（JSON 字符串）"
    )
    metrics: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="质量指标（JSON）"
    )
    score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="综合评分（0-1）"
    )

    def to_dict(self) -> dict:
        return {
            "resultId": self.result_id,
            "studentId": self.student_id,
            "aiType": self.ai_type,
            "inputSnapshot": self.input_snapshot,
            "output": self.output,
            "metrics": self.metrics or {},
            "score": self.score,
            "createdAt": self.created_at.isoformat() if self.created_at else "",
        }