"""
D-07：Trace 追踪接口。

提供协同事件追踪查询。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from backend.公共.auth_middleware import get_current_user
from backend.d_AI集成.ws_bridge import get_trace_events

router = APIRouter(prefix="/api/ai/trace", tags=["AI追踪"])


@router.get("/{trace_id}")
async def trace(trace_id: str, user=Depends(get_current_user)):
    """获取指定 trace 的所有协同事件。"""
    return await get_trace_events(trace_id)