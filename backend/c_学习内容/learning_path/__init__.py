"""学习路径服务（5 个非 AI 接口 + feedback）。"""
from . import overview, timeline, modules, tasks
from .feedback_adapter import handle_feedback
from .service import (
    get_overview,
    get_timeline,
    get_modules,
    get_tasks,
    save_ai_generated_path,
)

__all__ = [
    "get_overview",
    "get_timeline",
    "get_modules",
    "get_tasks",
    "save_ai_generated_path",
    "handle_feedback",
    "overview",
    "timeline",
    "modules",
    "tasks",
]
