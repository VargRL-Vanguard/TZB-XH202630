"""学习路径主表（LearningPath / LearningModule / LearningTask）。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class LearningPath(Base):
    __tablename__ = "learning_path"

    path_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="default")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now_utc, onupdate=_now_utc
    )

    modules: Mapped[list["LearningModule"]] = relationship(
        "LearningModule", back_populates="path", cascade="all, delete-orphan"
    )


class LearningModule(Base):
    __tablename__ = "learning_module"

    module_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    path_id: Mapped[str] = mapped_column(String(64), ForeignKey("learning_path.path_id"), index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    start_date: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    end_date: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    duration: Mapped[str] = mapped_column(String(16), nullable=False, default="")

    path: Mapped["LearningPath"] = relationship("LearningPath", back_populates="modules")
    tasks: Mapped[list["LearningTask"]] = relationship(
        "LearningTask", back_populates="module", cascade="all, delete-orphan"
    )


class LearningTask(Base):
    __tablename__ = "learning_task"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    module_id: Mapped[str] = mapped_column(String(64), ForeignKey("learning_module.module_id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meta: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_date: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    module: Mapped["LearningModule"] = relationship("LearningModule", back_populates="tasks")
