"""
B-01/B-02/B-03 路由处理器单测：直接调 handler 函数（绕过 FastAPI app 启动）。
覆盖 0% 文件：stats.py / courses.py / calendar.py / behavior.py。
"""
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_routes_{uuid.uuid4().hex[:8]}.db"
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
        bdb.engine, class_=AsyncSession, expire_on_commit=False, autoflush=False,
    )
    yield
    try:
        if os.path.exists(_test_db_path):
            os.remove(_test_db_path)
    except Exception:
        pass


async def _seed_for_routes():
    """造一个学生 + 5 条活动（3 course / 1 test / 1 exercise）。"""
    from backend.b_学情数据.db import create_all_tables, drop_all_tables, get_session
    from backend.b_学情数据.models.student import Student
    from backend.b_学情数据.models.activity import Activity

    await drop_all_tables()
    await create_all_tables()

    sid = f"s-{uuid.uuid4().hex[:6]}"
    now = datetime.now()
    async with get_session() as session:
        session.add(Student(student_id=sid, name="路由测试学生"))

    async with get_session() as session:
        session.add_all([
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
            Activity(activity_id=f"a-t-{uuid.uuid4().hex[:6]}",
                     student_id=sid, activity_type="test",
                     resource_id="t-1", resource_name="单元测试",
                     status="completed", progress=100, score=72.0,
                     start_time=now - timedelta(days=2),
                     duration_minutes=60, kp_tags=["kp01", "kp03"]),
            Activity(activity_id=f"a-e-{uuid.uuid4().hex[:6]}",
                     student_id=sid, activity_type="exercise",
                     resource_id="e-1", resource_name="习题 3.2",
                     status="in-progress", progress=30, score=None,
                     start_time=now - timedelta(hours=2),
                     duration_minutes=20, kp_tags=["kp03"]),
        ])
    return sid


def _mock_user(role="teacher", uid="u-teacher"):
    """构造一个已认证的 mock user dict。"""
    return {"role": role, "userId": uid, "name": "测试用户"}


# ============ stats.py ============

@pytest.mark.asyncio
async def test_stats_handler_returns_summary():
    """GET /api/activity/stats handler 直接调用。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.activity.stats import get_activity_stats

    resp = await get_activity_stats(studentId=sid, user=_mock_user())
    data = resp["data"]
    assert data["totalActivities"] == 5
    assert data["completedActivities"] == 2
    assert data["avgProgress"] > 0
    assert data["totalStudyMinutes"] > 0
    assert data["avgScore"] is not None


@pytest.mark.asyncio
async def test_stats_forbidden_for_other_student():
    """student 角色看别人 → ForbiddenError。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.activity.stats import get_activity_stats
    from backend.公共.errors import ForbiddenError

    with pytest.raises(ForbiddenError):
        await get_activity_stats(
            studentId=sid,
            user=_mock_user(role="student", uid="different-user"),
        )


# ============ courses.py ============

