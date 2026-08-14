"""
核心知识点覆盖率校验（D-06 ⭐ 夺奖专项）。

算法：
  1. 从 content 中提取实际覆盖的 kp 列表
  2. 调 A 的 calc_coverage 计算覆盖率
  3. 输出缺失的 kp 列表

返回：{coverage, coveredKps[], missingKps[], totalRequired}
"""
from __future__ import annotations

import logging
from typing import Any

from backend.公共.logger import get_logger
from backend.公共.metrics import calc_coverage

log = get_logger(__name__)

# 覆盖率达标阈值
COVERAGE_THRESHOLD = 0.90


def _extract_kp_from_content(content: Any) -> list[str]:
    """
    从 content 中提取实际覆盖的 kp 列表。
    content 可能是：
      - dict：含 kp_coverage 字段
      - str：JSON 字符串或纯文本
      - list：直接视为 kp 列表
    """
    if isinstance(content, list):
        return [str(k) for k in content]
    if isinstance(content, dict):
        covered = content.get("kp_coverage") or content.get("kpCoverage") or []
        return [str(k) for k in covered]
    if isinstance(content, str):
        import json
        try:
            parsed = json.loads(content)
            return _extract_kp_from_content(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return []


def check_coverage(
    content: Any,
    kp_ids: list[str],
) -> dict:
    """
    核心知识点覆盖率校验。

    :param content: 被审核的内容（dict / str / list）
    :param kp_ids: C 声称覆盖的知识点 ID 列表
    :return: {
        coverage: float,              # 覆盖率 [0,1]
        coveredKps: list[str],        # 实际覆盖的 kp
        missingKps: list[str],        # 缺失的 kp
        totalRequired: int,           # 需要覆盖的总数
        isPass: bool,                 # 是否达标（≥ 0.90）
    }
    """
    if not kp_ids:
        return {
            "coverage": 1.0,
            "coveredKps": [],
            "missingKps": [],
            "totalRequired": 0,
            "isPass": True,
        }

    required_set = set(str(k) for k in kp_ids)

    # 从 content 中提取覆盖的 kp
    covered = _extract_kp_from_content(content)
    covered_set = set(str(k) for k in covered)

    # 交集
    actual_covered = covered_set & required_set
    missing = sorted(required_set - covered_set)

    # 调用 A 区标准函数
    try:
        generated_dict = {"kp_coverage": list(actual_covered)}
        cov = calc_coverage(generated_dict, list(required_set))
    except Exception as e:
        log.warning(f"calc_coverage 调用失败，降级本地计算: {e}")
        cov = len(actual_covered) / len(required_set) if required_set else 1.0

    return {
        "coverage": round(cov, 4),
        "coveredKps": sorted(actual_covered),
        "missingKps": missing,
        "totalRequired": len(required_set),
        "isPass": cov >= COVERAGE_THRESHOLD,
    }