"""C-01 学习路径 4 个接口单测。"""
from __future__ import annotations

from tests.conftest import isolated_db
from c_pkg.learning_path import (
    get_modules, get_overview, get_tasks, get_timeline, save_ai_generated_path,
)


def test_overview_empty():
    with isolated_db():
        r = get_overview("s001")
        assert r["source"] == "fallback"
        assert r["progress"] == 0


def test_overview_with_data():
    with isolated_db():
        from c_pkg.db import get_session
        from c_pkg.models import LearningPath
        with get_session() as s:
            s.add(LearningPath(student_id="s002", target="掌握 Python", progress=35, estimated_days=12))
        r = get_overview("s002")
        assert r["target"] == "掌握 Python"
        assert r["progress"] == 35
        assert r["estimatedDays"] == 12


def test_timeline_status_filter():
    with isolated_db():
        from c_pkg.db import get_session
        from c_pkg.models import LearningPath, LearningModule
        with get_session() as s:
            p = LearningPath(student_id="s003", target="x", progress=0, estimated_days=1)
            s.add(p)
            s.flush()
            s.add(LearningModule(path_id=p.path_id, name="A", status="completed", order_index=0))
            s.add(LearningModule(path_id=p.path_id, name="B", status="current", order_index=1))
            s.add(LearningModule(path_id=p.path_id, name="C", status="pending", order_index=2))
        completed = get_timeline("s003", "completed")
        current = get_timeline("s003", "current")
        pending = get_timeline("s003", "pending")
        all_ = get_timeline("s003", "all")
        assert len(completed) == 1 and completed[0]["title"] == "A"
        assert len(current) == 1 and current[0]["title"] == "B"
        assert len(pending) == 1 and pending[0]["title"] == "C"
        assert len(all_) == 3


def test_timeline_invalid_status_returns_empty():
    with isolated_db():
        r = get_timeline("s404", "garbage")
        assert r == []


def test_modules_empty():
    with isolated_db():
        assert get_modules("ghost") == []


def test_tasks_empty():
    with isolated_db():
        assert get_tasks("ghost") == []


def test_save_ai_generated_path_persists():
    with isolated_db():
        content = '{"target":"掌握Python","modules":[{"name":"基础","status":"current","duration":"3天"}]}'
        out = save_ai_generated_path("s100", content)
        assert out["modules"] == 1
        r = get_overview("s100")
        assert r["target"] == "掌握Python"
        assert r["source"] == "ai"
        tl = get_timeline("s100", "all")
        assert len(tl) == 1
        assert tl[0]["title"] == "基础"
        assert tl[0]["status"] == "current"


def test_save_ai_generated_path_version_increments():
    with isolated_db():
        save_ai_generated_path("s101", '{"target":"v1","modules":[]}')
        save_ai_generated_path("s101", '{"target":"v2","modules":[]}')
        r = get_overview("s101")
        assert r["target"] == "v2"


def test_modules_with_data():
    with isolated_db():
        from c_pkg.db import get_session
        from c_pkg.models import LearningPath, LearningModule
        with get_session() as s:
            p = LearningPath(student_id="s200", target="x", progress=0)
            s.add(p)
            s.flush()
            s.add(LearningModule(path_id=p.path_id, name="基础语法", desc="变量与类型", progress=85, order_index=0))
        r = get_modules("s200")
        assert r[0]["name"] == "基础语法"
        assert r[0]["progress"] == 85
