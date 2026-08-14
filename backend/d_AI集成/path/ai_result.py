"""
D-05：PathAI 学习路径 — 获取生成结果。
"""
from __future__ import annotations

import json
import uuid
from typing import Optional

from backend.公共.logger import get_logger
from backend.d_AI集成.db import get_session
from backend.d_AI集成.models.ai_result import AIResult
from backend.d_AI集成.ai_service import generate_path

log = get_logger(__name__)


async def get_path_result(
    student_id: str,
    *,
    diagnosis: Optional[dict] = None,
    knowledge_chunks: Optional[list[dict]] = None,
) -> dict:
    """
    获取学习路径生成结果。

    :param student_id: 学生ID
    :param diagnosis: 学情诊断结果（来自 B 区）
    :param knowledge_chunks: 知识库切片（来自 B 区）
    :return: {"resultId": str, "path": dict, "usage": dict}
    """
    result_id = f"path-{uuid.uuid4().hex[:12]}"

    ai_result = await generate_path(
        student_id=student_id,
        diagnosis=diagnosis,
        knowledge_chunks=knowledge_chunks,
    )

    content = ai_result.get("content", "")
    try:
        path_data = json.loads(content)
    except json.JSONDecodeError:
        path_data = {"raw": content}

    # 保存到数据库
    try:
        async with get_session() as session:
            rec = AIResult(
                result_id=result_id,
                student_id=student_id,
                ai_type="path",
                input_snapshot=json.dumps(diagnosis or {}, ensure_ascii=False),
                output=json.dumps(path_data, ensure_ascii=False),
                metrics=ai_result.get("usage", {}),
            )
            session.add(rec)
    except Exception as e:
        log.error(f"保存路径结果失败: {e}")

    return {
        "resultId": result_id,
        "studentId": student_id,
        "path": path_data,
        "usage": ai_result.get("usage", {}),
        "model": ai_result.get("model", ""),
    }