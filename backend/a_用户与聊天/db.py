"""
A 区自有数据层：连接池 + Session 上下文管理器 + 跨区业务函数。

**重要**：
- 这个文件**只**在 A 区内部使用
- B / C / D 通过 `get_user_by_id` / `get_learner_profile` 模块级函数访问 A 的数据
- **禁止** B / C / D 直接 `from backend.a_用户与聊天.db import engine`（要数据走函数）
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.a_用户与聊天.config import a_config
from backend.a_用户与聊天.models.base import Base  # noqa: F401  # 注册到 metadata

# 引擎单例（进程级别）
# **关键**：用 NullPool 而不是默认连接池
# 原因：pytest-asyncio 默认每个测试新建 event loop，连接池绑第一个 loop 后，
#       后续测试用新 loop 调 engine 会触发 'Event loop is closed'
# NullPool 每次新建连接、用完即关，天然规避 loop 生命周期问题
# A 区并发不高（用户聊天），损失可忽略；后续要扩展再换回 QueuePool
engine = create_async_engine(
    a_config.USER_CHAT_DB_URL,
    echo=a_config.DB_ECHO,
    poolclass=NullPool,
)

# Session 工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ---------------- Session 上下文管理器 ----------------

@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    异步 session 上下文管理器。
    - 正常退出 → 自动 commit
    - 异常退出 → 自动 rollback + 重新抛出
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------- 跨区业务函数（暴露给 S-02 / B 的学情诊断 Agent）----------------

async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    S-02 鉴权中间件 / 任务 6 使用。
    :return: {userId, name, role} 或 None
    """
    # 延迟导入避免循环
    from backend.a_用户与聊天.models.user import User

    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return None
        return {
            "userId": user.id,
            "name": user.name,
            "role": user.role,
        }


async def get_learner_profile(user_id: str) -> Optional[dict]:
    """
    B 的学情诊断 Agent 使用。
    :return: {education, major, theoryTestScore, weakKPs[], strongKPs[], updatedAt} 或 None
    """
    from backend.a_用户与聊天.models.learner_profile import LearnerProfile

    async with get_session() as session:
        result = await session.execute(
            select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        )
        lp = result.scalar_one_or_none()
        if not lp:
            return None
        return {
            "education": lp.education,
            "major": lp.major,
            "theoryTestScore": lp.theory_test_score,
            "weakKPs": lp.weak_kps or [],
            "strongKPs": lp.strong_kps or [],
            "updatedAt": lp.updated_at.isoformat() if lp.updated_at else None,
        }


async def upsert_learner_profile(
    user_id: str,
    *,
    education: Optional[str] = None,
    major: Optional[str] = None,
    theory_test_score: Optional[int] = None,
    weak_kps: Optional[list] = None,
    strong_kps: Optional[list] = None,
) -> dict:
    """
    A-02 任务使用 + B-05 学情诊断后回写 weak_kps。
    不存在则插入，存在则更新。
    """
    from backend.a_用户与聊天.models.learner_profile import LearnerProfile

    async with get_session() as session:
        result = await session.execute(
            select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        )
        lp = result.scalar_one_or_none()
        if not lp:
            lp = LearnerProfile(
                user_id=user_id,
                education=education,
                major=major,
                theory_test_score=theory_test_score,
                weak_kps=weak_kps or [],
                strong_kps=strong_kps or [],
            )
            session.add(lp)
        else:
            if education is not None:
                lp.education = education
            if major is not None:
                lp.major = major
            if theory_test_score is not None:
                lp.theory_test_score = theory_test_score
            if weak_kps is not None:
                lp.weak_kps = weak_kps
            if strong_kps is not None:
                lp.strong_kps = strong_kps
        await session.flush()
        return await get_learner_profile(user_id)
