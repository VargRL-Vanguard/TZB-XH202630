"""
POST /api/auth/logout —— 用户登出，token 加入黑名单。

**鉴权**：需要从 Authorization: Bearer <token> 解析当前用户。

**为什么需要鉴权**：防止恶意调用者登出别人的 token。
                （虽然 token 本身可以伪造，但至少要拿到有效 token 才能加入黑名单）
"""
from fastapi import APIRouter, Header

from backend.公共.errors import AuthError
from backend.公共.response import ok
from backend.公共.logger import get_logger

from backend.a_用户与聊天.auth.schemas import LogoutResponse
from backend.a_用户与聊天.auth.tokens import decode_access_token
from backend.a_用户与聊天.auth.blacklist import add_to_blacklist, is_blacklisted

log = get_logger(__name__)
router = APIRouter()


def _extract_bearer_token(authorization: str | None) -> str:
    """从 Authorization: Bearer <token> 提取 token。"""
    if not authorization:
        raise AuthError("缺少 Authorization 头")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError("Authorization 头格式错误（应为 'Bearer <token>'）")
    return parts[1].strip()


@router.post("/logout", response_model=None, summary="用户登出")
async def logout(authorization: str | None = Header(default=None)) -> dict:
    """
    把当前 token 加入黑名单。
    - 后续用此 token 调用任何接口 → 401
    - 注意：JWT 本身仍然 24h 过期，黑名单是"立即失效"
    """
    token = _extract_bearer_token(authorization)

    # 1. 验证 token 有效性
    payload = decode_access_token(token)

    # 2. 二次检查：已经被登出过？
    if is_blacklisted(token):
        raise AuthError("token 已失效（已登出）")

    # 3. 加入黑名单
    add_to_blacklist(token)
    log.info(f"用户登出: userId={payload.get('sub')}")

    return ok(
        data=LogoutResponse(ok=True).model_dump(),
        message="登出成功",
    )
