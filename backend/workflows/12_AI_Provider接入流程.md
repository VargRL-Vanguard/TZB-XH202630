# 工作流程 12：AI Provider 接入流程（**D 区 3 个 AI 专用**）

> 3 个 AI 服务（AI 辅导 / AI 路径生成 / AI 建议生成）**必须能切换**。
> 本流程严格定义接入步骤，**防止 AI 在 provider 抽象上产生幻觉**。

---

## 前置条件

- D-00 数据层完成
- 3 个 AI 服务的 key / endpoint 已申请
- 已加入 `.env`（**不要** hardcode 到代码）

---

## 步骤 1：写抽象基类

**输入**：3 个 AI 服务的接口文档

**操作**：`backend/4_AI集成/providers/base.py`
```python
from abc import ABC, abstractmethod
from typing import List

class BaseAIProvider(ABC):
    """
    所有 AI provider 必须实现这两个方法
    """
    @abstractmethod
    def chat(self, messages: List[dict], **kwargs) -> str:
        """
        多轮对话
        messages: [{"role": "user|assistant|system", "content": "..."}]
        返回: AI 生成的文本
        """
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        文本向量化（可选，部分 provider 不支持）
        返回: 浮点数列表
        """
        pass
```

**输出**：1 个抽象基类

**验证**：
- [ ] 任何继承类必须实现 `chat` 和 `embed`
- [ ] 不实现的子类无法实例化（Python ABC 强制）

**失败处理**：方法签名不匹配 → 检查 `**kwargs` 是否接住

---

## 步骤 2：写 3 个具体 provider

**输入**：3 个 AI 服务的官方 SDK / API 文档

**操作**：`backend/4_AI集成/providers/`

### 2.1 chat_ai.py

```python
from backend.4_AI集成.providers.base import BaseAIProvider

class ChatAIProvider(BaseAIProvider):
    def __init__(self, api_key, endpoint):
        self.api_key = api_key
        self.endpoint = endpoint
    
    def chat(self, messages, **kwargs):
        # 调用具体 AI 服务（OpenAI / Qwen / GLM / ...）
        # 严格按官方 SDK 文档
        return response_text
    
    def embed(self, text):
        # 调用 embedding API
        return embedding_vector
```

### 2.2 path_ai.py

（与 chat_ai.py 结构一致，可继承或独立）

### 2.3 suggest_ai.py

（与 chat_ai.py 结构一致，可继承或独立）

**输出**：3 个具体 provider 类

**验证**：
- [ ] 每个 provider 都能独立 `python -c "from backend.4_AI集成.providers.chat_ai import ChatAIProvider; p = ChatAIProvider(...)"`
- [ ] mock 测试 1 个 chat 调用 → 返回 string

**详细提示**：[`prompts/04_成员D_AI集成_提示词.md`](../prompts/04_成员D_AI集成_提示词.md) 第 4 节

**失败处理**：API 报错 → 检查 key 是否过期 / endpoint 是否正确

---

## 步骤 3：写 provider 工厂

**输入**：3 个 provider 类 + 配置

**操作**：`backend/4_AI集成/providers/factory.py`
```python
import os
from backend.4_AI集成.providers.chat_ai import ChatAIProvider
from backend.4_AI集成.providers.path_ai import PathAIProvider
from backend.4_AI集成.providers.suggest_ai import SuggestAIProvider

def get_chat_provider():
    provider_name = os.getenv("AI_CHAT_PROVIDER", "openai")
    if provider_name == "openai":
        return ChatAIProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            endpoint="https://api.openai.com/v1/chat/completions"
        )
    elif provider_name == "qwen":
        return ChatAIProvider(
            api_key=os.getenv("QWEN_API_KEY"),
            endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        )
    # ... 其他 provider
    raise ValueError(f"Unknown AI_CHAT_PROVIDER: {provider_name}")
```

**输出**：3 个工厂函数

**验证**：
- [ ] 改 `.env` 中 `AI_CHAT_PROVIDER` → 服务行为变化
- [ ] 未知 provider → 抛 `ValueError`（**不要**默认用错的服务）

