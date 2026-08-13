"""C 区 ORM 模型（按表分文件）。

包含 6 张表：
- LearningPath / LearningModule / LearningTask : 学习路径主结构（C-01）
- Suggestion : 学习建议（C-02）
- Resource : 3 种形态资源（夺奖新增 C-04）
- ResourceVersion : 资源历史版本（夺奖新增 C-04）
- InteractionLog : 答题反馈日志（夺奖新增 C-06）
"""
from .base import Base
from .learning_path import LearningPath, LearningModule, LearningTask
from .suggestion import Suggestion
from .resource import Resource
from .resource_version import ResourceVersion
from .interaction_log import InteractionLog

__all__ = [
    "Base",
    "LearningPath",
    "LearningModule",
    "LearningTask",
    "Suggestion",
    "Resource",
    "ResourceVersion",
    "InteractionLog",
]
