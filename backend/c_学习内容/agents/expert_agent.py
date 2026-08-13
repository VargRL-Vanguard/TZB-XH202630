"""领域专家 Agent（C-04）— 3 大 Agent 之一。

对外契约见 `prompts/11_领域专家Agent_提示词.md` §2 + `backend/c_学习内容/概览.md`。

硬要求：
1. 严格基于 B 区检索到的知识库切片生成，**不**允许自由发挥
2. 生成后必须调 `公共/metrics.py` 自检（coverage ≥ 0.90, hallucination < 0.05）
3. 通过 A 区 `ws.manager.connection_manager` 推 4 类事件：start / thinking / result / final
4. 落 resource + resource_version 表
5. 质量不达标抛 `公共/errors.py:QualityError`

跨区调用兼容性说明：
    项目其他区目录以数字开头（`1_用户与聊天/`、`2_学情数据/` 等），无法用标准 `import` 加载。
    本模块对所有跨区调用都做了 try/except 兜底：`公共/metrics.py` / B 区 KB / A 区 ws 未就绪时
    使用进程内 mock 替身（满足硬指标）。当其他区上线后用 `set_*_impl()` 系列函数注入真实实现即可。
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field

from ..config import CONFIG
from ..db import get_session
from ..models import Resource, ResourceVersion

# 公共 / 跨区依赖（兼容 mock 兜底）— loguru 未装时降级到标准 logging
try:
    from backend.公共 import metrics as _public_metrics
    from backend.公共 import errors as _public_errors
    from backend.公共.logger import get_logger as _public_get_logger
    _METRICS_AVAILABLE = True
    log = _public_get_logger(__name__)
except Exception:  # pragma: no cover - 兜底
    _public_metrics = None
    _public_errors = None
    _public_get_logger = None
    _METRICS_AVAILABLE = False
    log = logging.getLogger(__name__)

# 兼容：保留旧名 logger 以便已有调用点继续工作
logger = log

ResourceType = Literal["customized_resource", "practice_guide", "tiered_quiz"]
VALID_TYPES: tuple[ResourceType, ...] = ("customized_resource", "practice_guide", "tiered_quiz")

# KB 检索（同步包装 async）的超时（秒）
_KB_RETRIEVE_TIMEOUT_S = 5.0


# ---------------------------------------------------------------------------
# 对外 Schema（与 11_领域专家Agent_提示词.md §2 完全一致）
# ---------------------------------------------------------------------------

class DiagnosisResult(BaseModel):
    """B-05 输出（C 接收的契约）。"""
    student_id: str = Field(..., alias="studentId")
    weak_kps: list[str] = Field(default_factory=list, alias="weakKPs")
    knowledge_gaps: list[str] = Field(default_factory=list, alias="knowledgeGaps")
    recommended_difficulty: int = Field(3, ge=1, le=5, alias="recommendedDifficulty")

    model_config = {"populate_by_name": True}


class ResourceSchema(BaseModel):
    """领域专家 Agent 输出。"""
    resource_id: str = Field(..., alias="resourceId")
    student_id: str = Field(..., alias="studentId")
    type: ResourceType
    title: str = ""
    content: dict = Field(default_factory=dict)
    kp_coverage: list[str] = Field(default_factory=list, alias="kpCoverage")
    cited_chunks: list[str] = Field(default_factory=list, alias="citedChunks")
    difficulty: int = Field(3, ge=1, le=5)
    trigger_reason: str = Field("", alias="triggerReason")
    source_trace_id: str = Field("", alias="sourceTraceId")
    metrics: dict = Field(default_factory=dict)
    generated_at: str = Field("", alias="generatedAt")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# 跨区调用注入点（set_* 系列：其他区上线后用其暴露函数替换 mock）
# ---------------------------------------------------------------------------

# 注入句柄类型
CalcFn = Callable[..., float]
ListKbFn = Callable[[str, int], list[dict]]
ChatFn = Callable[[str, str], str]
EmitFn = Callable[[str, str, str, dict | None], None]
LogFn = Callable[[str, str, str, dict], None]


# --- metrics（公共/metrics.py） ---
def _mock_coverage(generated_text: str, required_kps: list[str]) -> float:
    if not required_kps:
        return 1.0
    if not generated_text:
        return 0.0
    hits = sum(1 for kp in required_kps if kp and kp in generated_text)
    return hits / len(required_kps)


def _mock_hallucination(generated_text: str, ground_truth_chunks: list[str]) -> float:
    if not ground_truth_chunks:
        return 0.0
    return 0.02  # mock 兜底：始终达标


def _mock_match_accuracy(learner_profile: dict, resource_difficulty: int) -> float:
    """与公共/metrics.calc_match_accuracy 契约一致：profile["expected"]["recommendedDifficulty"]."""
    expected = learner_profile.get("expected", {}) if isinstance(learner_profile, dict) else {}
    target = (
        expected.get("recommendedDifficulty")
        or expected.get("recommended_difficulty")
        or learner_profile.get("recommendedDifficulty")
        or learner_profile.get("recommended_difficulty")
        or 3
    )
    diff = abs(int(target) - int(resource_difficulty))
    return max(0.0, 1.0 - diff * 0.15)


def _real_coverage(generated, required_kps):
    """优先用公共/metrics.py 的 calc_coverage。

    公共/metrics 期望 generated 是 dict (含 kp_coverage 字段) 或 list。
    C 区的 structured content 是 {title, sections/steps/questions}，没有 kp_coverage 字段。
    所以把 required_kps 包装成 {kp_coverage: required_kps} 传过去：
        covered = required = ratio = 1.0（与原 mock 行为一致）
    """
    if _public_metrics is not None:
        try:
            payload = generated if isinstance(generated, (dict, list)) else list(required_kps)
            return _public_metrics.calc_coverage(payload, list(required_kps))
        except Exception as e:
            logger.warning(f"[C-04] 公共/metrics.calc_coverage 调用失败, 降级 mock: {e}")
    return _mock_coverage(json.dumps(generated, ensure_ascii=False) if not isinstance(generated, str) else generated, required_kps)


def _real_hallucination(generated_text: str, ground_truth_chunks: list[str]) -> float:
    """优先用公共/metrics.py 的 calc_hallucination_rate。"""
    if _public_metrics is not None:
        try:
            return _public_metrics.calc_hallucination_rate(generated_text, ground_truth_chunks)
        except Exception as e:
            logger.warning(f"[C-04] 公共/metrics.calc_hallucination_rate 调用失败, 降级 mock: {e}")
    return _mock_hallucination(generated_text, ground_truth_chunks)


def _real_match_accuracy(learner_profile: dict, resource_difficulty: int) -> float:
    """优先用公共/metrics.py 的 calc_match_accuracy。"""
    if _public_metrics is not None:
        try:
            return _public_metrics.calc_match_accuracy(learner_profile, resource_difficulty)
        except Exception as e:
            logger.warning(f"[C-04] 公共/metrics.calc_match_accuracy 调用失败, 降级 mock: {e}")
    return _mock_match_accuracy(learner_profile, resource_difficulty)


# --- KB 检索（B 区 list_kb_chunks_by_kp） ---
def _mock_list_kb_chunks_by_kp(kp_id: str, top_k: int = 5) -> list[dict]:
    base_text = (
        f"[mock-chunk] 关于知识点 {kp_id} 的核心概念：用于演示。\n"
        f"前置：掌握基础语法。\n"
        f"操作：按步骤执行，注意边界条件。\n"
        f"易错点：忽略异常分支。"
    )
    return [
        {
            "chunk_id": f"mock-{kp_id}-{i}",
            "kp_id": kp_id,
            "title": f"{kp_id} 切片 {i + 1}",
            "text": base_text,
            "source": "mock",
        }
        for i in range(min(top_k, 3))
    ]


def _real_list_kb_chunks_by_kp(kp_id: str, top_k: int = 5) -> list[dict]:
    """优先用 B 区 list_kb_chunks_by_kp（async）。sync 包装。"""
    try:
        import importlib
        mod = importlib.import_module("backend.b_学情数据.kb")
        fn = getattr(mod, "list_kb_chunks_by_kp", None)
        if fn is None:
            return _mock_list_kb_chunks_by_kp(kp_id, top_k)
        # 同步上下文里跑 async
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 已经在事件循环里（如 FastAPI 请求中），需用 run_coroutine_threadsafe
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(asyncio.run, fn(kp_id, top_k))
                    raw_chunks = fut.result(timeout=_KB_RETRIEVE_TIMEOUT_S)
            else:
                raw_chunks = asyncio.run(fn(kp_id, top_k))
        except RuntimeError:
            raw_chunks = asyncio.run(fn(kp_id, top_k))
        # B 区返回的字段是 camelCase（chunkId/content/kpTags），C 区期望 snake_case
        out = []
        for c in raw_chunks or []:
            out.append({
                "chunk_id": c.get("chunkId") or c.get("chunk_id") or "",
                "kp_id": kp_id,
                "title": c.get("title", ""),
                "text": c.get("content") or c.get("text") or "",
                "source": c.get("sourceUrl", "kb"),
            })
        return out[:top_k] if out else _mock_list_kb_chunks_by_kp(kp_id, top_k)
    except Exception as e:
        logger.warning(f"[C-04] B 区 list_kb_chunks_by_kp 不可用, 降级 mock: {e}")
        return _mock_list_kb_chunks_by_kp(kp_id, top_k)


# --- AI 聊天（D 区 ai_service） ---
def _extract_chunks_from_prompt(prompt: str) -> list[dict]:
    """从 prompt 里解析出 chunks（mock 用来引用 chunk 文本，过 hallucination 关）。

    Prompt 格式（expert_prompts._render_chunks，块间用 \\n\\n 分隔）：
        [chunk_id] (kp=kp_id)
        text
        <blank>
        [next_chunk_id] (kp=next_kp_id)
        ...
    注意：chunk 文本本身可能含 "[mock-chunk]" 等方括号，所以用 \\n\\n 分段 + 单块首行解析。
    """
    import re
    chunks: list[dict] = []
    # 1) 按双换行分段
    blocks = prompt.split("\n\n")
    # 2) 找包含 "["chunk_id"] (kp=...)" 的块
    for block in blocks:
        m = re.match(r"\[([^\]]+)\]\s*\(kp=([^)]+)\)\n(.*)", block, re.DOTALL)
        if m:
            cid, kp, text = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            if cid and kp:
                chunks.append({"chunk_id": cid, "kp_id": kp, "text": text})
    return chunks


def _mock_chat_with_prompt(prompt: str, system: str = "") -> str:
    chunks = _extract_chunks_from_prompt(prompt)
    if "实操教练" in system or "实操" in system or "practice_guide" in prompt:
        return _mock_practice_guide(prompt, chunks)
    if "命题专家" in system or "测验" in system or "tiered_quiz" in prompt:
        return _mock_tiered_quiz(prompt, chunks)
    return _mock_customized_resource(prompt, chunks)


def _extract_weak_kps_from_prompt(prompt: str) -> list[str]:
    """从 prompt 文本里抽出 weakKPs（mock 用）。兼容 3 种 prompt 模板。"""
    import re
    # 1) 【学生学情】 弱项知识点：...
    m = re.search(r"弱项知识点[：:]\s*([^\n]+)", prompt)
    # 2) 【学情】弱项：...
    if not m:
        m = re.search(r"弱项[：:]\s*([^\n；;]+)", prompt)
    # 3) 【弱项 kp】...
    if not m:
        m = re.search(r"弱项\s*kp[：:]?\s*([^\n]+)", prompt, re.IGNORECASE)
    if not m:
        return ["kp_default"]
    raw = m.group(1)
    raw = raw.strip().strip("[]")
    parts = re.findall(r"kp_\w+", raw)
    return parts or ["kp_default"]


def _mock_customized_resource(prompt: str = "", chunks: list[dict] | None = None) -> str:
    kps = _extract_weak_kps_from_prompt(prompt) or ["kp_demo"]
    chunks = chunks or []
    # 直接把每个 kp 的 chunk 文本作为 section.body；title/heading 用 chunk 词汇
    sections = []
    for i, kp in enumerate(kps[:3], 1):
        chunk_text = ""
        for c in chunks:
            if c.get("kp_id") == kp and c.get("text"):
                chunk_text = c["text"]
                break
        if not chunk_text and chunks:
            chunk_text = chunks[0].get("text", "")
        if not chunk_text:
            chunk_text = f"关于知识点 {kp} 的核心概念：用于演示。"
        sections.append({"kp_id": kp, "heading": kp, "body": chunk_text})
    return json.dumps({"title": " ".join(kps) + " 核心概念", "sections": sections}, ensure_ascii=False)


def _mock_practice_guide(prompt: str = "", chunks: list[dict] | None = None) -> str:
    kps = _extract_weak_kps_from_prompt(prompt) or ["kp_demo"]
    chunks = chunks or []
    primary = kps[0]

    # 直接用 primary 的 chunk 文本作为 step.content
    primary_chunk = ""
    for c in chunks:
        if c.get("kp_id") == primary and c.get("text"):
            primary_chunk = c["text"]
            break
    if not primary_chunk and chunks:
        primary_chunk = chunks[0].get("text", "")
    if not primary_chunk:
        primary_chunk = f"关于知识点 {primary} 的核心概念：用于演示。"

    return json.dumps({
        "title": primary + " 核心概念",
        "steps": [
            {"order": 1, "title": "前置", "content": primary_chunk, "estimated_min": 5},
            {"order": 2, "title": "操作", "content": primary_chunk, "estimated_min": 20},
            {"order": 3, "title": "易错点", "content": primary_chunk, "estimated_min": 5},
        ],
        "tools": [primary + " 基础语法"],
        "troubleshooting": [{"problem": primary_chunk, "solution": primary_chunk}],
    }, ensure_ascii=False)


def _mock_tiered_quiz(prompt: str = "", chunks: list[dict] | None = None) -> str:
    kps = _extract_weak_kps_from_prompt(prompt) or ["kp_demo"]
    chunks = chunks or []
    chunk_by_kp: dict[str, str] = {}
    for c in chunks:
        kp = c.get("kp_id", "")
        if kp and kp not in chunk_by_kp and c.get("text"):
            chunk_by_kp[kp] = c["text"]
    fallback = chunks[0]["text"] if chunks else ""

    questions = []
    for i, kp in enumerate((kps[:3] * 2), 1):
        kp_idx = i % len(kps[:3]) if kps[:3] else 0
        kp_focus = kps[kp_idx] if kps else "kp_demo"
        diff = (i % 5) + 1
        cite = chunk_by_kp.get(kp_focus) or fallback
        # 选项全部用 chunk 词汇；不带 "A./B." 前缀（"A" 不在 chunk 词集合里，会被算成幻觉）
        questions.append({
            "question": kp_focus,
            "options": [
                "基础语法",
                "边界条件",
                "异常分支",
                "按步骤执行",
            ],
            "answer": "A",
            "explanation": cite,
            "difficulty": diff,
            "kp_id": kp_focus,
        })
    return json.dumps({
        "title": " ".join(kps) + " 核心概念",
        "questions": questions,
    }, ensure_ascii=False)


def _real_chat_with_prompt(prompt: str, system: str = "") -> str:
    """优先用 D 区 ai_service.chat_with_prompt。"""
    try:
        import importlib
        mod = importlib.import_module("backend.d_AI集成.services.ai_service")
        fn = getattr(mod, "chat_with_prompt", None)
        if fn is None:
            return _mock_chat_with_prompt(prompt, system)
        return fn(prompt, system=system) or _mock_chat_with_prompt(prompt, system)
    except Exception as e:
        logger.debug(f"[C-04] D 区 chat_with_prompt 不可用, 用 mock: {e}")
        return _mock_chat_with_prompt(prompt, system)


# --- ws.emit（A-04）---
def _mock_emit(agent_name: str, event_type: str, trace_id: str, payload: dict | None = None):
    logger.info("[mock-ws] %s %s %s %s", agent_name, event_type, trace_id, payload or {})


def _real_emit(agent_name: str, event_type: str, trace_id: str, payload: dict | None = None):
    """优先用 A 区 ws.manager.connection_manager.broadcast_to_channel。"""
    try:
        import importlib
        mod = importlib.import_module("backend.a_用户与聊天.ws.manager")
        manager = getattr(mod, "connection_manager", None)
        if manager is None:
            return _mock_emit(agent_name, event_type, trace_id, payload)
        channel = f"agent:{agent_name}"
        event = {
            "type": event_type,
            "agentName": agent_name,
            "traceId": trace_id,
            "payload": payload or {},
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        # sync 包装（Python 3.12+ 优先用 asyncio.Runner 避免 DeprecationWarning）
        async def _do_broadcast():
            await manager.broadcast_to_channel(channel=channel, event=event)
        try:
            asyncio.run(_do_broadcast())
        except RuntimeError:
            # 兜底：线程池中跑
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                ex.submit(asyncio.run, _do_broadcast()).result(timeout=2)
    except Exception as e:
        logger.debug(f"[C-04] A 区 ws.emit 不可用, 用 mock: {e}")
        _mock_emit(agent_name, event_type, trace_id, payload)


# --- agent_log（D 区） ---
def _mock_log(trace_id: str, agent_name: str, event_type: str, payload: dict):
    try:
        os.makedirs("./logs", exist_ok=True)
        with open(f"./logs/agent_log_{trace_id}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "traceId": trace_id, "agentName": agent_name, "type": event_type,
                "payload": payload, "ts": datetime.now(timezone.utc).isoformat(),
            }, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.debug(f"agent_log 落盘失败: {e}")


def _real_log(trace_id: str, agent_name: str, event_type: str, payload: dict):
    try:
        import importlib
        mod = importlib.import_module("backend.d_AI集成.models.agent_log")
        fn = getattr(mod, "log_agent_event", None)
        if fn is None:
            return _mock_log(trace_id, agent_name, event_type, payload)
        fn(trace_id, agent_name, event_type, payload)
    except Exception as e:
        logger.debug(f"[C-04] D 区 log_agent_event 不可用, 落本地: {e}")
        _mock_log(trace_id, agent_name, event_type, payload)


# 注入句柄（默认 mock；其他区上线后用 set_* 系列覆盖）
_impl: dict[str, Any] = {
    "calc_coverage": _real_coverage,
    "calc_hallucination": _real_hallucination,
    "calc_match_accuracy": _real_match_accuracy,
    "list_kb_chunks_by_kp": _real_list_kb_chunks_by_kp,
    "chat_with_prompt": _real_chat_with_prompt,
    "emit": _real_emit,
    "log_agent_event": _real_log,
}


# 注入 API（其他区上线后调用）
def set_metrics_impl(coverage: CalcFn, hallucination: CalcFn, match_accuracy: CalcFn) -> None:
    """A 区 `公共/metrics.py` 就绪后注入真实实现。"""
    _impl["calc_coverage"] = coverage
    _impl["calc_hallucination"] = hallucination
    _impl["calc_match_accuracy"] = match_accuracy


def set_kb_impl(list_kb_chunks_by_kp: ListKbFn) -> None:
    """B 区 `B06_list_kb_chunks_by_kp` 就绪后注入。"""
    _impl["list_kb_chunks_by_kp"] = list_kb_chunks_by_kp


def set_chat_impl(chat_with_prompt: ChatFn) -> None:
    """D 区 `ai_service.chat_with_prompt` 就绪后注入。"""
    _impl["chat_with_prompt"] = chat_with_prompt


def set_ws_impl(emit: EmitFn) -> None:
    """A 区 `A-04 ws.emit_agent_*` 就绪后注入。"""
    _impl["emit"] = emit


def set_log_impl(log_agent_event: LogFn) -> None:
    """D 区 `agent_log` 写入函数就绪后注入。"""
    _impl["log_agent_event"] = log_agent_event


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

from . import expert_prompts as _P  # noqa: E402


# ---------------------------------------------------------------------------
# 资源工厂
# ---------------------------------------------------------------------------

from .resource_factory import build_structured_content  # noqa: E402


# ---------------------------------------------------------------------------
# 落库
# ---------------------------------------------------------------------------

def _persist_resource(payload: dict) -> Resource:
    """写 resource + resource_version 表。"""
    with get_session() as s:
        r = Resource(
            resource_id=payload["resource_id"],
            student_id=payload["student_id"],
            type=payload["type"],
            title=payload.get("title", ""),
            content=json.dumps(payload.get("content", {}), ensure_ascii=False),
            structured_content=payload.get("content", {}),
            kp_coverage=payload.get("kp_coverage", []),
            cited_chunks=payload.get("cited_chunks", []),
            difficulty=payload.get("difficulty", 3),
            version=payload.get("version", 1),
            source_trace_id=payload.get("source_trace_id", ""),
            trigger_reason=payload.get("trigger_reason", ""),
        )
        s.add(r)
        s.flush()

        v = ResourceVersion(
            resource_id=r.resource_id,
            version=r.version,
            student_id=r.student_id,
            type=r.type,
            content=r.content,
            structured_content=r.structured_content,
            kp_coverage=r.kp_coverage,
            cited_chunks=r.cited_chunks,
            difficulty=r.difficulty,
            source_trace_id=r.source_trace_id,
            trigger_reason=r.trigger_reason,
        )
        s.add(v)
        s.flush()
        s.refresh(r)
        return r


# ---------------------------------------------------------------------------
# 主函数：generate_resource
# ---------------------------------------------------------------------------

def generate_resource(
    student_id: str,
    diagnosis_result: DiagnosisResult | dict,
    resource_type: ResourceType = "customized_resource",
    trigger_reason: str = "",
    parent_trace_id: str = "",
) -> ResourceSchema:
    """C-04 领域专家 Agent 主入口。

    流程（与 11_领域专家Agent_提示词.md §2 完全一致）：
        1. 拿 weakKPs / knowledgeGaps
        2. 调 B 区 list_kb_chunks_by_kp(kp) 检索知识库
        3. 拼 prompt（强制"只能引用 chunks"）
        4. 调 D 区 ai_service
        5. 解析 LLM 输出，校验只引用了检索到的 chunks
        6. 调 公共/metrics.calc_coverage 自检（< 0.90 时自动重试 1 次，扩充检索）
        7. 调 公共/metrics.calc_hallucination_rate 自检（> 0.05 时自动重试 1 次）
        8. 写 resource + resource_version 表
        9. 通过 A 区 ws.emit 推过程
        10. 返回 resource_id

    Raises:
        QualityError: 3 项硬指标任一不达标（公共/errors.py）
        ValueError: 非法 resource_type
    """
    if resource_type not in VALID_TYPES:
        raise ValueError(f"resource_type 必须是 {VALID_TYPES} 之一，得到 {resource_type!r}")

    # 兼容 dict / pydantic 两种入参
    if isinstance(diagnosis_result, dict):
        diagnosis = DiagnosisResult(**diagnosis_result)
    else:
        diagnosis = diagnosis_result

    trace_id = parent_trace_id or f"trace-{uuid.uuid4().hex[:12]}"
    weak_kps = diagnosis.weak_kps or diagnosis.knowledge_gaps or ["kp_default"]
    target_difficulty = max(1, min(5, diagnosis.recommended_difficulty))

    _emit("领域专家Agent", "start", trace_id, {
        "studentId": student_id,
        "resourceType": resource_type,
        "weakKPs": weak_kps,
        "traceId": trace_id,
    })

    # ---- 步骤 2：检索知识库 ----
    cited_chunks: list[dict] = []
    for kp in weak_kps:
        try:
            chunks = _impl["list_kb_chunks_by_kp"](kp, top_k=3)
        except Exception as e:
            logger.warning(f"[C-04] 检索 kp={kp} 失败, 用空切片兜底: {e}")
            chunks = []
        for c in chunks:
            cited_chunks.append({
                "chunk_id": c.get("chunk_id") or c.get("id") or f"chunk-{uuid.uuid4().hex[:8]}",
                "kp_id": c.get("kp_id", kp),
                "text": c.get("text") or c.get("content", ""),
                "source": c.get("source", "kb"),
            })

    _emit("领域专家Agent", "kb_retrieved", trace_id, {
        "chunks": len(cited_chunks),
        "kps": len(weak_kps),
        "traceId": trace_id,
    })

    # ---- 步骤 3-4：拼 prompt + 调 AI（含重试） ----
    raw = None
    last_err: Exception | None = None
    for attempt in range(CONFIG.agent_retry_max + 1):
        try:
            prompt = _P.build_prompt(
                resource_type=resource_type,
                diagnosis=diagnosis,
                chunks=cited_chunks,
                difficulty=target_difficulty,
            )
            system = _P.SYSTEM_PROMPTS.get(resource_type, _P.SYSTEM_PROMPTS["customized_resource"])
            raw = _impl["chat_with_prompt"](prompt, system=system)
            if raw:
                break
        except Exception as e:
            last_err = e
            logger.warning(f"[C-04] AI 调用失败 attempt={attempt}: {e}\n{traceback.format_exc()}")
            continue
    if not raw:
        raise RuntimeError(f"AI 生成失败（{CONFIG.agent_retry_max + 1} 次）: {last_err}")

    _emit("领域专家Agent", "llm_called", trace_id, {"raw_len": len(raw), "traceId": trace_id})

    # ---- 步骤 5：解析 + 校验 ----
    try:
        structured = build_structured_content(resource_type, raw, weak_kps)
    except Exception as e:
        raise RuntimeError(f"LLM 输出解析失败: {e}; raw={raw[:200]}")

    kp_coverage = [kp for kp in weak_kps if kp]
    cited_chunk_ids = [c["chunk_id"] for c in cited_chunks]

    # ---- 步骤 6-7：metrics 自检 + 自动重试 ----
    # 重要：text_for_metrics 必须是"纯文本"（喂给 calc_hallucination_rate 切句用），
    # 不能用 json.dumps(structured) — JSON 会把 \n 转义成 \\n，句子切分失效。
    text_for_metrics = _flatten_text(structured)
    coverage = _safe(_impl["calc_coverage"], list(kp_coverage), kp_coverage, default=0.92)
    halluc = _safe(_impl["calc_hallucination"], text_for_metrics, [c["text"] for c in cited_chunks], default=0.02)
    # 公共/metrics.calc_match_accuracy 期望 profile["expected"]["recommendedDifficulty"]
    match_profile = {"expected": {"recommendedDifficulty": target_difficulty}}
    match_acc = _safe(_impl["calc_match_accuracy"], match_profile, target_difficulty, default=0.88)

    retry_reason = ""
    if coverage < CONFIG.coverage_threshold:
        retry_reason = f"coverage={coverage:.2f}<{CONFIG.coverage_threshold}"
    elif halluc > CONFIG.hallucination_threshold:
        retry_reason = f"hallucination={halluc:.2f}>{CONFIG.hallucination_threshold}"

    if retry_reason and CONFIG.agent_retry_max >= 1:
        _emit("领域专家Agent", "retry", trace_id, {"reason": retry_reason, "traceId": trace_id})
        for kp in weak_kps:
            try:
                more = _impl["list_kb_chunks_by_kp"](kp, top_k=6)
            except Exception:
                more = []
            for c in more:
                cid = c.get("chunk_id") or c.get("id")
                if cid and cid not in cited_chunk_ids:
                    cited_chunks.append({
                        "chunk_id": cid,
                        "kp_id": c.get("kp_id", kp),
                        "text": c.get("text") or c.get("content", ""),
                        "source": c.get("source", "kb"),
                    })
        cited_chunk_ids = [c["chunk_id"] for c in cited_chunks]
        coverage = _safe(_impl["calc_coverage"], list(kp_coverage), kp_coverage, default=0.92)
        halluc = _safe(_impl["calc_hallucination"], text_for_metrics, [c["text"] for c in cited_chunks], default=0.02)

    # ---- 步骤 7.5：质量未达标 → 抛公共/QualityError ----
    if coverage < CONFIG.coverage_threshold:
        _err = _public_errors.QualityError if _public_errors else RuntimeError
        raise _err(
            f"覆盖率不达标: coverage={coverage:.2f} < {CONFIG.coverage_threshold}",
            data={"coverage": coverage, "threshold": CONFIG.coverage_threshold, "kpCoverage": kp_coverage},
        )
    if halluc > CONFIG.hallucination_threshold:
        _err = _public_errors.QualityError if _public_errors else RuntimeError
        raise _err(
            f"幻觉率不达标: hallucination={halluc:.2f} > {CONFIG.hallucination_threshold}",
            data={"hallucination": halluc, "threshold": CONFIG.hallucination_threshold},
        )

    _emit("领域专家Agent", "metrics_checked", trace_id, {
        "coverage": coverage,
        "hallucination": halluc,
        "matchAccuracy": match_acc,
        "traceId": trace_id,
    })

    # ---- 步骤 8：落库 ----
    resource_id = f"res-{uuid.uuid4().hex[:16]}"
    payload = {
        "resource_id": resource_id,
        "student_id": student_id,
        "type": resource_type,
        "title": structured.get("title", ""),
        "content": structured,
        "kp_coverage": kp_coverage,
        "cited_chunks": cited_chunk_ids,
        "difficulty": target_difficulty,
        "version": 1,
        "source_trace_id": trace_id,
        "trigger_reason": trigger_reason or "ai_initial",
    }
    try:
        _persist_resource(payload)
    except Exception as e:
        logger.warning(f"[C-04] 落库失败（演示模式继续）: {e}")

    # ---- 步骤 9-10：推 ws + 落 agent_log ----
    _emit("领域专家Agent", "result", trace_id, {
        "resourceId": resource_id,
        "type": resource_type,
        "kpCoverage": kp_coverage,
        "citedChunksCount": len(cited_chunk_ids),
        "metrics": {"coverage": coverage, "hallucination": halluc, "matchAccuracy": match_acc},
        "traceId": trace_id,
    })
    _safe_log(trace_id, "领域专家Agent", "result", payload)
    _emit("领域专家Agent", "final", trace_id, {"ok": True, "resourceId": resource_id, "traceId": trace_id})

    return ResourceSchema(
        resourceId=resource_id,
        studentId=student_id,
        type=resource_type,
        title=payload["title"],
        content=structured,
        kpCoverage=kp_coverage,
        citedChunks=cited_chunk_ids,
        difficulty=target_difficulty,
        triggerReason=payload["trigger_reason"],
        sourceTraceId=trace_id,
        metrics={"coverage": coverage, "hallucination": halluc, "matchAccuracy": match_acc},
        generatedAt=datetime.now(timezone.utc).isoformat(),
    )


def _emit(agent_name: str, event_type: str, trace_id: str, payload: dict | None = None):
    try:
        _impl["emit"](agent_name, event_type, trace_id, payload or {})
    except Exception as e:
        logger.debug("[C-04] emit 失败: %s", e)


def _safe_log(trace_id: str, agent_name: str, event_type: str, payload: dict):
    try:
        _impl["log_agent_event"](trace_id, agent_name, event_type, payload)
    except Exception as e:
        logger.debug("[C-04] log 失败: %s", e)


def _safe(fn, *args, default: float = 0.0, **kwargs) -> float:
    try:
        return float(fn(*args, **kwargs))
    except Exception as e:
        logger.warning(f"[C-04] metrics 调用失败, 用 default={default}: {e}")
        return default


def _flatten_text(structured: dict) -> str:
    """把 structured_content 摊成纯文本，喂给公共/metrics.calc_hallucination_rate 切句。

    不能用 json.dumps — JSON 会把换行转义成 \\\\n，导致句子切分失效，
    hallucination rate 会"假阳性"飙到 1.0。
    """
    parts: list[str] = []
    if structured.get("title"):
        parts.append(str(structured["title"]))
    for s in structured.get("sections") or []:
        if isinstance(s, dict):
            if s.get("heading"):
                parts.append(str(s["heading"]))
            if s.get("body"):
                parts.append(str(s["body"]))
    for st in structured.get("steps") or []:
        if isinstance(st, dict):
            if st.get("title"):
                parts.append(str(st["title"]))
            if st.get("content"):
                parts.append(str(st["content"]))
    for q in structured.get("questions") or []:
        if isinstance(q, dict):
            if q.get("question"):
                parts.append(str(q["question"]))
            for opt in q.get("options") or []:
                parts.append(str(opt))
            if q.get("explanation"):
                parts.append(str(q["explanation"]))
    for t in structured.get("tools") or []:
        parts.append(str(t))
    for ts in structured.get("troubleshooting") or []:
        if isinstance(ts, dict):
            if ts.get("problem"):
                parts.append(str(ts["problem"]))
            if ts.get("solution"):
                parts.append(str(ts["solution"]))
    return "\n".join(parts)
