"""
A-03 聊天 Pydantic 模型（请求/响应 schema）。

**契约**（按 api-doc.js §1.1 / §1.2 / §1.4 / §1.5）：
- POST /api/chat/send    → SendMessageRequest → SendMessageResponse
- GET  /api/chat/history → list[MessageItem]（含 total/hasMore）
- GET  /api/chat/list    → list[ChatListItem]
- POST /api/chat/read    → { success: bool }
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ========== 1. 发送消息 ==========

MessageType = Literal["text", "image", "file"]


class SendMessageRequest(BaseModel):
    """POST /api/chat/send 入参。"""
    userId: str = Field(..., description="发送者 userId（必须等于当前登录用户）")
    targetId: str = Field(..., description="接收者 userId")
    content: str = Field(..., min_length=1, max_length=2000, description="消息内容")
    type: MessageType = Field("text", description="消息类型：text/image/file")


class SendMessageResponse(BaseModel):
    """POST /api/chat/send 出参。"""
    id: int
    timestamp: str  # ISO 格式
    status: Literal["sent", "read"] = "sent"


# ========== 2. 聊天历史 ==========

class MessageItem(BaseModel):
    """单条消息。"""
    id: int
    userId: str       # 发送者
    targetId: str     # 接收者
    content: str
    type: MessageType
    timestamp: str
    status: Literal["sent", "read"]


class HistoryResponse(BaseModel):
    """GET /api/chat/history 出参。"""
    list: list[MessageItem]
    total: int
    hasMore: bool


# ========== 3. 聊天列表 ==========

class ChatListItem(BaseModel):
    """会话列表条目（按 targetId 聚合最近一条消息）。"""
    targetId: str
    name: str
    lastMessage: str
    lastTime: str
    unread: int


# ========== 4. 已读标记 ==========

class MarkReadRequest(BaseModel):
    """POST /api/chat/read 入参。"""
    userId: str = Field(..., description="当前用户（已登录，body 冗余便于前端）")
    targetId: str = Field(..., description="把该 user 发来的消息全部标记已读")


class MarkReadResponse(BaseModel):
    """POST /api/chat/read 出参。"""
    success: bool
    markedCount: int = 0
