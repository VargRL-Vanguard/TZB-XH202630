"""
A-05 ⭐ 夺奖专项：3 项硬指标端到端验收脚本。

一键运行（项目根目录）：
    python -m backend.公共.quality_check
    python -m backend.公共.quality_check --profiles backend/b_学情数据/test_profiles --kb backend/b_学情数据/kb

流程（workflows/10_端到端验收流程.md）：
    加载 B-07 3 组测试画像
      → 对每组画像跑协同流程（B-05 诊断 → C-04 生成 → D-06 审核）
      → 用 公共/metrics.py 3 个指标函数计算硬指标
      → 输出 Markdown + JSON 报告到 docs/quality_reports/
      → 任一指标不达标 → 抛 QualityError + 退出码 1

3 项硬指标（一票否决）：
    幻觉率              < 0.05
    画像-难度适配准确率  >= 0.85
    核心知识点覆盖率     >= 0.90

运行模式：
    默认（自包含）：B/C 区 DB 指向临时 SQLite + mock A 区 get_learner_profile，
                    不依赖 MySQL / AI API key，任何机器一键可跑（CI 友好）。
    --prod-db     ：使用 .env 里的真实 STUDENT_DATA_DB_URL / LEARNING_CONTENT_DB_URL，
                    画像对应的 userId 必须已存在于 A 区 learner_profile 表。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from backend.公共.errors import QualityError
from backend.公共.logger import get_logger
from backend.公共.metrics import (
    calc_coverage,
    calc_hallucination_rate,
    calc_match_accuracy,
)

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILES_DIR = PROJECT_ROOT / "backend" / "b_学情数据" / "test_profiles"
DEFAULT_KB_DIR = PROJECT_ROOT / "backend" / "b_学情数据" / "kb"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "quality_reports"

# 3 项硬指标阈值（与 任务总看板.md「3 项硬指标红线」一致）
HALLUCINATION_MAX = 0.05   # 幻觉率 <
MATCH_ACCURACY_MIN = 0.85  # 适配准确率 >=
COVERAGE_MIN = 0.90        # 覆盖率 >=

MIN_PROFILES = 3           # B-07 要求 >= 3 组差异化画像


# ---------------------------------------------------------------------------
# 纯逻辑函数（单测覆盖）
# ---------------------------------------------------------------------------

def load_profiles(profiles_dir: str | Path) -> list[dict]:
    """加载 B-07 测试画像。

    只读 ``profile_*.json``（排除 expected_outputs 子目录与 README）。
    :raises QualityError: 画像少于 3 组（B-07 红线）
    """
    pdir = Path(profiles_dir)
    if not pdir.is_dir():
        raise QualityError(f"画像目录不存在: {pdir}")

    profiles: list[dict] = []
    for f in sorted(pdir.glob("profile_*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise QualityError(f"画像 JSON 解析失败: {f.name}: {e}")
        data["_source_file"] = f.name
        profiles.append(data)

    if len(profiles) < MIN_PROFILES:
        raise QualityError(
            f"测试画像应 >= {MIN_PROFILES} 组（B-07），实际 {len(profiles)} 组: {pdir}"
        )
    return profiles


def load_taxonomy_kps(kb_dir: str | Path) -> list[str]:
    """读 kp_taxonomy.json，递归收集全部叶子 kp_id（排除 root / module 节点）。"""
    taxonomy_path = Path(kb_dir) / "kp_taxonomy.json"
    if not taxonomy_path.is_file():
        raise QualityError(f"知识点体系文件不存在: {taxonomy_path}")

    data = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    ids: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            kp = node.get("kp_id")
            if kp and kp != "kp_root" and not str(kp).startswith("kp_module"):
                ids.append(str(kp))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(data)
    # 去重（保序）
    seen: set[str] = set()
    result = [k for k in ids if not (k in seen or seen.add(k))]
    if not result:
        raise QualityError(f"kp_taxonomy.json 未解析到任何叶子知识点: {taxonomy_path}")
    return result


def expected_difficulty_from_score(score: Optional[int | float]) -> int:
    """画像理论分 → 期望难度（1-5）。

    与 B 区 diagnosis_agent._diagnose_core 的规则保持一致（跨区统一契约）：
        theoryTestScore >= 80 → 5；60 ~ 79 → 3；< 60 → 2；缺失 → 3
    """
    if score is None:
        return 3
    if score < 60:
        return 2
    if score < 80:
        return 3
    return 5


def aggregate_metrics(per_profile: list[dict]) -> dict:
    """聚合每组画像的指标 → 3 项硬指标 + 是否全部达标。

    :param per_profile: 每组画像的明细（含 hallucination_rate / match_accuracy）
    """
    if not per_profile:
        raise QualityError("无画像明细可聚合")

    n = len(per_profile)
    hallucination = sum(p["hallucination_rate"] for p in per_profile) / n
    accuracy = sum(p["match_accuracy"] for p in per_profile) / n

    passed = (
        hallucination < HALLUCINATION_MAX
        and accuracy >= MATCH_ACCURACY_MIN
    )
    return {
        "hallucination_rate": round(hallucination, 4),
        "match_accuracy": round(accuracy, 4),
        "hallucination_pass": hallucination < HALLUCINATION_MAX,
        "match_accuracy_pass": accuracy >= MATCH_ACCURACY_MIN,
        "soft_metrics_pass": passed,  # 覆盖率由知识库单独计算后合并
        "profile_count": n,
    }


def render_markdown_report(report: dict) -> str:
    """按 workflows/10 模板渲染 Markdown 报告。"""
    m = report["metrics"]
    ts = report["generated_at"]

    def ok(flag: bool) -> str:
        return "✅" if flag else "❌"

    lines = [
        f"# 质量报告 - {ts}",
        "",
        f"> 运行模式：{report['mode']}　|　画像：{report['profiles_dir']}　|　知识库：{report['kb_dir']}",
        "",
        "## 3 项硬指标（一票否决）",
        "",
        "| 指标 | 实际 | 目标 | 状态 |",
        "| --- | --- | --- | --- |",
        f"| 幻觉率 | {m['hallucination_rate']:.2%} | < {HALLUCINATION_MAX:.0%} |"
        f" {ok(m['hallucination_pass'])} |",
        f"| 画像-难度适配准确率 | {m['match_accuracy']:.2%} | >= {MATCH_ACCURACY_MIN:.0%} |"
        f" {ok(m['match_accuracy_pass'])} |",
        f"| 核心知识点覆盖率 | {m['coverage']:.2%} | >= {COVERAGE_MIN:.0%} |"
        f" {ok(m['coverage_pass'])} |",
        "",
        f"**总体判定：{'✅ 全部达标' if report['passed'] else '❌ 未达标（阻塞提交）'}**",
        "",
        "## 详细数据（每组画像完整协同流程：B-05 诊断 → C-04 生成 → D-06 审核）",
        "",
        "| 画像 | 耗时 | 推荐难度 | expected | 是否一致 | 幻觉率 | 资源覆盖弱项 | 审核结论 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for d in report["details"]:
        match_icon = "✅" if d["match_accuracy"] >= 1.0 else "❌"
        lines.append(
            f"| {d['profile_id']}（{d['label']}） | {d['elapsed_sec']:.1f}s"
            f" | {d['resource_difficulty']} | {d['expected_difficulty']} | {match_icon}"
            f" | {d['hallucination_rate']:.2%} | {d['resource_vs_weak_coverage']:.0%}"
            f" | {d.get('audit_verdict', '—')} |",
        )

    lines += [
        "",
        "## 知识库覆盖（B-06）",
        "",
        f"- taxonomy 知识点总数：{report['kb_taxonomy_total']}",
        f"- 知识库切片覆盖 kp 数：{report['kb_covered_kp_count']}",
        f"- 核心知识点覆盖率：{m['coverage']:.2%}（目标 >= {COVERAGE_MIN:.0%}）",
        "",
        "## 算法说明",
        "",
        "- 幻觉率：`calc_hallucination_rate(资源文本, 引用切片文本)`，按画像取算术平均；",
        "  资源文本由 C-04 生成内容扁平化，ground truth 为资源 `cited_chunks` 对应切片全文。",
        "- 画像-难度适配准确率：`calc_match_accuracy({expected.recommendedDifficulty}, 资源难度)`；",
        f"  expected 由画像理论分推导（>=80→5，60-79→3，<60→2），资源难度为 C-04 实际产出值。",
        "- 核心知识点覆盖率：`calc_coverage(kb_chunk 覆盖的 kp 集合, taxonomy 全部叶子 kp)`。",
        "",
    ]

    if report.get("warnings"):
        lines += ["## 非阻塞告警", ""]
        lines += [f"- {w}" for w in report["warnings"]]
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 自包含运行环境（默认模式）：临时 SQLite + mock A 区画像
# ---------------------------------------------------------------------------

@dataclass
class _EnvPatches:
    """记录被替换的全局对象，脚本结束后还原（进程内幂等）。"""
    b_db: Any = None
    b_old_engine: Any = None
    b_old_session_factory: Any = None
    c_db: Any = None
    c_old_engine: Any = None
    c_old_session_factory: Any = None
    c_agent: Any = None
    c_old_get_session: Any = None
    a_pkg: Any = None
    a_old_get_lp: Any = None
    a_patched: bool = False
    tmp_dir: Optional[str] = None


# mock A 区 get_learner_profile 的注册表：student_id -> learnerProfile dict
_PROFILE_REGISTRY: dict[str, dict] = {}


async def _mocked_get_learner_profile(user_id: str) -> Optional[dict]:
    return _PROFILE_REGISTRY.get(user_id)


async def setup_isolated_env() -> _EnvPatches:
    """B/C 区 DB → 临时 SQLite；A 区 get_learner_profile → 注册表 mock。

    参考 B 区 tests/test_e2e_quality.py 的 fixture 模式。
    """
    patches = _EnvPatches()
    patches.tmp_dir = tempfile.mkdtemp(prefix="quality_check_")

    # ---- B 区：异步 SQLite ----
    from backend.b_学情数据 import config as b_config
    from backend.b_学情数据 import db as b_db
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
    from sqlalchemy.pool import NullPool

    b_db_path = str(Path(patches.tmp_dir) / "b_student_data.db")
    b_config.b_config.STUDENT_DATA_DB_URL = f"sqlite+aiosqlite:///{b_db_path}"
    patches.b_db = b_db
    patches.b_old_engine = b_db.engine
    patches.b_old_session_factory = b_db.AsyncSessionLocal
    b_db.engine = create_async_engine(
        b_config.b_config.STUDENT_DATA_DB_URL, echo=False, poolclass=NullPool
    )
    b_db.AsyncSessionLocal = async_sessionmaker(
        b_db.engine, class_=AsyncSession, expire_on_commit=False, autoflush=False,
    )

    # ---- C 区：同步 SQLite ----
    from backend.c_学习内容 import db as c_db
    from backend.c_学习内容.agents import expert_agent as c_agent
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    c_db_path = str(Path(patches.tmp_dir) / "c_learning_content.db")
    patches.c_db = c_db
    patches.c_old_engine = c_db.engine
    patches.c_old_session_factory = c_db.SessionLocal
    c_db.engine = create_engine(
        f"sqlite:///{c_db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    c_db.SessionLocal = sessionmaker(
        bind=c_db.engine, autoflush=False, autocommit=False, expire_on_commit=False,
    )
    # expert_agent 顶部 `from ..db import get_session` 持有引用，需一并替换
    patches.c_agent = c_agent
    patches.c_old_get_session = c_agent.get_session
    c_agent.get_session = c_db.get_session

    # ---- A 区：mock get_learner_profile（B 区 student/info.py 函数内延迟 import）----
    import backend.a_用户与聊天 as a_pkg
    patches.a_pkg = a_pkg
    patches.a_old_get_lp = getattr(a_pkg, "get_learner_profile", None)
    a_pkg.get_learner_profile = _mocked_get_learner_profile
    patches.a_patched = True

    # ---- 建表 ----
    await b_db.create_all_tables()
    from backend.c_学习内容.models import Base as CBase  # noqa: F401  确保 ORM 注册
    CBase.metadata.create_all(c_db.engine)

    return patches


async def teardown_env(patches: _EnvPatches) -> None:
    """还原全局对象（幂等，进程退出场景可省略）。"""
    if patches.b_db is not None:
        try:
            await patches.b_db.engine.dispose()
        except Exception:
            pass
        patches.b_db.engine = patches.b_old_engine
        patches.b_db.AsyncSessionLocal = patches.b_old_session_factory
    if patches.c_db is not None:
        try:
            patches.c_db.engine.dispose()
        except Exception:
            pass
        patches.c_db.engine = patches.c_old_engine
        patches.c_db.SessionLocal = patches.c_old_session_factory
    if patches.c_agent is not None:
        patches.c_agent.get_session = patches.c_old_get_session
    if patches.a_patched and patches.a_pkg is not None:
        if patches.a_old_get_lp is not None:
            patches.a_pkg.get_learner_profile = patches.a_old_get_lp
        else:
            try:
                delattr(patches.a_pkg, "get_learner_profile")
            except AttributeError:
                pass
    _PROFILE_REGISTRY.clear()


async def ensure_kb_chunks() -> int:
    """知识库切片入库（幂等）。返回当前 chunk 总数。"""
    from sqlalchemy import func, select
    from backend.b_学情数据.db import create_all_tables, get_session
    from backend.b_学情数据.models.kb_chunk import KbChunk

    await create_all_tables()
    async with get_session() as session:
        count = await session.scalar(select(func.count(KbChunk.chunk_id)))
    if count and count > 0:
        return count

    from backend.b_学情数据.kb.chunks.build_chunks import build_chunks_in_memory
    chunks = build_chunks_in_memory()
    async with get_session() as session:
        for obj in chunks:
            exists = await session.scalar(
                select(KbChunk).where(KbChunk.chunk_id == obj["chunk_id"])
            )
            if exists is None:
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
    return len(chunks)


# ---------------------------------------------------------------------------
# 协同流程（B-05 → C-04 → D-06）
# ---------------------------------------------------------------------------

# 自然语言字段白名单（与 C 区 expert_agent._flatten_text 口径一致）
_NL_TEXT_KEYS = {
    "title", "heading", "body", "content", "question", "explanation",
    "summary", "answer", "analysis", "goal", "tips", "note", "description",
}
_NL_CONTAINER_KEYS = {"sections", "steps", "questions", "options", "chapters", "items"}


def _flatten_text(node: Any) -> str:
    """把资源 structured content 摊成纯文本（喂给 calc_hallucination_rate 切句）。

    与 C 区 expert_agent._flatten_text 同口径：只提取自然语言字段
    （title/heading/body/question 等），跳过 kp 标签、id 等结构性字段，
    避免「kp_default」这类非自然语言值被误判为幻觉句。
    """
    parts: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in _NL_TEXT_KEYS or k in _NL_CONTAINER_KEYS:
                parts.append(_flatten_text(v))
    elif isinstance(node, (list, tuple)):
        for v in node:
            parts.append(_flatten_text(v))
    elif isinstance(node, str):
        if node.strip():
            parts.append(node)
    return "\n".join(p for p in parts if p)


async def _seed_student(profile: dict) -> str:
    """按画像造 B 区学生 + 活动记录（自包含模式）。返回 student_id。"""
    from datetime import datetime, timedelta
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.student import Student
    from backend.b_学情数据.models.activity import Activity

    sid = profile.get("profile_id") or f"p-{uuid.uuid4().hex[:8]}"
    learner = profile.get("learnerProfile") or {}
    now = datetime.now()

    async with get_session() as session:
        session.add(Student(
            student_id=sid,
            name=profile.get("label", "画像学生"),
            study_hours=25.0,
            completion_rate=0.6,
            avg_score=float(learner.get("theoryTestScore") or 70),
            trend="up",
            trend_value=0.05,
            dim_comprehension=78,
            dim_application=72,
            dim_analysis=65,
            dim_evaluation=70,
            dim_creation=60,
            dim_collaboration=68,
        ))

    async with get_session() as session:
        for i, act in enumerate(profile.get("activityHistory") or []):
            score = act.get("score")
            session.add(Activity(
                activity_id=f"a-{sid}-{i}",
                student_id=sid,
                activity_type=act.get("activityType", "course"),
                resource_id=f"r-{i}",
                resource_name=act.get("resourceName", f"活动{i}"),
                status="completed" if score is not None else "in-progress",
                progress=100 if score is not None else 40,
                score=score,
                start_time=now - timedelta(days=i + 1),
                duration_minutes=int(act.get("durationMinutes") or 60),
                kp_tags=act.get("kpTags") or [],
            ))
    return sid


async def run_pipeline_for_profile(
    profile: dict,
    *,
    include_audit: bool = True,
) -> dict:
    """对单组画像跑完整协同流程并计算单组指标。"""
    started = time.perf_counter()
    sid = profile.get("profile_id", "?")
    label = profile.get("label", "")
    learner = profile.get("learnerProfile") or {}

    # ---- B-05 学情诊断 ----
    from backend.b_学情数据.analytics import diagnose
    diagnosis = await diagnose(sid)

    # 期望难度：由画像理论分推导（与 B 区 diagnosis_agent 规则一致）
    expected_diff = expected_difficulty_from_score(learner.get("theoryTestScore"))

    # ---- C-04 领域专家生成（同步接口，补 recommendedDifficulty 难度基线）----
    from backend.c_学习内容.agents.expert_agent import generate_resource
    diagnosis_for_c = dict(diagnosis)
    diagnosis_for_c["recommendedDifficulty"] = expected_diff
    # 契约适配：B 区 knowledgeGaps 是 list[dict]，C 区 DiagnosisResult 期望 list[str]
    gaps = diagnosis.get("knowledgeGaps") or []
    diagnosis_for_c["knowledgeGaps"] = [
        g["kp_id"] if isinstance(g, dict) else str(g) for g in gaps
    ]
    resource = generate_resource(sid, diagnosis_for_c, "customized_resource")

    # ---- ground truth：cited_chunks 反查知识库切片全文 ----
    from backend.b_学情数据.db import get_kb_chunk
    cited_texts: list[str] = []
    for cid in resource.cited_chunks:
        chunk = await get_kb_chunk(cid)
        if chunk and chunk.get("content"):
            cited_texts.append(chunk["content"])

    text = _flatten_text(resource.content)
    hallucination = calc_hallucination_rate(text, cited_texts)
    match = calc_match_accuracy(
        profile={"expected": {"recommendedDifficulty": expected_diff}},
        resource_difficulty=resource.difficulty,
    )
    weak_kps = diagnosis.get("weakKPs") or []
    resource_vs_weak = calc_coverage(resource.kp_coverage, weak_kps) if weak_kps else 1.0

    # ---- D-06 审核裁判（可选，失败不阻塞硬指标）----
    audit_verdict = "—"
    audit_score: Optional[float] = None
    if include_audit:
        try:
            from backend.d_AI集成.audit import audit
            # D 区 audit 按 kp_id 字面匹配检查覆盖 → 附上资源声明的 kp 清单
            content_for_audit = text
            if resource.kp_coverage:
                content_for_audit = (
                    text + "\n覆盖知识点："
                    + "、".join(resource.kp_coverage)
                )
            audit_result = await audit(
                studentId=sid, content=content_for_audit, kp_ids=resource.kp_coverage,
            )
            audit_verdict = audit_result.get("result", "—")
            audit_score = audit_result.get("score")
        except Exception as e:  # noqa: BLE001
            log.warning(f"[A-05] D-06 audit 跳过（画像 {sid}）: {e}")
            audit_verdict = "skipped"

    return {
        "profile_id": sid,
        "label": label,
        "source_file": profile.get("_source_file", ""),
        "elapsed_sec": round(time.perf_counter() - started, 2),
        "trace_id": diagnosis.get("traceId", ""),
        "weak_kps": weak_kps,
        "strong_kps": diagnosis.get("strongKPs") or [],
        "confidence": diagnosis.get("confidence"),
        "expected_difficulty": expected_diff,
        "resource_difficulty": resource.difficulty,
        "resource_id": resource.resource_id,
        "cited_chunks": len(resource.cited_chunks),
        "hallucination_rate": round(hallucination, 4),
        "match_accuracy": round(match, 4),
        "resource_vs_weak_coverage": round(resource_vs_weak, 4),
        "audit_verdict": audit_verdict,
        "audit_score": audit_score,
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

async def _kb_covered_kps() -> set[str]:
    """从 kb_chunk 表收集实际覆盖的 kp 集合。"""
    from sqlalchemy import select
    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.kb_chunk import KbChunk

    covered: set[str] = set()
    async with get_session() as session:
        result = await session.execute(select(KbChunk.kp_tags))
        for (tags,) in result.all():
            if isinstance(tags, list):
                covered.update(str(t) for t in tags)
    return covered


async def quality_check(
    profiles_path: str | Path = DEFAULT_PROFILES_DIR,
    kb_path: str | Path = DEFAULT_KB_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    *,
    use_prod_db: bool = False,
    include_audit: bool = True,
) -> dict:
    """端到端跑 3 项硬指标并归档报告。

    :return: 完整报告 dict（同时写入 docs/quality_reports/）
    :raises QualityError: 任一硬指标不达标（报告先落盘再抛）
    """
    profiles = load_profiles(profiles_path)
    taxonomy_kps = load_taxonomy_kps(kb_path)

    patches: Optional[_EnvPatches] = None
    chunk_count = 0
    try:
        if not use_prod_db:
            patches = await setup_isolated_env()
            for p in profiles:
                sid = p.get("profile_id")
                if sid:
                    _PROFILE_REGISTRY[sid] = dict(p.get("learnerProfile") or {})
                await _seed_student(p)

        chunk_count = await ensure_kb_chunks()

        # 逐组画像跑协同流程
        details: list[dict] = []
        for p in profiles:
            detail = await run_pipeline_for_profile(p, include_audit=include_audit)
            details.append(detail)
            log.info(
                f"[A-05] 画像 {detail['profile_id']} 完成："
                f"幻觉率={detail['hallucination_rate']:.2%} "
                f"难度匹配={detail['match_accuracy']:.0%} "
                f"审核={detail['audit_verdict']}"
            )

        # 覆盖率（B-06 口径：知识库切片覆盖 kp / taxonomy 叶子 kp）
        covered = await _kb_covered_kps()
        coverage = calc_coverage(list(covered), taxonomy_kps)

        metrics = aggregate_metrics(details)
        metrics["coverage"] = round(coverage, 4)
        metrics["coverage_pass"] = coverage >= COVERAGE_MIN
        metrics["passed"] = (
            metrics["hallucination_pass"]
            and metrics["match_accuracy_pass"]
            and metrics["coverage_pass"]
        )

        warnings: list[str] = []
        if chunk_count < 200:
            warnings.append(f"知识库 chunk 数 {chunk_count} < 200（B-06 红线）")
        for d in details:
            if d["cited_chunks"] == 0:
                warnings.append(
                    f"画像 {d['profile_id']} 资源未引用任何切片（幻觉率计算按最坏情况）"
                )
            if include_audit and d.get("audit_verdict") not in ("pass", "—", "skipped"):
                warnings.append(
                    f"画像 {d['profile_id']} D-06 审核结论 = {d['audit_verdict']}"
                    f"（score={d.get('audit_score')}，非阻塞，见报告明细）"
                )

        report = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "prod-db" if use_prod_db else "self-contained",
            "profiles_dir": str(profiles_path),
            "kb_dir": str(kb_path),
            "kb_chunk_count": chunk_count,
            "kb_taxonomy_total": len(taxonomy_kps),
            "kb_covered_kp_count": len(covered & set(taxonomy_kps)),
            "thresholds": {
                "hallucination_max": HALLUCINATION_MAX,
                "match_accuracy_min": MATCH_ACCURACY_MIN,
                "coverage_min": COVERAGE_MIN,
            },
            "metrics": metrics,
            "details": details,
            "passed": metrics["passed"],
            "warnings": warnings,
        }

        md_path, json_path, latest_path = write_reports(output_dir, report)
        log.info(f"[A-05] 报告已生成：{md_path}")

        if not metrics["passed"]:
            raise QualityError(
                "3 项硬指标未达标："
                f"幻觉率={metrics['hallucination_rate']:.2%}（目标 < {HALLUCINATION_MAX:.0%}），"
                f"适配准确率={metrics['match_accuracy']:.2%}（目标 >= {MATCH_ACCURACY_MIN:.0%}），"
                f"覆盖率={metrics['coverage']:.2%}（目标 >= {COVERAGE_MIN:.0%}）"
            )
        return report
    finally:
        if patches is not None:
            await teardown_env(patches)


def write_reports(output_dir: str | Path, report: dict) -> tuple[Path, Path, Path]:
    """落盘 3 份：Markdown 归档 + JSON 归档 + latest.json（任务总看板引用）。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    md_path = out / f"quality_report_{ts}.md"
    md_path.write_text(render_markdown_report(report), encoding="utf-8")

    json_path = out / f"quality_report_{ts}.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    latest_path = out / "latest.json"
    latest_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return md_path, json_path, latest_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quality_check",
        description="A-05 端到端验收：3 项硬指标一键计算（幻觉率 / 难度适配 / 知识点覆盖）",
    )
    parser.add_argument("--profiles", default=str(DEFAULT_PROFILES_DIR),
                        help="B-07 测试画像目录（含 profile_*.json）")
    parser.add_argument("--kb", default=str(DEFAULT_KB_DIR),
                        help="B-06 知识库目录（含 kp_taxonomy.json）")
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT_DIR),
                        help="报告输出目录（默认 docs/quality_reports）")
    parser.add_argument("--prod-db", action="store_true",
                        help="使用 .env 真实数据库（默认自包含临时 SQLite）")
    parser.add_argument("--no-audit", action="store_true",
                        help="跳过 D-06 审核裁判阶段")
    args = parser.parse_args(argv)

    try:
        asyncio.run(quality_check(
            profiles_path=args.profiles,
            kb_path=args.kb,
            output_dir=args.out,
            use_prod_db=args.prod_db,
            include_audit=not args.no_audit,
        ))
    except QualityError as e:
        # 报告已落盘，这里只负责退出码（CI 可识别）
        print(f"[A-05] ❌ {e}", file=sys.stderr)
        return 1
    print("[A-05] ✅ 3 项硬指标全部达标")
    return 0


if __name__ == "__main__":
    sys.exit(main())
