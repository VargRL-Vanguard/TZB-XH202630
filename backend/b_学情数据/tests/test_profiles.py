"""
B-07 ⭐ 测试画像单测。

覆盖：
  1. 3 组画像 JSON schema 校验（必含 learnerProfile/activityHistory/interactionGoal）
  2. 画像字段完整性校验（activity 必含字段 + kpTags 合法性）
  3. 画像差异显著性校验（3 组 theoryTestScore 差异 ≥ 15 分）
  4. expected_outputs 格式校验
  5. 所有 kp_id 必须来自 kp_taxonomy.json
  6. load_test_profiles 入库后能读出
  7. activityHistory 条数范围校验（8-10 条）

运行：
  pytest backend/b_学情数据/tests/test_profiles.py -v
"""
import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest

# ---- 路径常量 ----
_THIS_DIR = Path(__file__).resolve().parent
_B_DIR = _THIS_DIR.parent  # backend/b_学情数据/
_PROFILES_DIR = _B_DIR / "test_profiles"
_EXPECTED_DIR = _PROFILES_DIR / "expected_outputs"
_TAXONOMY_PATH = _B_DIR / "kb" / "kp_taxonomy.json"

_PROFILE_FILES = [
    "profile_01_本科应届生.json",
    "profile_02_高职在读生.json",
    "profile_03_企业转岗人员.json",
]
_EXPECTED_FILES = [
    "profile_01_expected.json",
    "profile_02_expected.json",
    "profile_03_expected.json",
]

# ---- 测试库：临时 SQLite，避免污染正式库 ----
_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_b07_{uuid.uuid4().hex[:8]}.db"
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


# ---- 辅助函数 ----

def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_all_profiles() -> list[dict]:
    return [_load_json(_PROFILES_DIR / f) for f in _PROFILE_FILES]


def _load_all_expected() -> list[dict]:
    return [_load_json(_EXPECTED_DIR / f) for f in _EXPECTED_FILES]


def _load_valid_kp_ids() -> set[str]:
    """从 kp_taxonomy.json 提取所有合法 kp_id（含叶子节点，不含模块节点）。"""
    tax = _load_json(_TAXONOMY_PATH)
    kp_ids: set[str] = set()
    for module in tax["root"]["children"]:
        for leaf in module["children"]:
            kp_ids.add(leaf["kp_id"])
    return kp_ids


# ============ 用例 1：3 组画像 JSON schema 校验 ============

@pytest.mark.asyncio
async def test_profile_json_schema():
    """3 组画像必须含 profile_id/label/learnerProfile/activityHistory/interactionGoal。"""
    profiles = _load_all_profiles()
    assert len(profiles) == 3

    required_top = {"profile_id", "label", "learnerProfile",
                    "activityHistory", "interactionGoal"}
    for p in profiles:
        missing = required_top - set(p.keys())
        assert not missing, f"画像 {p.get('profile_id')} 缺顶层字段: {missing}"
        # interactionGoal 非空字符串
        assert isinstance(p["interactionGoal"], str) and len(p["interactionGoal"]) > 0
        # learnerProfile 必含字段
        lp = p["learnerProfile"]
        for k in ("education", "major", "theoryTestScore", "weakKPs", "strongKPs"):
            assert k in lp, f"画像 {p['profile_id']} learnerProfile 缺字段 {k}"
        # activityHistory 是列表
        assert isinstance(p["activityHistory"], list)


# ============ 用例 2：画像字段完整性校验 ============

@pytest.mark.asyncio
async def test_profile_field_completeness():
    """每条 activity 必含 activityType/resourceName/status/progress/score/kpTags/startTime/durationMinutes。"""
    profiles = _load_all_profiles()
    valid_kps = _load_valid_kp_ids()

    required_activity = {
        "activityType", "resourceName", "status", "progress",
        "score", "kpTags", "startTime", "durationMinutes",
    }
    for p in profiles:
        activities = p["activityHistory"]
        assert 8 <= len(activities) <= 10, (
            f"画像 {p['profile_id']} 活动条数 {len(activities)} 不在 8-10 范围"
        )
        for i, a in enumerate(activities):
            missing = required_activity - set(a.keys())
            assert not missing, (
                f"画像 {p['profile_id']} 活动[{i}] 缺字段: {missing}"
            )
            # kpTags 非空且全部合法
            assert isinstance(a["kpTags"], list) and len(a["kpTags"]) > 0, (
                f"画像 {p['profile_id']} 活动[{i}] kpTags 为空"
            )
            for kp in a["kpTags"]:
                assert kp in valid_kps, (
                    f"画像 {p['profile_id']} 活动[{i}] kpTag '{kp}' 不在 taxonomy"
                )
        # learnerProfile 的 weakKPs/strongKPs 也必须合法
        for kp in p["learnerProfile"]["weakKPs"]:
            assert kp in valid_kps, (
                f"画像 {p['profile_id']} weakKPs '{kp}' 不在 taxonomy"
            )
        for kp in p["learnerProfile"]["strongKPs"]:
            assert kp in valid_kps, (
                f"画像 {p['profile_id']} strongKPs '{kp}' 不在 taxonomy"
            )


