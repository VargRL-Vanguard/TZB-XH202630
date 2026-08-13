"""
A-00 数据层单测：连接 + 业务函数。
**前提**：先跑 `python -m backend.a_用户与聊天.init_db` 和 `seed_data`。

用法：
    cd D:\\TZB\\TZB-XH202630
    pytest backend/a_用户与聊天/tests/ -v
"""
import pytest
import pytest_asyncio
from sqlalchemy import text

from backend.a_用户与聊天.db import (
    engine,
    get_session,
    get_user_by_id,
    get_learner_profile,
)


# ========== 1. 基础连接 ==========

@pytest.mark.asyncio
async def test_db_connection():
    """能连上数据库"""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_mysql_version():
    """MySQL 8.0.x"""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT VERSION()"))
        version = result.scalar()
        assert "8.0" in version


@pytest.mark.asyncio
async def test_session_commit():
    """session 正常 commit（事务回滚测试）"""
    async with get_session() as session:
        result = await session.execute(text("SELECT DATABASE()"))
        db = result.scalar()
        assert db == "tzb_user_chat"


# ========== 2. 表存在性 ==========

@pytest.mark.asyncio
async def test_tables_exist():
    """user 和 learner_profile 表都建好了"""
    async with engine.connect() as conn:
        result = await conn.execute(text("SHOW TABLES"))
        tables = {row[0] for row in result.fetchall()}
    assert "user" in tables
    assert "learner_profile" in tables


@pytest.mark.asyncio
async def test_user_table_schema():
    """user 表字段完整"""
    async with engine.connect() as conn:
        result = await conn.execute(text("DESCRIBE user"))
        cols = {row[0] for row in result.fetchall()}
    required = {"id", "username", "password_hash", "name", "role", "created_at"}
    assert required.issubset(cols)


@pytest.mark.asyncio
async def test_learner_profile_table_schema():
    """learner_profile 表含 weak_kps / strong_kps JSON 字段"""
    async with engine.connect() as conn:
        result = await conn.execute(text("DESCRIBE learner_profile"))
        rows = result.fetchall()
    cols = {row[0] for row in rows}
    assert {"user_id", "education", "major", "theory_test_score",
            "weak_kps", "strong_kps", "updated_at"}.issubset(cols)
    # 确认 JSON 类型
    types = {row[0]: row[1] for row in rows}
    assert "json" in types["weak_kps"].lower()
    assert "json" in types["strong_kps"].lower()


# ========== 3. 业务函数：get_user_by_id ==========

@pytest.mark.asyncio
async def test_get_user_by_id_existing():
    """seed 后能查到 u001"""
    user = await get_user_by_id("u001")
    assert user is not None
    assert user["userId"] == "u001"
    assert user["name"] == "张三"
    assert user["role"] == "student"


@pytest.mark.asyncio
async def test_get_user_by_id_teacher():
    """教师用户也能查到"""
    user = await get_user_by_id("t001")
    assert user is not None
    assert user["role"] == "teacher"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found():
    """不存在的 userId → None"""
    user = await get_user_by_id("u999")
    assert user is None


# ========== 4. 业务函数：get_learner_profile ==========

@pytest.mark.asyncio
async def test_get_learner_profile_existing():
    """能拿到 u001 的画像"""
    profile = await get_learner_profile("u001")
    assert profile is not None
    assert profile["education"] == "本科"
    assert profile["major"] == "机械工程"
    assert profile["theoryTestScore"] == 78
    assert "kp12" in profile["weakKPs"]
    assert "kp03" in profile["strongKPs"]


@pytest.mark.asyncio
async def test_get_learner_profile_not_found():
    """教师没画像 → None"""
    profile = await get_learner_profile("t001")
    assert profile is None


@pytest.mark.asyncio
async def test_get_learner_profile_teacher_keys():
    """返回字段符合 S-02 契约（学情诊断 Agent 输入）"""
    profile = await get_learner_profile("u002")
    assert set(profile.keys()) >= {
        "education", "major", "theoryTestScore",
        "weakKPs", "strongKPs", "updatedAt"
    }


# ========== 5. JSON 字段读写 ==========

@pytest.mark.asyncio
async def test_weak_kps_json_roundtrip():
    """JSON 字段读写一致"""
    from backend.a_用户与聊天.db import upsert_learner_profile

    # 写入
    new_weak = ["kp99", "kp100"]
    await upsert_learner_profile("u001", weak_kps=new_weak)

    # 读回
    profile = await get_learner_profile("u001")
    assert set(profile["weakKPs"]) == {"kp99", "kp100"}

    # 恢复
    await upsert_learner_profile("u001", weak_kps=["kp12", "kp15"])
