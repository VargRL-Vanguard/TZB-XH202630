"""
质量看板数据接口（A-05 产出的对外出口，供前端 Quality 页读取）。

GET /api/quality/latest → docs/quality_reports/ 下最新一份报告 JSON（data 原样返回）。

背景：08 号契约写的数据源 `GET /docs/quality_reports/latest.json` 实际不存在
（没有 latest.json 文件，也没有静态挂载），故由本接口按文件名时间取最新。
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from backend.公共.errors import BizError
from backend.公共.logger import get_logger
from backend.公共.response import ok

log = get_logger(__name__)

router = APIRouter(tags=["质量看板"])

# 项目根/docs/quality_reports（backend/公共/quality_api.py → 上两级为项目根）
_REPORTS_DIR = Path(__file__).resolve().parents[2] / "docs" / "quality_reports"


def _find_latest_report() -> Path | None:
    if not _REPORTS_DIR.is_dir():
        return None
    files = sorted(_REPORTS_DIR.glob("quality_report_*.json"))
    return files[-1] if files else None


@router.get("/api/quality/latest")
async def quality_latest():
    """GET /api/quality/latest — 最新质量报告（3 项硬指标 + 3 画像明细）。"""
    path = _find_latest_report()
    if path is None:
        raise BizError("暂无质量报告，请先运行 A-05 quality_check", code=404)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.error(f"读取质量报告失败: {path} {e}")
        raise BizError("质量报告读取失败", code=500)
    return ok(data=data)
