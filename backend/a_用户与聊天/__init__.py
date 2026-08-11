"""
A 区（用户与聊天）包入口。
**B/C/D 可通过以下方式调用 A 暴露的能力**：

    from backend.a_用户与聊天 import get_user_by_id, get_learner_profile
    from backend.a_用户与聊天.db import get_session, engine
"""
from backend.a_用户与聊天.config import a_config  # noqa: F401
from backend.a_用户与聊天.db import (  # noqa: F401
    engine,
    AsyncSessionLocal,
    get_session,
    get_user_by_id,
    get_learner_profile,
)

__all__ = [
    "a_config",
    "engine",
    "AsyncSessionLocal",
    "get_session",
    "get_user_by_id",
    "get_learner_profile",
]