**失败处理**：环境变量缺失 → 在 `.env.example` 中标注必填项

---

## 步骤 4：写统一调用层

**输入**：provider 工厂

**操作**：`backend/4_AI集成/services/ai_service.py`
```python
from backend.4_AI集成.providers.factory import get_chat_provider

def chat_with_prompt(prompt: str, system: str = "", **kwargs) -> str:
    """
    B-05 / C-04 / D-06 都用这个函数
    """
    provider = get_chat_provider()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return provider.chat(messages, **kwargs)
```

**输出**：3 个统一函数（chat_with_prompt / chat_with_history / embed_text）

**验证**：
- [ ] B-05 / C-04 / D-06 都能 `from backend.4_AI集成.services.ai_service import chat_with_prompt`
- [ ] 切换 provider 不需要改业务代码

**失败处理**：provider 报错 → fallback 到下一个 provider（重试 1 次）

---

## 步骤 5：写 fallback 机制

**输入**：3 个 provider

**操作**：
```python
def chat_with_fallback(prompt, system="", **kwargs):
    """
    主 provider 失败 → fallback
    """
    primary = os.getenv("AI_CHAT_PRIMARY", "openai")
    fallback = os.getenv("AI_CHAT_FALLBACK", "qwen")
    
    for provider_name in [primary, fallback]:
        try:
            return _call_provider(provider_name, prompt, system, **kwargs)
        except Exception as e:
            log_error(f"Provider {provider_name} failed: {e}")
            continue
    
    raise AllProvidersFailedError("All AI providers failed")
```

**输出**：1 个 fallback 函数

**验证**：
- [ ] 主 provider 故意配错 → fallback 接住
- [ ] 全部失败 → 抛 `AllProvidersFailedError`

**失败处理**：fallback 也失败 → 群里报告，**不要**静默

---

## 步骤 6：写单元测试（mock）

**输入**：3 个 provider + 工厂 + 调用层

**操作**：`tests/test_ai_service.py`
```python
import pytest
from unittest.mock import patch, MagicMock

def test_chat_with_prompt():
    with patch("backend.4_AI集成.providers.factory.get_chat_provider") as mock:
        mock_provider = MagicMock()
        mock_provider.chat.return_value = "test response"
        mock.return_value = mock_provider
        
        result = chat_with_prompt("hello", system="sys")
        assert result == "test response"
        mock_provider.chat.assert_called_once()
```

**输出**：≥ 3 个测试

**验证**：
- [ ] `pytest tests/test_ai_service.py` 全过
- [ ] 覆盖率 ≥ 80%

---

## 步骤 7：加监控 / 日志

**输入**：ai_service

**操作**：在 chat_with_prompt 里加：
```python
import time
import logging

def chat_with_prompt(prompt, system="", **kwargs):
    start = time.time()
    provider = get_chat_provider()
    try:
        result = provider.chat(...)
        log_metric("ai_chat_latency", time.time() - start)
        log_metric("ai_chat_tokens", count_tokens(result))
        return result
    except Exception as e:
        log_error(f"AI chat failed: {e}")
        raise
```

**输出**：1 份监控日志

**验证**：
- [ ] 每次 AI 调用都有 latency / tokens 记录
- [ ] 错误有 stack trace

**详细提示**：[`prompts/04_成员D_AI集成_提示词.md`](../prompts/04_成员D_AI集成_提示词.md) 第 4 节

---

## AI Provider 验收清单

- [ ] 步骤 1：BaseAIProvider 抽象基类
- [ ] 步骤 2：3 个具体 provider
- [ ] 步骤 3：工厂函数（按配置切换）
- [ ] 步骤 4：统一调用层 ai_service
- [ ] 步骤 5：fallback 机制
- [ ] 步骤 6：单元测试全过
- [ ] 步骤 7：监控 / 日志

**全部通过 = AI 接入层就绪，B/C/D 可放心调用**
