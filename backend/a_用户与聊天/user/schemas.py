"""
A-02 用户信息 + 学习者画像 Pydantic 模型（请求/响应 schema）。

**契约**（api-doc.js §1.3 兼容 + A-02 扩展）：
- GET  /api/user/info   → UserInfoResponse（User + LearnerProfile 合并）
- PUT  /api/user/profile → UserProfileRequest → UserInfoResponse（更新后回显）
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ========== 通用响应：User + LearnerProfile 合并 ==========

class UserInfoResponse(BaseModel):
    """GET /api/user/info 与 PUT /api/user/profile 的统一返回结构。"""
    # ---- User 部分 ----
    userId: str
    username: str
    name: str
    role: Literal["student", "teacher", "admin"]
    # ---- LearnerProfile 部分（可能为 None：无画像时）----
    education: Optional[str] = Field(None, description="学历：本科/硕士/大专/高中")
    major: Optional[str] = Field(None, description="专业")
    theoryTestScore: Optional[int] = Field(None, ge=0, le=100, description="理论测试分 0-100")
    weakKPs: list[str] = Field(default_factory=list, description="薄弱知识点 ID 列表")
    strongKPs: list[str] = Field(default_factory=list, description="擅长知识点 ID 列表")
    profileUpdatedAt: Optional[str] = Field(None, description="画像最近更新时间 ISO8601")


# ========== 更新画像请求 ==========

class UserProfileRequest(BaseModel):
    """PUT /api/user/profile 入参。"""
    education: Optional[str] = Field(None, max_length=32)
    major: Optional[str] = Field(None, max_length=64)
    theoryTestScore: Optional[int] = Field(None, ge=0, le=100)
    weakKPs: Optional[list[str]] = Field(None, description="薄弱知识点 ID 列表（覆盖式）")
    strongKPs: Optional[list[str]] = Field(None, description="擅长知识点 ID 列表（覆盖式）")
