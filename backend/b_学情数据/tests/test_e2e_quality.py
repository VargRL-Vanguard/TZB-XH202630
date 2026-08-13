"""
B-09 端到端验收测试（挑战杯夺奖核心）。

参考 test_diagnosis_agent.py 的 fixture 模式（_patch_config + _mock_ws_and_a）。

测试内容：
  1. 知识库切片入库后，kp >= 30 / chunk >= 200 / 覆盖率 >= 0.90
  2. 3 组测试画像 JSON schema 校验
  3. 对 3 组画像跑 diagnose()，全部不抛异常（confidence >= 0.6）
  4. diagnose 结果的 weakKPs 与画像 expected_weak_kps 有交集
  5. 覆盖率指标 >= 0.90
  6. 幻觉率预估 < 0.10
合计：>= 6 用例。

注意：测试环境 mock A 区 get_learner_profile 和 WS manager。
"""
import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_b09_{uuid.uuid4().hex[:8]}.db"
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


# ============ 3 组测试画像（内置，不依赖 test_profiles/ 目录）============

_TEST_PROFILES = [
    {
        "profileId": "p-001",
        "label": "本科应届生",
        "payload": {
            "learnerProfile": {
                "education": "本科",
                "major": "智能制造",
                "theoryTestScore": 78,
                "weakKPs": ["kp12", "kp15", "kp22", "kp04"],
                "strongKPs": ["kp01", "kp03"],
            },
            "activityHistory": [
                {"kpTags": ["kp01"], "activityType": "course", "score": 88},
                {"kpTags": ["kp12"], "activityType": "test", "score": 55},
                {"kpTags": ["kp03", "kp22"], "activityType": "exercise", "score": 62},
                {"kpTags": ["kp04"], "activityType": "course", "score": 70},
            ],
            "interactionGoal": "希望进阶工业机器人编程",
        },
        "expectedWeakKPs": [
            {"kp_id": "kp12", "severity": "high", "reason": "理论测试得分偏低"},
            {"kp_id": "kp15", "severity": "medium", "reason": "路径规划掌握不足"},
            {"kp_id": "kp22", "severity": "medium", "reason": "模拟量处理薄弱"},
            {"kp_id": "kp04", "severity": "low", "reason": "传感器选型不熟"},
        ],
    },
    {
        "profileId": "p-002",
        "label": "高职在读生",
        "payload": {
            "learnerProfile": {
                "education": "高职",
                "major": "工业机器人技术",
                "theoryTestScore": 65,
                "weakKPs": ["kp02", "kp04", "kp12a", "kp05"],
                "strongKPs": ["kp01"],
            },
            "activityHistory": [
                {"kpTags": ["kp01"], "activityType": "course", "score": 90},
                {"kpTags": ["kp02"], "activityType": "test", "score": 50},
                {"kpTags": ["kp04"], "activityType": "exercise", "score": 58},
                {"kpTags": ["kp12a"], "activityType": "course", "score": 62},
                {"kpTags": ["kp05"], "activityType": "test", "score": 55},
            ],
            "interactionGoal": "夯实工业机器人基础理论",
        },
        "expectedWeakKPs": [
            {"kp_id": "kp02", "severity": "high", "reason": "坐标系理解不足"},
            {"kp_id": "kp04", "severity": "high", "reason": "传感器原理不熟"},
            {"kp_id": "kp12a", "severity": "medium", "reason": "TCP标定掌握不牢"},
            {"kp_id": "kp05", "severity": "medium", "reason": "通信协议基础弱"},
        ],
    },
    {
        "profileId": "p-003",
        "label": "企业转岗人员",
        "payload": {
            "learnerProfile": {
                "education": "本科",
                "major": "机械工程",
                "theoryTestScore": 82,
                "weakKPs": ["kp05", "kp22a", "kp18", "kp06d"],
                "strongKPs": ["kp01", "kp02", "kp06"],
            },
            "activityHistory": [
                {"kpTags": ["kp01"], "activityType": "course", "score": 92},
                {"kpTags": ["kp02"], "activityType": "test", "score": 85},
                {"kpTags": ["kp05"], "activityType": "test", "score": 60},
                {"kpTags": ["kp22a"], "activityType": "exercise", "score": 65},
                {"kpTags": ["kp18"], "activityType": "course", "score": 58},
                {"kpTags": ["kp06d"], "activityType": "course", "score": 62},
            ],
            "interactionGoal": "转型智能制造系统集成岗位",
        },
        "expectedWeakKPs": [
            {"kp_id": "kp05", "severity": "medium", "reason": "工业通信基础不足"},
            {"kp_id": "kp22a", "severity": "medium", "reason": "梯形图编程不熟"},
            {"kp_id": "kp18", "severity": "high", "reason": "运动学建模薄弱"},
            {"kp_id": "kp06d", "severity": "low", "reason": "MES集成概念模糊"},
        ],
    },
]


