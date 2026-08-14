"""
D-03 ⭐：DecisionMaker — 决策融合器。

职责：
  收集学情诊断 Agent（B-05）+ 领域专家 Agent（C-04）+ 审核裁判 Agent（D-06）的结果，
  融合产出最终决策。
"""
from __future__ import annotations

from backend.公共.logger import get_logger
from backend.d_AI集成.orchestrator.event_emitter import EventEmitter

log = get_logger(__name__)


class DecisionMaker:
    """决策融合器。"""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def merge(
        self,
        diagnosis: dict,
        expert_output: dict,
        audit_result: dict,
    ) -> dict:
        """
        融合三个 Agent 的结果，产出最终决策。

        :param diagnosis: B 区学情诊断结果
        :param expert_output: C 区领域专家生成内容
        :param audit_result: D 区审核裁判结果
        :return: 最终决策 dict
        """
        await self.emitter.emit(
            "agent.thinking",
            agent_name="决策融合器",
            content="正在融合三个 Agent 的结果...",
        )

        final_score = round(
            0.2 * diagnosis.get("confidence", 0.8)
            + 0.4 * audit_result.get("score", 0.5)
            + 0.4 * expert_output.get("score", 0.5),
            4,
        )

        final_result = {
            "finalScore": final_score,
            "diagnosis": {
                "strengths": diagnosis.get("strengths", []),
                "weaknesses": diagnosis.get("weaknesses", []),
                "confidence": diagnosis.get("confidence", 0),
            },
            "expertContent": expert_output.get("content", ""),
            "auditVerdict": audit_result.get("result", "fail"),
            "auditScore": audit_result.get("score", 0),
            "issues": audit_result.get("issues", []),
            "debateRounds": audit_result.get("debate_rounds", 1),
            "recommendation": self._generate_recommendation(final_score, audit_result),
        }

        await self.emitter.emit(
            "agent.result",
            agent_name="决策融合器",
            content=f"融合完成，最终评分={final_score:.2f}",
            data=final_result,
        )

        return final_result

    def _generate_recommendation(self, score: float, audit_result: dict) -> str:
        """根据评分生成最终建议。"""
        if score >= 0.85:
            return "内容质量优秀，可直接推送给学生。"
        elif score >= 0.70:
            return "内容基本可用，建议人工审核后推送给学生。"
        else:
            return "内容质量不达标，建议重新生成或人工介入。"