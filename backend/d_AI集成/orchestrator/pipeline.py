"""
D-03 ⭐ 夺奖专项：OrchestrationPipeline — 多智能体协同编排流水线。

模块级入口：
    orchestrate(studentId) -> FinalDecision dict

流程：
  B 区学情诊断 Agent  →  C 区领域专家 Agent  →  D 区审核裁判 Agent 辩论  →  决策融合
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

from backend.公共.logger import get_logger
from backend.公共.errors import BizError
from backend.d_AI集成.orchestrator.event_emitter import EventEmitter
from backend.d_AI集成.orchestrator.debate_engine import DebateEngine
from backend.d_AI集成.orchestrator.decision_maker import DecisionMaker

log = get_logger(__name__)


class OrchestrationPipeline:
    """多智能体协同编排流水线。"""

    def __init__(self):
        self.emitter: Optional[EventEmitter] = None
        self.debate_engine: Optional[DebateEngine] = None
        self.decision_maker: Optional[DecisionMaker] = None

    async def run(self, student_id: str) -> dict:
        """
        执行完整的多智能体协同流水线。

        :param student_id: 学生ID
        :return: 最终决策 dict
        """
        trace_id = f"trace-orch-{student_id}-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        self.emitter = EventEmitter(trace_id)
        self.debate_engine = DebateEngine(self.emitter)
        self.decision_maker = DecisionMaker(self.emitter)

        # ---- Phase 1: 学情诊断 ----
        await self.emitter.emit(
            "agent.start",
            agent_name="编排流水线",
            content=f"多智能体协同编排启动，traceId={trace_id}",
            data={"phase": "start", "studentId": student_id},
        )

        diagnosis = await self._phase_diagnosis(student_id)

        await self.emitter.emit(
            "agent.result",
            agent_name="学情诊断Agent",
            content="学情诊断完成",
            data=diagnosis,
        )

        # ---- Phase 2: 领域专家生成 ----
        expert_output = await self._phase_expert(student_id, diagnosis)

        await self.emitter.emit(
            "agent.result",
            agent_name="领域专家Agent",
            content="领域专家生成完成",
            data=expert_output,
        )

        # ---- Phase 3: 审核裁判辩论 ----
        content = expert_output.get("content", "")
        kp_ids = expert_output.get("kp_ids", diagnosis.get("kp_ids", []))
        if isinstance(content, dict):
            import json
            content = json.dumps(content, ensure_ascii=False)

        audit_result = await self.debate_engine.debate(
            student_id=student_id,
            content=content,
            kp_ids=kp_ids,
        )

        # ---- Phase 4: 决策融合 ----
        final_decision = await self.decision_maker.merge(
            diagnosis=diagnosis,
            expert_output=expert_output,
            audit_result=audit_result,
        )

        # ---- Phase 5: 收尾 ----
        await self.emitter.emit(
            "agent.final",
            agent_name="编排流水线",
            content=f"多智能体协同编排完成，最终评分={final_decision['finalScore']:.2f}",
            data={
                "traceId": trace_id,
                "studentId": student_id,
                "finalScore": final_decision["finalScore"],
                "verdict": final_decision["auditVerdict"],
            },
        )

        final_decision["traceId"] = trace_id
        return final_decision

    async def _phase_diagnosis(self, student_id: str) -> dict:
        """Phase 1：调 B 区学情诊断 Agent。"""
        try:
            from backend.b_学情数据.analytics import diagnose
            return await diagnose(student_id)
        except ImportError:
            log.warning("B 区未就绪，使用空诊断结果")
            return {"strengths": [], "weaknesses": [], "confidence": 0.5, "kp_ids": []}
        except Exception as e:
            log.error(f"B 区诊断失败: {e}")
            return {"strengths": [], "weaknesses": [], "confidence": 0.5, "kp_ids": [], "error": str(e)}

    async def _phase_expert(self, student_id: str, diagnosis: dict) -> dict:
        """Phase 2：调 C 区领域专家 Agent。"""
        try:
            from backend.c_学习内容.agents.expert_agent import ExpertAgent
            agent = ExpertAgent()
            return await agent.generate_resource(student_id, diagnosis)
        except ImportError:
            log.warning("C 区未就绪，使用空生成结果")
            return {"content": "（C 区未就绪，占位内容）", "kp_ids": diagnosis.get("kp_ids", []), "score": 0.5}
        except Exception as e:
            log.error(f"C 区专家生成失败: {e}")
            return {"content": f"生成失败: {e}", "kp_ids": diagnosis.get("kp_ids", []), "score": 0.0, "error": str(e)}


async def orchestrate(studentId: str) -> dict:
    """
    D-03 模块级入口（暴露给 A / B / C 区调用）。

    :param studentId: 学生ID
    :return: 最终决策 dict
    """
    if not studentId:
        raise BizError("studentId 不能为空", code=400)
    pipeline = OrchestrationPipeline()
    return await pipeline.run(studentId)