@pytest.mark.asyncio
async def test_courses_handler_all_filter():
    """GET /api/activity/courses filter=all。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.activity.courses import list_activity_courses

    resp = await list_activity_courses(
        studentId=sid, filter="all", limit=50, offset=0, user=_mock_user(),
    )
    data = resp["data"]
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_courses_handler_completed_filter():
    """GET /api/activity/courses filter=completed。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.activity.courses import list_activity_courses

    resp = await list_activity_courses(
        studentId=sid, filter="completed", limit=50, offset=0, user=_mock_user(),
    )
    data = resp["data"]
    assert data["total"] == 1
    assert data["items"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_courses_handler_invalid_filter():
    """非法 filter → BizError。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.activity.courses import list_activity_courses
    from backend.公共.errors import BizError

    with pytest.raises(BizError):
        await list_activity_courses(
            studentId=sid, filter="invalid", limit=50, offset=0, user=_mock_user(),
        )


# ============ calendar.py ============

@pytest.mark.asyncio
async def test_calendar_handler_7days():
    """GET /api/activity/calendar 默认 7 天。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.activity.calendar import get_activity_calendar

    resp = await get_activity_calendar(studentId=sid, days=7, user=_mock_user())
    data = resp["data"]
    assert data["days"] == 7
    assert len(data["items"]) == 7
    # 至少有 1 天有活动
    has_activity = any(i["count"] > 0 for i in data["items"])
    assert has_activity


@pytest.mark.asyncio
async def test_calendar_handler_no_data():
    """学生无活动 → 所有天 count=0。"""
    sid = await _seed_for_routes()
    # 用另一个学生 ID 查询（但学生不存在）
    from backend.b_学情数据.activity.calendar import get_activity_calendar

    resp = await get_activity_calendar(
        studentId="s-nonexistent", days=3, user=_mock_user(),
    )
    data = resp["data"]
    assert data["days"] == 3
    assert all(i["count"] == 0 for i in data["items"])


# ============ behavior.py ============

@pytest.mark.asyncio
async def test_behavior_handler_week():
    """GET /api/student/behavior period=week。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.student.behavior import get_student_behavior

    resp = await get_student_behavior(
        studentId=sid, period="week", user=_mock_user(),
    )
    data = resp["data"]
    assert "period" in data
    assert data["period"] == "week"
    assert "activityCount" in data
    assert data["activityCount"] > 0


@pytest.mark.asyncio
async def test_behavior_handler_month():
    """GET /api/student/behavior period=month。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.student.behavior import get_student_behavior

    resp = await get_student_behavior(
        studentId=sid, period="month", user=_mock_user(),
    )
    assert resp["data"]["period"] == "month"


@pytest.mark.asyncio
async def test_behavior_handler_not_found():
    """学生不存在 → NotFoundError。"""
    from backend.b_学情数据.student.behavior import get_student_behavior
    from backend.公共.errors import NotFoundError

    with pytest.raises(NotFoundError):
        await get_student_behavior(
            studentId="s-does-not-exist", period="week", user=_mock_user(),
        )


@pytest.mark.asyncio
async def test_behavior_forbidden():
    """student 看别人 → ForbiddenError。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.student.behavior import get_student_behavior
    from backend.公共.errors import ForbiddenError

    with pytest.raises(ForbiddenError):
        await get_student_behavior(
            studentId=sid, period="week",
            user=_mock_user(role="student", uid="other"),
        )


# ============ info.py / metrics.py 路由覆盖（补充边界）============

@pytest.mark.asyncio
async def test_info_handler_returns_student():
    """GET /api/student/info handler 直接调用。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.student.info import get_student_info

    resp = await get_student_info(studentId=sid, user=_mock_user())
    assert resp["data"]["studentId"] == sid
    assert "name" in resp["data"]


@pytest.mark.asyncio
async def test_metrics_handler_returns_raw():
    """GET /api/student/metrics handler 直接调用。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.student.metrics import get_student_metrics

    resp = await get_student_metrics(studentId=sid, user=_mock_user())
    data = resp["data"]
    assert "studyHours" in data
    assert "completionRate" in data
    assert "avgScore" in data
    assert "trend" in data
    assert "trendValue" in data


@pytest.mark.asyncio
async def test_dimensions_handler_returns_6():
    """GET /api/student/dimensions handler 直接调用。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.student.dimensions import get_student_dimensions

    resp = await get_student_dimensions(studentId=sid, user=_mock_user())
    dims = resp["data"]
    assert set(dims.keys()) == {
        "comprehension", "application", "analysis",
        "evaluation", "creation", "collaboration",
    }


@pytest.mark.asyncio
async def test_knowledge_handler_returns_6_modules():
    """GET /api/student/knowledge handler 直接调用。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.student.knowledge import get_student_knowledge

    resp = await get_student_knowledge(studentId=sid, user=_mock_user())
    modules = resp["data"]
    assert isinstance(modules, list)
    assert len(modules) == 6
    assert {"kp_id", "kp_name", "mastery", "status"}.issubset(modules[0].keys())


@pytest.mark.asyncio
async def test_record_handler_creates_activity():
    """POST /api/activity/record handler 直接调用。"""
    sid = await _seed_for_routes()
    from backend.b_学情数据.activity.record import record_activity, ActivityRecordReq

    req = ActivityRecordReq(
        studentId=sid,
        activityType="course",
        resourceId="c-new",
        resourceName="新课程",
        status="in-progress",
        progress=10,
    )
    resp = await record_activity(req=req, user=_mock_user())
    assert resp["data"]["activityId"] is not None


# ============ routes.py 路由注册 ============

def test_routes_registers_all():
    """routes.py 导入后应有 ≥ 6 个子 router。"""
    from backend.b_学情数据.routes import router as b_router

    # b_router 是一个 APIRouter，其 routes 列表应包含 ≥ 6 个路由
    assert len(b_router.routes) >= 6