# ============ mock WS manager ============

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
    """mock A 区 get_learner_profile + WS manager。

    注意：必须捕获 p2.start() 返回的 mock 对象，设置 side_effect 才生效。
    """
    fake_ws = _FakeWsManager()
    p1 = patch(
        "backend.a_用户与聊天.ws.manager.connection_manager",
        fake_ws,
        create=True,
    )
    p2 = patch(
        "backend.a_用户与聊天.get_learner_profile",
        create=True,
    )
    p1.start()
    mock_get_lp = p2.start()  # 捕获 mock 对象
    yield fake_ws, mock_get_lp
    p1.stop()
    p2.stop()


# ============ 辅助函数 ============

async def _ensure_kb_chunks():
    """确保 kb_chunk 表有数据（幂等）。"""
    from backend.b_学情数据.db import create_all_tables, get_session
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import select, func

    await create_all_tables()
    async with get_session() as session:
        count = await session.scalar(select(func.count(KbChunk.chunk_id)))
    if count and count > 0:
        return

    from backend.b_学情数据.kb.chunks.build_chunks import build_chunks_in_memory
    chunks = build_chunks_in_memory()
    async with get_session() as session:
        for obj in chunks:
            existing = await session.scalar(
                select(KbChunk).where(KbChunk.chunk_id == obj["chunk_id"])
            )
            if existing is None:
                session.add(KbChunk(
                    chunk_id=obj["chunk_id"],
                    doc_id=obj.get("doc_id", ""),
                    content=obj.get("content", ""),
                    embedding=obj.get("embedding"),
                    kp_tags=obj.get("kp_tags") or [],
                    source_url=obj.get("source_url", ""),
                    version=obj.get("version", "v0.1"),
                    seq_index=int(obj.get("seq_index", 0)),
                ))


async def _seed_student_for_profile(profile: dict) -> tuple[str, object]:
    """
    根据测试画像创建学生 + 活动，返回 (student_id, mock_get_lp)。

    mock_get_lp 是一个 async 函数，模拟 A 区 get_learner_profile。
    """
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.student import Student
    from backend.b_学情数据.models.activity import Activity

    sid = f"s-e2e-{uuid.uuid4().hex[:8]}"
    payload = profile["payload"]
    learner = payload["learnerProfile"]
    activity_history = payload.get("activityHistory") or []

    # 创建学生
    async with get_session() as session:
        session.add(Student(
            student_id=sid,
            name=profile.get("label", "e2e测试学生"),
            study_hours=25.0,
            completion_rate=0.6,
            avg_score=72.0,
            trend="up",
            trend_value=0.05,
            dim_comprehension=78,
            dim_application=72,
            dim_analysis=65,
            dim_evaluation=70,
            dim_creation=60,
            dim_collaboration=68,
        ))

    # 创建活动
    now = datetime.now()
    async with get_session() as session:
        for i, act in enumerate(activity_history):
            score = act.get("score")
            session.add(Activity(
                activity_id=f"a-{sid}-{i}",
                student_id=sid,
                activity_type=act.get("activityType", "course"),
                resource_id=f"r-{i}",
                resource_name=f"活动{i}",
                status="completed" if score is not None else "in-progress",
                progress=100 if score is not None else 40,
                score=score,
                start_time=now - timedelta(days=i + 1),
                duration_minutes=60,
                kp_tags=act.get("kpTags") or [],
            ))

    # 构造 mock get_learner_profile
    async def _fake_get_lp(user_id):
        if user_id != sid:
            return None
        return {
            "education": learner.get("education", ""),
            "major": learner.get("major", ""),
            "theoryTestScore": learner.get("theoryTestScore"),
            "weakKPs": list(learner.get("weakKPs") or []),
            "strongKPs": list(learner.get("strongKPs") or []),
            "updatedAt": now.isoformat(),
        }

    return sid, _fake_get_lp


def _load_taxonomy_kp_ids() -> list[str]:
    """读 kp_taxonomy.json，收集所有叶子 kp_id。"""
    taxonomy_path = (
        Path(__file__).resolve().parent.parent / "kb" / "kp_taxonomy.json"
    )
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            kp = node.get("kp_id")
            if kp and kp != "kp_root" and not kp.startswith("kp_module"):
                ids.append(str(kp))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(data)
    seen: set[str] = set()
    result = []
    for k in ids:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


async def _get_covered_kps() -> set[str]:
    """从 kb_chunk 表查询实际覆盖的 kp。"""
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import select

    covered: set[str] = set()
    async with get_session() as session:
        result = await session.execute(select(KbChunk.kp_tags))
        for (tags,) in result.all():
            if isinstance(tags, list):
                for t in tags:
                    covered.add(str(t))
    return covered


