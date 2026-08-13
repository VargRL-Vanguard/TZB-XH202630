"""
B-05 ⭐ 夺奖专项：学情诊断 Agent 主体。

职责：拿 get_student_snapshot 的画像 + 最近活动 →
      精准锚定学习者的理论强项与技能盲区 →
      输出结构化 DiagnosisResult + WS 推送 + 历史入库。

模块级入口：
    diagnose(studentId) -> DiagnosisResult dict

验收标准（一票否决项）：
  ✅ 返回 {studentId, weakKPs[], strongKPs[], knowledgeGaps[], confidence, traceId, generatedAt}
  ✅ 推送 WS agent.thinking 事件（A-04 ws.emit）
  ✅ 保存诊断历史到 diagnosis_record 表
  ✅ 调用 calc_match_accuracy 自我校验（与学习者画像自洽）
  ✅ confidence < 0.6 抛 QualityError
  ✅ prompt 版本号
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Optional

from backend.公共.errors import QualityError
from backend.公共.logger import get_logger

from backend.b_学情数据.student import get_student_snapshot
from backend.b_学情数据.activity import get_recent_activities
from backend.b_学情数据.db import get_session
from backend.b_学情数据.models.diagnosis_record import DiagnosisRecord

from backend.b_学情数据.analytics import diagnosis_prompts as prompts

log = get_logger(__name__)

# 盲区严重度阈值
SEVERITY_THRESHOLDS = [
    ("high", 60.0),
    ("medium", 75.0),
    ("low", 85.0),
]


def _severity_from_score(score: float) -> str:
    for label, thr in SEVERITY_THRESHOLDS:
        if score < thr:
            return label
    return "none"


# -------- WS 推送（失败降级为 log.warn，不阻塞主流程）--------

async def _emit_agent_event(
    event_type: str,
    *,
    agent_name: str = "学情诊断Agent",
    step: int = 0,
    content: str = "",
    trace_id: str,
    data: Optional[dict] = None,
) -> None:
    """
    调 A-04 的 connection_manager.broadcast_to_channel 推送 Agent 事件。
    WS 不可用时（测试环境 / A 区未启动）降级为 warn log，保证 diagnose 主流程完成。
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
        # 也同时入环形缓冲（断线重连重放）
        try:
            await connection_manager.record_event(event)
        except Exception:
            pass
    except Exception as e:
        log.warning(f"WS 推送降级（A 区未就绪？）: type={event_type} err={e}")


# -------- 核心诊断算法（规则引擎 MVP）--------

def _aggregate_kp_stats(activities: list[dict]) -> dict[str, dict]:
    """
    从最近活动中聚合每个 kp 的统计：
    return {kp_id: {"sum": float, "count": int, "avg": float, "evidence": list[str]}}
    """
    stats: dict[str, dict] = {}
    for a in activities:
        kps = a.get("kpTags") or []
        score = a.get("score")
        rname = a.get("resourceName") or "未命名活动"
        for kp in kps:
            s = stats.setdefault(kp, {"sum": 0.0, "count": 0, "activities": []})
            if score is not None:
                s["sum"] += float(score)
                s["count"] += 1
            s["activities"].append(rname)
    out = {}
    for kp, s in stats.items():
        avg = (s["sum"] / s["count"]) if s["count"] > 0 else 0.0
        out[kp] = {
            "avg": avg,
            "count": s["count"],
            "evidence": s["activities"][:3],  # 最多取 3 条活动名当证据
        }
    return out


def _kp_name_map() -> dict[str, str]:
    """kp_id -> 中文名称：先硬编码 6 模块，B-06 后可从 kp_taxonomy.json 动态加载。"""
    return {
        "kp01": "工业机器人基础",
        "kp02": "工业机器人坐标系",
        "kp03": "PLC 编程基础",
        "kp04": "传感器与检测技术",
        "kp05": "工业互联网通信",
        "kp06": "智能制造系统集成",
        "kp12": "工业机器人坐标系（进阶）",
        "kp15": "工业机器人路径规划",
        "kp18": "机器人运动学建模",
        "kp22": "PLC 模拟量处理",
    }


