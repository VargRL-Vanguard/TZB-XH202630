"""
D-05：SuggestAI 业务接口包。

对外暴露：
  - get_suggest_result() — 获取学习建议生成结果
"""
from backend.d_AI集成.suggest.ai_result import get_suggest_result  # noqa: F401

__all__ = ["get_suggest_result"]