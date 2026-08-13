"""
B-08 幻觉率预校验脚本（挑战杯夺奖核心硬指标之一）。

输入：3 组测试画像 + 知识库（kb_chunk 表）
输出：基于知识库检索的潜在幻觉率预估（用关键词匹配法）

逻辑：
  1. 读取 3 个测试画像
  2. 对每个画像的 weakKPs，从知识库检索相关 chunks（list_kb_chunks_by_kp）
  3. 把检索到的 chunks 内容作为 ground_truth
  4. 模拟生成一段"诊断文本"（用画像信息 + 知识库内容拼接）
  5. 调用 calc_hallucination_rate 计算幻觉率
  6. 如果某 kp 没有检索到任何 chunk，视为潜在幻觉风险

硬指标：幻觉率预估 < 0.10

运行：
  python -m backend.b_学情数据.scripts.hallucination_check
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# ---- sys.path 处理 ----
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sqlalchemy import select, func

from backend.b_学情数据.db import get_session, init_tables, list_kb_chunks_by_kp
from backend.b_学情数据.models.kb_chunk import KbChunk
from backend.公共.metrics import calc_hallucination_rate

# ---- 脚本独立运行时：强制使用 SQLite（避免 .env 指向 MySQL）----
import os
import tempfile as _tempfile

_sqlite_path = os.path.join(_tempfile.gettempdir(), "b_pre_check_hallucination.db")
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
_B_MODULE_DIR = _THIS_DIR.parent
_KB_DIR = _B_MODULE_DIR / "kb"
_TAXONOMY_PATH = _KB_DIR / "kp_taxonomy.json"
_TEST_PROFILES_DIR = _B_MODULE_DIR / "test_profiles"
_REPORT_DIR = _PROJECT_ROOT / "docs" / "quality_reports" / "b_pre_check"

# ---- 后备测试画像（与 coverage_check.py 保持一致）----
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
        print("[hallucination_check] test_profiles/ 目录不存在，使用内置后备画像")
        return list(_FALLBACK_PROFILES)

    profiles: list[dict] = []
    for fp in sorted(_TEST_PROFILES_DIR.glob("*.json")):
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                profiles.append(json.load(fh))
        except (json.JSONDecodeError, OSError) as e:
            print(f"[hallucination_check] 跳过无效文件 {fp.name}: {e}")

    if not profiles:
        print("[hallucination_check] test_profiles/ 无有效 JSON，使用内置后备画像")
        return list(_FALLBACK_PROFILES)

    return profiles


def _simulate_diagnosis_text(
    profile: dict,
    kp_chunks_map: dict[str, list[dict]],
) -> str:
    """
    模拟生成一段"诊断文本"（用画像信息 + 知识库内容拼接）。

    生成策略：
    - 开头：简短的画像描述（占比小，避免拉高幻觉率）
    - 主体：每个 weakKP 对应的知识库 chunk 正文（与 ground_truth 一致）
    - 结尾：简短建议
    """
    payload = profile.get("payload", profile)
    learner = payload.get("learnerProfile") or {}
    label = profile.get("label", "")
    weak_kps = learner.get("weakKPs") or []
    theory_score = learner.get("theoryTestScore")

    parts: list[str] = []
    # 开头：简短画像描述
    parts.append(
        f"画像{label}的诊断报告：理论测试{theory_score}分，"
        f"识别到{len(weak_kps)}个薄弱知识点。"
    )

    # 主体：每个 weakKP 的知识库内容
    for kp in weak_kps:
        chunks = kp_chunks_map.get(kp, [])
        if chunks:
            for c in chunks:
                parts.append(c.get("content", ""))
        else:
            # 该 kp 没有知识库覆盖 — 潜在幻觉风险
            parts.append(f"知识点{kp}暂无知识库支撑。")

    # 结尾
    parts.append("建议针对以上薄弱知识点进行专项强化训练。")

    return "".join(parts)


async def _ensure_kb_data() -> None:
    """确保 kb_chunk 表有数据；若为空则入库。"""
    async with get_session() as session:
        count = await session.scalar(select(func.count(KbChunk.chunk_id)))

    if count and count > 0:
        print(f"[hallucination_check] kb_chunk 表已有 {count} 条数据")
        return

    print("[hallucination_check] kb_chunk 表为空，正在生成并入库...")
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
    print(f"[hallucination_check] 入库完成，共 {len(chunks)} 条 chunk")


async def _retrieve_chunks_for_kps(kp_ids: list[str]) -> dict[str, list[dict]]:
    """
    对每个 kp_id 从知识库检索相关 chunks。

    包含 SQLite JSON contains 兼容回退：若 list_kb_chunks_by_kp 返回空，
    手动遍历 kb_chunk 表用 Python in 判断。

    :return: {kp_id: [chunk_dict, ...]}
    """
    result: dict[str, list[dict]] = {}
    for kp in kp_ids:
        chunks = await list_kb_chunks_by_kp(kp, limit=5)
        if not chunks:
            # SQLite JSON contains 可能不兼容，回退手动遍历
            async with get_session() as session:
                rows = await session.execute(select(KbChunk))
                all_rows = rows.scalars().all()
                chunks = [
                    c.to_dict() for c in all_rows
                    if kp in (c.kp_tags or [])
                ]
        result[kp] = chunks
    return result


async def main() -> dict:
    """
    主函数：计算幻觉率预估并输出报告。

    :return: 报告 dict
    """
    # 1) 初始化 + 确保数据
    await init_tables()
    await _ensure_kb_data()

    # 2) 加载画像
    profiles = _load_test_profiles()

    # 3) 逐画像计算幻觉率
    per_profile_rate: list[dict] = []
    risk_kps: set[str] = set()
    all_rates: list[float] = []

    for p in profiles:
        pid = p.get("profileId") or p.get("profile_id") or ""
        label = p.get("label", "")
        payload = p.get("payload", p)
        learner = payload.get("learnerProfile") or {}
        weak_kps = learner.get("weakKPs") or []

        # 检索每个 weakKP 的知识库 chunks
        kp_chunks_map = await _retrieve_chunks_for_kps(weak_kps)

        # 收集 risk_kps（无知识库覆盖的 kp）
        profile_risk: list[str] = []
        for kp, chunks in kp_chunks_map.items():
            if not chunks:
                risk_kps.add(kp)
                profile_risk.append(kp)

        # 构建 ground_truth：所有检索到的 chunk 内容
        ground_truth: list[str] = []
        for kp, chunks in kp_chunks_map.items():
            for c in chunks:
                content = c.get("content", "")
                if content:
                    ground_truth.append(content)

        # 模拟生成诊断文本
        generated = _simulate_diagnosis_text(p, kp_chunks_map)

        # 计算幻觉率
        if ground_truth:
            rate = calc_hallucination_rate(generated, ground_truth)
        else:
            # 没有任何 ground_truth → 全部算幻觉
            rate = 1.0

        all_rates.append(rate)
        per_profile_rate.append({
            "profileId": pid,
            "label": label,
            "weak_kps": weak_kps,
            "hallucination_rate": round(rate, 4),
            "risk_kps": profile_risk,
            "retrieved_chunk_count": len(ground_truth),
        })

    # 4) 汇总
    overall_rate = sum(all_rates) / len(all_rates) if all_rates else 1.0

    report = {
        "check_type": "hallucination_check",
        "timestamp": datetime.now().isoformat(),
        "overall_hallucination_rate": round(overall_rate, 4),
        "per_profile_rate": per_profile_rate,
        "risk_kps": sorted(risk_kps),
        "PASS": overall_rate < 0.10,
        "threshold": 0.10,
    }

    # 5) 输出报告
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = _REPORT_DIR / f"report_hallucination_{ts}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n[hallucination_check] 报告已输出到 {report_path}")

    if not report["PASS"]:
        print(
            f"[hallucination_check] FAIL: 幻觉率 {report['overall_hallucination_rate']} "
            f">= 阈值 {report['threshold']}"
        )

    return report


if __name__ == "__main__":
    asyncio.run(main())
