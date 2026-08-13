"""3 种形态资源表（Resource）。夺奖核心表。

type 枚举：
- customized_resource : 定制化资源（讲义）
- practice_guide      : 实操指南
- tiered_quiz         : 分阶测试题

字段约束来自 任务清单_c_学习内容.md C-00 + 11_领域专家Agent_提示词.md §2。
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


RESOURCE_TYPES: tuple[str, ...] = ("customized_resource", "practice_guide", "tiered_quiz")


def _uuid() -> str:
    return str(uuid.uuid4())


class Resource(Base):
    __tablename__ = "resource"

    resource_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    # type: customized_resource | practice_guide | tiered_quiz
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[Any] = mapped_column(Text, nullable=False, default="")  # JSON 序列化字符串
    structured_content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    kp_coverage: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # List[str] kp_id
    cited_chunks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # List[str] chunk_id
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # 1-5
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_trace_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    trigger_reason: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    # trigger_reason: "" (默认) | "low_accuracy" | "high_accuracy" | "ai_initial"
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now_utc, onupdate=_now_utc
    )
