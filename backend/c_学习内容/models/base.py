"""SQLAlchemy 声明性基类（C 区专用）。"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """C 区所有 ORM 的统一基类。"""
    pass
