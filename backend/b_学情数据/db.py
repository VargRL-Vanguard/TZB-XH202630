"""
B 区自有数据层：连接池 + Session 上下文管理器 + 跨区业务函数。

**重要**：
- 这个文件只在 B 区内部使用
- A / C / D 通过 get_kb_chunk / list_kb_chunks_by_kp 等模块级函数访问
- **禁止** A / C / D 直接 from backend.b_学情数据.db import engine
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.b_学情数据.config import b_config
from backend.b_学情数据.models import Base  # noqa: F401  # 注册到 metadata

# 引擎单例（进程级别）
# **关键**：用 NullPool 而不是默认连接池
# 原因：pytest-asyncio 默认每个测试新建 event loop，连接池绑第一个 loop 后，
#       后续测试用新 loop 调 engine 会触发 'Event loop is closed'
# NullPool 每次新建连接、用完即关，天然规避 loop 生命周期问题
engine = create_async_engine(
    b_config.STUDENT_DATA_DB_URL,
    echo=b_config.DB_ECHO,
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


# ---------------- 建表工具（测试用 + init_db 用） ----------------

async def create_all_tables() -> None:
    """
    幂等建表：SQLite / MySQL 都能跑。
    注意：正式环境用 Alembic，这里只给 MVP + 单测用。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """清库：只给单测 tearDown 用。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# 别名：ingest.py / eval_coverage.py / B-08 脚本统一用 init_tables
init_tables = create_all_tables


# ---------------- 跨区业务函数：知识库检索 ----------------

async def get_kb_chunk(chunk_id: str) -> Optional[dict]:
    """
    暴露给 D 的领域专家 Agent：按 chunk_id 取切片详情。
    :return: KbChunk dict 或 None
    """
    from backend.b_学情数据.models.kb_chunk import KbChunk

    async with get_session() as session:
        chunk = await session.get(KbChunk, chunk_id)
        if not chunk:
            return None
        return chunk.to_dict()


async def list_kb_chunks_by_kp(kp_id: str, limit: int = 20) -> list[dict]:
    """
    暴露给 A-05 quality_check / C-04 领域专家 Agent：
    按 kp_id 检索挂载了该知识点的所有切片。
    :param kp_id: 知识点 ID（精确匹配 kp_tags 数组中的某一项）
    :param limit: 返回条数上限
    :return: list[KbChunk dict]
    """
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import func, JSON as SAJSON, String, text

    async with get_session() as session:
        if "mysql" in b_config.STUDENT_DATA_DB_URL:
            # MySQL: 使用原生 JSON_CONTAINS
            stmt = (
                select(KbChunk)
                .where(
                    func.json_contains(
                        KbChunk.kp_tags.cast(SAJSON),
                        f'"{kp_id}"',
                    )
                )
                .order_by(KbChunk.doc_id, KbChunk.seq_index)
                .limit(limit)
            )
            result = await session.execute(stmt)
            chunks = result.scalars().all()
        else:
            # SQLite/其他：先查全部再在 Python 层过滤
            # （MVP 阶段 chunk 总量 ≤ 300，全表扫描可接受）
            stmt = (
                select(KbChunk)
                .order_by(KbChunk.doc_id, KbChunk.seq_index)
            )
            result = await session.execute(stmt)
            all_chunks = result.scalars().all()
            # 精确匹配：kp_id 在 kp_tags 列表中
            chunks = [
                c for c in all_chunks
                if isinstance(c.kp_tags, list) and kp_id in c.kp_tags
            ][:limit]
        return [c.to_dict() for c in chunks]
