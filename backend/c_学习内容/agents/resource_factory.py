"""3 种形态资源工厂 — 把 LLM 原始输出解析为统一结构。"""
from __future__ import annotations

import json
import re
from typing import Any


def _safe_json_loads(raw: str) -> dict:
    """宽松解析：先剥 markdown 围栏，再 load。失败则抛。"""
    if not raw:
        raise ValueError("empty raw")
    s = raw.strip()
    # 去掉 ```json ... ``` 或 ``` ... ```
    fence = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL)
    if fence:
        s = fence.group(1).strip()
    # 找到第一个 { 与最后一个 }
    start = s.find("{")
    end = s.rfind("}")
    if start >= 0 and end > start:
        s = s[start:end + 1]
    return json.loads(s)


def build_structured_content(resource_type: str, raw: str, weak_kps: list[str]) -> dict:
    """把 LLM 原始输出转成统一的 structured_content。

    失败时根据 resource_type 兜底为最小可用结构。
    """
    try:
        obj = _safe_json_loads(raw)
    except Exception:
        obj = _fallback(resource_type, weak_kps)

    if resource_type == "customized_resource":
        return _norm_customized(obj, weak_kps)
    if resource_type == "practice_guide":
        return _norm_practice(obj, weak_kps)
    if resource_type == "tiered_quiz":
        return _norm_quiz(obj, weak_kps)
    raise ValueError(f"unsupported resource_type: {resource_type}")


def _fallback(resource_type: str, weak_kps: list[str]) -> dict:
    kp = weak_kps[0] if weak_kps else "kp_default"
    if resource_type == "customized_resource":
        return {"title": "讲解（兜底）", "sections": [{"kp_id": kp, "heading": "核心概念", "body": "切片不足，已用兜底内容"}]}
    if resource_type == "practice_guide":
        return {"title": "实操指南（兜底）", "steps": [{"order": 1, "title": "操作", "content": "按切片执行", "estimated_min": 10}], "tools": [], "troubleshooting": []}
    return {"title": "分阶测试（兜底）", "questions": [{"question": "占位", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "占位", "difficulty": 3, "kp_id": kp}]}


def _norm_customized(obj: dict, weak_kps: list[str]) -> dict:
    sections = obj.get("sections") or []
    normed = []
    for s in sections:
        if not isinstance(s, dict):
            continue
        normed.append({
            "kp_id": s.get("kp_id") or (weak_kps[0] if weak_kps else "kp_default"),
            "heading": str(s.get("heading", "")).strip() or "段落",
            "body": str(s.get("body", "")).strip(),
        })
    if not normed:
        normed = _fallback("customized_resource", weak_kps)["sections"]
    return {"title": str(obj.get("title", "定制化讲解")).strip(), "sections": normed}


def _norm_practice(obj: dict, weak_kps: list[str]) -> dict:
    steps = obj.get("steps") or []
    normed_steps = []
    for i, st in enumerate(steps, 1):
        if not isinstance(st, dict):
            continue
        normed_steps.append({
            "order": int(st.get("order", i)),
            "title": str(st.get("title", f"步骤{i}")).strip(),
            "content": str(st.get("content", "")).strip(),
            "estimated_min": int(st.get("estimated_min", 10) or 10),
        })
    if not normed_steps:
        normed_steps = _fallback("practice_guide", weak_kps)["steps"]
    return {
        "title": str(obj.get("title", "实操指南")).strip(),
        "steps": normed_steps,
        "tools": [str(t) for t in (obj.get("tools") or [])],
        "troubleshooting": [
            {"problem": str(t.get("problem", "")), "solution": str(t.get("solution", ""))}
            for t in (obj.get("troubleshooting") or []) if isinstance(t, dict)
        ],
    }


def _norm_quiz(obj: dict, weak_kps: list[str]) -> dict:
    qs = obj.get("questions") or []
    normed = []
    for i, q in enumerate(qs, 1):
        if not isinstance(q, dict):
            continue
        opts = q.get("options") or []
        normed.append({
            "question": str(q.get("question", f"题目{i}")).strip(),
            "options": [str(o) for o in opts][:4],
            "answer": str(q.get("answer", "A")).strip().upper()[:1] or "A",
            "explanation": str(q.get("explanation", "")).strip(),
            "difficulty": int(q.get("difficulty", 3) or 3),
            "kp_id": str(q.get("kp_id") or (weak_kps[0] if weak_kps else "kp_default")),
        })
    if not normed:
        normed = _fallback("tiered_quiz", weak_kps)["questions"]
    return {"title": str(obj.get("title", "分阶测试题")).strip(), "questions": normed}
