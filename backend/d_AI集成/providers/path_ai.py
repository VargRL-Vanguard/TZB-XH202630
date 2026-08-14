"""
D-02：PathAIProvider — 学习路径生成 AI。

对应 D-05 的 path/ai_result.py 调用。
"""
from __future__ import annotations

from backend.d_AI集成.providers.base import BaseAIProvider


class PathAIProvider(BaseAIProvider):
    """学习路径生成 AI Provider。"""

    provider_name = "PathAI"

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: list[dict], **kwargs) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.5),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": False,
        }

    def _parse_response(self, response_data: dict) -> dict:
        choices = response_data.get("choices", [])
        if not choices:
            return {"content": "", "usage": {}, "raw": response_data}
        msg = choices[0].get("message", {})
        return {
            "content": msg.get("content", ""),
            "usage": response_data.get("usage", {}),
            "raw": response_data,
        }