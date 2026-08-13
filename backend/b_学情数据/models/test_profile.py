"""
TestProfile 表：测试画像集（挑战杯新增 ⭐）。

B-07 验收标准强制字段：
  profile_id (PK) / payload (JSON) / label（可读名）
  / expected_weak_kps (JSON) / created_at
"""
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.b_学情数据.models.base import Base, TimestampMixin


class TestProfile(Base, TimestampMixin):
    """
    差异化学习者初始学情画像集。
    A-05 quality_check 用这 3 组画像跑 3 项硬指标。
    """

    __tablename__ = "test_profile"

    # 主键：p-001 本科应届生 / p-002 高职在读生 / p-003 企业转岗人员
    profile_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="画像ID（PK）"
    )

    # 完整画像 payload：包含 learnerProfile + activityHistory + interactionGoal
    payload: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="完整画像JSON"
    )

    # 可读名，如 "本科应届生"、"高职在读生"、"企业转岗人员"
    label: Mapped[str] = mapped_column(
        String(128), nullable=False, default="", index=True, comment="画像可读标签"
    )

    # 人工标注的预期弱知识清单（A-05 对比用）
    # 格式: [{"kp_id": "kp12", "severity": "high", "reason": "..."}]
    expected_weak_kps: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="预期弱知识清单"
    )

    def to_dict(self) -> dict:
        return {
            "profileId": self.profile_id,
            "label": self.label,
            "payload": self.payload or {},
            "expectedWeakKPs": self.expected_weak_kps or [],
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
