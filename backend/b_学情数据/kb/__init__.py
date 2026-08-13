"""
kb 包 __init__：暴露知识库检索函数给 C/D 区调用。

对外接口（B-06 验收标准 + 概览.md 对外约定）：
    from backend.b_学情数据.kb import get_kb_chunk, list_kb_chunks_by_kp

C-04 领域专家 Agent / D 审核裁判 Agent / A-05 quality_check 均通过这两个函数访问知识库。
"""
from backend.b_学情数据.db import get_kb_chunk, list_kb_chunks_by_kp  # noqa: F401

__all__ = ["get_kb_chunk", "list_kb_chunks_by_kp"]
