"""
audit 包 __init__：暴露审核裁判 Agent（D-06 ⭐ 夺奖专项）。

对外接口：
    from backend.d_AI集成.audit import audit

D-03 协同编排器 / A-05 quality_check 均通过此入口调用审核 Agent。
"""
from backend.d_AI集成.audit.audit_agent import audit  # noqa: F401

__all__ = ["audit"]