"""
D-05 补齐：/api/ai-chat/* HTTP 路由（08 号前端契约 §4）。

此前 D 区只有 chat/send.py 等内部函数，无 HTTP 入口，前端 AiChat 页无法联调。
本文件把内部函数包装成契约接口：
  POST   /api/ai-chat/send     {studentId, message, context?} -> {reply, conversationId, ...}
  GET    /api/ai-chat/history?studentId=&limit=  -> [{id, role("user"/"ai"), content, timestamp}]
  DELETE /api/ai-chat/history?studentId=          -> {success}

鉴权：student 仅本人；teacher/admin 任意（与 B/C 区口径一致）。
AI 未配置 Key 时 send 抛 BizError(503)，前端展示明确降级态（禁止假回复）。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import BizError, ForbiddenError
from backend.公共.response import ok

from backend.d_AI集成.chat.send import send_message
from backend.d_AI集成.chat.history import get_history
from backend.d_AI集成.chat.clear import clear_history

router = APIRouter(prefix="/api/ai-chat", tags=["AI辅导对话"])


def _can_access(current_user: dict, target_student_id: str) -> bool:
    role = current_user.get("role", "")
    uid = current_user.get("userId", "")
    if role in ("teacher", "admin"):
        return True
    if role == "student":
        return uid == target_student_id
    return False


class AiChatSendRequest(BaseModel):
    studentId: str = Field(..., min_length=1, description="学生ID")
    message: str = Field(..., min_length=1, max_length=2000, description="用户提问")
    context: dict | None = Field(default=None, description="上下文（currentModule/studyProgress 等）")


@router.post("/send")
async def ai_chat_send(req: AiChatSendRequest, user: dict = Depends(get_current_user)):
    """POST /api/ai-chat/send — 发送辅导对话消息（真实走 D 区 pipeline）。"""
    if not _can_access(user, req.studentId):
        raise ForbiddenError("无权代他人使用 AI 辅导（需要本人/教师/管理员）")

    try:
        result = await send_message(
            student_id=req.studentId,
            question=req.message,
            profile=req.context,
        )
    except Exception as e:  # noqa: BLE001 — 统一降级为明确错误，不透出堆栈
        from backend.公共.logger import get_logger
        get_logger(__name__).warning(f"ai-chat send 失败: {e}")
        raise BizError("AI 服务未配置或暂时不可用，请联系管理员配置 AI Key", code=503)

    # 对齐 08 号契约字段：reply + conversationId（保留 usage/model 附加信息）
    return ok(data={
        "reply": result.get("reply", ""),
        "conversationId": result.get("convId", ""),
        "usage": result.get("usage", {}),
        "model": result.get("model", ""),
    })


@router.get("/history")
async def ai_chat_history(
    studentId: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """GET /api/ai-chat/history — 最近一条对话的消息列表（契约 §4 扁平结构）。"""
    if not _can_access(user, studentId):
        raise ForbiddenError("无权查看他人 AI 对话（需要本人/教师/管理员）")

    convs = await get_history(studentId, limit=1)
    if not convs:
        return ok(data=[])

    messages = convs[0].get("messages") or []
    out = []
    for i, m in enumerate(messages[-limit * 2:]):  # user+ai 成对，放宽取数
        role = "user" if m.get("role") == "user" else "ai"
        out.append({
            "id": i + 1,
            "role": role,
            "content": str(m.get("content", "")),
            "timestamp": convs[0].get("updatedAt", ""),
        })
    return ok(data=out)


@router.delete("/history")
async def ai_chat_clear(
    studentId: str = Query(..., min_length=1),
    user: dict = Depends(get_current_user),
):
    """DELETE /api/ai-chat/history — 清空该学生全部 AI 对话。"""
    if not _can_access(user, studentId):
        raise ForbiddenError("无权清空他人 AI 对话（需要本人/教师/管理员）")

    result = await clear_history(studentId)
    return ok(data={"success": True, "deleted": result.get("deleted", 0)})
