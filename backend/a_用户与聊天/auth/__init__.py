"""
A 区鉴权模块：A-01 注册/登录/登出 + token 黑名单 + JWT。

**接口契约**（前端 + B/C/D 必看）：
- POST /api/auth/register  → {username, password, name, role, education?, major?}  → {userId}
- POST /api/auth/login     → {username, password}                                   → {token, userId, role}
- POST /api/auth/logout    → Authorization: Bearer <token>                           → {ok: true}

**B/C/D 调用方式**（后续 S-02 会封装 get_current_user）：
    from backend.a_用户与聊天.auth.tokens import decode_access_token
    payload = decode_access_token(token)  # {'sub': 'u001', 'role': 'student', 'exp': ...}
"""
from backend.a_用户与聊天.auth.passwords import (  # noqa: F401
    hash_password,
    verify_password,
    validate_password_strength,
)
from backend.a_用户与聊天.auth.tokens import (  # noqa: F401
    create_access_token,
    decode_access_token,
)
from backend.a_用户与聊天.auth.blacklist import (  # noqa: F401
    add_to_blacklist,
    is_blacklisted,
)

__all__ = [
    "hash_password", "verify_password", "validate_password_strength",
    "create_access_token", "decode_access_token",
    "add_to_blacklist", "is_blacklisted",
]
