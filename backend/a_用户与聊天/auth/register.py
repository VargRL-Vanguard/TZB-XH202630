"""
POST /api/auth/register —— 用户注册。

**业务规则**（A-01 验收标准）：
- role 必须 ∈ {student, teacher, admin}
- username 唯一（重复 → BizError 400 "用户名已存在"）
- 密码强度：≥ 8 位 + 字母 + 数字（不够 → BizError 400）
- 自动创建 User + 可选 LearnerProfile
"""
import uuid
from fastapi import APIRouter

from backend.公共.errors import BizError
from backend.公共.response import ok
from backend.公共.logger import get_logger

from backend.a_用户与聊天.auth.schemas import RegisterRequest, RegisterResponse
from backend.a_用户与聊天.auth.passwords import hash_password, ensure_strong_password
from backend.a_用户与聊天.db import get_session

log = get_logger(__name__)
router = APIRouter()


@router.post("/register", response_model=None, summary="用户注册")
async def register(req: RegisterRequest) -> dict:
    """
    注册新用户。
    - **username** 唯一
    - **password** 强度校验：≥ 8 位 + 字母 + 数字
    - **role** ∈ {student, teacher, admin}
    - 注册成功自动创建 LearnerProfile（如果给了 education/major）
    """
    # 1. 密码强度
    ensure_strong_password(req.password)

    # 2. 延迟导入模型（避免循环）
    from backend.a_用户与聊天.models.user import User
    from backend.a_用户与聊天.models.learner_profile import LearnerProfile
    from sqlalchemy import select

    # 3. 检查 username 是否已存在
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.username == req.username)
        )
        if result.scalar_one_or_none() is not None:
            raise BizError("用户名已存在", code=400)

        # 4. 生成 userId（u + 6位随机）
        user_id = "u" + uuid.uuid4().hex[:6]
        # 5. 哈希密码
        pwd_hash = hash_password(req.password)

        # 6. INSERT User
        user = User(
            id=user_id,
            username=req.username,
            password_hash=pwd_hash,
            name=req.name,
            role=req.role,
        )
        session.add(user)
        await session.flush()  # 先 INSERT 满足外键

        # 7. 如果有 education/major → 同步建 LearnerProfile
        if req.education or req.major:
            profile = LearnerProfile(
                user_id=user_id,
                education=req.education,
                major=req.major,
                weak_kps=[],
                strong_kps=[],
            )
            session.add(profile)
            await session.flush()

    log.info(f"用户注册成功: userId={user_id} role={req.role}")

    return ok(
        data=RegisterResponse(userId=user_id).model_dump(),
        message="注册成功",
    )
