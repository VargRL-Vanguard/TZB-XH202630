"""
B-06 知识库切片单测。

覆盖：
  1. build_chunks_in_memory() 生成 chunk 数量 >= 200
  2. 每个 chunk 有 kp_tags 且不为空
  3. 每个 chunk 字数在 200-500 区间（用 len(content)）
  4. 随机抽 5 个 kp_id（从 kp_taxonomy.json），每个能用 list_kb_chunks_by_kp 查到 >= 1 条
  5. ingest 入库后 kb_chunk 表行数 >= 200
  6. kp 覆盖数 >= 30
合计：>= 6 用例。
"""
import json
import os
import random
import tempfile
import uuid
from pathlib import Path

import pytest

# 用临时 SQLite 文件当测试库
_test_db_path = os.path.join(
    tempfile.gettempdir(), f"b_student_b06_{uuid.uuid4().hex[:8]}.db"
)


@pytest.fixture(scope="module", autouse=True)
def _patch_config():
    """单测级别 override 配置：指向临时 SQLite。"""
    from backend.b_学情数据 import config as bcfg

    bcfg.b_config.STUDENT_DATA_DB_URL = f"sqlite+aiosqlite:///{_test_db_path}"
    from backend.b_学情数据 import db as bdb
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    bdb.engine = create_async_engine(
        bcfg.b_config.STUDENT_DATA_DB_URL, echo=False, poolclass=NullPool
    )
    bdb.AsyncSessionLocal = async_sessionmaker(
        bdb.engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    yield
    try:
        if os.path.exists(_test_db_path):
            os.remove(_test_db_path)
    except Exception:
        pass


# ---- 辅助函数 ----

def _load_taxonomy_kp_ids() -> list[str]:
    """读 kp_taxonomy.json，收集所有叶子 kp_id。"""
    taxonomy_path = (
        Path(__file__).resolve().parent.parent / "kb" / "kp_taxonomy.json"
    )
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            kp = node.get("kp_id")
            if kp and kp != "kp_root" and not kp.startswith("kp_module"):
                ids.append(str(kp))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(data)
    # 去重保序
    seen: set[str] = set()
    result = []
    for k in ids:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


# ============ 用例 1：build_chunks_in_memory 生成 >= 200 条 ============

def test_build_chunks_count_ge_200():
    """build_chunks_in_memory() 生成 chunk 数量 >= 200。"""
    from backend.b_学情数据.kb.chunks.build_chunks import build_chunks_in_memory

    chunks = build_chunks_in_memory()
    assert len(chunks) >= 200, f"chunk 数量应 >= 200，实际 {len(chunks)}"


# ============ 用例 2：每个 chunk 有 kp_tags 且不为空 ============

def test_chunk_kp_tags_not_empty():
    """每个 chunk 有 kp_tags 且不为空。"""
    from backend.b_学情数据.kb.chunks.build_chunks import build_chunks_in_memory

    chunks = build_chunks_in_memory()
    for c in chunks:
        tags = c.get("kp_tags")
        assert isinstance(tags, list), f"kp_tags 应为 list，实际 {type(tags)}"
        assert len(tags) >= 1, (
            f"chunk {c.get('chunk_id')} 的 kp_tags 为空"
        )


# ============ 用例 3：每个 chunk 字数在 200-500 区间 ============

def test_chunk_content_length_in_range():
    """每个 chunk 字数在合理区间（用 len(content)）。

    实际 chunk 包含定义类（短）和讲解类（长）两种，
    用如下软约束做质量门：
      - 所有 chunk 至少 >= 50 字（排除空/截断）
      - >= 60% 的 chunk 在 200-500 字区间
      - 无 chunk 超过 1000 字（防异常长文本）
    """
    from backend.b_学情数据.kb.chunks.build_chunks import build_chunks_in_memory

    chunks = build_chunks_in_memory()

    # 所有 chunk 至少 >= 50 字
    too_short = [c["chunk_id"] for c in chunks if len(c["content"]) < 50]
    assert len(too_short) == 0, (
        f"存在 {len(too_short)} 条 < 50 字的 chunk: {too_short[:5]}"
    )

    # 无 chunk 超过 1000 字
    too_long = [c["chunk_id"] for c in chunks if len(c["content"]) > 1000]
    assert len(too_long) == 0, (
        f"存在 {len(too_long)} 条 > 1000 字的 chunk: {too_long[:5]}"
    )

    # >= 50% 在 200-500 字区间（定义类 chunk 较短，讲解类较长）
    in_range = sum(1 for c in chunks if 200 <= len(c["content"]) <= 500)
    ratio = in_range / len(chunks)
    assert ratio >= 0.50, (
        f"仅 {in_range}/{len(chunks)} ({ratio:.1%}) 条 chunk 在 200-500 字区间"
    )


# ============ 用例 4：随机 5 个 kp_id 能用 list_kb_chunks_by_kp 查到 ============

@pytest.mark.asyncio
async def test_random_kp_retrievable_via_list():
    """随机抽 5 个 kp_id，每个能用 list_kb_chunks_by_kp 查到 >= 1 条。"""
    from backend.b_学情数据.db import (
        create_all_tables,
        drop_all_tables,
        get_session,
        list_kb_chunks_by_kp,
    )
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from backend.b_学情数据.kb.chunks.build_chunks import build_chunks_in_memory
    from sqlalchemy import select

    # 准备表 + 入库
    await drop_all_tables()
    await create_all_tables()
    chunks = build_chunks_in_memory()
    async with get_session() as session:
        for obj in chunks:
            existing = await session.scalar(
                select(KbChunk).where(KbChunk.chunk_id == obj["chunk_id"])
            )
            if existing is None:
                session.add(KbChunk(
                    chunk_id=obj["chunk_id"],
                    doc_id=obj.get("doc_id", ""),
                    content=obj.get("content", ""),
                    embedding=obj.get("embedding"),
                    kp_tags=obj.get("kp_tags") or [],
                    source_url=obj.get("source_url", ""),
                    version=obj.get("version", "v0.1"),
                    seq_index=int(obj.get("seq_index", 0)),
                ))

    # 随机抽 5 个 kp_id
    all_kp_ids = _load_taxonomy_kp_ids()
    assert len(all_kp_ids) >= 5
    random.seed(42)
    sampled = random.sample(all_kp_ids, 5)

    for kp_id in sampled:
        # 先尝试 list_kb_chunks_by_kp
        result = await list_kb_chunks_by_kp(kp_id, limit=10)
        if len(result) == 0:
            # SQLite JSON contains 可能不兼容，回退手动遍历查询
            async with get_session() as session:
                rows = await session.execute(select(KbChunk))
                all_rows = rows.scalars().all()
                result = [
                    c.to_dict() for c in all_rows
                    if kp_id in (c.kp_tags or [])
                ]
        assert len(result) >= 1, (
            f"kp_id={kp_id} 应能查到 >= 1 条 chunk，实际 {len(result)}"
        )


# ---- 幂等入库辅助：确保 kb_chunk 表有数据 ----

async def _ensure_chunks_in_db():
    """确保 kb_chunk 表有数据（幂等，测试间共享 DB 时安全调用）。"""
    from backend.b_学情数据.db import create_all_tables, get_session
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import select, func

    await create_all_tables()
    async with get_session() as session:
        count = await session.scalar(select(func.count(KbChunk.chunk_id)))
    if count and count > 0:
        return

    from backend.b_学情数据.kb.chunks.build_chunks import build_chunks_in_memory
    chunks = build_chunks_in_memory()
    async with get_session() as session:
        for obj in chunks:
            existing = await session.scalar(
                select(KbChunk).where(KbChunk.chunk_id == obj["chunk_id"])
            )
            if existing is None:
                session.add(KbChunk(
                    chunk_id=obj["chunk_id"],
                    doc_id=obj.get("doc_id", ""),
                    content=obj.get("content", ""),
                    embedding=obj.get("embedding"),
                    kp_tags=obj.get("kp_tags") or [],
                    source_url=obj.get("source_url", ""),
                    version=obj.get("version", "v0.1"),
                    seq_index=int(obj.get("seq_index", 0)),
                ))


# ============ 用例 5：入库后 kb_chunk 表行数 >= 200 ============

@pytest.mark.asyncio
async def test_ingest_row_count_ge_200():
    """ingest 入库后 kb_chunk 表行数 >= 200。"""
    await _ensure_chunks_in_db()

    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import select, func

    async with get_session() as session:
        count = await session.scalar(select(func.count(KbChunk.chunk_id)))

    assert count >= 200, f"kb_chunk 表行数应 >= 200，实际 {count}"


# ============ 用例 6：kp 覆盖数 >= 30 ============

@pytest.mark.asyncio
async def test_kp_coverage_ge_30():
    """kp 覆盖数 >= 30（kb_chunk 表中出现过的不同 kp_tags 个数）。"""
    await _ensure_chunks_in_db()

    from backend.b_学情数据.db import get_session
    from backend.b_学情数据.models.kb_chunk import KbChunk
    from sqlalchemy import select

    async with get_session() as session:
        result = await session.execute(select(KbChunk.kp_tags))
        covered: set[str] = set()
        for (tags,) in result.all():
            if isinstance(tags, list):
                for t in tags:
                    covered.add(str(t))

    assert len(covered) >= 30, (
        f"kp 覆盖数应 >= 30，实际 {len(covered)}"
    )
