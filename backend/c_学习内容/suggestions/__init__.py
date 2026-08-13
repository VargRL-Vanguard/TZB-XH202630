"""学习建议模块对外暴露。"""
from .service import (
    list_suggestions,
    mark_suggestion_read,
    save_ai_generated_suggestions,
)

__all__ = [
    "list_suggestions",
    "mark_suggestion_read",
    "save_ai_generated_suggestions",
]
