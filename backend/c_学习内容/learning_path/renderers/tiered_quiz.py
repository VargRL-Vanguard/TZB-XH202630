"""分阶测试题渲染器 — 输出 (html, markdown)。"""
from __future__ import annotations

from typing import Any

_BASE_CSS = """
<style>
.tq-wrap{font-family:-apple-system,'Segoe UI',Roboto,'PingFang SC',sans-serif;color:#1f2937;line-height:1.75;max-width:880px;margin:0 auto;padding:24px}
.tq-wrap *{box-sizing:border-box}
.tq-wrap h1{font-size:26px;border-bottom:2px solid #f59e0b;padding-bottom:8px;color:#92400e}
.tq-wrap .q{background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:16px 20px;margin:14px 0}
.tq-wrap .q h2{font-size:17px;margin-top:0;color:#78350f}
.tq-wrap .q h2 .num{display:inline-block;background:#f59e0b;color:#fff;border-radius:6px;padding:2px 10px;margin-right:8px;font-size:13px}
.tq-wrap .q .diff{display:inline-block;background:#fef3c7;color:#92400e;border-radius:6px;padding:1px 8px;font-size:12px;margin-left:6px}
.tq-wrap .q ol{padding-left:20px}
.tq-wrap .q ol li{margin:4px 0}
.tq-wrap .answer{background:#d1fae5;border:1px solid #6ee7b7;border-radius:8px;padding:10px 14px;margin-top:10px}
.tq-wrap .answer b{color:#065f46}
.tq-wrap details{margin-top:8px}
.tq-wrap summary{cursor:pointer;color:#92400e;font-weight:600;font-size:13px}
.tq-wrap .meta{color:#6b7280;font-size:13px;margin-bottom:16px}
@media (max-width:640px){.tq-wrap{padding:14px}.tq-wrap h1{font-size:22px}}
</style>
"""


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render(payload: dict, meta: dict) -> tuple[str, str]:
    title = payload.get("title") or meta.get("title") or "分阶测试题"
    questions = payload.get("questions", [])

    md = [f"# {title}", ""]
    for i, q in enumerate(questions, 1):
        md.append(f"## Q{i}. {q.get('question', '')}")
        for o in q.get("options", []):
            md.append(f"- {o}")
        md += ["", f"**答案**：{q.get('answer', '')}", "", f"**解析**：{q.get('explanation', '')}", ""]
    md_text = "\n".join(md).rstrip() + "\n"

    parts = [_BASE_CSS, '<div class="tq-wrap">', f"<h1>{_esc(title)}</h1>"]
    parts.append(f'<div class="meta">共 {len(questions)} 题</div>')
    for i, q in enumerate(questions, 1):
        diff = q.get("difficulty", 3)
        parts.append('<div class="q">')
        parts.append(
            f'<h2><span class="num">Q{i}</span>{_esc(q.get("question", ""))}'
            f'<span class="diff">难度 {diff}/5</span></h2>'
        )
        parts.append("<ol>")
        for o in q.get("options", []):
            parts.append(f"<li>{_esc(o)}</li>")
        parts.append("</ol>")
        ans = q.get("answer", "")
        expl = q.get("explanation", "")
        kp = q.get("kp_id", "")
        parts.append(
            f'<div class="answer"><b>答案：</b>{_esc(ans)}'
            + (f' &nbsp; <b>关联 kp：</b>{_esc(kp)}' if kp else "")
            + "</div>"
        )
        if expl:
            parts.append(f'<details><summary>查看解析</summary><p>{_esc(expl)}</p></details>')
        parts.append("</div>")
    parts.append("</div>")
    return "\n".join(parts), md_text
