"""
POST /api/auth/login —— 用户登录，签发 JWT。

**安全要点**（A-01 验收标准）：
- 错误密码 / 用户不存在 → **统一返回** "用户名或密码错误"（**不**暴露用户是否存在，防枚举）
- JWT 必须含 `role` 和 `exp`（24h）
"""
from fastapi import APIRouter

from backend.公共.errors import AuthError
from backend.公共.response import ok
from backend.公共.logger import get_logger

from backend.a_用户与聊天.auth.schemas import LoginRequest, LoginResponse
from backend.a_用户与聊天.auth.passwords import verify_password
from backend.a_用户与聊天.auth.tokens import create_access_token
from backend.a_用户与聊天.db import get_session

log = get_logger(__name__)
router = APIRouter()


@router.post("/login", response_model=None, summary="用户登录")
async def login(req: LoginRequest) -> dict:
    """
    用户名 + 密码登录，签发 JWT。
    - 返回 `{token, userId, role}`
    - 错误密码/用户不存在 → 401 统一消息（防用户名枚举）
    """
    from backend.a_用户与聊天.models.user import User
    from sqlalchemy import select

    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.username == req.username)
        )
        user = result.scalar_one_or_none()

        # 关键：用户不存在 OR 密码错 → 抛同一个错误
        if user is None or not verify_password(req.password, user.password_hash):
            log.warning(f"登录失败: username={req.username}")
            raise AuthError("用户名或密码错误")

        # 签发 JWT
        token = create_access_token(
            user_id=user.id,
            role=user.role,
            name=user.name,
        )

    log.info(f"登录成功: userId={user.id} role={user.role}")

    return ok(
        data=LoginResponse(
            token=token,
            userId=user.id,
            role=user.role,
        ).model_dump(),
        message="登录成功",
    )
