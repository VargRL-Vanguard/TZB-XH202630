"""
D-01 / D-02：AI Provider 包。

对外暴露：
  - BaseAIProvider — 抽象基类
  - ChatAIProvider / PathAIProvider / SuggestAIProvider / EmbedAIProvider — 实现
"""
from backend.d_AI集成.providers.base import BaseAIProvider  # noqa: F401
from backend.d_AI集成.providers.chat_ai import ChatAIProvider  # noqa: F401
from backend.d_AI集成.providers.path_ai import PathAIProvider  # noqa: F401
from backend.d_AI集成.providers.suggest_ai import SuggestAIProvider  # noqa: F401
from backend.d_AI集成.providers.embed_ai import EmbedAIProvider  # noqa: F401

__all__ = [
    "BaseAIProvider",
    "ChatAIProvider",
    "PathAIProvider",
    "SuggestAIProvider",
    "EmbedAIProvider",
]