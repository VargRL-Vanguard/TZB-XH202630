"""
D-07 ⭐：WebSocket 协同事件桥接。

职责：
  - 将 D 区的协同事件转发到 A 区 WebSocket 通道
  - 提供 trace 查询接口
  - 提供可视化数据聚合接口
"""
from __future__ import annotations

from backend.公共.logger import get_logger
from backend.d_AI集成.db import get_session
from backend.d_AI集成.models.agent_log import AgentLog
from backend.d_AI集成.models.audit_record import AuditRecord

log = get_logger(__name__)


async def get_trace_events(trace_id: str) -> dict:
    """
    获取指定 trace 的所有协同事件。

    :param trace_id: 协同追踪ID
    :return: {"traceId": str, "events": list[dict]}
    """
    try:
        async with get_session() as session:
            from sqlalchemy import select
            stmt = (
                select(AgentLog)
                .where(AgentLog.trace_id == trace_id)
                .order_by(AgentLog.step.asc())
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return {
                "traceId": trace_id,
                "events": [row.to_dict() for row in rows],
            }
    except Exception as e:
        log.error(f"获取 trace 事件失败: {e}")
        return {"traceId": trace_id, "events": [], "error": str(e)}


async def get_visualization_data(student_id: str) -> dict:
    """
    获取可视化数据：学生维度下的所有 Agent 协同数据聚合。

    :param student_id: 学生ID
    :return: 可视化数据 dict
    """
    try:
        async with get_session() as session:
            from sqlalchemy import select
            # 审核记录
            audit_stmt = (
                select(AuditRecord)
                .where(AuditRecord.student_id == student_id)
                .order_by(AuditRecord.created_at.desc())
                .limit(20)
            )
            audit_result = await session.execute(audit_stmt)
            audit_rows = audit_result.scalars().all()

            # 日志
            log_stmt = (
                select(AgentLog)
                .where(AgentLog.payload.contains({"studentId": student_id}))
                .order_by(AgentLog.created_at.desc())
                .limit(50)
            )
            log_result = await session.execute(log_stmt)
            log_rows = log_result.scalars().all()

            return {
                "studentId": student_id,
                "auditRecords": [r.to_dict() for r in audit_rows],
                "agentLogs": [r.to_dict() for r in log_rows],
                "summary": {
                    "totalAudits": len(audit_rows),
                    "passedAudits": sum(1 for r in audit_rows if r.result == "pass"),
                    "avgScore": round(
                        sum(r.score for r in audit_rows) / len(audit_rows) if audit_rows else 0, 4
                    ),
                },
            }
    except Exception as e:
        log.error(f"获取可视化数据失败: {e}")
        return {"studentId": student_id, "error": str(e)}


async def broadcast_orchestration_event(event: dict) -> None:
    """
    广播协同编排事件到所有连接的客户端。

    :param event: 事件 dict
    """
    try:
        from backend.a_用户与聊天.ws.manager import connection_manager
        from backend.a_用户与聊天.ws.events import EVENT_CHANNEL_PREFIX
        channel = f"{EVENT_CHANNEL_PREFIX}orchestrator"
        await connection_manager.broadcast_to_channel(channel=channel, event=event)
    except Exception as e:
        log.warning(f"WS 广播失败（降级）: {e}")