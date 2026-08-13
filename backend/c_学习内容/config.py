"""C 区自有配置 — 仅读取 LEARNING_CONTENT_DB_URL。

参考：backend/概览.md "数据库由各区自管"。
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LearningContentConfig:
    db_url: str
    pool_size: int = 5
    pool_recycle_sec: int = 1800
    echo_sql: bool = False
    agent_retry_max: int = 2  # 资源生成失败时最大重试次数
    coverage_threshold: float = 0.90
    hallucination_threshold: float = 0.05


def load_config() -> LearningContentConfig:
    """读取 C 区配置。

    优先从环境变量读取；缺省时使用 SQLite 本地文件，便于 C 独立开发/单测。
    """
    db_url = os.environ.get(
        "LEARNING_CONTENT_DB_URL",
        "sqlite:///./learning_content.db",  # C 独立开发兜底
    )
    return LearningContentConfig(db_url=db_url)


CONFIG = load_config()
