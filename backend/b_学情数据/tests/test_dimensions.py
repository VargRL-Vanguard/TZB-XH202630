"""
B-02 能力维度 / 行为 / 知识接口单测。

覆盖：
  1. _get_student_dimensions 返回 6 个固定字段名
  2. _get_student_knowledge 返回 6 个模块，字段名固定
  3. aggregate_behavior period=week/month/semester 三种切换
  4. 行为数据缺失时 _isMock=true
  5. knowledge 中 mastery 与 status 映射正确
合计：>= 5 用例。
"""
import os
import tempfile
import uuid
from datetime import datetime, timedelta

import pytest

_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_b02_{uuid.uuid4().hex[:8]}.db"
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

async def _seed_student_with_activities(
    sid: str,
    activities: list[dict] | None = None,
):
    """
    造一个学生 + 可选活动数据。

    :param activities: [{type, score, kps, days_ago}, ...]
    """
    from backend.b_学情数据.db import create_all_tables, drop_all_tables, get_session
    from backend.b_学情数据.models.student import Student
    from backend.b_学情数据.models.activity import Activity

    await drop_all_tables()
    await create_all_tables()

    async with get_session() as session:
        session.add(Student(
            student_id=sid,
            name="维度测试学生",
            study_hours=20.0,
            completion_rate=0.5,
            avg_score=75.0,
            trend="up",
            trend_value=0.05,
            dim_comprehension=80,
            dim_application=75,
            dim_analysis=65,
            dim_evaluation=70,
            dim_creation=60,
            dim_collaboration=68,
        ))

    if activities:
        now = datetime.now()
        async with get_session() as session:
            for i, a in enumerate(activities):
                session.add(Activity(
                    activity_id=f"a-{sid}-{i}",
                    student_id=sid,
                    activity_type=a.get("type", "course"),
                    resource_id=f"r-{i}",
                    resource_name=f"活动{i}",
                    status="completed" if a.get("score") is not None else "in-progress",
                    progress=100 if a.get("score") is not None else 40,
                    score=a.get("score"),
                    start_time=now - timedelta(days=a.get("days_ago", 1)),
                    duration_minutes=60,
                    kp_tags=a.get("kps", []),
                ))


# ============ 用例 1：_get_student_dimensions 返回 6 个固定字段名 ============

@pytest.mark.asyncio
async def test_dimensions_returns_6_fixed_fields():
    """_get_student_dimensions 返回 6 个固定字段名。"""
    sid = f"s-dim-{uuid.uuid4().hex[:6]}"
    await _seed_student_with_activities(sid)

    from backend.b_学情数据.student.dimensions import _get_student_dimensions

    dims = await _get_student_dimensions(sid)
    assert dims is not None, "dimensions 不应为 None"

    expected = {
        "comprehension", "application", "analysis",
        "evaluation", "creation", "collaboration",
    }
    assert set(dims.keys()) == expected, (
        f"dimensions 字段名不符: {set(dims.keys())} != {expected}"
    )
    # 所有值应为 0-100 整数
    for k, v in dims.items():
        assert isinstance(v, int), f"{k} 应为 int，实际 {type(v)}"
        assert 0 <= v <= 100, f"{k} 应在 0-100，实际 {v}"


# ============ 用例 2：_get_student_knowledge 返回 6 个模块，字段名固定 ============

@pytest.mark.asyncio
async def test_knowledge_returns_6_modules_fixed_fields():
    """_get_student_knowledge 返回 6 个模块，字段名固定。"""
    sid = f"s-know-{uuid.uuid4().hex[:6]}"
    await _seed_student_with_activities(sid, activities=[
        {"type": "course", "score": 88.0, "kps": ["kp01"], "days_ago": 1},
    ])

    from backend.b_学情数据.student.knowledge import _get_student_knowledge

    klist = await _get_student_knowledge(sid)
    assert isinstance(klist, list)
    assert len(klist) == 6, f"应返回 6 个知识模块，实际 {len(klist)}"

    required_fields = {"kp_id", "kp_name", "mastery", "status"}
    for item in klist:
        assert required_fields.issubset(item.keys()), (
            f"knowledge 条目字段缺失: {item.keys()} 缺 {required_fields - item.keys()}"
        )

    # kp_id 应覆盖 kp01-kp06
    kp_ids = {item["kp_id"] for item in klist}
    assert {"kp01", "kp02", "kp03", "kp04", "kp05", "kp06"}.issubset(kp_ids), (
        f"knowledge 应包含 kp01-kp06: {kp_ids}"
    )


# ============ 用例 3：aggregate_behavior period=week/month/semester ============

