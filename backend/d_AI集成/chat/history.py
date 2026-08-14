"""
D-05：ChatAI 辅导对话 — 获取历史。
"""
from __future__ import annotations

from backend.公共.logger import get_logger
from backend.d_AI集成.db import get_session
from backend.d_AI集成.models.ai_conversation import AIConversation

log = get_logger(__name__)


async def get_history(
    student_id: str,
    *,
    conv_id: str = "",
    limit: int = 20,
) -> list[dict]:
    """
    获取辅导对话历史。

    :param student_id: 学生ID
    :param conv_id: 指定对话ID（不传则返回该学生所有对话摘要）
    :param limit: 最大返回数
    :return: 对话列表
    """
    try:
        async with get_session() as session:
            from sqlalchemy import select
            if conv_id:
                stmt = (
                    select(AIConversation)
                    .where(
                        AIConversation.conv_id == conv_id,
                        AIConversation.student_id == student_id,
                    )
                )
            else:
                stmt = (
                    select(AIConversation)
                    .where(AIConversation.student_id == student_id)
                    .order_by(AIConversation.updated_at.desc())
                    .limit(limit)
                )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [row.to_dict() for row in rows]
    except Exception as e:
        log.error(f"获取对话历史失败: {e}")
        return []