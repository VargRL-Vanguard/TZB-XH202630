"""
单测：response.py
覆盖：ok / fail / 默认参数 / 自定义参数
"""
import pytest
from backend.公共.response import ok, fail


def test_ok_default():
    """默认 data=None, message='success'"""
    result = ok()
    assert result == {"code": 200, "message": "success", "data": None}


def test_ok_with_data():
    """带 data"""
    result = ok(data={"userId": "u001"})
    assert result == {"code": 200, "message": "success", "data": {"userId": "u001"}}


def test_ok_with_message():
    """自定义 message"""
    result = ok(data=[1, 2, 3], message="查询成功")
    assert result == {"code": 200, "message": "查询成功", "data": [1, 2, 3]}


def test_fail_basic():
    """fail 基本"""
    result = fail(400, "参数错误")
    assert result == {"code": 400, "message": "参数错误", "data": None}


def test_fail_with_data():
    """fail 带附加 data"""
    result = fail(400, "参数错误", data={"field": "username"})
    assert result == {
        "code": 400,
        "message": "参数错误",
        "data": {"field": "username"},
    }


def test_fail_401():
    """401 鉴权失败"""
    result = fail(401, "未登录")
    assert result["code"] == 401


def test_fail_500():
    """500 服务器错误"""
    result = fail(500, "Agent 调度失败")
    assert result["code"] == 500
