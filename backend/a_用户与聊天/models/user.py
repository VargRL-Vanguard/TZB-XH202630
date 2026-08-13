"""
User 表：用户基础信息。
字段严格按任务清单 A-00 验收标准：id / username / password_hash / name / role / created_at
"""
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.a_用户与聊天.models.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="用户ID（u001/u002/t001...）"
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, comment="登录名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="bcrypt 哈希（A-01 实现）"
    )
    name: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="显示名"
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="角色：student/teacher/admin"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="注册时间"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
