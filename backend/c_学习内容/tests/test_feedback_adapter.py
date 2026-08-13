"""C-06 动态迭代机制单测。"""
from __future__ import annotations

import pytest

from tests.conftest import isolated_db
from c_pkg.learning_path.feedback_adapter import handle_feedback


def test_insufficient_samples_no_trigger():
    with isolated_db():
        r1 = handle_feedback("s001", "kp_x", correct=False)
        assert r1["action"] == "none"
        assert r1["triggerReason"] == "insufficient_samples"
        assert "resourceId" not in r1


def test_low_accuracy_triggers_downgrade():
    with isolated_db():
        for _ in range(3):
            handle_feedback("s002", "kp_y", correct=False)
        r = handle_feedback("s002", "kp_y", correct=False)
        assert r["samples"] >= 3
        assert r["action"] == "downgrade"
        assert r["triggerReason"] == "low_accuracy"
        assert r.get("resourceId")


def test_high_accuracy_triggers_upgrade():
    with isolated_db():
        for _ in range(3):
            handle_feedback("s003", "kp_z", correct=True)
        r = handle_feedback("s003", "kp_z", correct=True)
        assert r["samples"] >= 3
        assert r["action"] == "upgrade"
        assert r["triggerReason"] == "high_accuracy"
        assert r.get("resourceId")
        assert r.get("resourceType") == "tiered_quiz"


def test_stable_accuracy_no_trigger():
    with isolated_db():
        # 4 错 4 对 = 0.5，< 0.6 触发降维（4/8=0.5 实际降维）
        # 6 错 4 对 = 0.4 也会降维
        # 要"稳定"，需要准确率 ∈ [0.6, 0.9]
        # 用 4 对 2 错 = 0.667（6 条样本）
        for _ in range(2):
            handle_feedback("s004", "kp_w", correct=False)
        for _ in range(4):
            handle_feedback("s004", "kp_w", correct=True)
        # 第 6 次：2 错 4 对 = 0.667（稳定区，不触发任何动作）
        # 截断到第 6 次 - 此时样本数=6, accuracy=0.667
        # 改为：直接在 stable 区间内观察第 6 次的返回值
        # 用 get_shadow_state 查看，但 handle_feedback 返回的是当前 state
        # 实际上：要保证第 6 次之后是 stable，第 7 次不能是 wrong
        # 简化：先 4 对 2 错（accuracy=0.667），再 1 对（accuracy=5/7=0.714，stable）
        r = handle_feedback("s004", "kp_w", correct=True)  # 第 7 次：2 错 5 对 = 0.714 stable
        assert r["samples"] == 7
        assert r["action"] == "none"
        assert r["triggerReason"] == "stable"


def test_missing_args_raises():
    with isolated_db():
        with pytest.raises(ValueError):
            handle_feedback("", "kp_x")
        with pytest.raises(ValueError):
            handle_feedback("s005", "")


def test_logged_in_db():
    with isolated_db():
        handle_feedback("s006", "kp_v", correct=True)
        from c_pkg.db import get_session
        from c_pkg.models import InteractionLog
        with get_session() as s:
            rows = s.query(InteractionLog).all()
            assert len(rows) >= 1
            assert rows[0].student_id == "s006"
            assert rows[0].kp_id == "kp_v"
