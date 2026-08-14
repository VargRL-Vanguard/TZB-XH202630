"""
D 区自有数据层：连接池 + Session 上下文管理器。

**重要**：
- 这个文件只在 D 区内部使用
- A / B / C 通过 audit() / orchestrate() 等模块级函数访问
- **禁止** A / B / C 直接 from backend.d_AI集成.db import engine
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.d_AI集成.config import d_config
from backend.d_AI集成.models import Base  # noqa: F401

engine = create_async_engine(
    d_config.AI_INTEGRATION_DB_URL,
    echo=d_config.DB_ECHO,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """异步 session 上下文管理器。正常退出自动 commit，异常自动 rollback。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    """幂等建表。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """清库（仅单测用）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


init_tables = create_all_tables