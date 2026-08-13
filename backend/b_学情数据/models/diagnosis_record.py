"""
DiagnosisRecord 表：学情诊断结果历史（挑战杯新增 ⭐ B-05）。

保存每次 diagnose() 调用的完整 payload，用于：
1. 诊断历史回溯
2. A-05 quality_check 回放对比
3. 幻觉率 / 适配准确率抽样检查
"""
from datetime import datetime
from sqlalchemy import String, Text, JSON, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column

from backend.b_学情数据.models.base import Base, TimestampMixin


class DiagnosisRecord(Base, TimestampMixin):
    """
    学情诊断历史记录表。
    每条对应一次 diagnose(studentId) 调用。
    """

    __tablename__ = "diagnosis_record"

    # 主键：雪花 / uuid
    record_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="诊断记录ID（PK）"
    )

    # 与 traceId 对齐（WS 事件 + 协同编排全链路追踪）
    trace_id: Mapped[str] = mapped_column(
        String(128), nullable=False, default="", index=True, comment="全链路traceId"
    )

    # 学生
    student_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", index=True, comment="学生ID"
    )

    # 诊断置信度 [0,1]，< 0.6 会抛 QualityError
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="诊断置信度 [0,1]"
    )

    # === 诊断结果（完整快照，避免反复重算）===
    # weakKPs[]：弱知识点 ID 列表
    weak_kps: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="弱知识点ID列表"
    )
    # strongKPs[]：强知识点 ID 列表
    strong_kps: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="强知识点ID列表"
    )
    # knowledgeGaps[]：详细知识盲区
    # 格式：[{"kp_id":..., "kp_name":..., "severity":..., "evidence":...}]
    knowledge_gaps: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="知识盲区列表"
    )

    # 完整输入快照（get_student_snapshot 返回值）— 用于事后追溯
    input_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="输入学生画像快照"
    )

    # prompt 版本号（来自 diagnosis_prompts.py）
    prompt_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="v0.1", comment="prompt版本号"
    )

    # 诊断生成时间
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True, comment="诊断生成时间"
    )

    def to_dict(self) -> dict:
        return {
            "recordId": self.record_id,
            "traceId": self.trace_id,
            "studentId": self.student_id,
            "weakKPs": self.weak_kps or [],
            "strongKPs": self.strong_kps or [],
            "knowledgeGaps": self.knowledge_gaps or [],
            "confidence": self.confidence,
            "inputSnapshot": self.input_snapshot or {},
            "promptVersion": self.prompt_version,
            "generatedAt": self.generated_at.isoformat() if self.generated_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
