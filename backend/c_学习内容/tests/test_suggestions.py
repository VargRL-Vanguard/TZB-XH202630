"""C-02 学习建议 + C-03 写回方法 单测。"""
from __future__ import annotations

import json

from tests.conftest import isolated_db
from c_pkg.suggestions import (
    list_suggestions,
    mark_suggestion_read,
    save_ai_generated_suggestions,
)


def test_list_suggestions_empty():
    with isolated_db():
        assert list_suggestions("ghost") == []


def test_save_and_list_suggestions():
    with isolated_db():
        content = json.dumps({
            "suggestions": [
                {"title": "加强练习", "content": "...", "category": "practice", "priority": "high"},
                {"title": "方法论", "content": "...", "category": "method", "priority": "medium"},
            ]
        }, ensure_ascii=False)
        out = save_ai_generated_suggestions("s300", content)
        assert out["saved"] == 2
        all_ = list_suggestions("s300", "all")
        assert len(all_) == 2
        practice = list_suggestions("s300", "practice")
        assert len(practice) == 1
        assert practice[0]["category"] == "practice"
        method = list_suggestions("s300", "method")
        assert len(method) == 1
        assert method[0]["categoryLabel"] == "方法建议"


def test_category_filter_5_types():
    with isolated_db():
        save_ai_generated_suggestions("s301", json.dumps({"suggestions": [
            {"title": "a", "category": "method", "priority": "high"},
            {"title": "b", "category": "resource", "priority": "low"},
            {"title": "c", "category": "review", "priority": "medium"},
            {"title": "d", "category": "practice", "priority": "high"},
        ]}))
        for cat in ("method", "resource", "review", "practice"):
            assert len(list_suggestions("s301", cat)) == 1
        assert len(list_suggestions("s301", "all")) == 4


def test_mark_read():
    with isolated_db():
        save_ai_generated_suggestions("s302", json.dumps({"suggestions": [
            {"title": "x", "category": "practice", "priority": "high"}
        ]}))
        items = list_suggestions("s302", "all")
        sid = items[0]["id"]
        assert mark_suggestion_read("s302", sid) is True
        assert mark_suggestion_read("s302", sid) is True
        assert mark_suggestion_read("ghost", sid) is False
        assert mark_suggestion_read("s302", "nope") is False


def test_save_invalid_category_falls_back():
    with isolated_db():
        save_ai_generated_suggestions("s303", json.dumps({"suggestions": [
            {"title": "x", "category": "garbage", "priority": "garbage"}
        ]}))
        items = list_suggestions("s303", "practice")
        assert len(items) == 1
        assert items[0]["category"] == "practice"
        assert items[0]["priority"] == "medium"
