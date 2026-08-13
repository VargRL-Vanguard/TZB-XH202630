"""核心知识点覆盖率校验（对接 A 的 公共/metrics.py）。"""
from __future__ import annotations

from typing import Iterable

from ..config import CONFIG

# 复用 metrics 兼容层
try:
    from backend.公共.metrics import calc_coverage  # type: ignore
except Exception:
    def calc_coverage(generated_text: str, required_kps: Iterable[str]) -> float:  # type: ignore
        if not required_kps:
            return 1.0
        # 极简 mock：generated_text 中每出现一次 kp_id 算命中
        if not generated_text:
            return 0.0
        hits = sum(1 for kp in required_kps if kp and kp in generated_text)
        return hits / len(list(required_kps))


def is_covered(generated_text: str, required_kps: Iterable[str]) -> tuple[bool, float]:
    coverage = float(calc_coverage(generated_text, list(required_kps)))
    return coverage >= CONFIG.coverage_threshold, coverage
