"""
统一异常类。
所有业务异常都继承 BizError，对应 HTTP 状态码由调用方决定。
"""
from typing import Optional


class BizError(Exception):
    """业务异常基类。"""

    def __init__(self, message: str, code: int = 400, data: Optional[dict] = None):
        self.message = message
        self.code = code
        self.data = data or {}
        super().__init__(message)


class AuthError(BizError):
    """认证失败：缺 token / token 过期 / 伪造 token。HTTP 401。"""

    def __init__(self, message: str = "未登录或 token 过期", data: Optional[dict] = None):
        super().__init__(message, code=401, data=data)


class NotFoundError(BizError):
    """资源不存在。HTTP 404。"""

    def __init__(self, message: str = "资源不存在", data: Optional[dict] = None):
        super().__init__(message, code=404, data=data)


class AgentError(BizError):
    """Agent 调度失败：B/C/D 三个 Agent 任意一个超时 / 解析失败 / 异常。HTTP 500。"""

    def __init__(self, message: str = "Agent 调度失败", data: Optional[dict] = None):
        super().__init__(message, code=500, data=data)


class QualityError(BizError):
    """质量指标不达标：3 项硬指标任一不达标。HTTP 422。"""

    def __init__(self, message: str = "3 项硬指标未达标", data: Optional[dict] = None):
        super().__init__(message, code=422, data=data)
