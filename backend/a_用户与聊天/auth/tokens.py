"""
JWT 签发 / 解析。

**Payload 结构**（A-01 验收标准）：
{
    "sub":   "u001",              # user_id
    "role":  "student",           # 角色
    "name":  "张三",              # 显示名（前端展示用）
    "iat":   1691750000,          # 签发时间
    "exp":   1691836400,          # 24h 过期
}

**关键点**：
- exp 必须有（24h 过期由 PyJWT 自动校验）
- role 必须在 payload 里（前端路由用）
- 用 settings.JWT_SECRET（来自 backend.公共.config）
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from backend.公共.config import settings
from backend.公共.errors import AuthError


def create_access_token(
    user_id: str,
    role: str,
    name: str = "",
    expire_hours: int | None = None,
) -> str:
    """
    签发 JWT。
    :param user_id: 用户 ID（payload['sub']）
    :param role: 角色（student/teacher/admin）
    :param name: 显示名（可选，前端展示用）
    :param expire_hours: 过期小时数（默认从 settings 读）
    :return: 编码后的 JWT 字符串
    """
    if expire_hours is None:
        expire_hours = settings.JWT_EXPIRE_HOURS

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "name": name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expire_hours)).timestamp()),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    解析 JWT。
    :return: payload dict
    :raises AuthError: 401（过期 / 伪造 / 格式错）
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise AuthError("token 已过期")
    except jwt.InvalidTokenError as e:
        raise AuthError(f"token 无效：{e}")

    # 必备字段校验
    if "sub" not in payload or "role" not in payload:
        raise AuthError("token 缺少必要字段")

    return payload
