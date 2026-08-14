"""
D-10：联调 — AI集成 全部接口端到端测试。
"""
from __future__ import annotations

import pytest


@pytest.mark.e2e
class TestE2EChat:
    """ChatAI 端到端测试。"""

    @pytest.mark.asyncio
    async def test_send_message(self):
        from backend.d_AI集成.chat.send import send_message
        result = await send_message(
            student_id="e2e-s001",
            question="什么是工业机器人？",
        )
        assert "convId" in result
        assert "reply" in result

    @pytest.mark.asyncio
    async def test_get_history(self):
        from backend.d_AI集成.chat.history import get_history
        result = await get_history(student_id="e2e-s001")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_clear_history(self):
        from backend.d_AI集成.chat.clear import clear_history
        result = await clear_history(student_id="e2e-s001")
        assert "deleted" in result


@pytest.mark.e2e
class TestE2EPath:
    """PathAI 端到端测试。"""

    @pytest.mark.asyncio
    async def test_get_path_result(self):
        from backend.d_AI集成.path.ai_result import get_path_result
        result = await get_path_result(
            student_id="e2e-s001",
            diagnosis={"strengths": ["数学"], "weaknesses": ["编程"]},
        )
        assert "resultId" in result
        assert "path" in result


@pytest.mark.e2e
class TestE2ESuggest:
    """SuggestAI 端到端测试。"""

    @pytest.mark.asyncio
    async def test_get_suggest_result(self):
        from backend.d_AI集成.suggest.ai_result import get_suggest_result
        result = await get_suggest_result(
            student_id="e2e-s001",
            diagnosis={"strengths": ["理论"], "weaknesses": ["实操"]},
        )
        assert "resultId" in result
        assert "suggestions" in result


@pytest.mark.e2e
class TestE2EOrchestrator:
    """协同编排器端到端测试。"""

    @pytest.mark.asyncio
    async def test_orchestrate(self):
        from backend.d_AI集成.orchestrator.pipeline import orchestrate
        result = await orchestrate("e2e-s001")
        assert "finalScore" in result
        assert "traceId" in result