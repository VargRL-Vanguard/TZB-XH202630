"""
LearnerProfile 表：学习者画像（**挑战杯核心**，B 的学情诊断 Agent 唯一输入源）。

字段按任务清单 A-00 验收标准：
user_id / education / major / theory_test_score / weak_kps (JSON) / strong_kps (JSON) / updated_at
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.a_用户与聊天.models.base import Base


class LearnerProfile(Base):
    __tablename__ = "learner_profile"

    # 关联 User.id（删除 User 时级联删除画像）
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        comment="关联 User.id",
    )
    education: Mapped[Optional[str]] = mapped_column(
        String(32), comment="学历：本科/硕士/大专/高中"
    )
    major: Mapped[Optional[str]] = mapped_column(
        String(64), comment="专业：机械工程/计算机科学..."
    )
    theory_test_score: Mapped[Optional[int]] = mapped_column(
        Integer, comment="理论测试分（0-100）"
    )
    # 关键字段：JSON 数组存知识点 ID 列表
    weak_kps: Mapped[Optional[list]] = mapped_column(
        JSON, default=list, comment="薄弱知识点 ID 列表（其他区只读）"
    )
    strong_kps: Mapped[Optional[list]] = mapped_column(
        JSON, default=list, comment="擅长知识点 ID 列表（其他区只读）"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="最近更新时间",
    )

    def __repr__(self) -> str:
        return f"<LearnerProfile user_id={self.user_id} weak_kps={self.weak_kps}>"