@pytest.mark.asyncio
async def test_aggregate_behavior_three_periods():
    """aggregate_behavior period=week/month/semester 三种切换。"""
    sid = f"s-beh-{uuid.uuid4().hex[:6]}"
    # 造 3 天前和 20 天前和 60 天前的活动
    await _seed_student_with_activities(sid, activities=[
        {"type": "course", "score": 80.0, "kps": ["kp01"], "days_ago": 1},
        {"type": "test", "score": 70.0, "kps": ["kp02"], "days_ago": 3},
        {"type": "exercise", "score": 60.0, "kps": ["kp03"], "days_ago": 20},
        {"type": "course", "score": 55.0, "kps": ["kp04"], "days_ago": 60},
    ])

    from backend.b_学情数据.analytics.aggregator import aggregate_behavior

    # week：应只包含最近 7 天的数据（2 条）
    week = await aggregate_behavior(sid, "week")
    assert week["period"] == "week"
    assert week["activityCount"] >= 2, f"week 应至少 2 条活动，实际 {week['activityCount']}"
    assert week["_isMock"] is False

    # month：应包含最近 30 天（3 条）
    month = await aggregate_behavior(sid, "month")
    assert month["period"] == "month"
    assert month["activityCount"] >= 3, f"month 应至少 3 条活动，实际 {month['activityCount']}"

    # semester：应包含最近 112 天（4 条）
    semester = await aggregate_behavior(sid, "semester")
    assert semester["period"] == "semester"
    assert semester["activityCount"] >= 4, f"semester 应至少 4 条活动，实际 {semester['activityCount']}"

    # 三种 period 的 dailySeries 长度应递增
    assert len(week["dailySeries"]) <= len(month["dailySeries"]) <= len(semester["dailySeries"])


# ============ 用例 4：行为数据缺失时 _isMock=true ============

@pytest.mark.asyncio
async def test_behavior_missing_is_mock():
    """行为数据缺失时 _isMock=true。"""
    sid = f"s-mock-{uuid.uuid4().hex[:6]}"
    # 只造学生，不造活动
    await _seed_student_with_activities(sid, activities=[])

    from backend.b_学情数据.analytics.aggregator import aggregate_behavior

    result = await aggregate_behavior(sid, "week")
    assert result["_isMock"] is True, "无活动数据时 _isMock 应为 True"
    assert result["activityCount"] == 0
    assert result["totalStudyMinutes"] == 0


# ============ 用例 5：knowledge 中 mastery 与 status 映射正确 ============

@pytest.mark.asyncio
async def test_knowledge_mastery_status_mapping():
    """knowledge 中 mastery 与 status 映射正确。

    mastery >= 80 -> "mastered"
    mastery > 0   -> "learning"
    mastery == 0  -> "not-started"
    """
    sid = f"s-map-{uuid.uuid4().hex[:6]}"
    await _seed_student_with_activities(sid, activities=[
        # kp01: 平均分 90 -> mastered
        {"type": "test", "score": 90.0, "kps": ["kp01"], "days_ago": 1},
        # kp02: 平均分 60 -> learning
        {"type": "test", "score": 60.0, "kps": ["kp02"], "days_ago": 2},
        # kp03: 无活动 -> not-started (mastery=0)
    ])

    from backend.b_学情数据.student.knowledge import _get_student_knowledge

    klist = await _get_student_knowledge(sid)
    by_kp = {item["kp_id"]: item for item in klist}

    # kp01: mastery >= 80 -> mastered
    assert by_kp["kp01"]["mastery"] >= 80, (
        f"kp01 mastery 应 >= 80，实际 {by_kp['kp01']['mastery']}"
    )
    assert by_kp["kp01"]["status"] == "mastered", (
        f"kp01 status 应为 mastered，实际 {by_kp['kp01']['status']}"
    )

    # kp02: mastery > 0 且 < 80 -> learning
    assert 0 < by_kp["kp02"]["mastery"] < 80, (
        f"kp02 mastery 应在 (0, 80)，实际 {by_kp['kp02']['mastery']}"
    )
    assert by_kp["kp02"]["status"] == "learning", (
        f"kp02 status 应为 learning，实际 {by_kp['kp02']['status']}"
    )

    # kp03: 无活动 -> mastery=0 -> not-started
    assert by_kp["kp03"]["mastery"] == 0, (
        f"kp03 mastery 应为 0，实际 {by_kp['kp03']['mastery']}"
    )
    assert by_kp["kp03"]["status"] == "not-started", (
        f"kp03 status 应为 not-started，实际 {by_kp['kp03']['status']}"
    )


# ============ 用例 6：不存在的学生 dimensions 返回 None ============

@pytest.mark.asyncio
async def test_dimensions_not_found_returns_none():
    """_get_student_dimensions 对不存在的学生返回 None。"""
    from backend.b_学情数据.student.dimensions import _get_student_dimensions

    result = await _get_student_dimensions("s-never-exists-dim")
    assert result is None
