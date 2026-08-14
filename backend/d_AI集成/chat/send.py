"""
D-05：ChatAI 辅导对话 — 发送消息。
"""
from __future__ import annotations

import uuid
from typing import Optional

from backend.公共.logger import get_logger
from backend.d_AI集成.db import get_session
from backend.d_AI集成.models.ai_conversation import AIConversation
from backend.d_AI集成.ai_service import chat

log = get_logger(__name__)


async def send_message(
    student_id: str,
    question: str,
    *,
    conv_id: Optional[str] = None,
    profile: Optional[dict] = None,
) -> dict:
    """
    发送辅导对话消息。

    :param student_id: 学生ID
    :param question: 学生问题
    :param conv_id: 对话ID（续接已有对话，不传则新开）
    :param profile: 学生画像（可选）
    :return: {"convId": str, "reply": str, "usage": dict}
    """
    if not conv_id:
        conv_id = f"conv-{uuid.uuid4().hex[:12]}"

    # 读取历史消息
    history: list[dict] = []
    try:
        async with get_session() as session:
            from sqlalchemy import select
            stmt = select(AIConversation).where(AIConversation.conv_id == conv_id)
            result = await session.execute(stmt)
            conv = result.scalar_one_or_none()
            if conv and conv.messages:
                history = conv.messages[-10:]  # 最近 10 条
    except Exception as e:
        log.warning(f"读取对话历史失败: {e}")

    # 调 AI
    ai_result = await chat(
        student_id=student_id,
        question=question,
        history=history,
        profile=profile,
    )

    reply = ai_result.get("content", "")

    # 保存到数据库
    new_messages = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": reply},
    ]
    try:
        async with get_session() as session:
            from sqlalchemy import select
            stmt = select(AIConversation).where(AIConversation.conv_id == conv_id)
            result = await session.execute(stmt)
            conv = result.scalar_one_or_none()
            if conv:
                conv.messages = new_messages
                conv.msg_count = len(new_messages)
                conv.summary = question[:100]
            else:
                conv = AIConversation(
                    conv_id=conv_id,
                    student_id=student_id,
                    ai_type="chat",
                    messages=new_messages,
                    msg_count=len(new_messages),
                    summary=question[:100],
                )
                session.add(conv)
    except Exception as e:
        log.error(f"保存对话失败: {e}")

    return {
        "convId": conv_id,
        "studentId": student_id,
        "reply": reply,
        "usage": ai_result.get("usage", {}),
        "model": ai_result.get("model", ""),
    }