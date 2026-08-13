"""
B-06：知识库入库脚本

功能：
1. 调用 build_chunks 生成 240 条 chunk（内存中直接生成，不依赖 JSONL 中间文件）
2. 写入 kb_chunk 表（upsert：chunk_id 存在则更新，不存在则插入）
3. 输出入库统计

运行：
  python backend/b_学情数据/kb/ingest.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# 允许以脚本方式直接运行
_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_ROOT = _THIS_DIR.parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select

from backend.b_学情数据.db import get_session, init_tables
from backend.b_学情数据.models.kb_chunk import KbChunk
from backend.b_学情数据.kb.chunks.build_chunks import build_chunks_in_memory  # 稍后在 build_chunks.py 里补上


async def _upsert_chunk(session, obj: dict) -> None:
    cid = obj["chunk_id"]
    row = await session.scalar(select(KbChunk).where(KbChunk.chunk_id == cid))
    if row is None:
        session.add(KbChunk(
            chunk_id=cid,
            doc_id=obj.get("doc_id", ""),
            content=obj.get("content", ""),
            embedding=obj.get("embedding"),
            kp_tags=obj.get("kp_tags") or [],
            source_url=obj.get("source_url", ""),
            version=obj.get("version", "v0.1"),
            seq_index=int(obj.get("seq_index", 0)),
        ))
    else:
        row.doc_id = obj.get("doc_id", row.doc_id)
        row.content = obj.get("content", row.content)
        row.embedding = obj.get("embedding", row.embedding)
        row.kp_tags = obj.get("kp_tags") or row.kp_tags
        row.source_url = obj.get("source_url", row.source_url)
        row.version = obj.get("version", row.version)
        row.seq_index = int(obj.get("seq_index", row.seq_index))


async def main() -> dict:
    await init_tables()
    # 1) 内存生成 240 条 chunks
    chunks: list[dict] = build_chunks_in_memory()
    print(f"[build_chunks] 生成条数：{len(chunks)}")
    # 2) upsert 入库
    async with get_session() as session:
        for obj in chunks:
            await _upsert_chunk(session, obj)
        # 显式提交（get_session 退出时也会 commit，但这里提前刷一把计数）
        await session.flush()
        total = (await session.execute(select(KbChunk.chunk_id))).all()
        kp_set: set[str] = set()
        for row in total:
            pass  # 下面重新查
        result = await session.execute(select(KbChunk))
        all_rows = result.scalars().all()
        for r in all_rows:
            for t in r.kp_tags:
                kp_set.add(t)
    stats = {
        "chunks_written": len(chunks),
        "total_in_db": len(all_rows),
        "distinct_kp_count": len(kp_set),
        "kp_ids": sorted(kp_set),
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


if __name__ == "__main__":
    asyncio.run(main())
