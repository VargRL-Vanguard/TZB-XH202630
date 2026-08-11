"""
单测：errors.py
覆盖：5 类异常的 message / code / data
"""
import pytest

from backend.公共.errors import (
    BizError,
    AuthError,
    NotFoundError,
    AgentError,
    QualityError,
)


def test_biz_error_base():
    """基类"""
    err = BizError("业务错误", code=400)
    assert err.message == "业务错误"
    assert err.code == 400
    assert err.data == {}
    assert str(err) == "业务错误"


def test_biz_error_with_data():
    """带 data"""
    err = BizError("错误", code=400, data={"field": "x"})
    assert err.data == {"field": "x"}


def test_auth_error():
    """AuthError 默认 401"""
    err = AuthError()
    assert err.code == 401
    assert "token" in err.message or "登录" in err.message


def test_auth_error_custom_message():
    """AuthError 自定义"""
    err = AuthError("token 已过期")
    assert err.code == 401
    assert err.message == "token 已过期"


def test_not_found_error():
    """NotFoundError 默认 404"""
    err = NotFoundError("用户不存在")
    assert err.code == 404


def test_agent_error():
    """AgentError 默认 500"""
    err = AgentError("B-05 超时")
    assert err.code == 500


def test_quality_error():
    """QualityError 默认 422"""
    err = QualityError("幻觉率超标")
    assert err.code == 422


def test_all_errors_inherit_bizerror():
    """5 类异常都继承 BizError"""
    for cls in [AuthError, NotFoundError, AgentError, QualityError]:
        err = cls("test")
        assert isinstance(err, BizError)


def test_quality_error_with_metrics_data():
    """QualityError 携带指标数据"""
    err = QualityError(
        "3 项硬指标未达标",
        data={"hallucination": 0.08, "accuracy": 0.90, "coverage": 0.88},
    )
    assert err.data["hallucination"] == 0.08
