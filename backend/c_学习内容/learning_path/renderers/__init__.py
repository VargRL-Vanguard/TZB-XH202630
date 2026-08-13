"""3 个渲染器（C-05）。

统一接口 `render(resource_like) -> {"html", "markdown", "structuredData"}`。
- html: 内联 CSS 样式，前端无需额外样式表
- markdown: 原始 markdown（备用导出）
- structuredData: TOC + 元信息
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from . import customized_resource, practice_guide, tiered_quiz

__all__ = ["render", "RENDERERS"]


RENDERERS = {
    "customized_resource": customized_resource.render,
    "practice_guide": practice_guide.render,
    "tiered_quiz": tiered_quiz.render,
}


def _extract_payload(resource: Any) -> dict:
    """兼容 Resource ORM / dict / pydantic 多种入参。"""
    if hasattr(resource, "structured_content") and resource.structured_content:
        return dict(resource.structured_content)
    if hasattr(resource, "content") and resource.content:
        if isinstance(resource.content, str):
            try:
                return json.loads(resource.content)
            except Exception:
                return {"raw": resource.content}
        return dict(resource.content)
    if isinstance(resource, dict):
        if resource.get("structured_content"):
            return dict(resource["structured_content"])
        if resource.get("content"):
            c = resource["content"]
            if isinstance(c, str):
                try:
                    return json.loads(c)
                except Exception:
                    return {"raw": c}
            return dict(c)
        return dict(resource)
    return {}


def _meta(resource: Any) -> dict:
    """从 resource 提取元信息。"""
    out: dict = {}
    for k in ("resource_id", "resourceId", "student_id", "studentId",
              "type", "title", "difficulty", "kp_coverage", "kpCoverage",
              "cited_chunks", "citedChunks", "version", "generated_at", "generatedAt",
              "trigger_reason", "triggerReason"):
        if hasattr(resource, k):
            out[k] = getattr(resource, k)
        elif isinstance(resource, dict) and k in resource:
            out[k] = resource[k]
    if "generatedAt" not in out and "generated_at" not in out:
        out["generatedAt"] = datetime.now(timezone.utc).isoformat()
    return out


def render(resource: Any) -> dict[str, Any]:
    """统一渲染入口。

    输入：Resource ORM / dict / pydantic（必须含 type 字段）
    输出：{"html", "markdown", "structuredData"}
    """
    payload = _extract_payload(resource)
    meta = _meta(resource)
    rtype = meta.get("type") or (resource.get("type") if isinstance(resource, dict) else "customized_resource")
    fn = RENDERERS.get(rtype)
    if fn is None:
        raise ValueError(f"未知 resource.type={rtype!r}")

    html, markdown = fn(payload, meta)
    toc = _build_toc(rtype, payload)
    return {
        "html": html,
        "markdown": markdown,
        "structuredData": {
            "type": rtype,
            "toc": toc,
            "meta": {
                "resourceId": meta.get("resource_id") or meta.get("resourceId", ""),
                "title": meta.get("title", ""),
                "difficulty": meta.get("difficulty", 3),
                "kpCoverage": meta.get("kp_coverage") or meta.get("kpCoverage", []),
                "citedChunks": meta.get("cited_chunks") or meta.get("citedChunks", []),
                "version": meta.get("version", 1),
                "generatedAt": meta.get("generatedAt") or meta.get("generated_at", ""),
                "triggerReason": meta.get("trigger_reason") or meta.get("triggerReason", ""),
            },
        },
    }


def _build_toc(rtype: str, payload: dict) -> list[dict]:
    if rtype == "customized_resource":
        return [{"id": f"sec-{i}", "title": s.get("heading", "")} for i, s in enumerate(payload.get("sections", []))]
    if rtype == "practice_guide":
        return [{"id": f"step-{s.get('order', i)}", "title": s.get("title", "")} for i, s in enumerate(payload.get("steps", []))]
    if rtype == "tiered_quiz":
        return [{"id": f"q-{i}", "title": f"Q{i + 1}: {q.get('question', '')[:24]}"} for i, q in enumerate(payload.get("questions", []))]
    return []
