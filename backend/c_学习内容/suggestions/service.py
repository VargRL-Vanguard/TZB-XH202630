"""学习建议 service 层。"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

from ..db import get_session
from ..models import Suggestion

# 公共/logger 兼容兜底（loguru 未装时降级到标准 logging）
try:
    from backend.公共.logger import get_logger as _public_get_logger
    log = _public_get_logger(__name__)
except Exception:  # pragma: no cover
    log = logging.getLogger(__name__)
# 兼容：保留旧名 logger
logger = log

ALLOWED_CATEGORIES = {"all", "method", "resource", "review", "practice", ""}

CATEGORY_LABELS = {
    "method": "方法建议",
    "resource": "资源推荐",
    "review": "复习建议",
    "practice": "练习推荐",
    "all": "全部",
}

PRIORITY_LABELS = {"high": "重要", "medium": "普通", "low": "可选"}


def _serialize(row: Suggestion) -> dict:
    return {
        "id": row.suggestion_id,
        "title": row.title,
        "content": row.content,
        "category": row.category,
        "categoryLabel": row.category_label or CATEGORY_LABELS.get(row.category, ""),
        "priority": row.priority,
        "priorityLabel": row.priority_label or PRIORITY_LABELS.get(row.priority, ""),
        "source": row.source,
        "isRead": bool(row.is_read),
        "createdAt": row.created_at.isoformat() if row.created_at else "",
    }


def list_suggestions(student_id: str, category: str = "all") -> list[dict]:
    """GET /api/suggestions/list?studentId&category"""
    if category not in ALLOWED_CATEGORIES:
        category = "all"
    if not student_id:
        return []
    try:
        with get_session() as s:
            stmt = select(Suggestion).where(Suggestion.student_id == student_id)
            if category and category != "all":
                stmt = stmt.where(Suggestion.category == category)
            stmt = stmt.order_by(Suggestion.created_at.desc()).limit(200)
            rows = s.execute(stmt).scalars().all()
            return [_serialize(r) for r in rows]
    except Exception as e:  # pragma: no cover
        logger.warning("list_suggestions 失败, fallback: %s", e)
        return []


def mark_suggestion_read(student_id: str, suggestion_id: str) -> bool:
    """POST /api/suggestions/read"""
    from datetime import datetime, timezone

    if not student_id or not suggestion_id:
        return False
    try:
        with get_session() as s:
            row = s.execute(
                select(Suggestion).where(
                    Suggestion.student_id == student_id,
                    Suggestion.suggestion_id == suggestion_id,
                )
            ).scalar_one_or_none()
            if row is None:
                return False
            row.is_read = 1
            row.read_at = datetime.now(timezone.utc)
            return True
    except Exception as e:  # pragma: no cover
        log.warning(f"mark_suggestion_read 失败: {e}")
        return False


def save_ai_generated_suggestions(student_id: str, content: str) -> dict:
    """D 写回 AI 生成的学习建议。

    参数：
        student_id: 学生 id
        content: JSON 字符串，形如
            {"suggestions": [{"title":..., "content":..., "category":..., "priority":..., "source":...}]}

    返回：
        {"saved": N}
    """
    if not student_id:
        raise ValueError("student_id 不能为空")
    import json as _json
    try:
        payload = _json.loads(content) if content.strip().startswith(("{", "[")) else {}
    except _json.JSONDecodeError:
        payload = {"raw": content}

    items = payload.get("suggestions") or payload.get("items") or []
    if not isinstance(items, list):
        items = []

    saved = 0
    with get_session() as s:
        for it in items:
            if not isinstance(it, dict):
                continue
            cat = str(it.get("category", "practice"))
            if cat not in {"method", "resource", "review", "practice"}:
                cat = "practice"
            prio = str(it.get("priority", "medium"))
            if prio not in {"high", "medium", "low"}:
                prio = "medium"
            s.add(Suggestion(
                student_id=student_id,
                title=str(it.get("title", ""))[:255],
                content=str(it.get("content", "")),
                category=cat,
                category_label=CATEGORY_LABELS.get(cat, ""),
                priority=prio,
                priority_label=PRIORITY_LABELS.get(prio, ""),
                source=str(it.get("source", "ai"))[:128],
                extra=it.get("extra", {}),
            ))
            saved += 1
    return {"saved": saved}
