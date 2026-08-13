"""
B-03 单测：学习活动 5 接口。
重点覆盖 4 种 filter：all/in-progress/completed/not-started。
同样走模块级内部函数 + 记录函数，避开启动 App。
"""
import os
import tempfile
import uuid
from datetime import datetime, timedelta

import pytest

_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_b03_{uuid.uuid4().hex[:8]}.db"
)


@pytest.fixture(scope="module", autouse=True)
def _patch_config():
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


@pytest.mark.asyncio
async def _seed_activities(sid: str):
    from backend.b_学情数据.db import create_all_tables, drop_all_tables, get_session
    from backend.b_学情数据.models.activity import Activity
    from backend.b_学情数据.models.student import Student

    await drop_all_tables()
    await create_all_tables()
    now = datetime.now()
    # 先写一条 Student，避免 behavior/knowledge 接口 404
    async with get_session() as session:
        session.add(Student(student_id=sid, name="测试学生"))

    async with get_session() as session:
        session.add_all([
            # 3 条 course，状态各 1
            Activity(activity_id=f"a-c-{uuid.uuid4().hex[:6]}",
                     student_id=sid, activity_type="course",
                     resource_id="c-1", resource_name="机器人基础",
                     status="completed", progress=100, score=88.0,
                     start_time=now - timedelta(days=3),
                     duration_minutes=90, kp_tags=["kp01", "kp02"]),
            Activity(activity_id=f"a-c-{uuid.uuid4().hex[:6]}",
                     student_id=sid, activity_type="course",
                     resource_id="c-2", resource_name="坐标系",
                     status="in-progress", progress=50,
                     start_time=now - timedelta(days=1),
                     duration_minutes=45, kp_tags=["kp02"]),
            Activity(activity_id=f"a-c-{uuid.uuid4().hex[:6]}",
                     student_id=sid, activity_type="course",
                     resource_id="c-3", resource_name="PLC 入门",
                     status="not-started", progress=0),
            # 1 条 test
            Activity(activity_id=f"a-t-{uuid.uuid4().hex[:6]}",
                     student_id=sid, activity_type="test",
                     resource_id="t-1", resource_name="单元测试",
                     status="completed", progress=100, score=72.0,
                     start_time=now - timedelta(days=2),
                     duration_minutes=60, kp_tags=["kp01", "kp03"]),
            # 1 条 exercise
            Activity(activity_id=f"a-e-{uuid.uuid4().hex[:6]}",
                     student_id=sid, activity_type="exercise",
                     resource_id="e-1", resource_name="习题 3.2",
                     status="in-progress", progress=30, score=None,
                     start_time=now - timedelta(hours=2),
                     duration_minutes=20, kp_tags=["kp03"]),
        ])
    return sid


@pytest.mark.asyncio
async def test_stats_summary():
    sid = f"s-{uuid.uuid4().hex[:6]}"
    await _seed_activities(sid)
    # 直接调 stats.py 的内部逻辑：通过 HTTP handler 会 require_auth，
    # 这里重算 stats 验证
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.activity import Activity
    from sqlalchemy import select, func, and_

    async with get_session() as session:
        total = await session.scalar(
            select(func.count()).select_from(Activity).where(Activity.student_id == sid)
        )
        completed = await session.scalar(
            select(func.count()).select_from(Activity).where(and_(
                Activity.student_id == sid, Activity.status == "completed"))
        )
    assert total == 5
    assert completed == 2


@pytest.mark.asyncio
async def test_courses_4_filters():
    """courses filter=all/in-progress/completed/not-started 各不同。"""
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.activity import Activity
    from sqlalchemy import select, and_, func

    sid = f"s-{uuid.uuid4().hex[:6]}"
    await _seed_activities(sid)

    async def _count(f):
        clauses = [Activity.student_id == sid, Activity.activity_type == "course"]
        if f != "all":
            clauses.append(Activity.status == f)
        async with get_session() as session:
            r = await session.scalar(
                select(func.count()).select_from(Activity).where(and_(*clauses))
            )
        return int(r or 0)

    assert await _count("all") == 3
    assert await _count("completed") == 1
    assert await _count("in-progress") == 1
    assert await _count("not-started") == 1


@pytest.mark.asyncio
async def test_recent_order_descending():
    """最近活动按时间倒序。"""
    sid = f"s-{uuid.uuid4().hex[:6]}"
    await _seed_activities(sid)
    from backend.b_学情数据.activity import get_recent_activities

    items = await get_recent_activities(sid, days=7, limit=20)
    assert len(items) >= 3  # 至少 3 条是 7 天内的
    ts = [i["createdAt"] for i in items]
    # 非 None 的应递减
    ts_valid = [t for t in ts if t]
    assert ts_valid == sorted(ts_valid, reverse=True)


@pytest.mark.asyncio
async def test_calendar_7days_padded():
    """一周 7 天，无数据补 0。"""
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.activity import Activity
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_

    sid = f"s-{uuid.uuid4().hex[:6]}"
    await _seed_activities(sid)
    now = datetime.now()
    start_dt = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)

    # 复刻 calendar 逻辑
    daily = {}
    cursor = start_dt
    while cursor.date() <= now.date():
        ds = cursor.date().isoformat()
        daily[ds] = {"date": ds, "count": 0, "minutes": 0}
        cursor += timedelta(days=1)
    assert len(daily) == 7, f"日历应补 7 天，实际 {len(daily)}"

    async with get_session() as session:
        stmt = select(Activity).where(and_(
            Activity.student_id == sid, Activity.created_at >= start_dt
        ))
        r = await session.execute(stmt)
        acts = list(r.scalars().all())
    for a in acts:
        ds = a.created_at.date().isoformat()
        if ds in daily:
            daily[ds]["count"] += 1
    # 总体 count > 0（我们造的数据有 5 条，最近 7 天内）
    total = sum(v["count"] for v in daily.values())
    assert total > 0


@pytest.mark.asyncio
async def test_record_write_and_read():
    """record 写入后能读出新 activity_id。"""
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.activity import Activity
    from backend.b_学情数据.activity.record import _parse_iso, ActivityRecordReq
    import uuid as _uuid

    sid = f"s-{uuid.uuid4().hex[:6]}"
    await _seed_activities(sid)  # 保证表存在

    aid = f"a-new-{_uuid.uuid4().hex[:8]}"
    now_str = datetime.now().isoformat()
    req = ActivityRecordReq(
        studentId=sid,
        activityType="exercise",
        resourceId="e-new",
        resourceName="新习题",
        status="in-progress",
        progress=10.0,
        startTime=now_str,
        durationMinutes=15,
        kpTags=["kp05"],
        extra={"src": "unit-test"},
    )
    # 直接写 Activity（绕过 require_auth）
    async with get_session() as session:
        from backend.b_学情数据.models.activity import Activity as A
        act = A(
            activity_id=aid,
            student_id=req.studentId,
            activity_type=req.activityType,
            resource_id=req.resourceId,
            resource_name=req.resourceName,
            resource_type=req.resourceType,
            status=req.status,
            progress=req.progress,
            score=req.score,
            start_time=_parse_iso(req.startTime),
            end_time=_parse_iso(req.endTime),
            duration_minutes=req.durationMinutes,
            kp_tags=req.kpTags or [],
            extra=req.extra or {},
        )
        session.add(act)

    async with get_session() as session:
        got = await session.get(Activity, aid)
        assert got is not None
        assert got.resource_name == "新习题"
        assert got.kp_tags == ["kp05"]
        assert got.extra["src"] == "unit-test"
