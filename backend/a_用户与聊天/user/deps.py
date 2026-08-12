"""
A 区鉴权依赖：get_current_user（**A-02 提取出来复用**）。

**为什么提取出来**：
- A-01 的 logout.py 已经有解析 Authorization 头的逻辑
- A-02 的 /api/user/info 和 /api/user/profile 都需要鉴权
- 提取成 FastAPI Depends 依赖，3 处复用，行为一致

**B/C/D 使用方式**（在主项目里）：
    from backend.a_用户与聊天.user.deps import get_current_user
    @router.get(...)
    async def my_endpoint(user: dict = Depends(get_current_user)):
        ...
"""
from typing import Optional

from fastapi import Header

from backend.公共.errors import AuthError
from backend.a_用户与聊天.auth.tokens import decode_access_token
from backend.a_用户与聊天.auth.blacklist import is_blacklisted


def _extract_bearer_token(authorization: Optional[str]) -> str:
    """从 Authorization: Bearer <token> 提取 token。"""
    if not authorization:
        raise AuthError("缺少 Authorization 头")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError("Authorization 头格式错误（应为 'Bearer <token>'）")
    return parts[1].strip()


async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """
    FastAPI 依赖：从 Authorization 头解析当前用户。

    :return: dict 含 sub (userId) / role / name
    :raises: AuthError (401) - 缺头 / 格式错 / token 无效 / token 过期 / token 已登出
    """
    token = _extract_bearer_token(authorization)

    # 1. 解码 + 验证签名 + 验证 exp
    payload = decode_access_token(token)

    # 2. 检查黑名单（登出后 token 立即失效）
    if is_blacklisted(token):
        raise AuthError("token 已失效（已登出）")

    return payload  # {"sub": "u001", "role": "student", "name": "张三", "exp": ...}
