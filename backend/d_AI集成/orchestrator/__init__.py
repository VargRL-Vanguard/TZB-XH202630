"""
D-03 ⭐ 夺奖专项：多智能体协同编排器。

对外暴露：
  - orchestrate() — 多智能体协同编排入口
  - OrchestrationPipeline — 流水线
  - DebateEngine — 辩论引擎
  - EventEmitter — 事件发射器
  - DecisionMaker — 决策融合器
"""
from backend.d_AI集成.orchestrator.pipeline import orchestrate  # noqa: F401
from backend.d_AI集成.orchestrator.pipeline import OrchestrationPipeline  # noqa: F401
from backend.d_AI集成.orchestrator.debate_engine import DebateEngine  # noqa: F401
from backend.d_AI集成.orchestrator.event_emitter import EventEmitter  # noqa: F401
from backend.d_AI集成.orchestrator.decision_maker import DecisionMaker  # noqa: F401

__all__ = [
    "orchestrate",
    "OrchestrationPipeline",
    "DebateEngine",
    "EventEmitter",
    "DecisionMaker",
]