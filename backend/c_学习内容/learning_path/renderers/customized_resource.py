"""定制化资源（讲义）渲染器 — 输出 (html, markdown)。"""
from __future__ import annotations

from typing import Any

# 内联 CSS（移动端友好，代码块语法高亮用 <pre><code>）
_BASE_CSS = """
<style>
.cr-wrap{font-family:-apple-system,'Segoe UI',Roboto,'PingFang SC',sans-serif;color:#1f2937;line-height:1.75;max-width:880px;margin:0 auto;padding:24px;}
.cr-wrap *{box-sizing:border-box}
.cr-wrap h1{font-size:26px;border-bottom:2px solid #6366f1;padding-bottom:8px;color:#4338ca}
.cr-wrap h2{font-size:20px;margin-top:28px;color:#1e3a8a;border-left:4px solid #6366f1;padding-left:10px}
.cr-wrap h3{font-size:16px;margin-top:18px;color:#374151}
.cr-wrap .kp-tag{display:inline-block;background:#eef2ff;color:#4338ca;border-radius:12px;padding:2px 10px;font-size:12px;margin-right:6px}
.cr-wrap .section{background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;margin:14px 0}
.cr-wrap pre{background:#0f172a;color:#e2e8f0;padding:14px;border-radius:8px;overflow:auto;font-size:13px}
.cr-wrap code{font-family:'JetBrains Mono',Consolas,monospace;background:#f1f5f9;padding:1px 6px;border-radius:4px;font-size:13px}
.cr-wrap pre code{background:transparent;padding:0;color:inherit}
.cr-wrap .meta{color:#6b7280;font-size:13px;margin-bottom:16px}
.cr-wrap .meta b{color:#111827}
@media (max-width:640px){.cr-wrap{padding:14px}.cr-wrap h1{font-size:22px}.cr-wrap h2{font-size:18px}}
</style>
"""


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render(payload: dict, meta: dict) -> tuple[str, str]:
    title = payload.get("title") or meta.get("title") or "定制化讲解"
    sections = payload.get("sections", [])

    # markdown
    md_lines = [f"# {title}", ""]
    for s in sections:
        md_lines += [f"## {s.get('heading', '')}", "", s.get("body", ""), ""]
    md = "\n".join(md_lines).rstrip() + "\n"

    # html
    parts = [_BASE_CSS, '<div class="cr-wrap">', f"<h1>{_esc(title)}</h1>"]
    kps = meta.get("kp_coverage") or meta.get("kpCoverage") or []
    if kps:
        parts.append('<div class="meta"><b>覆盖知识点：</b>')
        parts.append("".join(f'<span class="kp-tag">{_esc(k)}</span>' for k in kps))
        parts.append("</div>")
    diff = meta.get("difficulty", 3)
    parts.append(f'<div class="meta"><b>难度：</b>{diff}/5 · <b>版本：</b>{meta.get("version", 1)}</div>')
    for s in sections:
        parts.append('<div class="section">')
        parts.append(f'<span class="kp-tag">{_esc(s.get("kp_id", ""))}</span>')
        parts.append(f"<h2>{_esc(s.get('heading', ''))}</h2>")
        body = _esc(s.get("body", "")).replace("\n\n", "</p><p>").replace("\n", "<br>")
        parts.append(f"<p>{body}</p>")
        parts.append("</div>")
    parts.append("</div>")
    return "\n".join(parts), md
