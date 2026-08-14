"""
D-02：EmbedAIProvider — 知识库 Embedding 检索 AI。

用于知识库切片的向量化检索，支持单文本和批量文本。
"""
from __future__ import annotations

from backend.d_AI集成.providers.base import BaseAIProvider, AIProviderError


class EmbedAIProvider(BaseAIProvider):
    """Embedding AI Provider。"""

    provider_name = "EmbedAI"

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: list[dict], **kwargs) -> dict:
        raise NotImplementedError("EmbedAI 使用 embed() 接口，不支持 generate()")

    def _parse_response(self, response_data: dict) -> dict:
        raise NotImplementedError("EmbedAI 使用 embed() 接口，不支持 generate()")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        对文本列表做 embedding。

        :param texts: 待向量化的文本列表
        :return: 向量列表 [[float, ...], ...]
        """
        if not self.api_key or not self.endpoint:
            raise AIProviderError(
                f"{self.provider_name} 未配置 API Key 或 Endpoint",
                provider=self.provider_name,
            )

        import httpx

        headers = self._get_headers()
        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        embeddings = []
        for item in data.get("data", []):
            embeddings.append(item.get("embedding", []))
        return embeddings

    async def embed_single(self, text: str) -> list[float]:
        """单文本 embedding。"""
        result = await self.embed([text])
        return result[0] if result else []