"""
B-05 ⭐ 学情诊断 Agent 单测。
覆盖：happy path / 弱知识画像 / 强知识画像 / 低 confidence 抛错
      / 事件推送至少 1 次 / 诊断历史入库 / 字段契约完整性 / A 区画像自洽校验
合计：≥ 8 用例。

注意：测试环境会 mock A 区 get_learner_profile / WS manager，
      避免跨区依赖。
"""
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_b05_{uuid.uuid4().hex[:8]}.db"
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


# ============ 通用种子：造一个学生 + 若干活动 ============

async def _seed_scenario(
    *,
    name: str,
    theory_score: int | None,
    weak_kps: list[str],
    strong_kps: list[str],
    activity_scores: list[tuple[str, float | None, list[str]]],
    # (activity_type, score_or_None, kpTags)
    study_hours: float = 20.0,
    completion_rate: float = 0.5,
    avg_score: float = 70.0,
    trend: str = "flat",
    trend_value: float = 0.0,
    education: str | None = "本科",
):
    from backend.b_学情数据.db import create_all_tables, drop_all_tables, get_session
    from backend.b_学情数据.models.student import Student
    from backend.b_学情数据.models.activity import Activity

    await drop_all_tables()
    await create_all_tables()

    sid = f"s-{uuid.uuid4().hex[:8]}"
    now = datetime.now()

    async with get_session() as session:
        session.add(Student(
            student_id=sid, name=name,
            study_hours=study_hours, completion_rate=completion_rate,
            avg_score=avg_score, trend=trend, trend_value=trend_value,
            dim_comprehension=70, dim_application=70, dim_analysis=70,
            dim_evaluation=70, dim_creation=70, dim_collaboration=70,
        ))

    # 构造 activities：每条 activity 时间递减
    async with get_session() as session:
        for i, (atype, score, kps) in enumerate(activity_scores):
            a = Activity(
                activity_id=f"a-{sid}-{i}",
                student_id=sid,
                activity_type=atype,
                resource_id=f"r-{i}",
                resource_name=f"活动 {i}: {atype}",
                status=("completed" if score is not None else "in-progress"),
                progress=(100 if score is not None else 40),
                score=score,
                start_time=now - timedelta(days=i, hours=1),
                duration_minutes=60 if score else 30,
                kp_tags=kps,
            )
            session.add(a)

    # mock A 区 learner_profile：返回指定的 weak/strong/theoryScore
    async def _fake_get_lp(user_id):
        if user_id != sid:
            return None
        return {
            "education": education,
            "major": "智能制造",
            "theoryTestScore": theory_score,
            "weakKPs": list(weak_kps),
            "strongKPs": list(strong_kps),
            "updatedAt": now.isoformat(),
        }

    return sid, _fake_get_lp


# ============ mock WS：记录收到的事件 ============

class _FakeWsManager:
    def __init__(self):
        self.events: list[dict] = []

    async def broadcast_to_channel(self, channel, event):
        self.events.append(event)
        return 1

    async def record_event(self, event):
        pass


@pytest.fixture()
def _mock_ws_and_a():
    """mock A 区 get_learner_profile + WS manager。"""
    fake_ws = _FakeWsManager()
    # patch WS
    p1 = patch(
        "backend.a_用户与聊天.ws.manager.connection_manager",
        fake_ws,
        create=True,  # 单测环境 A 区不一定 import
    )
    # patch A 区 get_learner_profile（由 info.py 延迟导入 backend.a_用户与聊天.get_learner_profile）
    p2 = patch(
        "backend.a_用户与聊天.get_learner_profile",
        side_effect=RuntimeError("will be overridden per test"),
        create=True,
    )
    p1.start()
    mock_lp = p2.start()  # 拿到真正的 mock 对象
    yield fake_ws, mock_lp
    p1.stop()
    p2.stop()


# ============ 用例 1：happy path ============

@pytest.mark.asyncio
async def test_diagnose_happy_path(_mock_ws_and_a):
    """强+弱知识都有、活动数据充足 → confidence ≥ 0.6、字段契约完整。"""
    fake_ws, p2 = _mock_ws_and_a
    sid, fake_lp = await _seed_scenario(
        name="综合画像学生",
        theory_score=78,
        weak_kps=["kp12", "kp15"],
        strong_kps=["kp03"],
        activity_scores=[
            ("course", 55.0, ["kp12"]),           # weak 证据
            ("test", 62.0, ["kp15", "kp04"]),     # weak 证据
            ("course", 90.0, ["kp03"]),           # strong 证据
            ("exercise", 92.0, ["kp03"]),
            ("course", 88.0, ["kp01", "kp02"]),
            ("test", 86.0, ["kp05", "kp06"]),
            ("course", 80.0, ["kp01"]),
            ("exercise", 78.0, ["kp02"]),
            ("discussion", None, ["kp05"]),       # 没分的
            ("test", 82.0, ["kp06", "kp04"]),
        ],
    )
    # override patch 2 的 side_effect
    p2.side_effect = fake_lp

    from backend.b_学情数据.analytics import diagnose
    result = await diagnose(sid)

    # 字段契约
    for k in ("studentId", "weakKPs", "strongKPs", "knowledgeGaps",
              "confidence", "traceId", "generatedAt"):
        assert k in result, f"返回缺字段 {k}"

    assert result["studentId"] == sid
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["confidence"] >= 0.6, f"happy path 置信度应 ≥ 0.6，实际 {result['confidence']}"

    # WS 事件至少 1 次
    assert len(fake_ws.events) >= 1, "至少推送 1 次 WS 事件"
    # 必须有 thinking
    types = [e["type"] for e in fake_ws.events]
    assert "agent.thinking" in types, "应有 agent.thinking 事件"
    # traceId 一致
    for e in fake_ws.events:
        assert e["traceId"] == result["traceId"]


