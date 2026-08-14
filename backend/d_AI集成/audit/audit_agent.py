"""
D-06 ⭐ 夺奖专项：审核裁判 Agent 主体。

职责：把 C 区领域专家 Agent 生成的内容严格与 B 区知识库切片做比对 →
      计算幻觉率 + 覆盖率 → 输出 0-1 评分 + 结构化审核结果。

模块级入口：
    audit(studentId, content, kp_ids) -> AuditResult dict

验收标准（一票否决项）：
  ✅ 返回 {auditId, traceId, score, result, issues[], metrics: {hallucinationRate, coverage}, ts}
  ✅ 幻觉率校验：逐句检索知识库，相似度 < 0.5 视为幻觉
  ✅ 核心知识点覆盖率校验：< 0.90 列入 issues
  ✅ 评分公式：score = 0.6 * (1 - hallucinationRate) + 0.4 * coverage
  ✅ 推送 WS agent.thinking + agent.result 事件
  ✅ 写审核日志到 audit_record 表
  ✅ 单测覆盖 ≥ 8 用例
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Optional

from backend.公共.errors import QualityError
from backend.公共.logger import get_logger

from backend.d_AI集成.db import get_session
from backend.d_AI集成.models.audit_record import AuditRecord

from backend.d_AI集成.audit import audit_prompts as prompts
from backend.d_AI集成.audit.groundness_check import check_hallucination
from backend.d_AI集成.audit.coverage_check import check_coverage

log = get_logger(__name__)


# -------- 评分判定 --------

def _score_to_result(score: float) -> str:
    """评分 → 审核结论。"""
    if score >= 0.85:
        return "pass"
    elif score >= 0.70:
        return "retry"
    else:
        return "fail"


# -------- WS 推送（失败降级为 log.warn，不阻塞主流程）--------

async def _emit_agent_event(
    event_type: str,
    *,
    agent_name: str = "审核裁判Agent",
    step: int = 0,
    content: str = "",
    trace_id: str,
    data: Optional[dict] = None,
) -> None:
    """
    调 A-04 的 connection_manager.broadcast_to_channel 推送 Agent 事件。
    WS 不可用时降级为 warn log。
    """
    event = {
        "type": event_type,
        "agentName": agent_name,
        "step": step,
        "content": content,
        "traceId": trace_id,
        "timestamp": time.time(),
    }
    if data is not None:
        event["data"] = data
    try:
        from backend.a_用户与聊天.ws.manager import connection_manager
        from backend.a_用户与聊天.ws.events import EVENT_CHANNEL_PREFIX
        channel = f"{EVENT_CHANNEL_PREFIX}{agent_name}"
        await connection_manager.broadcast_to_channel(channel=channel, event=event)
        try:
            await connection_manager.record_event(event)
        except Exception:
            pass
    except Exception as e:
        log.warning(f"WS 推送降级（A 区未就绪？）: type={event_type} err={e}")


# -------- 入库 --------

async def _save_audit_record(
    *,
    audit_id: str,
    trace_id: str,
    student_id: str,
    result: str,
    issues: list[dict],
    score: float,
    hallucination_rate: float,
    coverage: float,
    content_snapshot: str,
    kp_ids: list[str],
) -> None:
    """保存审核记录到 audit_record 表。"""
    try:
        async with get_session() as session:
            rec = AuditRecord(
                audit_id=audit_id,
                trace_id=trace_id,
                student_id=student_id,
                result=result,
                issues=issues,
                score=score,
                hallucination_rate=hallucination_rate,
                coverage=coverage,
                content_snapshot=content_snapshot,
                kp_ids=kp_ids,
            )
            session.add(rec)
    except Exception as e:
        log.error(f"保存审核记录失败: {e}")


# -------- 模块级入口：audit() --------

async def audit(
    studentId: str,
    content: str,
    kp_ids: list[str],
) -> dict:
    """
    D-06 审核裁判 Agent 入口（暴露给 D-03 协同编排器）。

    :param studentId: 学生 ID
    :param content: C 区 generate_resource 输出的内容文本
    :param kp_ids: C 声称覆盖的知识点 ID 列表
    :return: AuditResult dict
      {
        auditId, traceId, studentId, score, result,
        issues[], metrics: {hallucinationRate, coverage},
        ts
      }
    """
    if not studentId:
        from backend.公共.errors import BizError
        raise BizError("studentId 不能为空", code=400)
    if not content:
        from backend.公共.errors import BizError
        raise BizError("content 不能为空", code=400)

    trace_id = f"trace-aud-{studentId}-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    audit_id = f"aud-{uuid.uuid4().hex[:16]}"
    now = datetime.now()

    # 1) agent.start
    await _emit_agent_event(
        "agent.start",
        step=1,
        content=prompts.START_STEP_CONTENT,
        trace_id=trace_id,
    )

    # 2) 幻觉率校验
    await _emit_agent_event(
        "agent.thinking",
        step=2,
        content=prompts.THINKING_STEPS[0],
        trace_id=trace_id,
    )
    await _emit_agent_event(
        "agent.thinking",
        step=3,
        content=prompts.THINKING_STEPS[1],
        trace_id=trace_id,
    )
    hallucination_result = await check_hallucination(content, kp_ids)
    hallucination_rate = hallucination_result["hallucinationRate"]

    # 3) 覆盖率校验
    await _emit_agent_event(
        "agent.thinking",
        step=4,
        content=prompts.THINKING_STEPS[2],
        trace_id=trace_id,
    )
    coverage_result = check_coverage(content, kp_ids)
    coverage = coverage_result["coverage"]

    # 4) 综合评分
    await _emit_agent_event(
        "agent.thinking",
        step=5,
        content=prompts.THINKING_STEPS[3],
        trace_id=trace_id,
    )
    score = round(0.6 * (1 - hallucination_rate) + 0.4 * coverage, 4)
    result = _score_to_result(score)

    # 5) 汇总 issues
    issues: list[dict] = []
    for sent_detail in hallucination_result.get("sentenceDetails", []):
        if sent_detail.get("isHallucination"):
            issues.append({
                "type": "hallucination",
                "detail": prompts.ISSUE_HALLUCINATION.format(
                    sentence=sent_detail["sentence"],
                    similarity=sent_detail["similarity"],
                ),
            })
    if not coverage_result["isPass"]:
        issues.append({
            "type": "coverage_low",
            "detail": prompts.ISSUE_COVERAGE_LOW.format(
                covered=len(coverage_result["coveredKps"]),
                total=coverage_result["totalRequired"],
                ratio=coverage,
            ),
        })
    for missing_kp in coverage_result.get("missingKps", []):
        issues.append({
            "type": "kp_missing",
            "detail": prompts.ISSUE_KP_MISSING.format(
                kp_id=missing_kp,
                kp_name=missing_kp,
            ),
        })

    # 6) agent.result 推送
    result_summary = prompts.RESULT_SUMMARY_TEMPLATE.format(
        hr=hallucination_rate,
        cov=coverage,
        score=score,
        result=prompts.RESULT_LABELS.get(result, result),
    )
    result_payload = {
        "auditId": audit_id,
        "traceId": trace_id,
        "studentId": studentId,
        "score": score,
        "result": result,
        "issues": issues,
        "metrics": {
            "hallucinationRate": hallucination_rate,
            "coverage": coverage,
        },
        "ts": now.isoformat(),
    }
    await _emit_agent_event(
        "agent.result",
        step=6,
        content=result_summary,
        data=result_payload,
        trace_id=trace_id,
    )

    # 7) 写入 audit_record 表
    await _save_audit_record(
        audit_id=audit_id,
        trace_id=trace_id,
        student_id=studentId,
        result=result,
        issues=issues,
        score=score,
        hallucination_rate=hallucination_rate,
        coverage=coverage,
        content_snapshot=content[:500] if content else "",
        kp_ids=kp_ids,
    )

    return result_payload