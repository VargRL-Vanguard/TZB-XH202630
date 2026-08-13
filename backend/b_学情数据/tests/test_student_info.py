"""
B-01 单测：/api/student/info + /api/student/metrics。
覆盖：正常 / 越权 / 不存在 / 字段完整性，≥8 用例。

注意：由于单测环境没有启动 FastAPI TestClient 且 A 区依赖多，
这里走模块级内部函数 + 越权规则函数，避开启动 App 的重成本。
"""
import os
import tempfile
import uuid

import pytest

_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_b01_{uuid.uuid4().hex[:8]}.db"
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
async def _setup_student(sid: str, **kwargs):
    from backend.b_学情数据.db import create_all_tables, drop_all_tables, get_session
    from backend.b_学情数据.models.student import Student

    await drop_all_tables()
    await create_all_tables()
    async with get_session() as session:
        s = Student(
            student_id=sid,
            name=kwargs.pop("name", "测试学生"),
            study_hours=kwargs.pop("study_hours", 32.0),
            completion_rate=kwargs.pop("completion_rate", 0.68),
            avg_score=kwargs.pop("avg_score", 82.0),
            trend=kwargs.pop("trend", "up"),
            trend_value=kwargs.pop("trend_value", 0.05),
            dim_comprehension=78,
            dim_application=72,
            dim_analysis=65,
            dim_evaluation=70,
            dim_creation=60,
            dim_collaboration=68,
        )
        for k, v in kwargs.items():
            setattr(s, k, v)
        session.add(s)
    return sid


# ============= 越权规则 =============

def test_can_view_student_self():
    from backend.b_学情数据.student.info import _can_view
    user = {"userId": "s001", "role": "student"}
    assert _can_view(user, "s001") is True


def test_can_view_student_forbidden():
    from backend.b_学情数据.student.info import _can_view
    user = {"userId": "s001", "role": "student"}
    assert _can_view(user, "s002") is False


def test_can_view_teacher_any():
    from backend.b_学情数据.student.info import _can_view
    user = {"userId": "t001", "role": "teacher"}
    assert _can_view(user, "s-any") is True


def test_can_view_admin_any():
    from backend.b_学情数据.student.info import _can_view
    user = {"userId": "a001", "role": "admin"}
    assert _can_view(user, "s-any") is True


# ============= info 接口 字段完整性 =============

@pytest.mark.asyncio
async def test_info_fields_contract():
    sid = f"s-{uuid.uuid4().hex[:6]}"
    await _setup_student(sid, name="张三")
    from backend.b_学情数据.student.info import _get_student_info_raw

    raw = await _get_student_info_raw(sid)
    assert raw is not None
    # 顶级字段
    assert raw["studentId"] == sid
    assert raw["name"] == "张三"
    # learnerProfile 5 字段（education/major/theoryTestScore/weakKPs/strongKPs）
    lp = raw["learnerProfile"]
    assert isinstance(lp, dict)
    for k in ("education", "major", "theoryTestScore", "weakKPs", "strongKPs"):
        assert k in lp, f"learnerProfile 缺字段 {k}"
    assert isinstance(lp["weakKPs"], list)
    assert isinstance(lp["strongKPs"], list)
    # metrics 5 字段
    m = raw["metrics"]
    for k in ("studyHours", "completionRate", "avgScore", "trend", "trendValue"):
        assert k in m, f"metrics 缺字段 {k}"
    assert m["studyHours"] == 32.0
    assert m["trend"] == "up"
    assert m["trendValue"] == 0.05


@pytest.mark.asyncio
async def test_info_not_found_returns_none():
    # 已经 setup 过表了，查一个不存在的
    from backend.b_学情数据.student.info import _get_student_info_raw

    raw = await _get_student_info_raw("s-never-exists")
    assert raw is None


# ============= metrics 接口 =============

@pytest.mark.asyncio
async def test_metrics_raw_ok():
    from backend.b_学情数据.student.metrics import _get_student_metrics

    # 复用上面 setup 的一个存在的学生
    sid = f"s-m-{uuid.uuid4().hex[:6]}"
    await _setup_student(sid, study_hours=15.5, completion_rate=0.42,
                         avg_score=66.0, trend="flat", trend_value=0.0)
    m = await _get_student_metrics(sid)
    assert m is not None
    assert m["studyHours"] == 15.5
    assert m["completionRate"] == 0.42
    assert m["avgScore"] == 66.0
    assert m["trend"] == "flat"
    assert m["trendValue"] == 0.0


@pytest.mark.asyncio
async def test_metrics_not_found_returns_none():
    from backend.b_学情数据.student.metrics import _get_student_metrics

    m = await _get_student_metrics("s-not-exist-metrics")
    assert m is None


# ============= 合计 ≥8 用例 =============
# 统计：4 越权 + 1 info字段完整 + 1 info不存在 + 1 metricsOK + 1 metrics不存在 = 8
