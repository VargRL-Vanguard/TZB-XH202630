"""
所有 A 区 ORM 模型的基类。
集中放这里避免 user.py / learner_profile.py 互相继承时循环引用。
"""
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 A 区表的基类。"""

    pass


class TimestampMixin:
    """created_at / updated_at 自动时间戳（按需在模型里 mixin）。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
