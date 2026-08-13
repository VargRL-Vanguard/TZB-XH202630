"""
B-07 测试画像一键导入脚本。

功能：
  1. 读取 test_profiles/ 下的 3 个画像 JSON 文件
  2. 读取 expected_outputs/ 下对应的预期输出 JSON
  3. upsert 到 TestProfile 表（profile_id 存在则更新，不存在则插入）
  4. 输出统计：导入数量、成功/失败

运行方式：
  # 方式 1：模块方式运行（推荐，项目根目录下）
  python -m backend.b_学情数据.scripts.load_test_profiles

  # 方式 2：直接运行脚本
  python backend/b_学情数据/scripts/load_test_profiles.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# ---- sys.path 处理：支持直接 `python scripts/load_test_profiles.py` 运行 ----
_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_ROOT = _THIS_DIR.parent.parent.parent  # 项目根目录
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select

from backend.b_学情数据.db import get_session, init_tables
from backend.b_学情数据.models.test_profile import TestProfile


# ---- 画像文件清单 ----
_PROFILES_DIR = _THIS_DIR.parent / "test_profiles"
_EXPECTED_DIR = _PROFILES_DIR / "expected_outputs"

_PROFILE_FILES = [
    ("profile_01_本科应届生.json", "profile_01_expected.json"),
    ("profile_02_高职在读生.json", "profile_02_expected.json"),
    ("profile_03_企业转岗人员.json", "profile_03_expected.json"),
]


def _load_json(path: Path) -> dict[str, Any]:
    """以 UTF-8 编码读取 JSON 文件。"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


async def _upsert_profile(
    session,
    profile: dict[str, Any],
    expected: dict[str, Any],
) -> str:
    """
    upsert 单个画像到 TestProfile 表。
    :return: "inserted" 或 "updated"
    """
    pid = profile["profile_id"]
    row = await session.scalar(
        select(TestProfile).where(TestProfile.profile_id == pid)
    )
    if row is None:
        session.add(TestProfile(
            profile_id=pid,
            label=profile.get("label", ""),
            payload=profile,
            expected_weak_kps=expected.get("expected_weak_kps", []),
        ))
        return "inserted"
    else:
        row.label = profile.get("label", row.label)
        row.payload = profile
        row.expected_weak_kps = expected.get("expected_weak_kps", [])
        return "updated"


async def main() -> dict:
    """
    主入口：导入 3 个画像到 test_profile 表。
    :return: 统计字典
    """
    # 1. 确保表存在
    await init_tables()

    total = 0
    success = 0
    failed = 0
    details: list[dict] = []

    for profile_file, expected_file in _PROFILE_FILES:
        total += 1
        profile_path = _PROFILES_DIR / profile_file
        expected_path = _EXPECTED_DIR / expected_file

        try:
            profile = _load_json(profile_path)
            expected = _load_json(expected_path)

            async with get_session() as session:
                action = await _upsert_profile(session, profile, expected)

            success += 1
            details.append({
                "profile_id": profile["profile_id"],
                "label": profile.get("label", ""),
                "action": action,
                "status": "ok",
            })
        except Exception as e:
            failed += 1
            details.append({
                "file": profile_file,
                "status": "error",
                "error": str(e),
            })

    stats = {
        "total": total,
        "success": success,
        "failed": failed,
        "details": details,
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


if __name__ == "__main__":
    asyncio.run(main())
