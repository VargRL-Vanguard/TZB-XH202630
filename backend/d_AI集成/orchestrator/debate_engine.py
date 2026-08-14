"""
D-03 ⭐：DebateEngine — 辩论引擎。

职责：
  领域专家 Agent（C）生成内容 → 审核裁判 Agent（D-06）审核 →
  如果不通过，通知 C 优化重试 → 再次审核 → 最多 3 轮辩论。
"""
from __future__ import annotations

from typing import Optional

from backend.公共.logger import get_logger
from backend.d_AI集成.orchestrator.event_emitter import EventEmitter

log = get_logger(__name__)

MAX_DEBATE_ROUNDS = 3


class DebateEngine:
    """辩论引擎。"""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter
        self.round = 0

    async def debate(
        self,
        student_id: str,
        content: str,
        kp_ids: list[str],
        *,
        regenerate_fn=None,
    ) -> dict:
        """
        执行辩论流程：专家生成 → 裁判审核 → 不通过则重试。

        :param student_id: 学生ID
        :param content: 初始生成内容
        :param kp_ids: 知识点列表
        :param regenerate_fn: async fn(content, issues) -> new_content 优化重生成函数
        :return: 最终审核结果
        """
        from backend.d_AI集成.audit import audit

        current_content = content
        feedback_notes: list[str] = []

        for round_num in range(1, MAX_DEBATE_ROUNDS + 1):
            self.round = round_num

            await self.emitter.emit(
                "agent.debate",
                agent_name="辩论引擎",
                content=f"第 {round_num}/{MAX_DEBATE_ROUNDS} 轮辩论开始",
                data={"round": round_num, "maxRounds": MAX_DEBATE_ROUNDS},
            )

            audit_result = await audit(
                studentId=student_id,
                content=current_content,
                kp_ids=kp_ids,
            )

            if audit_result["result"] == "pass":
                await self.emitter.emit(
                    "agent.debate",
                    agent_name="辩论引擎",
                    content=f"第 {round_num} 轮辩论通过，审核裁判 Agent 判定 pass",
                    data={"round": round_num, "verdict": "pass"},
                )
                audit_result["debate_rounds"] = round_num
                audit_result["feedback_notes"] = feedback_notes
                return audit_result

            if audit_result["result"] == "fail" and round_num == MAX_DEBATE_ROUNDS:
                await self.emitter.emit(
                    "agent.debate",
                    agent_name="辩论引擎",
                    content=f"辩论已达最大轮次 {MAX_DEBATE_ROUNDS}，最终判定 fail",
                    data={"round": round_num, "verdict": "fail"},
                )
                audit_result["debate_rounds"] = round_num
                audit_result["feedback_notes"] = feedback_notes
                return audit_result

            feedback_notes.append(
                f"第{round_num}轮反馈: score={audit_result['score']:.2f}, issues={len(audit_result['issues'])}条"
            )

            if regenerate_fn is not None:
                try:
                    current_content = await regenerate_fn(current_content, audit_result["issues"])
                    await self.emitter.emit(
                        "agent.thinking",
                        agent_name="领域专家Agent",
                        content=f"收到审核反馈，正在优化内容（第{round_num}轮）",
                        data={"round": round_num},
                    )
                except Exception as e:
                    log.error(f"重生成失败: {e}")
                    audit_result["debate_rounds"] = round_num
                    audit_result["feedback_notes"] = feedback_notes
                    return audit_result

        return audit_result