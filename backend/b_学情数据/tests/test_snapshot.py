"""
B-04 聚合快照单测。

覆盖：
  1. get_student_snapshot 返回 info+metrics+dimensions+knowledge 合并结果
  2. snapshot 字段完整性
  3. get_recent_activities 按时间倒序
  4. snapshot 是纯只读（不写库）
  5. 不存在的 studentId 返回 None
合计：>= 5 用例。
"""
import os
import tempfile
import uuid
from datetime import datetime, timedelta

import pytest

_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_b04_{uuid.uuid4().hex[:8]}.db"
)


@pytest.fixture(scope="module", autouse=True)
def _patch_config():
    """单测级别 override 配置：指向临时 SQLite。"""
    from backend.b_学情数据 import config as bcfg

    bcfg.b_config.STUDENT_DATA_DB_URL = f"sqlite+aiosqlite:///{_test_db_path}"
    from backend.b_学情数据 import db as bdb
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    bdb.engine = create_async_engine(
        bcfg.b_config.STUDENT_DATA_DB_URL, echo=False, poolclass=NullPool
    )
    bdb.AsyncSessionLocal = async_sessionmaker(
        bdb.engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    yield
    try:
        if os.path.exists(_test_db_path):
            os.remove(_test_db_path)
    except Exception:
        pass


# ---- 辅助：造一个学生 + 若干活动 ----

async def _seed_snapshot_data(sid: str):
    """造一个学生 + 3 条活动（时间递减）。"""
    from backend.b_学情数据.db import create_all_tables, drop_all_tables, get_session
    from backend.b_学情数据.models.student import Student
    from backend.b_学情数据.models.activity import Activity

    await drop_all_tables()
    await create_all_tables()

    async with get_session() as session:
        session.add(Student(
            student_id=sid,
            name="快照测试学生",
            study_hours=35.0,
            completion_rate=0.72,
            avg_score=80.0,
            trend="up",
            trend_value=0.06,
            dim_comprehension=82,
            dim_application=76,
            dim_analysis=68,
            dim_evaluation=72,
            dim_creation=65,
            dim_collaboration=70,
        ))

    now = datetime.now()
    # 手动设置 created_at 确保时间不同且递减
    times = [
        now - timedelta(days=1),
        now - timedelta(days=2),
        now - timedelta(days=3),
    ]
    async with get_session() as session:
        for i, t in enumerate(times):
            a = Activity(
                activity_id=f"a-{sid}-{i}",
                student_id=sid,
                activity_type="course",
                resource_id=f"r-{i}",
                resource_name=f"课程{i}",
                status="completed",
                progress=100,
                score=80.0 + i * 5,
                start_time=t,
                duration_minutes=60,
                kp_tags=["kp01", "kp02"],
            )
            # 手动覆盖 created_at 以确保排序
            a.created_at = t
            session.add(a)


# ============ 用例 1：get_student_snapshot 返回合并结果 ============

@pytest.mark.asyncio
async def test_snapshot_returns_merged_result():
    """get_student_snapshot 返回 info+metrics+dimensions+knowledge 合并结果。"""
    sid = f"s-snap-{uuid.uuid4().hex[:6]}"
    await _seed_snapshot_data(sid)

    from backend.b_学情数据.student import get_student_snapshot

    snapshot = await get_student_snapshot(sid)
    assert snapshot is not None, "snapshot 不应为 None"
    assert snapshot["studentId"] == sid
    assert snapshot["name"] == "快照测试学生"

    # 应包含 info + metrics + dimensions + knowledge 四个部分
    assert "learnerProfile" in snapshot
    assert "metrics" in snapshot
    assert "dimensions" in snapshot
    assert "knowledge" in snapshot


# ============ 用例 2：snapshot 字段完整性 ============

@pytest.mark.asyncio
async def test_snapshot_field_completeness():
    """snapshot 字段完整性。"""
    sid = f"s-fields-{uuid.uuid4().hex[:6]}"
    await _seed_snapshot_data(sid)

    from backend.b_学情数据.student import get_student_snapshot

    snapshot = await get_student_snapshot(sid)
    assert snapshot is not None

    # 顶级字段
    for k in ("studentId", "name", "learnerProfile", "metrics", "dimensions", "knowledge"):
        assert k in snapshot, f"snapshot 缺顶级字段 {k}"

    # learnerProfile 子字段
    lp = snapshot["learnerProfile"]
    for k in ("education", "major", "theoryTestScore", "weakKPs", "strongKPs"):
        assert k in lp, f"learnerProfile 缺字段 {k}"

    # metrics 子字段
    m = snapshot["metrics"]
    for k in ("studyHours", "completionRate", "avgScore", "trend", "trendValue"):
        assert k in m, f"metrics 缺字段 {k}"
    assert m["studyHours"] == 35.0
    assert m["trend"] == "up"

    # dimensions 子字段
    d = snapshot["dimensions"]
    expected_dims = {
        "comprehension", "application", "analysis",
        "evaluation", "creation", "collaboration",
    }
    assert set(d.keys()) == expected_dims, (
        f"dimensions 字段不符: {set(d.keys())}"
    )

    # knowledge 是 list
    assert isinstance(snapshot["knowledge"], list)
    assert len(snapshot["knowledge"]) == 6


# ============ 用例 3：get_recent_activities 按时间倒序 ============

@pytest.mark.asyncio
async def test_recent_activities_descending():
    """get_recent_activities 按时间倒序。"""
    sid = f"s-recent-{uuid.uuid4().hex[:6]}"
    await _seed_snapshot_data(sid)

    from backend.b_学情数据.activity import get_recent_activities

    items = await get_recent_activities(sid, days=7, limit=20)
    assert len(items) >= 3, f"应至少 3 条活动，实际 {len(items)}"

    # 检查 created_at 倒序
    timestamps = [i.get("createdAt") for i in items if i.get("createdAt")]
    assert len(timestamps) >= 2
    # 倒序：前面的应大于等于后面的
    for i in range(len(timestamps) - 1):
        assert timestamps[i] >= timestamps[i + 1], (
            f"活动未按倒序排列: {timestamps[i]} < {timestamps[i + 1]}"
        )


# ============ 用例 4：snapshot 是纯只读（不写库）============

@pytest.mark.asyncio
async def test_snapshot_is_readonly():
    """snapshot 是纯只读：调用前后各表行数不变。"""
    sid = f"s-ro-{uuid.uuid4().hex[:6]}"
    await _seed_snapshot_data(sid)

    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.student import Student
    from backend.b_学情数据.models.activity import Activity
    from backend.b_学情数据.models.diagnosis_record import DiagnosisRecord
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import select, func

    async def _count_all():
        counts = {}
        async with get_session() as session:
            for name, model in [
                ("student", Student),
                ("activity", Activity),
                ("diagnosis_record", DiagnosisRecord),
                ("kb_chunk", KbChunk),
            ]:
                c = await session.scalar(
                    select(func.count()).select_from(model)
                )
                counts[name] = int(c or 0)
        return counts

    before = await _count_all()

    from backend.b_学情数据.student import get_student_snapshot
    snapshot = await get_student_snapshot(sid)
    assert snapshot is not None

    after = await _count_all()

    # 行数不变 → 纯只读
    for table, count_before in before.items():
        count_after = after[table]
        assert count_before == count_after, (
            f"表 {table} 行数变化: {count_before} -> {count_after}，"
            f"snapshot 不是纯只读"
        )


# ============ 用例 5：不存在的 studentId 返回 None ============

@pytest.mark.asyncio
async def test_snapshot_not_found_returns_none():
    """不存在的 studentId 返回 None。"""
    from backend.b_学情数据.student import get_student_snapshot

    result = await get_student_snapshot("s-never-exists-snap")
    assert result is None


# ============ 用例 6：knowledge 在 snapshot 中是 6 模块 ============

@pytest.mark.asyncio
async def test_snapshot_knowledge_has_6_modules():
    """snapshot 中 knowledge 包含 6 个知识模块且字段完整。"""
    sid = f"s-know6-{uuid.uuid4().hex[:6]}"
    await _seed_snapshot_data(sid)

    from backend.b_学情数据.student import get_student_snapshot

    snapshot = await get_student_snapshot(sid)
    assert snapshot is not None

    knowledge = snapshot["knowledge"]
    assert len(knowledge) == 6

    required_fields = {"kp_id", "kp_name", "mastery", "status"}
    for item in knowledge:
        assert required_fields.issubset(item.keys()), (
            f"knowledge 条目缺字段: {item.keys()}"
        )
        assert item["status"] in ("mastered", "learning", "not-started"), (
            f"status 值非法: {item['status']}"
        )