# ============ 用例 2：弱知识画像 + 低分证据 ============

@pytest.mark.asyncio
async def test_diagnose_weak_profile(_mock_ws_and_a):
    fake_ws, p2 = _mock_ws_and_a
    sid, fake_lp = await _seed_scenario(
        name="理论偏弱学生",
        theory_score=58,  # < 60
        weak_kps=["kp02", "kp03", "kp04"],
        strong_kps=[],
        activity_scores=[
            ("test", 45.0, ["kp02"]),
            ("test", 52.0, ["kp03"]),
            ("exercise", 48.0, ["kp04"]),
            ("course", 55.0, ["kp02", "kp04"]),
            ("test", 60.0, ["kp01"]),
            ("exercise", 62.0, ["kp05"]),
        ],
    )
    p2.side_effect = fake_lp
    from backend.b_学情数据.analytics import diagnose
    result = await diagnose(sid)

    # 画像 weakKPs 应至少包含 2 个来自 profile 的
    overlap = set(result["weakKPs"]) & {"kp02", "kp03", "kp04"}
    assert len(overlap) >= 2, f"弱知识应覆盖画像标注：{result['weakKPs']}"

    # knowledgeGaps 中 kp02/kp03/kp04 至少有 1 个 high severity
    gaps_by_kp = {g["kp_id"]: g for g in result["knowledgeGaps"]}
    high_sev = [g for g in gaps_by_kp.values() if g["severity"] == "high"]
    assert len(high_sev) >= 1, f"低分学生应有 high severity 盲区，实际 gaps={result['knowledgeGaps'][:2]}"


# ============ 用例 3：强知识画像 ============

@pytest.mark.asyncio
async def test_diagnose_strong_profile(_mock_ws_and_a):
    fake_ws, p2 = _mock_ws_and_a
    sid, fake_lp = await _seed_scenario(
        name="理论扎实学生",
        theory_score=90,
        weak_kps=["kp06"],
        strong_kps=["kp01", "kp02", "kp03"],
        activity_scores=[
            ("test", 95.0, ["kp01"]),
            ("test", 92.0, ["kp02"]),
            ("course", 88.0, ["kp03"]),
            ("exercise", 90.0, ["kp01", "kp02"]),
            ("test", 85.0, ["kp04"]),
            ("course", 82.0, ["kp05"]),
            ("test", 65.0, ["kp06"]),  # kp06 弱
        ],
        study_hours=60.0, completion_rate=0.9, avg_score=88.0,
        trend="up", trend_value=0.12,
    )
    p2.side_effect = fake_lp
    from backend.b_学情数据.analytics import diagnose
    result = await diagnose(sid)

    # strongKPs 至少含画像里的 2 个
    overlap_strong = set(result["strongKPs"]) & {"kp01", "kp02", "kp03"}
    assert len(overlap_strong) >= 2, f"强知识应覆盖画像：{result['strongKPs']}"
    # confidence 应该比较高（≥ 0.7）
    assert result["confidence"] >= 0.7


# ============ 用例 4：confidence < 0.6 抛 QualityError ============

@pytest.mark.asyncio
async def test_diagnose_low_confidence_raises_quality_error(_mock_ws_and_a):
    fake_ws, p2 = _mock_ws_and_a
    # 学生有，但：无活动数据 + 画像缺 theoryScore/education → confidence 很低
    sid, fake_lp = await _seed_scenario(
        name="无数据新生",
        theory_score=None,
        weak_kps=[],
        strong_kps=[],
        activity_scores=[],  # 0 条活动
        study_hours=0.0, completion_rate=0.0, avg_score=0.0,
        education=None,  # 画像不完整，拉低置信度
    )
    p2.side_effect = fake_lp
    from backend.公共.errors import QualityError
    from backend.b_学情数据.analytics import diagnose

    with pytest.raises(QualityError) as exc_info:
        await diagnose(sid)

    # QualityError data 里应含 confidence + traceId
    d = exc_info.value.data or {}
    assert "confidence" in d
    assert "traceId" in d
    assert d["confidence"] < 0.6