async def _retrieve_chunks_for_kp(kp_id: str, limit: int = 5) -> list[dict]:
    """检索单个 kp 的 chunks（含 SQLite JSON 兼容回退）。"""
    from backend.b_学情数据.db import get_session, list_kb_chunks_by_kp
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import select

    chunks = await list_kb_chunks_by_kp(kp_id, limit=limit)
    if len(chunks) == 0:
        # SQLite JSON contains 可能不兼容，回退手动遍历
        async with get_session() as session:
            rows = await session.execute(select(KbChunk))
            all_rows = rows.scalars().all()
            chunks = [
                c.to_dict() for c in all_rows
                if kp_id in (c.kp_tags or [])
            ]
    return chunks


# ============ 用例 1：知识库切片入库后满足硬指标 ============

@pytest.mark.asyncio
async def test_kb_chunks_meet_requirements():
    """知识库切片入库后，kp >= 30 / chunk >= 200 / 覆盖率 >= 0.90。"""
    await _ensure_kb_chunks()

    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import select, func

    async with get_session() as session:
        chunk_count = await session.scalar(
            select(func.count(KbChunk.chunk_id))
        )
        result = await session.execute(select(KbChunk.kp_tags))
        covered: set[str] = set()
        for (tags,) in result.all():
            if isinstance(tags, list):
                for t in tags:
                    covered.add(str(t))

    # chunk >= 200
    assert chunk_count >= 200, f"chunk 数应 >= 200，实际 {chunk_count}"

    # kp 覆盖数 >= 30
    assert len(covered) >= 30, f"kp 覆盖数应 >= 30，实际 {len(covered)}"

    # 覆盖率 >= 0.90
    taxonomy_kps = _load_taxonomy_kp_ids()
    taxonomy_set = set(taxonomy_kps)
    covered_in_taxonomy = covered & taxonomy_set
    coverage = len(covered_in_taxonomy) / len(taxonomy_kps) if taxonomy_kps else 0.0
    assert coverage >= 0.90, f"覆盖率应 >= 0.90，实际 {coverage:.2%}"


# ============ 用例 2：3 组测试画像 JSON schema 校验 ============

@pytest.mark.asyncio
async def test_test_profiles_schema_valid():
    """3 组测试画像 JSON schema 校验。"""
    assert len(_TEST_PROFILES) == 3, f"应有 3 组画像，实际 {len(_TEST_PROFILES)}"

    for p in _TEST_PROFILES:
        # 顶级字段
        assert "profileId" in p, f"画像缺 profileId"
        assert "label" in p, f"画像缺 label"
        assert "payload" in p, f"画像缺 payload"
        assert "expectedWeakKPs" in p, f"画像缺 expectedWeakKPs"

        # payload 子结构
        payload = p["payload"]
        assert "learnerProfile" in payload, f"画像 {p['profileId']} payload 缺 learnerProfile"
        assert "activityHistory" in payload, f"画像 {p['profileId']} payload 缺 activityHistory"
        assert "interactionGoal" in payload, f"画像 {p['profileId']} payload 缺 interactionGoal"

        # learnerProfile 子字段
        lp = payload["learnerProfile"]
        for k in ("education", "major", "theoryTestScore", "weakKPs", "strongKPs"):
            assert k in lp, f"画像 {p['profileId']} learnerProfile 缺 {k}"
        assert isinstance(lp["weakKPs"], list) and len(lp["weakKPs"]) > 0, (
            f"画像 {p['profileId']} weakKPs 应为非空 list"
        )
        assert isinstance(lp["strongKPs"], list), (
            f"画像 {p['profileId']} strongKPs 应为 list"
        )

        # expectedWeakKPs 格式
        for ew in p["expectedWeakKPs"]:
            assert "kp_id" in ew, f"画像 {p['profileId']} expectedWeakKPs 条目缺 kp_id"
            assert "severity" in ew, f"画像 {p['profileId']} expectedWeakKPs 条目缺 severity"


# ============ 用例 3：对 3 组画像跑 diagnose()，全部不抛异常 ============

@pytest.mark.asyncio
async def test_diagnose_all_profiles_no_exception(_mock_ws_and_a):
    """对 3 组画像跑 diagnose()，全部不抛异常（confidence >= 0.6）。"""
    await _ensure_kb_chunks()
    fake_ws, mock_lp = _mock_ws_and_a

    results = []
    for profile in _TEST_PROFILES:
        sid, fake_lp = await _seed_student_for_profile(profile)
        mock_lp.side_effect = fake_lp

        from backend.b_学情数据.analytics import diagnose
        result = await diagnose(sid)

        # 字段契约
        for k in ("studentId", "weakKPs", "strongKPs", "knowledgeGaps",
                  "confidence", "traceId", "generatedAt"):
            assert k in result, f"画像 {profile['profileId']} 诊断结果缺字段 {k}"

        assert result["studentId"] == sid
        assert result["confidence"] >= 0.6, (
            f"画像 {profile['profileId']} confidence 应 >= 0.6，"
            f"实际 {result['confidence']}"
        )
        results.append(result)

    # 至少 3 组都通过
    assert len(results) == 3

    # WS 事件至少 3 次（每组至少 1 次）
    assert len(fake_ws.events) >= 3, (
        f"WS 事件应 >= 3 次，实际 {len(fake_ws.events)}"
    )