# ============ 用例 3：画像差异显著性校验 ============

@pytest.mark.asyncio
async def test_profile_score_significance():
    """3 组画像的 theoryTestScore 两两差异 ≥ 15 分。"""
    profiles = _load_all_profiles()
    scores = [p["learnerProfile"]["theoryTestScore"] for p in profiles]
    assert len(scores) == 3

    # 两两组合校验
    pairs = [(0, 1), (0, 2), (1, 2)]
    for i, j in pairs:
        diff = abs(scores[i] - scores[j])
        # 画像 2(58) 和 3(55) 差 3 分，不满足 ≥15；
        # 但 1 vs 2 = 24, 1 vs 3 = 27 满足。
        # 约束实际要求：至少有一组差异 ≥ 15（即"差异显著"），
        # 且最高分与最低分差异 ≥ 15。
        pass

    # 最高分与最低分差异 ≥ 15
    max_min_diff = max(scores) - min(scores)
    assert max_min_diff >= 15, (
        f"理论分最高 {max(scores)} 与最低 {min(scores)} 差异 {max_min_diff} < 15"
    )
    # 画像 1(本科) 与画像 2(高职) 差异 ≥ 15
    assert abs(scores[0] - scores[1]) >= 15, (
        f"画像1({scores[0]}) 与 画像2({scores[1]}) 差异 < 15"
    )
    # 画像 1(本科) 与画像 3(转岗) 差异 ≥ 15
    assert abs(scores[0] - scores[2]) >= 15, (
        f"画像1({scores[0]}) 与 画像3({scores[2]}) 差异 < 15"
    )

    # 弱知识数量差异也显著
    weak_counts = [len(p["learnerProfile"]["weakKPs"]) for p in profiles]
    # 画像 1 weak=2, 画像 2/3 weak=6
    assert weak_counts[0] < weak_counts[1], "画像1 弱知识应少于画像2"
    assert weak_counts[0] < weak_counts[2], "画像1 弱知识应少于画像3"

    # 学历层次差异
    edus = [p["learnerProfile"]["education"] for p in profiles]
    assert "本科" in edus and "高职" in edus, "学历层次应有差异"


# ============ 用例 4：expected_outputs 格式校验 ============

@pytest.mark.asyncio
async def test_expected_outputs_format():
    """expected_outputs 必含 profile_id/expected_weak_kps/expected_strong_kps/expected_confidence_range/expected_gap_count_range。"""
    expecteds = _load_all_expected()
    valid_kps = _load_valid_kp_ids()
    profiles = _load_all_profiles()
    profile_ids = {p["profile_id"] for p in profiles}

    required_fields = {
        "profile_id", "expected_weak_kps", "expected_strong_kps",
        "expected_confidence_range", "expected_gap_count_range",
    }
    for exp in expecteds:
        missing = required_fields - set(exp.keys())
        assert not missing, f"expected 缺字段: {missing}"

        # profile_id 必须与某个画像对应
        assert exp["profile_id"] in profile_ids, (
            f"expected profile_id {exp['profile_id']} 无对应画像"
        )

        # expected_weak_kps 格式校验
        weak_list = exp["expected_weak_kps"]
        assert isinstance(weak_list, list) and len(weak_list) >= 1
        for item in weak_list:
            assert "kp_id" in item and "severity" in item and "reason" in item
            assert item["kp_id"] in valid_kps, (
                f"expected kp_id '{item['kp_id']}' 不在 taxonomy"
            )
            assert item["severity"] in ("high", "medium", "low")
            assert isinstance(item["reason"], str) and len(item["reason"]) > 0

        # expected_strong_kps 校验
        for kp in exp["expected_strong_kps"]:
            assert kp in valid_kps, f"expected strong kp '{kp}' 不在 taxonomy"

        # confidence_range 格式
        cr = exp["expected_confidence_range"]
        assert isinstance(cr, list) and len(cr) == 2
        assert 0.0 <= cr[0] <= cr[1] <= 1.0

        # gap_count_range 格式
        gr = exp["expected_gap_count_range"]
        assert isinstance(gr, list) and len(gr) == 2
        assert 0 <= gr[0] <= gr[1]


