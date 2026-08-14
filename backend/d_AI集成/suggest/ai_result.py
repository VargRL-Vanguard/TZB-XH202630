"""
D-05：SuggestAI 学习建议 — 获取生成结果。
"""
from __future__ import annotations

import json
import uuid
from typing import Optional

from backend.公共.logger import get_logger
from backend.d_AI集成.db import get_session
from backend.d_AI集成.models.ai_result import AIResult
from backend.d_AI集成.ai_service import generate_suggestions

log = get_logger(__name__)


async def get_suggest_result(
    student_id: str,
    *,
    diagnosis: Optional[dict] = None,
    activities: Optional[list[dict]] = None,
) -> dict:
    """
    获取学习建议生成结果。

    :param student_id: 学生ID
    :param diagnosis: 学情诊断结果（来自 B 区）
    :param activities: 最近学习活动（来自 B 区）
    :return: {"resultId": str, "suggestions": list, "usage": dict}
    """
    result_id = f"sug-{uuid.uuid4().hex[:12]}"

    ai_result = await generate_suggestions(
        student_id=student_id,
        diagnosis=diagnosis,
        activities=activities,
    )

    content = ai_result.get("content", "")
    try:
        suggestions_data = json.loads(content)
    except json.JSONDecodeError:
        suggestions_data = [{"content": content}]

    # 保存到数据库
    try:
        async with get_session() as session:
            rec = AIResult(
                result_id=result_id,
                student_id=student_id,
                ai_type="suggest",
                input_snapshot=json.dumps(diagnosis or {}, ensure_ascii=False),
                output=json.dumps(suggestions_data, ensure_ascii=False),
                metrics=ai_result.get("usage", {}),
            )
            session.add(rec)
    except Exception as e:
        log.error(f"保存建议结果失败: {e}")

    return {
        "resultId": result_id,
        "studentId": student_id,
        "suggestions": suggestions_data if isinstance(suggestions_data, list) else [suggestions_data],
        "usage": ai_result.get("usage", {}),
        "model": ai_result.get("model", ""),
    }