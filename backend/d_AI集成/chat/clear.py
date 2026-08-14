"""
D-05：ChatAI 辅导对话 — 清空历史。
"""
from __future__ import annotations

from backend.公共.logger import get_logger
from backend.d_AI集成.db import get_session
from backend.d_AI集成.models.ai_conversation import AIConversation

log = get_logger(__name__)


async def clear_history(student_id: str, *, conv_id: str = "") -> dict:
    """
    清空辅导对话历史。

    :param student_id: 学生ID
    :param conv_id: 指定对话ID（不传则清空该学生全部对话）
    :return: {"deleted": int}
    """
    try:
        async with get_session() as session:
            from sqlalchemy import delete
            if conv_id:
                stmt = delete(AIConversation).where(
                    AIConversation.conv_id == conv_id,
                    AIConversation.student_id == student_id,
                )
            else:
                stmt = delete(AIConversation).where(
                    AIConversation.student_id == student_id,
                )
            result = await session.execute(stmt)
            deleted = result.rowcount
            return {"deleted": deleted, "studentId": student_id}
    except Exception as e:
        log.error(f"清空对话历史失败: {e}")
        return {"deleted": 0, "studentId": student_id, "error": str(e)}