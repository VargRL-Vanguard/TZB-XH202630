"""
D-04：统一 AI 服务层。

职责：
  - 管理 3 个 AI Provider 实例（ChatAI / PathAI / SuggestAI）
  - 提供统一的 chat() / generate_path() / generate_suggestions() 入口
  - 负责 prompt 组装 + 上下文注入
  - 对外被 D-05 各业务接口调用
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from backend.公共.logger import get_logger
from backend.d_AI集成.config import d_config
from backend.d_AI集成.providers.chat_ai import ChatAIProvider
from backend.d_AI集成.providers.path_ai import PathAIProvider
from backend.d_AI集成.providers.suggest_ai import SuggestAIProvider
from backend.d_AI集成.prompt_templates import (
    CHAT_SYSTEM_PROMPT,
    CHAT_CONTEXT_PROMPT,
    PATH_SYSTEM_PROMPT,
    PATH_CONTEXT_PROMPT,
    SUGGEST_SYSTEM_PROMPT,
    SUGGEST_CONTEXT_PROMPT,
)

log = get_logger(__name__)

# 全局 Provider 实例（懒加载）
_chat_provider: Optional[ChatAIProvider] = None
_path_provider: Optional[PathAIProvider] = None
_suggest_provider: Optional[SuggestAIProvider] = None


def _get_chat_provider() -> ChatAIProvider:
    global _chat_provider
    if _chat_provider is None:
        _chat_provider = ChatAIProvider(
            api_key=d_config.CHAT_AI_API_KEY,
            endpoint=d_config.CHAT_AI_ENDPOINT,
            model=d_config.CHAT_AI_MODEL,
        )
    return _chat_provider


def _get_path_provider() -> PathAIProvider:
    global _path_provider
    if _path_provider is None:
        _path_provider = PathAIProvider(
            api_key=d_config.PATH_AI_API_KEY,
            endpoint=d_config.PATH_AI_ENDPOINT,
            model=d_config.PATH_AI_MODEL,
        )
    return _path_provider


def _get_suggest_provider() -> SuggestAIProvider:
    global _suggest_provider
    if _suggest_provider is None:
        _suggest_provider = SuggestAIProvider(
            api_key=d_config.SUGGEST_AI_API_KEY,
            endpoint=d_config.SUGGEST_AI_ENDPOINT,
            model=d_config.SUGGEST_AI_MODEL,
        )
    return _suggest_provider


async def chat(
    student_id: str,
    question: str,
    history: Optional[list[dict]] = None,
    profile: Optional[dict] = None,
) -> dict:
    """
    辅导对话。

    :return: {"content": str, "usage": dict, "model": str, "provider": str}
    """
    provider = _get_chat_provider()
    context = CHAT_CONTEXT_PROMPT.format(
        profile=json.dumps(profile or {}, ensure_ascii=False, indent=2),
        history=json.dumps(history or [], ensure_ascii=False, indent=2),
        question=question,
    )
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]
    return await provider.generate(messages)


async def generate_path(
    student_id: str,
    diagnosis: Optional[dict] = None,
    knowledge_chunks: Optional[list[dict]] = None,
) -> dict:
    """
    生成学习路径。

    :return: {"content": str, "usage": dict, "model": str, "provider": str}
    """
    provider = _get_path_provider()
    context = PATH_CONTEXT_PROMPT.format(
        diagnosis=json.dumps(diagnosis or {}, ensure_ascii=False, indent=2),
        knowledge_chunks=json.dumps(knowledge_chunks or [], ensure_ascii=False, indent=2),
    )
    messages = [
        {"role": "system", "content": PATH_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]
    return await provider.generate(messages)


async def generate_suggestions(
    student_id: str,
    diagnosis: Optional[dict] = None,
    activities: Optional[list[dict]] = None,
) -> dict:
    """
    生成学习建议。

    :return: {"content": str, "usage": dict, "model": str, "provider": str}
    """
    provider = _get_suggest_provider()
    context = SUGGEST_CONTEXT_PROMPT.format(
        diagnosis=json.dumps(diagnosis or {}, ensure_ascii=False, indent=2),
        activities=json.dumps(activities or [], ensure_ascii=False, indent=2),
    )
    messages = [
        {"role": "system", "content": SUGGEST_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]
    return await provider.generate(messages)