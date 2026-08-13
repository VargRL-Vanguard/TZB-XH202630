"""
Student 表：学生学情画像基础信息（B 区自有扩展字段）。
注意：userId 与 A 区 User.id 对齐，但表在 B 区独立库。
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.b_学情数据.models.base import Base, TimestampMixin


class Student(Base, TimestampMixin):
    """
    学生学情画像表。
    补充 A 区 learner_profile 的量化指标，避免跨库 join。
    """

    __tablename__ = "student"

    # 主键：与 A 区 User.id 对齐（如 s001 / u001）
    student_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="学生ID，与A区User.id对齐"
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", comment="姓名"
    )

    # === 核心指标（B-01 /api/student/metrics 直接读取）===
    # 累计学习时长（小时）
    study_hours: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="累计学习时长（小时）"
    )
    # 课程完成率 0-1
    completion_rate: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="课程完成率 [0,1]"
    )
    # 平均成绩 0-100
    avg_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="平均成绩 [0,100]"
    )
    # 学习趋势：up / down / flat
    trend: Mapped[str] = mapped_column(
        String(16), nullable=False, default="flat", comment="学习趋势 up/down/flat"
    )
    # 趋势量化值（最近 N 次成绩斜率归一化到 [-1,1]）
    trend_value: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="趋势量化值 [-1,1]"
    )

    # === 6 维能力雷达（B-02 /api/student/dimensions 直接读取）===
    # 理解能力 0-100
    dim_comprehension: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="理解能力"
    )
    dim_application: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="应用能力"
    )
    dim_analysis: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="分析能力"
    )
    dim_evaluation: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="评价能力"
    )
    dim_creation: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="创造能力"
    )
    dim_collaboration: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="协作能力"
    )

    def to_info_dict(self) -> dict:
        """转成 /api/student/info 需要的 dict。"""
        return {
            "studentId": self.student_id,
            "name": self.name,
        }

    def to_metrics_dict(self) -> dict:
        """转成 /api/student/metrics 需要的 dict。"""
        return {
            "studyHours": self.study_hours,
            "completionRate": self.completion_rate,
            "avgScore": self.avg_score,
            "trend": self.trend,
            "trendValue": self.trend_value,
        }

    def to_dimensions_dict(self) -> dict:
        """转成 6 维能力雷达 dict。字段名固定。"""
        return {
            "comprehension": self.dim_comprehension,
            "application": self.dim_application,
            "analysis": self.dim_analysis,
            "evaluation": self.dim_evaluation,
            "creation": self.dim_creation,
            "collaboration": self.dim_collaboration,
        }
