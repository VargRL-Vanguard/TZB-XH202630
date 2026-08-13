"""C-07 E2E 质量验收脚本 — 3 种形态资源 × 3 项硬指标。

跑法（与 A-05 quality_check 配合）：
    cd backend
    pytest c_学习内容/tests/test_e2e_quality.py -v
"""
from __future__ import annotations

import pytest

# conftest 已经在 import 时把 c_pkg 加载好了
from tests.conftest import _generate_resource as generate_resource, DiagnosisResult, render, isolated_db


THREE_PROFILES = [
    {"name": "基础薄弱", "studentId": "demo-weak-001", "weakKPs": ["kp_basics", "kp_loops"], "difficulty": 1},
    {"name": "中等进阶", "studentId": "demo-mid-002",  "weakKPs": ["kp_funcs", "kp_oop"],   "difficulty": 3},
    {"name": "高阶突破", "studentId": "demo-strong-003", "weakKPs": ["kp_async", "kp_design"], "difficulty": 5},
]


@pytest.mark.parametrize("rtype", ["customized_resource", "practice_guide", "tiered_quiz"])
@pytest.mark.parametrize("profile", THREE_PROFILES, ids=[p["name"] for p in THREE_PROFILES])
def test_3_forms_x_3_profiles(rtype, profile):
    """3 种形态资源 × 3 种难度档位 = 9 条用例，必须全部能生成 + 渲染。"""
    with isolated_db():
        diag = DiagnosisResult(
            studentId=profile["studentId"],
            weakKPs=profile["weakKPs"],
            knowledgeGaps=profile["weakKPs"],
            recommendedDifficulty=profile["difficulty"],
        )
        r = generate_resource(profile["studentId"], diag, rtype)
        assert r.type == rtype
        assert r.resource_id
        # kp_coverage 必须非空且都在 weakKPs 里
        assert r.kp_coverage
        assert all(kp in profile["weakKPs"] for kp in r.kp_coverage)
        # 渲染器必须能渲染
        out = render({
            "type": r.type,
            "structured_content": r.content,
            "title": r.title,
            "difficulty": r.difficulty,
            "version": 1,
            "kp_coverage": r.kp_coverage,
            "cited_chunks": r.cited_chunks,
        })
        assert "<style>" in out["html"], "渲染输出必须含内联 CSS"
        assert out["structuredData"]["type"] == rtype
        # 指标必须存在
        assert r.metrics.get("coverage", 0) > 0
        assert "hallucination" in r.metrics


def test_hard_metrics_three_forms():
    """3 种形态资源 × 3 项硬指标必须都达标（mock 兜底下也应达标）。"""
    with isolated_db():
        results = []
        for rtype in ("customized_resource", "practice_guide", "tiered_quiz"):
            r = generate_resource(
                "metric-test",
                DiagnosisResult(
                    studentId="metric-test",
                    weakKPs=["kp_a", "kp_b", "kp_c"],
                    knowledgeGaps=[],
                    recommendedDifficulty=3,
                ),
                rtype,
            )
            results.append((rtype, r.metrics))

        for rtype, m in results:
            coverage = m.get("coverage", 0)
            halluc = m.get("hallucination", 1)
            match_acc = m.get("matchAccuracy", m.get("match_accuracy", 0))
            assert coverage >= 0.85, f"{rtype} coverage={coverage} < 0.85"
            assert halluc <= 0.10, f"{rtype} hallucination={halluc} > 0.10"
            assert match_acc > 0, f"{rtype} match_accuracy={match_acc} == 0"


def test_cited_chunks_not_empty():
    """生成资源必须引用至少 1 个 chunk（防幻觉）。"""
    with isolated_db():
        r = generate_resource(
            "cited-test",
            DiagnosisResult(studentId="cited-test", weakKPs=["kp_x"], recommendedDifficulty=2),
            "customized_resource",
        )
        assert r.cited_chunks
        assert len(r.cited_chunks) >= 1


def test_invalid_resource_type_raises():
    """非法 type 必须被 reject。"""
    with pytest.raises(ValueError):
        generate_resource(
            "x", DiagnosisResult(studentId="x", weakKPs=["kp_a"], recommendedDifficulty=1),
            "bad_type",
        )
