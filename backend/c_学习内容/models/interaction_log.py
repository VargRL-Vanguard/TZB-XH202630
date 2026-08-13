"""答题反馈日志表（InteractionLog）— C-06 动态迭代用。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class InteractionLog(Base):
    __tablename__ = "interaction_log"

    log_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    kp_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    question_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0/1
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    accuracy_rolling: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    triggered_action: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    # triggered_action: "" | "downgrade" | "upgrade"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, index=True)
