"""C-04 领域专家 Agent 单测（3 种形态 × happy path）。"""
from __future__ import annotations

import pytest

# conftest 已经在 import 时把 c_pkg 加载好了
from tests.conftest import (
    _generate_resource as generate_resource,
    DiagnosisResult,
    _VALID_TYPES as VALID_TYPES,
    isolated_db,
)
from c_pkg.agents.expert_agent import ResourceSchema


def _diag(student_id="s001", weak=None, difficulty=3):
    return DiagnosisResult(
        studentId=student_id,
        weakKPs=weak or ["kp_basics", "kp_loops"],
        knowledgeGaps=[],
        recommendedDifficulty=difficulty,
    )


def test_invalid_resource_type_raises():
    with isolated_db():
        with pytest.raises(ValueError):
            generate_resource("s001", _diag(), "bogus_type")  # type: ignore


def test_customized_resource_happy():
    with isolated_db():
        r = generate_resource("s001", _diag(), "customized_resource")
        assert isinstance(r, ResourceSchema)
        assert r.type == "customized_resource"
        assert r.resource_id.startswith("res-")
        assert r.kp_coverage == ["kp_basics", "kp_loops"]
        assert r.difficulty == 3
        assert r.content.get("title")
        assert r.content.get("sections")


def test_practice_guide_happy():
    with isolated_db():
        r = generate_resource("s001", _diag(), "practice_guide")
        assert r.type == "practice_guide"
        steps = r.content.get("steps", [])
        assert len(steps) >= 1
        assert r.content.get("tools") is not None


def test_tiered_quiz_happy():
    with isolated_db():
        r = generate_resource("s001", _diag(), "tiered_quiz")
        assert r.type == "tiered_quiz"
        qs = r.content.get("questions", [])
        assert len(qs) >= 1
        for q in qs:
            assert "question" in q and "options" in q and "answer" in q


def test_trigger_reason_propagated():
    with isolated_db():
        r = generate_resource("s001", _diag(), "tiered_quiz", trigger_reason="high_accuracy")
        assert r.trigger_reason == "high_accuracy"


def test_metrics_present():
    with isolated_db():
        r = generate_resource("s001", _diag(), "customized_resource")
        m = r.metrics
        assert "coverage" in m and "hallucination" in m and "matchAccuracy" in m
        assert 0.0 <= m["coverage"] <= 1.0
        assert 0.0 <= m["hallucination"] <= 1.0


def test_dict_diagnosis_accepted():
    with isolated_db():
        r = generate_resource("s001", {
            "studentId": "s001",
            "weakKPs": ["kp_x"],
            "recommendedDifficulty": 4,
        }, "customized_resource")
        assert r.difficulty == 4


def test_valid_types_constant():
    assert set(VALID_TYPES) == {"customized_resource", "practice_guide", "tiered_quiz"}