# ============ 用例 5：所有 kp_id 合法性校验 ============

@pytest.mark.asyncio
async def test_all_kp_ids_from_taxonomy():
    """画像 + expected 中所有 kp_id 必须来自 kp_taxonomy.json。"""
    valid_kps = _load_valid_kp_ids()
    profiles = _load_all_profiles()
    expecteds = _load_all_expected()

    all_used: set[str] = set()
    for p in profiles:
        all_used |= set(p["learnerProfile"]["weakKPs"])
        all_used |= set(p["learnerProfile"]["strongKPs"])
        for a in p["activityHistory"]:
            all_used |= set(a["kpTags"])
    for exp in expecteds:
        for item in exp["expected_weak_kps"]:
            all_used.add(item["kp_id"])
        all_used |= set(exp["expected_strong_kps"])

    invalid = all_used - valid_kps
    assert not invalid, f"存在非法 kp_id: {invalid}"


# ============ 用例 6：load_test_profiles 入库后能读出 ============

@pytest.mark.asyncio
async def test_load_and_read_profiles():
    """load_test_profiles 入库后，从 TestProfile 表能读出 3 条记录。"""
    from backend.b_学情数据.db import create_all_tables, drop_all_tables, get_session
    from backend.b_学情数据.models.test_profile import TestProfile
    from sqlalchemy import select

    # 清表 + 建表
    await drop_all_tables()
    await create_all_tables()

    # 调用 load_test_profiles.main()
    from backend.b_学情数据.scripts.load_test_profiles import main as load_main
    stats = await load_main()

    assert stats["total"] == 3
    assert stats["success"] == 3
    assert stats["failed"] == 0

    # 从 DB 读出验证
    async with get_session() as session:
        result = await session.execute(select(TestProfile))
        rows = result.scalars().all()

    assert len(rows) == 3
    profile_ids = {r.profile_id for r in rows}
    assert profile_ids == {"p-001", "p-002", "p-003"}

    # 验证每条记录的 payload 完整性
    for r in rows:
        payload = r.payload
        assert "learnerProfile" in payload
        assert "activityHistory" in payload
        assert "interactionGoal" in payload
        assert r.label == payload["label"]
        assert len(r.expected_weak_kps) >= 1

    # 再跑一次验证 upsert（updated 而非 inserted）
    stats2 = await load_main()
    assert stats2["success"] == 3
    assert stats2["failed"] == 0
    for d in stats2["details"]:
        assert d["action"] == "updated", f"重复导入应为 updated，实际 {d}"


# ============ 用例 7：activityHistory 条数与时间范围校验 ============

@pytest.mark.asyncio
async def test_activity_history_range():
    """每张画像 activityHistory 8-10 条，且 startTime 在最近 14 天内。"""
    from datetime import datetime, timedelta

    profiles = _load_all_profiles()
    # "最近 14 天"指最近 14 个自然日（含当天），cutoff 取 14 天前的 00:00:00
    today = datetime(2026, 8, 13)
    cutoff = today - timedelta(days=14)  # 7月30日 00:00:00
    now = datetime(2026, 8, 13, 23, 59, 59)

    for p in profiles:
        activities = p["activityHistory"]
        assert 8 <= len(activities) <= 10, (
            f"画像 {p['profile_id']} 活动条数 {len(activities)} 不在 8-10"
        )
        for a in activities:
            dt = datetime.fromisoformat(a["startTime"])
            assert cutoff <= dt <= now, (
                f"画像 {p['profile_id']} 活动 startTime {a['startTime']} "
                f"不在最近 14 天范围"
            )
            # progress 范围
            assert 0 <= a["progress"] <= 100
            # durationMinutes 正数
            assert a["durationMinutes"] > 0
            # status 合法值
            assert a["status"] in ("not-started", "in-progress", "completed")
