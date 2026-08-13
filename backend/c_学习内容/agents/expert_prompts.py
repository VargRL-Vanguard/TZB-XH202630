"""领域专家 Agent Prompt 模板（与 11_领域专家Agent_提示词.md §3 完全一致）。"""
# version: 0.1

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPTS: dict[str, str] = {
    "customized_resource": "你是一位资深领域教师。请仅基于提供的知识库切片生成内容，禁止自由发挥。",
    "practice_guide": "你是一位实操教练。请仅基于提供的知识库切片生成 3 步实操指南，禁止引入切片外内容。",
    "tiered_quiz": "你是一位命题专家。请仅基于提供的知识库切片生成 5 道分层选择题，每题 explanation 必须引用切片原文。",
}


def _render_chunks(chunks: list[dict]) -> str:
    """把 chunks 渲染为 prompt 中的 'chunks_with_ids' 段。"""
    lines = []
    for c in chunks:
        cid = c.get("chunk_id", "unknown")
        kp = c.get("kp_id", "")
        text = (c.get("text") or "").strip()
        if len(text) > 800:  # 限长，避免 prompt 爆炸
            text = text[:800] + "..."
        lines.append(f"[{cid}] (kp={kp})\n{text}")
    return "\n\n".join(lines) if lines else "(无切片)"


def build_prompt(
    resource_type: str,
    diagnosis: Any,
    chunks: list[dict],
    difficulty: int = 3,
) -> str:
    """按 11_领域专家Agent_提示词.md §3 拼 prompt。"""
    weak_kps = getattr(diagnosis, "weak_kps", None) or getattr(diagnosis, "weakKPs", None) or []
    knowledge_gaps = (
        getattr(diagnosis, "knowledge_gaps", None) or getattr(diagnosis, "knowledgeGaps", None) or []
    )
    if isinstance(weak_kps, str):
        weak_kps = [weak_kps]

    chunks_text = _render_chunks(chunks)

    if resource_type == "customized_resource":
        return _build_customized_resource_prompt(weak_kps, knowledge_gaps, difficulty, chunks_text)
    if resource_type == "practice_guide":
        return _build_practice_guide_prompt(weak_kps, knowledge_gaps, chunks_text)
    if resource_type == "tiered_quiz":
        return _build_tiered_quiz_prompt(weak_kps, difficulty, chunks_text)
    raise ValueError(f"unsupported resource_type: {resource_type}")


def _build_customized_resource_prompt(weak_kps, knowledge_gaps, difficulty, chunks_text: str) -> str:
    return f"""你是一位资深领域教师。请基于以下知识库切片，为学生生成定制讲解。

【学生学情】
- 弱项知识点：{json.dumps(weak_kps, ensure_ascii=False)}
- 推荐难度：{difficulty}/5
- 知识缺口：{json.dumps(knowledge_gaps, ensure_ascii=False)}

【允许引用的切片】（只能用这里的，不要自由发挥）
{chunks_text}

请输出 JSON（**仅** JSON，不要包裹 markdown 标记）：
{{
  "title": "...",
  "sections": [
    {{"kp_id": "kp_xxx", "heading": "核心概念", "body": "..."}},
    {{"kp_id": "kp_xxx", "heading": "示例", "body": "..."}},
    {{"kp_id": "kp_xxx", "heading": "易错点", "body": "..."}}
  ]
}}
"""


def _build_practice_guide_prompt(weak_kps, knowledge_gaps, chunks_text: str) -> str:
    return f"""你是一位实操教练。基于以下切片，为学生生成 3 步实操指南。

【学情】弱项：{json.dumps(weak_kps, ensure_ascii=False)}；缺口：{json.dumps(knowledge_gaps, ensure_ascii=False)}
【切片】
{chunks_text}

要求：
- 每步 50-100 字
- 必须包含"前置准备 / 操作步骤 / 验收标准"三段
- 不能引入切片外的设备/参数
- 仅输出 JSON：
{{
  "title": "...",
  "steps": [
    {{"order": 1, "title": "前置准备", "content": "...", "estimated_min": 5}},
    {{"order": 2, "title": "操作步骤", "content": "...", "estimated_min": 20}},
    {{"order": 3, "title": "验收标准", "content": "...", "estimated_min": 5}}
  ],
  "tools": ["..."],
  "troubleshooting": [{{"problem": "...", "solution": "..."}}]
}}
"""


def _build_tiered_quiz_prompt(weak_kps, difficulty: int, chunks_text: str) -> str:
    return f"""你是一位命题专家。基于以下切片，生成 5 道分层选择题。

【学情难度等级】{difficulty}/5
【弱项 kp】{json.dumps(weak_kps, ensure_ascii=False)}
【切片】
{chunks_text}

每道题结构：
{{
  "question": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "answer": "A/B/C/D",
  "explanation": "引用切片原文",
  "difficulty": 1-5,
  "kp_id": "..."
}}

仅输出 JSON：{{"title":"...","questions":[...]}}
"""
