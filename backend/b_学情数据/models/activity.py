"""
Activity 表：学习活动记录（看课 / 做题 / 测试 / 讨论）。
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from backend.b_学情数据.models.base import Base, TimestampMixin


class Activity(Base, TimestampMixin):
    """
    学习活动记录表。
    覆盖 api-doc §5 所有活动接口的数据源。
    """

    __tablename__ = "activity"

    # 主键
    activity_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="活动记录ID"
    )

    # 关联学生
    student_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="学生ID"
    )

    # === 活动类型 ===
    # course: 看课 / exercise: 做题 / test: 测试 / discussion: 讨论 / other
    activity_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="other", index=True, comment="活动类型"
    )

    # === 关联资源（课程 / 题目 / 讨论帖）===
    resource_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", index=True, comment="关联资源ID"
    )
    resource_name: Mapped[str] = mapped_column(
        String(256), nullable=False, default="", comment="资源名称（前端展示用）"
    )
    resource_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="", comment="资源类型"
    )

    # === 进度 / 状态 ===
    # not-started / in-progress / completed
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="not-started", index=True, comment="状态"
    )
    progress: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="进度百分比 [0,100]"
    )
    # 得分 0-100（测试 / 做题时）
    score: Mapped[float] = mapped_column(
        Float, nullable=True, comment="得分（可选）"
    )

    # === 时间 ===
    # 开始时间
    start_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, index=True, comment="开始时间"
    )
    # 结束 / 完成时间
    end_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, index=True, comment="结束时间"
    )
    # 活动耗时（分钟）
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="耗时（分钟）"
    )

    # === 扩展字段（挂载弱知识点等）===
    # 这次活动涉及的知识点 ID 列表
    kp_tags: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="涉及的知识点ID列表"
    )
    # 任意扩展信息
    extra: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展字段"
    )

    def to_dict(self) -> dict:
        return {
            "activityId": self.activity_id,
            "studentId": self.student_id,
            "activityType": self.activity_type,
            "resourceId": self.resource_id,
            "resourceName": self.resource_name,
            "resourceType": self.resource_type,
            "status": self.status,
            "progress": self.progress,
            "score": self.score,
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "durationMinutes": self.duration_minutes,
            "kpTags": self.kp_tags or [],
            "extra": self.extra or {},
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
