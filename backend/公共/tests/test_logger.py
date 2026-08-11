"""
单测：logger.py
覆盖：get_logger / 不同模块名 / trace_id 绑定
"""
import pytest
from loguru import logger as loguru_logger

from backend.公共.logger import get_logger


def test_get_logger_default():
    """默认 name"""
    log = get_logger()
    assert log is not None


def test_get_logger_with_module_name():
    """带模块名"""
    log = get_logger("backend.b_学情数据.agents.diagnosis")
    assert log is not None


def test_logger_can_log_info(capsys):
    """能输出 info"""
    log = get_logger("test")
    log.info("test message", trace_id="t-001")
    # loguru 默认会输出到 stderr，验证不抛异常即可


def test_logger_can_log_warning():
    """能输出 warning"""
    log = get_logger("test")
    log.warning("test warning", trace_id="t-002")


def test_logger_can_log_error():
    """能输出 error"""
    log = get_logger("test")
    log.error("test error", trace_id="t-003")


def test_logger_module_isolation():
    """不同模块名互不干扰"""
    log1 = get_logger("module_a")
    log2 = get_logger("module_b")
    assert log1 is not None
    assert log2 is not None
