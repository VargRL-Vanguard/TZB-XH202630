"""C 区自有 DB 连接。

参考：backend/概览.md "数据库由各区自管"。
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# 兼容相对/绝对导入（项目目录以 c_/数字 开头，不能用 from backend.c_学习内容...）
try:
    from .config import CONFIG
except (ImportError, ValueError):
    _cfg = sys.modules.get("c_config")
    if _cfg is not None:
        CONFIG = _cfg.CONFIG
    else:
        # 兜底：直接读环境变量
        import os
        class _Cfg:
            db_url = os.environ.get("LEARNING_CONTENT_DB_URL", "sqlite:///./learning_content.db")
            pool_size = 5
            pool_recycle_sec = 1800
            echo_sql = False
            agent_retry_max = 2
            coverage_threshold = 0.90
            hallucination_threshold = 0.05
        CONFIG = _Cfg()


def _build_engine() -> Engine:
    url = CONFIG.db_url
    connect_args = {}
    if url.startswith("sqlite"):
        # SQLite 需要 check_same_thread=False 才能在多线程下共用
        connect_args = {"check_same_thread": False}
    return create_engine(
        url,
        pool_size=CONFIG.pool_size,
        pool_recycle=CONFIG.pool_recycle_sec,
        echo=CONFIG.echo_sql,
        future=True,
        connect_args=connect_args,
    )


engine: Engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    """C 区数据库会话上下文管理器。

    用法：
        with get_session() as s:
            s.add(...)
        # 退出 with 时自动 commit；异常时自动 rollback
    """
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def init_db() -> None:
    """幂等建表（仅 C 区自己的表，不影响公共/他区）。"""
    # 延迟 import 避免循环引用
    from .models import Base

    Base.metadata.create_all(bind=engine)
