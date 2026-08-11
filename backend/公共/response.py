"""
统一响应封装。
所有 API 返回格式：{"code": int, "message": str, "data": Any}
对应 api-doc.js §1 通用响应规范。
"""
from typing import Any, Optional


def ok(data: Any = None, message: str = "success") -> dict:
    """
    成功响应。
    :param data: 业务数据
    :param message: 提示信息（默认 "success"）
    :return: {"code": 200, "message": ..., "data": ...}
    """
    return {"code": 200, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict:
    """
    失败响应。
    :param code: 业务错误码（非 HTTP 状态码，但通常对齐：400/401/403/404/500）
    :param message: 错误信息
    :param data: 可选附加信息（如字段级错误）
    :return: {"code": ..., "message": ..., "data": ...}
    """
    return {"code": code, "message": message, "data": data}
