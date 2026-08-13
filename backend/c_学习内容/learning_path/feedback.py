"""POST /api/learning-path/feedback — C-06 动态迭代。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.公共.auth_middleware import get_current_user
from backend.公共.response import ok

from .feedback_adapter import handle_feedback

router = APIRouter()


class FeedbackBody(BaseModel):
    studentId: str
    kpId: str
    questionId: str = ""
    correct: bool = True
    responseTime: int = Field(0, alias="responseTime")
    difficulty: int = 3
    resourceId: str = Field("", alias="resourceId")

    model_config = {"populate_by_name": True}


@router.post("/feedback")
def feedback(body: FeedbackBody, user: dict = Depends(get_current_user)):
    """学生提交答题反馈；正确率极端时触发动态迭代。"""
    # 权限：仅本人可提交自己的反馈（教师/管理员可代理提交）
    role = user.get("role", "")
    uid = user.get("userId", "")
    if role == "student" and uid != body.studentId:
        from backend.公共.errors import ForbiddenError
        raise ForbiddenError("只能提交自己的反馈")

    result = handle_feedback(
        student_id=body.studentId,
        kp_id=body.kpId,
        question_id=body.questionId,
        correct=body.correct,
        response_time_ms=body.responseTime,
        difficulty=body.difficulty,
        resource_id=body.resourceId,
    )
    return ok(data=result)
