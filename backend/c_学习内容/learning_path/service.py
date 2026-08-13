"""学习路径 service 层：4 个非 AI 接口 + feedback。

接口契约见 api-doc.js §3。
- GET /api/learning-path/overview
- GET /api/learning-path/timeline  （支持 status 过滤：completed/current/pending）
- GET /api/learning-path/modules
- GET /api/learning-path/tasks
- POST /api/learning-path/feedback（C-06 动态迭代用，定义在 feedback_adapter）

错误处理约定：
- 空数据 → 返回默认结构（**不要** 404）
- 数据库错误 → 返回默认结构 + 标记 source=fallback
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select

from ..db import get_session
from ..models import LearningModule, LearningPath, LearningTask

# 公共/logger 兼容兜底（loguru 未装时降级到标准 logging）
try:
    from backend.公共.logger import get_logger as _public_get_logger
    log = _public_get_logger(__name__)
except Exception:  # pragma: no cover
    log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 默认结构（空数据兜底，符合协作协议 "空数据 → 默认结构"）
# ---------------------------------------------------------------------------

def _default_overview() -> dict:
    return {
        "target": "暂未配置学习目标",
        "progress": 0,
        "estimatedDays": 0,
        "source": "fallback",
    }


def _default_timeline() -> list[dict]:
    return []


def _default_modules() -> list[dict]:
    return []


def _default_tasks() -> list[dict]:
    return []


# ---------------------------------------------------------------------------
# 接口实现
# ---------------------------------------------------------------------------

def get_overview(student_id: str) -> dict:
    """GET /api/learning-path/overview?studentId=xxx"""
    if not student_id:
        return _default_overview()
    try:
        with get_session() as s:
            row = s.execute(
                select(LearningPath)
                .where(LearningPath.student_id == student_id)
                .order_by(LearningPath.updated_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            if row is None:
                return _default_overview()
            return {
                "target": row.target,
                "progress": row.progress,
                "estimatedDays": row.estimated_days,
                "source": row.source,
            }
    except Exception as e:  # pragma: no cover - 兜底
        logger.warning("get_overview 失败, fallback: %s", e)
        return _default_overview()


def get_timeline(student_id: str, status: str | None = None) -> list[dict]:
    """GET /api/learning-path/timeline?studentId=xxx&status=completed/current/pending

    status 为 None / 'all' 时不过滤。
    """
    if not student_id:
        return _default_timeline()
    try:
        with get_session() as s:
            stmt = (
                select(LearningModule)
                .join(LearningPath, LearningModule.path_id == LearningPath.path_id)
                .where(LearningPath.student_id == student_id)
                .order_by(LearningModule.order_index.asc())
            )
            if status and status != "all":
                if status not in ("completed", "current", "pending"):
                    return _default_timeline()
                stmt = stmt.where(LearningModule.status == status)
            rows = s.execute(stmt).scalars().all()
            return [
                {
                    "id": idx + 1,  # 兼容前端按数字 id 取值
                    "moduleId": m.module_id,
                    "title": m.name,
                    "desc": m.desc,
                    "status": m.status,
                    "progress": m.progress,
                    "duration": m.duration,
                    "startDate": m.start_date,
                    "endDate": m.end_date,
                }
                for idx, m in enumerate(rows)
            ]
    except Exception as e:  # pragma: no cover
        logger.warning("get_timeline 失败, fallback: %s", e)
        return _default_timeline()


def get_modules(student_id: str) -> list[dict]:
    """GET /api/learning-path/modules?studentId=xxx"""
    if not student_id:
        return _default_modules()
    try:
        with get_session() as s:
            rows = (
                s.execute(
                    select(LearningModule)
                    .join(LearningPath, LearningModule.path_id == LearningPath.path_id)
                    .where(LearningPath.student_id == student_id)
                    .order_by(LearningModule.order_index.asc())
                )
                .scalars()
                .all()
            )
            return [
                {"name": m.name, "progress": m.progress, "desc": m.desc}
                for m in rows
            ]
    except Exception as e:  # pragma: no cover
        logger.warning("get_modules 失败, fallback: %s", e)
        return _default_modules()


def get_tasks(student_id: str) -> list[dict]:
    """GET /api/learning-path/tasks?studentId=xxx

    返回今日任务清单（due_date == today 或 completed=0 的前 N 个）。
    """
    if not student_id:
        return _default_tasks()
    try:
        with get_session() as s:
            rows = (
                s.execute(
                    select(LearningTask)
                    .join(LearningModule, LearningTask.module_id == LearningModule.module_id)
                    .join(LearningPath, LearningModule.path_id == LearningPath.path_id)
                    .where(LearningPath.student_id == student_id)
                    .order_by(LearningTask.completed.asc(), LearningTask.due_date.asc())
                    .limit(20)
                )
                .scalars()
                .all()
            )
            return [
                {
                    "id": idx + 1,
                    "taskId": t.task_id,
                    "title": t.title,
                    "meta": t.meta,
                    "priority": t.priority,
                    "completed": bool(t.completed),
                }
                for idx, t in enumerate(rows)
            ]
    except Exception as e:  # pragma: no cover
        log.warning(f"get_tasks 失败, fallback: {e}")
        return _default_tasks()


# ---------------------------------------------------------------------------
# 给 D 调用的写回方法
# ---------------------------------------------------------------------------

def save_ai_generated_path(student_id: str, content: str) -> dict:
    """D 写回 AI 生成的学习路径（保留历史版本于 ResourceVersion 体系外，路径主表用 source=ai 标记）。

    参数：
        student_id: 学生 id
        content: AI 生成的路径 JSON 字符串 / Markdown

    返回：
        {"pathId": "...", "modules": N}
    """
    if not student_id:
        raise ValueError("student_id 不能为空")
    from ..models import LearningPath, LearningModule

    import json as _json
    try:
        payload = _json.loads(content) if content.strip().startswith(("{", "[")) else {"raw": content}
    except _json.JSONDecodeError:
        payload = {"raw": content}

    target = str(payload.get("target", "掌握 AI 推荐的目标"))
    modules_in = payload.get("modules") or []

    with get_session() as s:
        # 取最新一条 path
        existing = s.execute(
            select(LearningPath)
            .where(LearningPath.student_id == student_id)
            .order_by(LearningPath.updated_at.desc())
        ).scalar_one_or_none()

        if existing is not None:
            path = existing
            path.target = target  # 用最新内容覆盖
            path.source = "ai"
            path.version += 1
        else:
            path = LearningPath(student_id=student_id, source="ai", target=target)
            s.add(path)
            s.flush()  # 取 path_id

        # 清掉旧 modules，覆写
        s.query(LearningModule).filter(LearningModule.path_id == path.path_id).delete()

        for idx, m in enumerate(modules_in if isinstance(modules_in, list) else []):
            s.add(LearningModule(
                path_id=path.path_id,
                name=str(m.get("name", f"模块{idx + 1}")),
                desc=str(m.get("desc", "")),
                progress=int(m.get("progress", 0)),
                order_index=idx,
                status=str(m.get("status", "pending")),
                start_date=str(m.get("startDate", "")),
                end_date=str(m.get("endDate", "")),
                duration=str(m.get("duration", "")),
            ))

        return {"pathId": path.path_id, "modules": len(modules_in) if isinstance(modules_in, list) else 0}
