"""
D-05：ChatAI 业务接口包。

对外暴露：
  - send_message() — 发送辅导对话消息
  - get_history() — 获取对话历史
  - clear_history() — 清空对话历史
"""
from backend.d_AI集成.chat.send import send_message  # noqa: F401
from backend.d_AI集成.chat.history import get_history  # noqa: F401
from backend.d_AI集成.chat.clear import clear_history  # noqa: F401

__all__ = ["send_message", "get_history", "clear_history"]