async def _diagnose_core(
    student_id: str,
    trace_id: str,
) -> tuple[dict, list[str], list[str], list[dict], float]:
    """
    核心诊断逻辑（不包含 WS 推送 / 入库，纯函数便于单测）。
    返回：(snapshot, weakKPs, strongKPs, knowledgeGaps, confidence)
    """
    # 1) 取画像快照
    snapshot = await get_student_snapshot(student_id)
    if snapshot is None:
        from backend.公共.errors import NotFoundError
        raise NotFoundError(f"学生 {student_id} 不存在（快照为空）")

    # 推送思考：步骤 1
    await _emit_agent_event(
        "agent.thinking",
        step=1,
        content=prompts.THINKING_STEPS[0],
        trace_id=trace_id,
    )

    learner = snapshot.get("learnerProfile") or {}
    profile_weak = set(learner.get("weakKPs") or [])
    profile_strong = set(learner.get("strongKPs") or [])
    theory_score = learner.get("theoryTestScore")

    # 2) 聚合最近 30 天活动
    activities = await get_recent_activities(student_id, days=30, limit=200)
    await _emit_agent_event(
        "agent.thinking", step=2,
        content=prompts.THINKING_STEPS[1].replace("30", "30"),
        trace_id=trace_id,
    )

    kp_stats = _aggregate_kp_stats(activities)
    kp_names = _kp_name_map()

    # 3) 基于活动数据扩展弱/强知识列表
    await _emit_agent_event(
        "agent.thinking", step=3,
        content=prompts.THINKING_STEPS[2],
        trace_id=trace_id,
    )

    activity_weak: set[str] = set()
    activity_strong: set[str] = set()
    knowledge_gaps: list[dict] = []

    for kp_id, stat in kp_stats.items():
        if stat["count"] == 0:
            continue
        avg = stat["avg"]
        sev = _severity_from_score(avg)
        if sev == "high" or sev == "medium":
            activity_weak.add(kp_id)
        if avg >= 85.0:
            activity_strong.add(kp_id)
        if sev in ("high", "medium", "low") and avg < 85.0:
            evidence_str = (
                f"基于 {stat['count']} 次活动得分均值 {avg:.1f}；"
                f"相关活动：{', '.join(stat['evidence']) or '无'}"
            )
            knowledge_gaps.append({
                "kp_id": kp_id,
                "kp_name": kp_names.get(kp_id, kp_id),
                "severity": sev,
                "evidence": evidence_str,
            })

    # 合并：画像优先，活动数据作为扩展
    weak_kps_set = profile_weak | activity_weak
    strong_kps_set = profile_strong | activity_strong

    # 对画像中声明的 weakKPs，如果没有活动证据，也补一条盲区（low severity）
    for kp_id in profile_weak:
        if kp_id not in {g["kp_id"] for g in knowledge_gaps}:
            knowledge_gaps.append({
                "kp_id": kp_id,
                "kp_name": kp_names.get(kp_id, kp_id),
                "severity": "medium",
                "evidence": "画像 learnerProfile.weakKPs 标注为弱知识，暂无活动数据佐证。",
            })

    # 4) 置信度计算
    await _emit_agent_event(
        "agent.thinking", step=4,
        content=prompts.THINKING_STEPS[3],
        trace_id=trace_id,
    )
    confidence = _calc_confidence(
        learner=learner,
        theory_score=theory_score,
        activity_count=len(activities),
        kp_stat_count=len(kp_stats),
        profile_weak=profile_weak,
        activity_weak=activity_weak,
    )

    # 自洽性校验：calc_match_accuracy（S-01）
    # 以"理论测试分"预期难度为例：
    # theoryTestScore >=80 -> expected difficulty 4/5，60-80 -> 3，<60 -> 2
    if theory_score is not None:
        expected_diff = 2 if theory_score < 60 else (3 if theory_score < 80 else 5)
    else:
        expected_diff = 3
    try:
        from backend.公共.metrics import calc_match_accuracy
        # 用"平均 6 维能力得分 / 20"映射到难度 1-5 作为"资源侧难度"近似，
        # 规则引擎预期自洽度 ≥0.5，低于则 confidence 适当下降
        dims = snapshot.get("dimensions") or {}
        if dims:
            avg_dim = sum(int(d or 0) for d in dims.values()) / max(1, len(dims))
            resource_diff = max(1, min(5, round(avg_dim / 20)))
            ma = calc_match_accuracy(
                profile={"expected": {"recommendedDifficulty": expected_diff}},
                resource_difficulty=resource_diff,
            )
            if ma < 1.0 and confidence > 0.65:
                confidence = round(confidence * 0.92, 3)
    except Exception as e:
        log.warning(f"calc_match_accuracy 跳过: {e}")

    return (
        snapshot,
        sorted(weak_kps_set),
        sorted(strong_kps_set),
        knowledge_gaps,
        confidence,
    )


