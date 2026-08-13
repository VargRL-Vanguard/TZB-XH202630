"""C-05 渲染器单测（3 个 × 至少 1 份样本）。"""
from __future__ import annotations

import pytest

from tests.conftest import render


SAMPLE = {
    "customized_resource": {
        "resource_id": "res-1",
        "student_id": "s001",
        "type": "customized_resource",
        "title": "讲解样例",
        "structured_content": {
            "title": "讲解样例",
            "sections": [
                {"kp_id": "kp_a", "heading": "核心概念", "body": "这是概念。\n\n第二段。"},
                {"kp_id": "kp_a", "heading": "示例", "body": "示例代码：\n```\nprint(1)\n```"},
            ],
        },
        "kp_coverage": ["kp_a"],
        "cited_chunks": ["c1", "c2"],
        "difficulty": 3,
        "version": 1,
    },
    "practice_guide": {
        "resource_id": "res-2",
        "student_id": "s001",
        "type": "practice_guide",
        "title": "实操指南样例",
        "structured_content": {
            "title": "实操指南样例",
            "steps": [
                {"order": 1, "title": "前置", "content": "环境准备", "estimated_min": 5},
                {"order": 2, "title": "操作", "content": "按步骤执行", "estimated_min": 20},
                {"order": 3, "title": "验收", "content": "检查输出", "estimated_min": 5},
            ],
            "tools": ["Python 3.10+"],
            "troubleshooting": [{"problem": "报错 X", "solution": "重装依赖"}],
        },
        "difficulty": 2,
        "version": 1,
    },
    "tiered_quiz": {
        "resource_id": "res-3",
        "student_id": "s001",
        "type": "tiered_quiz",
        "title": "分阶题样例",
        "structured_content": {
            "title": "分阶题样例",
            "questions": [
                {"question": "Q1", "options": ["A. a", "B. b", "C. c", "D. d"], "answer": "A", "explanation": "因为 A 正确", "difficulty": 1, "kp_id": "kp_a"},
                {"question": "Q2", "options": ["A. a", "B. b", "C. c", "D. d"], "answer": "B", "explanation": "B 对", "difficulty": 3, "kp_id": "kp_a"},
            ],
        },
        "difficulty": 3,
        "version": 1,
    },
}


def test_render_customized():
    r = render(SAMPLE["customized_resource"])
    assert "html" in r and "markdown" in r and "structuredData" in r
    assert "<style>" in r["html"]
    assert "讲解样例" in r["html"]
    assert "核心概念" in r["html"]
    assert r["structuredData"]["type"] == "customized_resource"
    assert len(r["structuredData"]["toc"]) == 2


def test_render_practice_guide():
    r = render(SAMPLE["practice_guide"])
    assert "实操指南样例" in r["html"]
    assert "前置" in r["html"] and "操作" in r["html"] and "验收" in r["html"]
    assert "Python 3.10+" in r["html"]
    assert r["structuredData"]["toc"][0]["id"] == "step-1"


def test_render_tiered_quiz():
    r = render(SAMPLE["tiered_quiz"])
    assert "Q1" in r["html"] and "Q2" in r["html"]
    assert r["structuredData"]["toc"][0]["id"] == "q-0"


def test_render_invalid_type_raises():
    with pytest.raises(ValueError):
        render({"type": "bogus", "structured_content": {}})


def test_render_inlines_css_for_mobile():
    r = render(SAMPLE["customized_resource"])
    assert "@media" in r["html"]
