"""实操指南渲染器 — 输出 (html, markdown)。"""
from __future__ import annotations

from typing import Any

_BASE_CSS = """
<style>
.pg-wrap{font-family:-apple-system,'Segoe UI',Roboto,'PingFang SC',sans-serif;color:#1f2937;line-height:1.75;max-width:880px;margin:0 auto;padding:24px}
.pg-wrap *{box-sizing:border-box}
.pg-wrap h1{font-size:26px;border-bottom:2px solid #10b981;padding-bottom:8px;color:#065f46}
.pg-wrap .step{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px 20px;margin:14px 0;position:relative}
.pg-wrap .step h2{font-size:18px;color:#065f46;margin-top:0}
.pg-wrap .step h2 .order{display:inline-block;background:#10b981;color:#fff;border-radius:50%;width:28px;height:28px;line-height:28px;text-align:center;margin-right:10px;font-size:14px}
.pg-wrap .tools{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:10px 14px;margin:12px 0}
.pg-wrap .tools b{color:#92400e}
.pg-wrap .faq{background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:12px 16px;margin:8px 0}
.pg-wrap .faq b{color:#991b1b}
.pg-wrap pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow:auto;font-size:13px}
.pg-wrap .meta{color:#6b7280;font-size:13px;margin-bottom:16px}
@media (max-width:640px){.pg-wrap{padding:14px}.pg-wrap h1{font-size:22px}}
</style>
"""


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render(payload: dict, meta: dict) -> tuple[str, str]:
    title = payload.get("title") or meta.get("title") or "实操指南"
    steps = payload.get("steps", [])
    tools = payload.get("tools", [])
    troubleshooting = payload.get("troubleshooting", [])

    md = [f"# {title}", ""]
    if tools:
        md.append(f"**工具**：{', '.join(tools)}\n")
    for s in steps:
        md += [f"## {s.get('order', '?')}. {s.get('title', '')}", "", s.get("content", ""), ""]
    if troubleshooting:
        md.append("## 排错 FAQ")
        for t in troubleshooting:
            md += [f"- **{t.get('problem', '')}** — {t.get('solution', '')}", ""]
    md_text = "\n".join(md).rstrip() + "\n"

    parts = [_BASE_CSS, '<div class="pg-wrap">', f"<h1>{_esc(title)}</h1>"]
    diff = meta.get("difficulty", 3)
    parts.append(f'<div class="meta"><b>难度：</b>{diff}/5 · <b>步骤数：</b>{len(steps)}</div>')
    if tools:
        parts.append('<div class="tools"><b>工具：</b>')
        parts.append(" · ".join(_esc(t) for t in tools))
        parts.append("</div>")
    for s in steps:
        parts.append('<div class="step">')
        parts.append(
            f'<h2><span class="order">{s.get("order", "?")}</span>{_esc(s.get("title", ""))}</h2>'
        )
        parts.append(f"<p>{_esc(s.get('content', ''))}</p>")
        est = s.get("estimated_min")
        if est:
            parts.append(f'<div class="meta">预计 {est} 分钟</div>')
        parts.append("</div>")
    if troubleshooting:
        parts.append("<h2>排错 FAQ</h2>")
        for t in troubleshooting:
            parts.append(
                f'<div class="faq"><b>{_esc(t.get("problem", ""))}</b><br>{_esc(t.get("solution", ""))}</div>'
            )
    parts.append("</div>")
    return "\n".join(parts), md_text
