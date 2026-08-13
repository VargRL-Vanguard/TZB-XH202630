"""
analytics 包 __init__：B-04 聚合器 + B-05 ⭐ 学情诊断 Agent 入口。

D 区调用方式：
    from backend.b_学情数据.analytics import diagnose, aggregate_behavior
    result = diagnose("s001")
"""
from backend.b_学情数据.analytics.aggregator import aggregate_behavior  # noqa: F401
from backend.b_学情数据.analytics.diagnosis_agent import diagnose  # noqa: F401

__all__ = ["aggregate_behavior", "diagnose"]
