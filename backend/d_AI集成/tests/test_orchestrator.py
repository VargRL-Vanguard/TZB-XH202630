"""
D-03 / D-10：多智能体协同编排器 单测 + 联调测试。
"""
from __future__ import annotations

import pytest
from backend.d_AI集成.orchestrator.event_emitter import EventEmitter
from backend.d_AI集成.orchestrator.decision_maker import DecisionMaker


class TestEventEmitter:
    """事件发射器测试。"""

    def test_emitter_init(self):
        emitter = EventEmitter("trace-test-001")
        assert emitter.trace_id == "trace-test-001"
        assert emitter.step == 0

    @pytest.mark.asyncio
    async def test_emit_no_ws(self):
        """无 WS 连接时 emit 不报错（降级）。"""
        emitter = EventEmitter("trace-test-002")
        await emitter.emit(
            "agent.thinking",
            agent_name="测试Agent",
            content="测试事件",
        )
        assert emitter.step == 1


class TestDecisionMaker:
    """决策融合器测试。"""

    @pytest.mark.asyncio
    async def test_merge_basic(self):
        emitter = EventEmitter("trace-test-dm")
        dm = DecisionMaker(emitter)
        result = await dm.merge(
            diagnosis={"strengths": ["s1"], "weaknesses": ["w1"], "confidence": 0.9},
            expert_output={"content": "测试内容", "score": 0.85},
            audit_result={"score": 0.9, "result": "pass", "issues": [], "debate_rounds": 1},
        )
        assert "finalScore" in result
        assert result["auditVerdict"] == "pass"
        assert result["finalScore"] >= 0.8

    @pytest.mark.asyncio
    async def test_merge_fail(self):
        emitter = EventEmitter("trace-test-dm-fail")
        dm = DecisionMaker(emitter)
        result = await dm.merge(
            diagnosis={"strengths": [], "weaknesses": ["w1"], "confidence": 0.3},
            expert_output={"content": "低质量", "score": 0.3},
            audit_result={"score": 0.2, "result": "fail", "issues": ["幻觉高"], "debate_rounds": 3},
        )
        assert result["auditVerdict"] == "fail"
        assert result["finalScore"] < 0.5