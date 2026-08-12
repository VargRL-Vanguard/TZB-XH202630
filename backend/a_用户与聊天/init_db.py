"""
A-00 一键建库脚本：
1. 解析 USER_CHAT_DB_URL，先连 MySQL server 建库（utf8mb4）
2. 用 SQLAlchemy 在库里建所有表

用法：
    cd D:\\TZB\\TZB-XH202630
    python -m backend.a_用户与聊天.init_db
"""
import asyncio
from urllib.parse import urlparse

import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine

from backend.a_用户与聊天.config import a_config
# 关键：导入模型以注册到 Base.metadata
from backend.a_用户与聊天.models.base import Base  # noqa: F401
from backend.a_用户与聊天.models.user import User  # noqa: F401
from backend.a_用户与聊天.models.learner_profile import LearnerProfile  # noqa: F401
from backend.a_用户与聊天.models.message import Message  # noqa: F401


def _parse_url(url: str) -> dict:
    """从 SQLAlchemy URL 解析出 host/port/user/password/dbname。"""
    # 去掉驱动前缀（mysql+aiomysql → mysql）
    cleaned = url.replace("+aiomysql", "").replace("+pymysql", "")
    u = urlparse(cleaned)
    return {
        "host": u.hostname or "localhost",
        "port": u.port or 3306,
        "user": u.username or "root",
        "password": u.password or "",
        "dbname": u.path.lstrip("/").split("?")[0],
    }


async def create_database_if_not_exists() -> str:
    """连 MySQL server 建库（如果还没建）。"""
    info = _parse_url(a_config.USER_CHAT_DB_URL)
    if not info["dbname"]:
        raise ValueError("USER_CHAT_DB_URL 必须包含数据库名（如 tzb_user_chat）")

    conn = await aiomysql.connect(
        host=info["host"],
        port=info["port"],
        user=info["user"],
        password=info["password"],
        autocommit=True,
        charset="utf8mb4",
    )
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{info['dbname']}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        return info["dbname"]
    finally:
        conn.close()


async def create_tables() -> None:
    """用 SQLAlchemy 建所有表。"""
    engine = create_async_engine(a_config.USER_CHAT_DB_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


async def main() -> None:
    print("=" * 60)
    print("  A-00 初始化：建库 + 建表")
    print("=" * 60)
    print(f"URL  : {a_config.USER_CHAT_DB_URL}")
    print(f"驱动 : aiomysql + SQLAlchemy 2.0 async")
    print("-" * 60)

    dbname = await create_database_if_not_exists()
    print(f"✅ 数据库 `{dbname}` 已就绪（utf8mb4）")

    await create_tables()
    print(f"✅ 表已创建：{', '.join(Base.metadata.tables.keys())}")

    print("-" * 60)
    print("下一步：")
    print("  python -m backend.a_用户与聊天.seed_data   # 插入 3 个测试用户")
    print("  pytest backend/a_用户与聊天/tests/ -v        # 跑连接测试")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
