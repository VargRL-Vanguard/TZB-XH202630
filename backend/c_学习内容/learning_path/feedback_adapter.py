"""动态迭代机制（C-06）— 降维解释 / 进阶挑战。

接入位置：POST /api/learning-path/feedback

触发规则（来自任务清单_c_学习内容.md C-06）：
- 某 kp 正确率 < 0.6 且样本数 ≥ 3 → 自动生成 difficulty-1 的 customized_resource（降维解释）
- 某 kp 正确率 > 0.9 且样本数 ≥ 3 → 自动生成 difficulty+1 的 tiered_quiz（进阶挑战）
- 样本不足 → 不触发（仅写日志）

事件推送：通过 A 区 `ws.manager.connection_manager.broadcast_to_channel` 推
agent.start / agent.thinking / agent.final（与 expert_agent.py 共用通道 `agent:领域专家Agent`）。
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import deque

from ..agents import generate_resource
from ..db import get_session
from ..models import InteractionLog

# 公共/logger 兼容兜底（loguru 未装时降级到标准 logging）
try:
    from backend.公共.logger import get_logger as _public_get_logger
    log = _public_get_logger(__name__)
except Exception:  # pragma: no cover
    log = logging.getLogger(__name__)
# 兼容：保留旧名 logger
logger = log

DOWNGRADE_THRESHOLD = 0.6   # < 此值触发降维
UPGRADE_THRESHOLD = 0.9     # > 此值触发进阶
MIN_SAMPLES = 3             # 至少 N 条样本才触发
RECENT_WINDOW = 10          # 计算正确率时只看最近 N 条


# 进程内缓存（演示模式；生产用 Redis 替代）
_recent_buffers: dict[tuple[str, str], deque[int]] = {}


def _recent_buffer_key(student_id: str, kp_id: str) -> tuple[str, str]:
    return (student_id, kp_id)


def _rolling_accuracy(student_id: str, kp_id: str) -> tuple[float, int]:
    """拿最近 RECENT_WINDOW 条交互，计算正确率。"""
    key = _recent_buffer_key(student_id, kp_id)
    buf = _recent_buffers.get(key)
    if buf is None:
        buf = deque(maxlen=RECENT_WINDOW)
        _recent_buffers[key] = buf
    if not buf:
        return 0.0, 0
    correct = sum(buf)
    return correct / len(buf), len(buf)


def _emit(agent: str, event_type: str, trace_id: str, payload: dict):
    """通过 A 区 `ws.manager.connection_manager` 推送事件。

    事件协议（与 `a_用户与聊天/ws/events.py` 对齐）：
        agent.start    →  AgentStartEvent
        agent.thinking →  AgentThinkingEvent
        agent.final    →  AgentFinalEvent
    """
    try:
        import importlib
        mod = importlib.import_module("backend.a_用户与聊天.ws.manager")
        manager = getattr(mod, "connection_manager", None)
        if manager is None:
            return
        channel = f"agent:{agent}"
        ts = time.time()
        # 事件类型归一化（start/thinking/final → agent.*）
        evt_type_map = {"start": "agent.start", "thinking": "agent.thinking", "final": "agent.final"}
        evt_type = evt_type_map.get(event_type, f"agent.{event_type}")

        if event_type == "start":
            event = {
                "type": evt_type,
                "agentName": agent,
                "step": 1,
                "traceId": trace_id,
                "timestamp": ts,
                "payload": payload or {},
            }
        elif event_type == "thinking":
            content = (payload or {}).get("content") or (payload or {}).get("summary") or ""
            event = {
                "type": evt_type,
                "agentName": agent,
                "step": 2,
                "content": content,
                "traceId": trace_id,
                "timestamp": ts,
                "payload": payload or {},
            }
        else:  # final / 其它
            ok = bool((payload or {}).get("ok", True))
            summary = (payload or {}).get("summary") or (payload or {}).get("error") or ""
            event = {
                "type": evt_type,
                "agentName": agent,
                "step": 99,
                "ok": ok,
                "summary": summary,
                "traceId": trace_id,
                "timestamp": ts,
                "payload": payload or {},
            }

        # sync 包装（A 区 manager 是 async）；用 asyncio.run 避免 3.12+ DeprecationWarning
        async def _do_broadcast():
            await manager.broadcast_to_channel(channel=channel, event=event)
        try:
            asyncio.run(_do_broadcast())
        except RuntimeError:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                ex.submit(asyncio.run, _do_broadcast()).result(timeout=2)
    except Exception as e:
        log.debug(f"[C-06] A 区 ws.connection_manager 不可用（mock 兜底）: {e}")


def _decide(accuracy: float, samples: int) -> tuple[str, str]:
    """返回 (action, trigger_reason) — action in {"downgrade","upgrade","none"}。"""
    if samples < MIN_SAMPLES:
        return "none", "insufficient_samples"
    if accuracy < DOWNGRADE_THRESHOLD:
        return "downgrade", "low_accuracy"
    if accuracy > UPGRADE_THRESHOLD:
        return "upgrade", "high_accuracy"
    return "none", "stable"


def _persist_log(
    student_id: str,
    kp_id: str,
    question_id: str,
    correct: bool,
    response_time_ms: int,
    difficulty: int,
    resource_id: str,
    accuracy: float,
    action: str,
):
    with get_session() as s:
        s.add(InteractionLog(
            student_id=student_id,
            kp_id=kp_id,
            question_id=question_id,
            correct=1 if correct else 0,
            response_time_ms=response_time_ms,
            difficulty=difficulty,
            resource_id=resource_id,
            accuracy_rolling=accuracy,
            triggered_action=action,
        ))


def handle_feedback(
    student_id: str,
    kp_id: str,
    question_id: str = "",
    correct: bool = True,
    response_time_ms: int = 0,
    difficulty: int = 3,
    resource_id: str = "",
) -> dict:
    """POST /api/learning-path/feedback 的核心处理函数。

    返回：
        {
            "logged": True,
            "accuracy": 0.45,
            "samples": 5,
            "action": "downgrade" | "upgrade" | "none",
            "triggerReason": "low_accuracy" | "high_accuracy" | "stable" | "insufficient_samples",
            "resourceId": "..."  # 若触发生成
        }
    """
    if not student_id or not kp_id:
        raise ValueError("student_id 和 kp_id 必填")

    # 1. 写日志 + 更新最近正确率窗口
    key = _recent_buffer_key(student_id, kp_id)
    buf = _recent_buffers.setdefault(key, deque(maxlen=RECENT_WINDOW))
    buf.append(1 if correct else 0)
    accuracy, samples = _rolling_accuracy(student_id, kp_id)

    action, reason = _decide(accuracy, samples)
    _persist_log(student_id, kp_id, question_id, correct, response_time_ms, difficulty, resource_id, accuracy, action)

    result: dict = {
        "logged": True,
        "accuracy": round(accuracy, 3),
        "samples": samples,
        "action": action,
        "triggerReason": reason,
    }

    if action == "none":
        return result

    # 2. 触发领域专家 Agent
    trace_id = f"iter-{uuid.uuid4().hex[:12]}"
    _emit("领域专家Agent", "start", trace_id, {
        "studentId": student_id, "kpId": kp_id, "action": action,
        "accuracy": accuracy, "traceId": trace_id,
    })

    target_type = "customized_resource" if action == "downgrade" else "tiered_quiz"
    new_difficulty = max(1, min(5, difficulty - 1)) if action == "downgrade" else min(5, difficulty + 1)

    try:
        from ..agents import DiagnosisResult
        diagnosis = DiagnosisResult(
            studentId=student_id,
            weakKPs=[kp_id],
            knowledgeGaps=[kp_id],
            recommendedDifficulty=new_difficulty,
        )
        resource = generate_resource(
            student_id=student_id,
            diagnosis_result=diagnosis,
            resource_type=target_type,
            trigger_reason=reason,
            parent_trace_id=trace_id,
        )
        result["resourceId"] = resource.resource_id
        result["resourceType"] = target_type
        result["newDifficulty"] = new_difficulty
        _emit("领域专家Agent", "thinking", trace_id, {
            "resourceId": resource.resource_id, "type": target_type, "difficulty": new_difficulty,
            "traceId": trace_id,
        })
        _emit("领域专家Agent", "final", trace_id, {
            "ok": True, "resourceId": resource.resource_id, "traceId": trace_id,
        })
    except Exception as e:
        log.warning(f"[C-06] 动态迭代触发生成失败, 保持当前难度: {e}")
        result["error"] = str(e)
        _emit("领域专家Agent", "final", trace_id, {"ok": False, "error": str(e), "traceId": trace_id})

    return result


# 给 service.py re-export
__all__ = ["handle_feedback"]