# ============ 用例 5：诊断历史入库 ============

@pytest.mark.asyncio
async def test_diagnosis_record_persisted(_mock_ws_and_a):
    fake_ws, p2 = _mock_ws_and_a
    sid, fake_lp = await _seed_scenario(
        name="入库测试学生",
        theory_score=82,
        weak_kps=["kp04"],
        strong_kps=["kp01"],
        activity_scores=[
            ("test", 88.0, ["kp01"]),
            ("course", 55.0, ["kp04"]),
            ("exercise", 80.0, ["kp02"]),
            ("test", 85.0, ["kp03"]),
            ("course", 90.0, ["kp01"]),
            ("exercise", 78.0, ["kp05"]),
        ],
    )
    p2.side_effect = fake_lp
    from backend.b_学情数据.analytics import diagnose
    result = await diagnose(sid)

    # 查 diagnosis_record 表
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.diagnosis_record import DiagnosisRecord
    from sqlalchemy import select, and_

    async with get_session() as session:
        stmt = select(DiagnosisRecord).where(and_(
            DiagnosisRecord.student_id == sid,
            DiagnosisRecord.trace_id == result["traceId"],
        ))
        r = (await session.execute(stmt)).scalar_one_or_none()
    assert r is not None, "诊断记录未入库"
    assert r.weak_kps == result["weakKPs"]
    assert r.strong_kps == result["strongKPs"]
    assert abs(r.confidence - result["confidence"]) < 1e-6
    assert r.prompt_version == "0.1"


# ============ 用例 6：studentId 不存在 -> NotFoundError ============

@pytest.mark.asyncio
async def test_diagnose_not_found(_mock_ws_and_a):
    fake_ws, p2 = _mock_ws_and_a
    # 保证表存在即可
    from backend.b_学情数据.db import create_all_tables
    await create_all_tables()

    async def _fake_none(user_id):
        return None
    p2.side_effect = _fake_none

    from backend.公共.errors import NotFoundError
    from backend.b_学情数据.analytics import diagnose
    with pytest.raises(NotFoundError):
        await diagnose("s-never-exist-12345")


# ============ 用例 7：thinking 事件推送至少 1 次（更严格）============

@pytest.mark.asyncio
async def test_diagnose_at_least_one_thinking_event(_mock_ws_and_a):
    fake_ws, p2 = _mock_ws_and_a
    sid, fake_lp = await _seed_scenario(
        name="事件推送学生",
        theory_score=75,
        weak_kps=["kp02"],
        strong_kps=["kp05"],
        activity_scores=[
            ("course", 70.0, ["kp02"]),
            ("test", 92.0, ["kp05"]),
            ("exercise", 80.0, ["kp03"]),
            ("discussion", None, ["kp04"]),
            ("test", 85.0, ["kp06"]),
        ],
    )
    p2.side_effect = fake_lp
    from backend.b_学情数据.analytics import diagnose
    await diagnose(sid)

    thinking_events = [e for e in fake_ws.events if e["type"] == "agent.thinking"]
    assert len(thinking_events) >= 1, (
        f"B-05 验收：必须至少推送 1 次 agent.thinking，实际 {fake_ws.events}"
    )
    # step 字段递增
    steps = sorted(e["step"] for e in thinking_events)
    assert steps == sorted(set(steps)), "step 应该是整数且排序后一致"


# ============ 用例 8：weakKPs 与画像 learnerProfile.weakKPs 强相关 ============

@pytest.mark.asyncio
async def test_diagnose_weakkps_correlated_with_profile(_mock_ws_and_a):
    fake_ws, p2 = _mock_ws_and_a
    profile_weak = ["kp02", "kp04", "kp06"]
    sid, fake_lp = await _seed_scenario(
        name="画像关联校验",
        theory_score=70,
        weak_kps=profile_weak,
        strong_kps=["kp01"],
        activity_scores=[
            # kp02/kp04/kp06 各给一条 60-70 的证据
            ("test", 65.0, ["kp02"]),
            ("course", 68.0, ["kp04"]),
            ("exercise", 66.0, ["kp06"]),
            # 再加几条凑活动数
            ("course", 90.0, ["kp01"]),
            ("test", 82.0, ["kp03"]),
            ("exercise", 78.0, ["kp05"]),
        ],
    )
    p2.side_effect = fake_lp
    from backend.b_学情数据.analytics import diagnose
    result = await diagnose(sid)

    # 画像 weakKPs 至少 2/3 出现在结果 weakKPs
    hit = sum(1 for kp in profile_weak if kp in result["weakKPs"])
    assert hit >= 2, (
        f"weakKPs 与画像标注相关性不足："
        f"画像 {profile_weak} 实际 {result['weakKPs']} 命中 {hit}"
    )
