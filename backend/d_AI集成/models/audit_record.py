"""
AuditRecord 表：审核裁判 Agent 审核记录（D-06 挑战杯新增 ⭐）。

D-00 验收标准强制字段：
  audit_id (PK) / trace_id / result (pass/fail/retry) / issues (JSON) / score (0-1) / ts
"""
from sqlalchemy import String, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column

from backend.d_AI集成.models.base import Base, TimestampMixin


class AuditRecord(Base, TimestampMixin):
    """审核裁判 Agent 审核记录表。"""

    __tablename__ = "audit_record"

    audit_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="审核记录ID（PK）"
    )
    trace_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True, comment="协同追踪ID"
    )
    student_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", comment="学生ID"
    )
    result: Mapped[str] = mapped_column(
        String(16), nullable=False, default="fail", comment="审核结果：pass / fail / retry"
    )
    issues: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="审核问题列表（JSON数组）"
    )
    score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="审核评分（0-1）"
    )
    hallucination_rate: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="幻觉率"
    )
    coverage: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="核心知识点覆盖率"
    )
    content_snapshot: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="被审核内容摘要"
    )
    kp_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="审核涉及的知识点ID列表"
    )

    def to_dict(self) -> dict:
        return {
            "auditId": self.audit_id,
            "traceId": self.trace_id,
            "studentId": self.student_id,
            "result": self.result,
            "issues": self.issues or [],
            "score": self.score,
            "hallucinationRate": self.hallucination_rate,
            "coverage": self.coverage,
            "contentSnapshot": self.content_snapshot,
            "kpIds": self.kp_ids or [],
            "createdAt": self.created_at.isoformat() if self.created_at else "",
        }