def _calc_confidence(
    *,
    learner: dict,
    theory_score,
    activity_count: int,
    kp_stat_count: int,
    profile_weak: set[str],
    activity_weak: set[str],
) -> float:
    """
    置信度计算公式：
      base    = 0.5（基线，纯瞎猜）
      画像完整 +0.2（education/theoryScore 非空）
      活动数据 +0.15（>=10 条）/ +0.10（>=5）/ +0.05（>=1）
      kp 统计覆盖 +0.10（>=6 个 kp）/ +0.05（>=3）
      画像 vs 活动 弱知识一致性（交集 / 并集） 加权 ±0.05
    最终 clip 到 [0,1]，保留 3 位。
    """
    c = 0.5
    # 画像完整
    if learner.get("education") or theory_score is not None:
        c += 0.1
    if theory_score is not None:
        c += 0.1
    # 活动数据量
    if activity_count >= 10:
        c += 0.15
    elif activity_count >= 5:
        c += 0.10
    elif activity_count >= 1:
        c += 0.05
    # kp 覆盖
    if kp_stat_count >= 6:
        c += 0.10
    elif kp_stat_count >= 3:
        c += 0.05
    # 弱知识一致性
    union = profile_weak | activity_weak
    if union:
        inter = profile_weak & activity_weak
        agree = len(inter) / len(union)
        c += (agree - 0.5) * 0.1
    c = max(0.0, min(1.0, c))
    return round(c, 3)


# -------- 入库 --------

async def _save_diagnosis_record(
    *,
    trace_id: str,
    student_id: str,
    snapshot: dict,
    weak_kps: list[str],
    strong_kps: list[str],
    knowledge_gaps: list[dict],
    confidence: float,
    generated_at: datetime,
) -> str:
    rid = f"dr-{uuid.uuid4().hex[:16]}"
    async with get_session() as session:
        rec = DiagnosisRecord(
            record_id=rid,
            trace_id=trace_id,
            student_id=student_id,
            confidence=confidence,
            weak_kps=weak_kps,
            strong_kps=strong_kps,
            knowledge_gaps=knowledge_gaps,
            input_snapshot=snapshot,
            prompt_version=prompts.VERSION,
            generated_at=generated_at,
        )
        session.add(rec)
    return rid


# -------- 模块级入口：diagnose() --------

async def diagnose(studentId: str) -> dict:
    """
    B-05 学情诊断 Agent 入口（暴露给 D 的协同编排器）。

    :param studentId: 学生 ID
    :return: DiagnosisResult dict
      {
        studentId, weakKPs[], strongKPs[], knowledgeGaps[],
        confidence[0,1], traceId, generatedAt(ISO)
      }
    :raises QualityError: confidence < 0.6 时抛出（由调用方决定是否降级）
    :raises NotFoundError: 学生快照取不到（不存在）
    """
    if not studentId:
        from backend.公共.errors import BizError
        raise BizError("studentId 不能为空", code=400)

    trace_id = f"trace-dia-{studentId}-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    generated_at = datetime.now()

    # 1) agent.start
    await _emit_agent_event(
        "agent.start", step=1,
        content=prompts.START_STEP_CONTENT,
        trace_id=trace_id,
    )

    # 2) 核心诊断
    snapshot, weak_kps, strong_kps, knowledge_gaps, confidence = await _diagnose_core(
        student_id=studentId, trace_id=trace_id,
    )

    # 3) 置信度门槛
    if confidence < 0.6:
        # ⭐ 一票否决：必须抛 QualityError
        raise QualityError(
            message=(
                f"学情诊断置信度 {confidence} 低于阈值 0.6，"
                f"弱知识 {weak_kps}，建议补全学习活动后重试。"
            ),
            data={
                "traceId": trace_id,
                "confidence": confidence,
                "weakKPs": weak_kps,
                "strongKPs": strong_kps,
            },
        )

    # 4) 保存诊断历史
    await _save_diagnosis_record(
        trace_id=trace_id,
        student_id=studentId,
        snapshot=snapshot,
        weak_kps=weak_kps,
        strong_kps=strong_kps,
        knowledge_gaps=knowledge_gaps,
        confidence=confidence,
        generated_at=generated_at,
    )

    # 5) agent.result 推送
    result_summary = prompts.RESULT_SUMMARY_TEMPLATE.format(
        n_weak=len(weak_kps),
        n_strong=len(strong_kps),
        n_gap=len(knowledge_gaps),
        conf=confidence,
    )
    result_payload = {
        "studentId": studentId,
        "weakKPs": weak_kps,
        "strongKPs": strong_kps,
        "knowledgeGaps": knowledge_gaps,
        "confidence": confidence,
        "traceId": trace_id,
        "generatedAt": generated_at.isoformat(),
    }
    await _emit_agent_event(
        "agent.result",
        step=5,
        content=result_summary,
        data=result_payload,
        trace_id=trace_id,
    )

    return result_payload
