"""POST /api/suggestions/read"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.公共.auth_middleware import get_current_user
from backend.公共.errors import NotFoundError
from backend.公共.response import ok

from .service import mark_suggestion_read

router = APIRouter()


class ReadBody(BaseModel):
    studentId: str
    suggestionId: str


@router.post("/read")
def read_suggestion(body: ReadBody, user: dict = Depends(get_current_user)):
    """标记建议已读。"""
    role = user.get("role", "")
    uid = user.get("userId", "")
    if role == "student" and uid != body.studentId:
        from backend.公共.errors import ForbiddenError
        raise ForbiddenError("只能标记自己的建议为已读")

    success = mark_suggestion_read(body.studentId, body.suggestionId)
    if not success:
        raise NotFoundError(f"建议 {body.suggestionId} 不存在")
    return ok(data={"success": True})
