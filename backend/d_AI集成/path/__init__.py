"""
D-05：PathAI 业务接口包。

对外暴露：
  - get_path_result() — 获取学习路径生成结果
"""
from backend.d_AI集成.path.ai_result import get_path_result  # noqa: F401

__all__ = ["get_path_result"]