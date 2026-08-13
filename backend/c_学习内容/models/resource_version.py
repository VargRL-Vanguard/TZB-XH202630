"""资源历史版本表（ResourceVersion）。

每次 AI 生成资源时同时写一份版本快照，用于：
- 演示视频决策回放
- 资源对比与回滚
- audit 追溯
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class ResourceVersion(Base):
    __tablename__ = "resource_version"

    version_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    resource_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    student_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    content: Mapped[Any] = mapped_column(Text, nullable=False, default="")
    structured_content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    kp_coverage: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cited_chunks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    source_trace_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    trigger_reason: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
