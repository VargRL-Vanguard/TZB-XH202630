"""
A-02 用户信息 + 学习者画像模块。

**对外暴露的依赖**（B/C/D 也能用）：
    from backend.a_用户与聊天.user.deps import get_current_user
"""
from backend.a_用户与聊天.user.deps import get_current_user  # noqa: F401

__all__ = ["get_current_user"]