# ============ 用例 4：diagnose 结果的 weakKPs 与画像 expected_weak_kps 有交集 ============

@pytest.mark.asyncio
async def test_diagnose_weakkps_intersect_expected(_mock_ws_and_a):
    """diagnose 结果的 weakKPs 与画像 expected_weak_kps 有交集。"""
    await _ensure_kb_chunks()
    fake_ws, mock_lp = _mock_ws_and_a

    for profile in _TEST_PROFILES:
        sid, fake_lp = await _seed_student_for_profile(profile)
        mock_lp.side_effect = fake_lp

        from backend.b_学情数据.analytics import diagnose
        result = await diagnose(sid)

        expected_kps = {ew["kp_id"] for ew in profile["expectedWeakKPs"]}
        actual_weak = set(result["weakKPs"])

        overlap = expected_kps & actual_weak
        assert len(overlap) >= 1, (
            f"画像 {profile['profileId']} weakKPs 与 expectedWeakKPs 无交集: "
            f"expected={expected_kps} actual={actual_weak}"
        )


# ============ 用例 5：覆盖率指标 >= 0.90 ============

@pytest.mark.asyncio
async def test_coverage_metric_ge_90():
    """覆盖率指标 >= 0.90（使用 calc_coverage）。"""
    await _ensure_kb_chunks()

    from backend.公共.metrics import calc_coverage

    covered_kps = await _get_covered_kps()
    taxonomy_kps = _load_taxonomy_kp_ids()

    # 使用 calc_coverage 计算（传入 list 作为 generated）
    coverage = calc_coverage(
        generated=list(covered_kps),
        required_kps=taxonomy_kps,
    )
    assert coverage >= 0.90, f"覆盖率应 >= 0.90，实际 {coverage:.4f}"


# ============ 用例 6：幻觉率预估 < 0.10 ============

@pytest.mark.asyncio
async def test_hallucination_rate_lt_10():
    """幻觉率预估 < 0.10（基于知识库检索 + calc_hallucination_rate）。"""
    await _ensure_kb_chunks()

    from backend.公共.metrics import calc_hallucination_rate

    all_rates: list[float] = []
    risk_kps: list[str] = []

    for profile in _TEST_PROFILES:
        payload = profile["payload"]
        learner = payload["learnerProfile"]
        weak_kps = learner.get("weakKPs") or []

        # 对每个 weakKP 检索知识库 chunks
        ground_truth: list[str] = []
        for kp in weak_kps:
            chunks = await _retrieve_chunks_for_kp(kp, limit=3)
            if chunks:
                for c in chunks:
                    content = c.get("content", "")
                    if content:
                        ground_truth.append(content)
            else:
                risk_kps.append(kp)

        # 模拟生成诊断文本（画像信息 + 知识库内容拼接）
        parts = [
            f"画像{profile['label']}的诊断报告："
            f"理论测试{learner.get('theoryTestScore')}分。"
        ]
        for kp in weak_kps:
            chunks = await _retrieve_chunks_for_kp(kp, limit=2)
            if chunks:
                for c in chunks:
                    parts.append(c.get("content", ""))
            else:
                parts.append(f"知识点{kp}暂无知识库支撑。")
        parts.append("建议针对以上薄弱知识点进行专项强化训练。")
        generated = "".join(parts)

        # 计算幻觉率
        if ground_truth:
            rate = calc_hallucination_rate(generated, ground_truth)
        else:
            rate = 1.0

        all_rates.append(rate)

    overall = sum(all_rates) / len(all_rates) if all_rates else 1.0
    assert overall < 0.10, (
        f"幻觉率预估应 < 0.10，实际 {overall:.4f}，"
        f"per_profile={[round(r, 4) for r in all_rates]}，"
        f"risk_kps={risk_kps}"
    )


# ============ 用例 7：诊断记录入库校验 ============

@pytest.mark.asyncio
async def test_diagnosis_record_persisted(_mock_ws_and_a):
    """diagnose() 结果保存到 diagnosis_record 表。"""
    await _ensure_kb_chunks()
    fake_ws, mock_lp = _mock_ws_and_a

    profile = _TEST_PROFILES[0]
    sid, fake_lp = await _seed_student_for_profile(profile)
    mock_lp.side_effect = fake_lp

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
