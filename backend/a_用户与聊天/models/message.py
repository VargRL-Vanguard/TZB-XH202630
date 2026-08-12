"""
Message 表：聊天消息。

**字段**（按 api-doc.js §1.1 / §1.2 契约）：
- id:           主键自增
- user_id:      发送者（外键 → user.id）
- target_id:    接收者（外键 → user.id）
- content:      消息内容（text 直接存；image/file 存 URL/路径）
- type:         text | image | file
- status:       sent（发送）| read（已读，target 调 /api/chat/read 后回写）
- created_at:   发送时间

**注意**：
- 双人会话：user_id ↔ target_id 两条记录（A 发给 B 一条，B 发给 A 一条），不分会话表
- 这样 /api/chat/list 用 GROUP BY target_id 聚合最近消息；/api/chat/history 用 OR 过滤
- 简单、够用，符合 P1 优先级
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.a_用户与聊天.models.base import Base


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="消息 ID（自增）"
    )
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="发送者 userId",
    )
    target_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="接收者 userId",
    )
    content: Mapped[str] = mapped_column(
        String(2000), nullable=False, comment="消息内容（text 直接存 / image+file 存 URL）"
    )
    type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="text", comment="消息类型：text/image/file"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="sent", comment="状态：sent（发送）/read（已读）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="发送时间"
    )

    # 常用查询：拉某对用户的历史 → WHERE (user_id=A AND target_id=B) OR (user_id=B AND target_id=A) ORDER BY created_at
    __table_args__ = (
        Index("idx_user_target_time", "user_id", "target_id", "created_at"),
        Index("idx_target_user_time", "target_id", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} {self.user_id}->{self.target_id} type={self.type}>"
