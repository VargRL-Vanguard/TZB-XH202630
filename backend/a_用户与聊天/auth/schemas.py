"""
A-01 鉴权相关 Pydantic 模型（请求/响应 schema）。
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ========== 注册 ==========

class RegisterRequest(BaseModel):
    """POST /api/auth/register 入参。"""
    username: str = Field(..., min_length=3, max_length=64, description="登录名（唯一）")
    password: str = Field(..., min_length=8, max_length=128, description="明文密码（强度校验在 handler 里）")
    name: str = Field(..., min_length=1, max_length=64, description="显示名")
    role: Literal["student", "teacher", "admin"] = Field(..., description="角色")
    education: Optional[str] = Field(None, max_length=32, description="学历（学生可选）")
    major: Optional[str] = Field(None, max_length=64, description="专业（学生可选）")


class RegisterResponse(BaseModel):
    """POST /api/auth/register 出参。"""
    userId: str


# ========== 登录 ==========

class LoginRequest(BaseModel):
    """POST /api/auth/login 入参。"""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """POST /api/auth/login 出参。"""
    token: str
    userId: str
    role: str


# ========== 登出 ==========

class LogoutResponse(BaseModel):
    """POST /api/auth/logout 出参。"""
    ok: bool = True
