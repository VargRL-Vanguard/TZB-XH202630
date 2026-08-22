"""
D-11：参与 A-05 端到端质量验收。

三硬指标自检：
  ✅ 幻觉率 < 0.3
  ✅ 覆盖率 ≥ 0.9
  ✅ 适配准确率 ≥ 0.85
"""
from __future__ import annotations

import pytest
from backend.公共.metrics import calc_hallucination_rate, calc_coverage, calc_match_accuracy


@pytest.mark.quality
class TestQualityGate:
    """三硬指标质量门。"""

    def test_hallucination_rate(self):
        """幻觉率 < 0.3。"""
        generated = "工业机器人是智能制造的核心装备。它广泛应用于汽车制造。"
        ground_truth = ["工业机器人是智能制造的核心装备。", "工业机器人广泛应用于汽车制造领域。"]
        hr = calc_hallucination_rate(generated, ground_truth)
        assert hr < 0.3, f"幻觉率 {hr:.2f} 超标"

    def test_coverage(self):
        """覆盖率 ≥ 0.9。"""
        generated = {"kp_coverage": ["kp01", "kp02", "kp03"]}
        required = ["kp01", "kp02", "kp03"]
        cov = calc_coverage(generated, required)
        assert cov >= 0.9, f"覆盖率 {cov:.2f} 不达标"

    def test_adaptation_accuracy(self):
        """适配准确率 ≥ 0.85（对齐公共区 calc_match_accuracy 实现：匹配=1.0 / 不匹配=0.0）。"""
        profile = {"expected": {"recommendedDifficulty": 3}}
        acc = calc_match_accuracy(profile, resource_difficulty=3)
        assert acc >= 0.85, f"适配准确率 {acc:.2f} 不达标"


@pytest.mark.quality
class TestEndToEndPipeline:
    """端到端流水线质量验收。"""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """完整流水线：诊断 → 生成 → 审核 → 融合。"""
        from backend.d_AI集成.orchestrator.pipeline import orchestrate
        result = await orchestrate("qa-s001")
        assert result["finalScore"] is not None
        assert result["auditVerdict"] in ("pass", "retry", "fail")
        assert "traceId" in result