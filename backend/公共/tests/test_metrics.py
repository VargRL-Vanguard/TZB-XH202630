"""
单测：metrics.py（3 项硬指标计算器）
**每个函数 ≥ 3 用例**（含边界 0、1、空输入），任务清单硬要求。
"""
import pytest

from backend.公共.metrics import (
    calc_hallucination_rate,
    calc_match_accuracy,
    calc_coverage,
)


# ========== 1. calc_hallucination_rate ==========

def test_hallucination_rate_zero():
    """完全引用切片 → 幻觉率 = 0"""
    truth = ["工业机器人是自动执行工作的机器装置。"]
    generated = "工业机器人是自动执行工作的机器装置。"
    rate = calc_hallucination_rate(generated, truth)
    assert rate < 0.05


def test_hallucination_rate_full():
    """完全不相关 → 幻觉率接近 1"""
    truth = ["工业机器人是自动执行工作的机器装置。"]
    generated = "今天天气真好我们去公园散步吧。"
    rate = calc_hallucination_rate(generated, truth)
    assert rate > 0.90


def test_hallucination_rate_empty_generated():
    """空 generated → 0"""
    rate = calc_hallucination_rate("", ["some truth"])
    assert rate == 0.0


def test_hallucination_rate_empty_truth():
    """空 truth → 1（无参考 = 全幻觉）"""
    rate = calc_hallucination_rate("some content", [])
    assert rate == 1.0


def test_hallucination_rate_partial():
    """部分引用 → 介于 0-1 之间"""
    truth = ["工业机器人是自动执行工作的机器装置。它由控制器驱动。"]
    generated = (
        "工业机器人是自动执行工作的机器装置。"
        "它由控制器驱动。"
        "今天我们学习它的应用场景。"
    )
    rate = calc_hallucination_rate(generated, truth)
    assert 0.0 <= rate <= 1.0


def test_hallucination_rate_returns_float():
    """返回 float"""
    rate = calc_hallucination_rate("test", ["test"])
    assert isinstance(rate, float)


# ========== 2. calc_match_accuracy ==========

def test_match_accuracy_match():
    """难度相等 → 1.0"""
    profile = {"expected": {"recommendedDifficulty": 3}}
    accuracy = calc_match_accuracy(profile, resource_difficulty=3)
    assert accuracy == 1.0


def test_match_accuracy_mismatch():
    """难度不等 → 0.0"""
    profile = {"expected": {"recommendedDifficulty": 3}}
    accuracy = calc_match_accuracy(profile, resource_difficulty=5)
    assert accuracy == 0.0


def test_match_accuracy_missing_expected():
    """缺 expected → 0.0"""
    accuracy = calc_match_accuracy({}, resource_difficulty=3)
    assert accuracy == 0.0


def test_match_accuracy_invalid_profile():
    """profile 不是 dict → 0.0"""
    accuracy = calc_match_accuracy(None, resource_difficulty=3)
    assert accuracy == 0.0


def test_match_accuracy_string_to_int():
    """expected 是字符串 "3" → 也能匹配"""
    profile = {"expected": {"recommendedDifficulty": "3"}}
    accuracy = calc_match_accuracy(profile, resource_difficulty=3)
    assert accuracy == 1.0


def test_match_accuracy_returns_float():
    """返回 float"""
    accuracy = calc_match_accuracy({"expected": {"recommendedDifficulty": 3}}, 3)
    assert isinstance(accuracy, float)


# ========== 3. calc_coverage ==========

def test_coverage_full():
    """全部覆盖 → 1.0"""
    generated = {"kp_coverage": ["kp_001", "kp_002", "kp_003"]}
    required = ["kp_001", "kp_002", "kp_003"]
    cov = calc_coverage(generated, required)
    assert cov == 1.0


def test_coverage_partial():
    """部分覆盖 → 0.66"""
    generated = {"kp_coverage": ["kp_001", "kp_002"]}
    required = ["kp_001", "kp_002", "kp_003"]
    cov = calc_coverage(generated, required)
    assert abs(cov - 2 / 3) < 0.01


def test_coverage_empty_required():
    """空 required → 1.0（视为全覆盖）"""
    cov = calc_coverage({"kp_coverage": []}, [])
    assert cov == 1.0


def test_coverage_empty_generated():
    """空 generated → 0.0"""
    cov = calc_coverage({"kp_coverage": []}, ["kp_001"])
    assert cov == 0.0


def test_coverage_list_input():
    """generated 是 list（直接视为 kp_coverage）"""
    cov = calc_coverage(["kp_001", "kp_002"], ["kp_001"])
    assert cov == 1.0


def test_coverage_returns_float():
    """返回 float"""
    cov = calc_coverage({"kp_coverage": ["kp_001"]}, ["kp_001"])
    assert isinstance(cov, float)


def test_coverage_string_ids():
    """字符串 ID 也能匹配"""
    generated = {"kp_coverage": ["kp_001", "kp_002"]}
    required = ["kp_001", "kp_002"]
    cov = calc_coverage(generated, required)
    assert cov == 1.0
