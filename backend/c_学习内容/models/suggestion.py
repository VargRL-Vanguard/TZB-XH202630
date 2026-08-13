"""学习建议表（Suggestion）。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Suggestion(Base):
    __tablename__ = "suggestion"

    suggestion_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="practice")
    # category: all | method | resource | review | practice
    category_label: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    # priority: high | medium | low
    priority_label: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    is_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0/1
    extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
