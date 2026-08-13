"""
B-06：知识库覆盖率评估脚本

指标：
  - kp 覆盖数：chunks 中出现过的不同 kp_tags 的 kp 个数
  - chunk 总数：kb_chunk 表行数
  - 覆盖率 = (chunk 中出现过的 kp 数) / (kp_taxonomy.json 中 kp 总数)

硬指标：kp≥30, chunk≥200, 覆盖率≥90%

运行：
  python backend/b_学情数据/kb/eval_coverage.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_ROOT = _THIS_DIR.parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select, func

from backend.b_学情数据.db import get_session, init_tables
from backend.b_学情数据.models.kb_chunk import KbChunk


def _load_taxonomy_kp_ids() -> list[str]:
    """读 kp_taxonomy.json，收集所有叶子节点的 kp_id。"""
    path = _THIS_DIR / "kp_taxonomy.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            if "kp_id" in node and node["kp_id"]:
                ids.append(str(node["kp_id"]))
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


async def main() -> dict:
    await init_tables()
    all_kp_ids = _load_taxonomy_kp_ids()
    async with get_session() as session:
        total_rows = (await session.execute(
            select(func.count(KbChunk.chunk_id))
        )).scalar_one()
        # 为了统计 kp 覆盖：遍历所有行的 kp_tags
        result = await session.execute(select(KbChunk.kp_tags))
        covered: set[str] = set()
        for (tags,) in result.all():
            if isinstance(tags, list):
                for t in tags:
                    covered.add(str(t))

    # 计算覆盖率：以 taxonomy 全集为分母
    if all_kp_ids:
        covered_in_taxonomy = {k for k in covered if k in set(all_kp_ids)}
        coverage_in_taxonomy = len(covered_in_taxonomy) / len(all_kp_ids)
        missing = sorted(set(all_kp_ids) - covered_in_taxonomy)
    else:
        coverage_in_taxonomy = 0.0
        missing = []

    stats = {
        "taxonomy_kp_total": len(all_kp_ids),
        "kb_chunk_total": int(total_rows),
        "chunk_distinct_kp_total": len(covered),
        "covered_in_taxonomy": len(covered_in_taxonomy) if all_kp_ids else len(covered),
        "coverage_pct": round(coverage_in_taxonomy * 100, 2),
        "missing_kp_ids": missing,
        # 硬指标判断
        "PASS_kp_ge_30": len(covered) >= 30,
        "PASS_chunk_ge_200": int(total_rows) >= 200,
        "PASS_coverage_ge_90pct": coverage_in_taxonomy >= 0.90,
    }
    stats["ALL_PASS"] = all([
        stats["PASS_kp_ge_30"],
        stats["PASS_chunk_ge_200"],
        stats["PASS_coverage_ge_90pct"],
    ])
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


if __name__ == "__main__":
    asyncio.run(main())
