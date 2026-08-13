"""
b_学情数据 包 __init__：暴露对外模块级函数。

跨区调用约定（协作协议 §4 + A/B/C/D 对接契约）：
- A / C / D 任何代码不可直连本区数据库
- 只能通过本 __init__.py 暴露的函数访问本区数据
"""
from backend.b_学情数据.db import (
    get_session,  # noqa: F401
    create_all_tables,  # noqa: F401
    init_tables,  # noqa: F401  # 别名，ingest/eval_coverage/B-08 脚本用
    get_kb_chunk,  # noqa: F401  # B-00 验收：暴露给 D 的领域专家 Agent
    list_kb_chunks_by_kp,  # noqa: F401  # B-00 验收：暴露给 A-05 quality_check
)

# B-05 ⭐ 学情诊断 Agent
from backend.b_学情数据.analytics import diagnose  # noqa: F401

# B-04 聚合快照入口
from backend.b_学情数据.student import get_student_snapshot  # noqa: F401
from backend.b_学情数据.activity import get_recent_activities  # noqa: F401

__all__ = [
    "get_session",
    "create_all_tables",
    "init_tables",
    "get_kb_chunk",
    "list_kb_chunks_by_kp",
    "diagnose",
    "get_student_snapshot",
    "get_recent_activities",
]
