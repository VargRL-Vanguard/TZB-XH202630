"""
统一日志。
按模块命名；输出含 timestamp / level / module / trace_id。
基于 loguru（零配置、彩色输出）。
"""
import sys
from loguru import logger as _loguru_logger

# 移除 loguru 默认 handler
_loguru_logger.remove()

# 1. 控制台输出（开发用）
_loguru_logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    level="INFO",
    colorize=True,
)

# 2. 文件输出（生产用，按天轮转）
_loguru_logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "trace_id={extra[trace_id]} | "
        "{message}"
    ),
    level="DEBUG",
    rotation="00:00",
    retention="30 days",
    encoding="utf-8",
    enqueue=True,  # 异步写入，进程安全
)


def get_logger(name: str = "app"):
    """
    获取按模块命名的 logger。

    用法：
        from backend.公共.logger import get_logger
        log = get_logger(__name__)
        log.info("hello", trace_id="t-001")
    """
    return _loguru_logger.bind(module=name)


# 兼容旧代码：直接 import logger 也可用
logger = get_logger("公共")
