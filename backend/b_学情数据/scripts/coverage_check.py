"""
B-08 覆盖率自检脚本（挑战杯夺奖核心硬指标之一）。

输入：3 组测试画像（test_profiles/ 目录）+ 知识库（kb_chunk 表）
输出：核心知识点覆盖率报告 JSON

逻辑：
  1. 读取 test_profiles/ 下的 3 个 JSON 文件（不存在则使用内置后备画像）
  2. 收集所有画像中出现的 kp_id（weakKPs + strongKPs + activityHistory 中的 kpTags）
  3. 从 kb_chunk 表查询实际覆盖的 kp
  4. 读取 kb/kp_taxonomy.json 获取全部 kp_id 列表
  5. 覆盖率 = 画像涉及的 kp 中在知识库有 chunk 的数量 / 画像涉及的 kp 总数
  6. 也计算知识库对 taxonomy 全集的覆盖率

硬指标：覆盖率 >= 0.90

运行：
  python -m backend.b_学情数据.scripts.coverage_check
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# ---- sys.path 处理：让 from backend.xxx import yyy 可用 ----
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sqlalchemy import select, func

from backend.b_学情数据.db import get_session, init_tables
from backend.b_学情数据.models.kb_chunk import KbChunk

# ---- 脚本独立运行时：强制使用 SQLite（避免 .env 指向 MySQL）----
import os
import tempfile as _tempfile

_sqlite_path = os.path.join(_tempfile.gettempdir(), "b_pre_check_coverage.db")
from backend.b_学情数据 import config as _bcfg

_bcfg.b_config.STUDENT_DATA_DB_URL = f"sqlite+aiosqlite:///{_sqlite_path}"

from backend.b_学情数据 import db as _bdb
from sqlalchemy.ext.asyncio import create_async_engine as _cae
from sqlalchemy.pool import NullPool as _NP
from sqlalchemy.ext.asyncio import async_sessionmaker as _asm, AsyncSession as _AS

_bdb.engine = _cae(
    _bcfg.b_config.STUDENT_DATA_DB_URL, echo=False, poolclass=_NP
)
_bdb.AsyncSessionLocal = _asm(
    _bdb.engine, class_=_AS, expire_on_commit=False, autoflush=False,
)

# ---- 路径常量 ----
_B_MODULE_DIR = _THIS_DIR.parent  # backend/b_学情数据/
_KB_DIR = _B_MODULE_DIR / "kb"
_TAXONOMY_PATH = _KB_DIR / "kp_taxonomy.json"
_TEST_PROFILES_DIR = _B_MODULE_DIR / "test_profiles"
_REPORT_DIR = _PROJECT_ROOT / "docs" / "quality_reports" / "b_pre_check"

# ---- 后备测试画像（当 test_profiles/ 不存在时使用） ----
_FALLBACK_PROFILES = [
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


def _load_test_profiles() -> list[dict]:
    """从 test_profiles/ 目录读取 JSON 文件；不存在则使用后备画像。"""
    if not _TEST_PROFILES_DIR.exists():
        print("[coverage_check] test_profiles/ 目录不存在，使用内置后备画像")
        return list(_FALLBACK_PROFILES)

    profiles: list[dict] = []
    for fp in sorted(_TEST_PROFILES_DIR.glob("*.json")):
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                profiles.append(json.load(fh))
        except (json.JSONDecodeError, OSError) as e:
            print(f"[coverage_check] 跳过无效文件 {fp.name}: {e}")

    if not profiles:
        print("[coverage_check] test_profiles/ 无有效 JSON 文件，使用内置后备画像")
        return list(_FALLBACK_PROFILES)

    return profiles


def _load_taxonomy_kp_ids() -> list[str]:
    """读 kp_taxonomy.json，递归收集所有 kp_id（去重保序）。"""
    with open(_TAXONOMY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            kp = node.get("kp_id")
            if kp:
                ids.append(str(kp))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(data)

    seen: set[str] = set()
    result: list[str] = []
    for k in ids:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


def _collect_profile_kps(profiles: list[dict]) -> set[str]:
    """收集所有画像中出现的 kp_id（weakKPs + strongKPs + activityHistory.kpTags）。"""
    kps: set[str] = set()
    for p in profiles:
        payload = p.get("payload", p)
        learner = payload.get("learnerProfile") or {}
        for kp in learner.get("weakKPs") or []:
            kps.add(str(kp))
        for kp in learner.get("strongKPs") or []:
            kps.add(str(kp))
        for act in payload.get("activityHistory") or []:
            for kp in act.get("kpTags") or []:
                kps.add(str(kp))
    return kps


def _collect_single_profile_kps(profile: dict) -> set[str]:
    """收集单个画像中出现的 kp_id。"""
    return _collect_profile_kps([profile])


async def _get_covered_kps() -> set[str]:
    """从 kb_chunk 表查询实际覆盖的 kp 集合。"""
    covered: set[str] = set()
    async with get_session() as session:
        result = await session.execute(select(KbChunk.kp_tags))
        for (tags,) in result.all():
            if isinstance(tags, list):
                for t in tags:
                    covered.add(str(t))
    return covered


async def _ensure_kb_data() -> None:
    """确保 kb_chunk 表有数据；若为空则调用 build_chunks_in_memory 入库。"""
    async with get_session() as session:
        count = await session.scalar(select(func.count(KbChunk.chunk_id)))

    if count and count > 0:
        print(f"[coverage_check] kb_chunk 表已有 {count} 条数据")
        return

    print("[coverage_check] kb_chunk 表为空，正在生成并入库...")
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
    print(f"[coverage_check] 入库完成，共 {len(chunks)} 条 chunk")


async def main() -> dict:
    """
    主函数：计算覆盖率并输出报告。

    :return: 报告 dict
    """
    # 1) 初始化表 + 确保有数据
    await init_tables()
    await _ensure_kb_data()

    # 2) 加载画像 + taxonomy
    profiles = _load_test_profiles()
    taxonomy_kps = _load_taxonomy_kp_ids()
    profile_kps = _collect_profile_kps(profiles)
    covered_kps = await _get_covered_kps()

    # 3) 画像涉及 kp 的覆盖率
    profile_kps_covered = profile_kps & covered_kps
    profile_kps_missing = profile_kps - covered_kps
    coverage_pct = (
        len(profile_kps_covered) / len(profile_kps) if profile_kps else 1.0
    )

    # 4) 知识库对 taxonomy 全集的覆盖率
    taxonomy_set = set(taxonomy_kps)
    taxonomy_covered = covered_kps & taxonomy_set
    taxonomy_coverage = (
        len(taxonomy_covered) / len(taxonomy_kps) if taxonomy_kps else 0.0
    )

    # 5) per_profile_breakdown
    per_profile: list[dict] = []
    for p in profiles:
        pid = p.get("profileId") or p.get("profile_id") or ""
        label = p.get("label", "")
        p_kps = _collect_single_profile_kps(p)
        p_covered = p_kps & covered_kps
        p_missing = p_kps - covered_kps
        p_coverage = len(p_covered) / len(p_kps) if p_kps else 1.0

        per_profile.append({
            "profileId": pid,
            "label": label,
            "total_kps": len(p_kps),
            "covered_kps": len(p_covered),
            "missing_kps": sorted(p_missing),
            "coverage_pct": round(p_coverage * 100, 2),
        })

    # 6) 组装报告
    report = {
        "check_type": "coverage_check",
        "timestamp": datetime.now().isoformat(),
        "coverage_pct": round(coverage_pct * 100, 2),
        "total_required_kps": len(profile_kps),
        "covered_kps": len(profile_kps_covered),
        "missing_kps": sorted(profile_kps_missing),
        "taxonomy_total_kps": len(taxonomy_kps),
        "taxonomy_covered_kps": len(taxonomy_covered),
        "taxonomy_coverage_pct": round(taxonomy_coverage * 100, 2),
        "kb_distinct_kp_count": len(covered_kps),
        "per_profile_breakdown": per_profile,
        "PASS": coverage_pct >= 0.90,
        "threshold": 0.90,
    }

    # 7) 输出报告 JSON
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = _REPORT_DIR / f"report_coverage_{ts}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n[coverage_check] 报告已输出到 {report_path}")

    if not report["PASS"]:
        print(
            f"[coverage_check] FAIL: 覆盖率 {report['coverage_pct']}% < "
            f"阈值 {report['threshold'] * 100:.0f}%"
        )

    return report


if __name__ == "__main__":
    asyncio.run(main())
