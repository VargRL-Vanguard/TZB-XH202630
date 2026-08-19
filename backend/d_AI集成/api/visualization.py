"""
D-07：可视化数据接口。

FastAPI 路由，返回可视化所需的聚合数据。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from backend.公共.auth_middleware import get_current_user
from backend.d_AI集成.ws_bridge import get_visualization_data

router = APIRouter(prefix="/api/ai/visualization", tags=["AI可视化"])


@router.get("/{student_id}")
async def visualization(student_id: str, user=Depends(get_current_user)):
    """获取学生维度的可视化数据。"""
    return await get_visualization_data(student_id)