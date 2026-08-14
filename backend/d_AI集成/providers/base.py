"""
D-01：BaseAIProvider 抽象基类。

验收标准：
  ✅ 统一接口：generate(messages, **kwargs) -> dict
  ✅ 强制子类实现 _build_payload / _parse_response / _get_headers
  ✅ 内置重试（最多 3 次）+ 超时控制
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from backend.公共.logger import get_logger

log = get_logger(__name__)

# 默认超时（秒）
DEFAULT_TIMEOUT = 60.0
# 最大重试次数
MAX_RETRIES = 3
# 重试间隔基数（秒）
RETRY_BASE_DELAY = 1.0


class AIProviderError(Exception):
    """AI Provider 统一异常。"""
    def __init__(self, message: str, provider: str = "", status_code: int = 0):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class BaseAIProvider(ABC):
    """
    AI Provider 抽象基类。

    子类必须实现：
      - _get_headers() -> dict
      - _build_payload(messages, **kwargs) -> dict
      - _parse_response(response_data: dict) -> dict
    """

    provider_name: str = "base"

    def __init__(self, api_key: str, endpoint: str, model: str, timeout: float = DEFAULT_TIMEOUT):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    @abstractmethod
    def _get_headers(self) -> dict:
        """构建请求头。"""
        ...

    @abstractmethod
    def _build_payload(self, messages: list[dict], **kwargs) -> dict:
        """构建请求体。"""
        ...

    @abstractmethod
    def _parse_response(self, response_data: dict) -> dict:
        """
        解析 AI 返回的原始响应。
        返回：{"content": str, "usage": dict, "raw": dict}
        """
        ...

    async def generate(
        self,
        messages: list[dict],
        *,
        retries: int = MAX_RETRIES,
        **kwargs,
    ) -> dict:
        """
        统一生成入口（含重试 + 超时）。

        :param messages: OpenAI 格式消息列表 [{"role":"user","content":"..."}]
        :param retries: 最大重试次数
        :return: {"content": str, "usage": dict, "model": str, "provider": str}
        """
        if not self.api_key or not self.endpoint:
            raise AIProviderError(
                f"{self.provider_name} 未配置 API Key 或 Endpoint",
                provider=self.provider_name,
            )

        payload = self._build_payload(messages, **kwargs)
        headers = self._get_headers()

        last_error: Optional[Exception] = None
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        self.endpoint,
                        json=payload,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    parsed = self._parse_response(data)
                    parsed["provider"] = self.provider_name
                    parsed["model"] = self.model
                    return parsed
            except httpx.HTTPStatusError as e:
                last_error = AIProviderError(
                    f"{self.provider_name} HTTP {e.response.status_code}: {e.response.text[:200]}",
                    provider=self.provider_name,
                    status_code=e.response.status_code,
                )
                if e.response.status_code in (429, 503):
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    log.warning(f"{self.provider_name} 限流/不可用，{delay}s 后重试 (attempt={attempt+1})")
                    await asyncio.sleep(delay)
                    continue
                raise last_error
            except httpx.TimeoutException as e:
                last_error = AIProviderError(
                    f"{self.provider_name} 请求超时 ({self.timeout}s)",
                    provider=self.provider_name,
                )
                if attempt < retries - 1:
                    await asyncio.sleep(RETRY_BASE_DELAY)
                    continue
                raise last_error
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    await asyncio.sleep(RETRY_BASE_DELAY)
                    continue
                raise AIProviderError(
                    f"{self.provider_name} 未知错误: {e}",
                    provider=self.provider_name,
                )

        raise last_error or AIProviderError("未知错误", provider=self.provider_name)