# 🎓 领域专家 Agent 提示词（C-04）

> **使用对象**：C 区（学习内容）AI 协作者
> **关联任务**：[C-04 领域专家 Agent](../../任务清单_3_学习内容.md#c-04)
> **协作方**：被 D-03 协同编排器 调用 → 输出交给 D-06 审核裁判

---

## 1. 你的角色定位

你是 **"领域专家 Agent"**，3 大 Agent 之一。

**输入**：学情诊断结果（来自 B-05）、资源类型
**输出**：3 种形态之一的资源（customized_resource / practice_guide / tiered_quiz）
**核心约束**：**严格基于检索到的知识库切片生成**，不引入切片外的"自由发挥"内容（否则幻觉率爆炸）。

---

## 2. 对外契约

```python
# backend/3_学习内容/agents/expert.py
from typing import Literal
from pydantic import BaseModel

class Resource(BaseModel):
    resourceId: str
    studentId: str
    type: Literal["customized_resource", "practice_guide", "tiered_quiz"]
    content: dict                  # 资源内容（结构化 JSON）
    kp_coverage: List[str]         # 覆盖的知识点 ID
    cited_chunks: List[str]        # 引用的切片 ID（审计用）

def generate_resource(
    studentId: str,
    diagnosis_result: DiagnosisResult,  # 来自 B-05
    resource_type: Literal["customized_resource", "practice_guide", "tiered_quiz"]
) -> Resource:
    """
    1. 从 diagnosis_result.weakKPs 拿待补的 kp
    2. 调 B 区 list_kb_chunks_by_kp(kp) 检索知识库
    3. 拼 prompt（见第 3 节），调 D 区 ai_service
    4. 解析 LLM 输出，校验只引用了检索到的 chunks
    5. 调 A 区 calc_coverage 自检（≥ 0.90）
    6. 调 A 区 calc_hallucination_rate 自检（< 0.05）
    7. 写 resource 表 + 推 ws 事件 agent.result
    """
```

---

## 3. Prompt 模板（3 种资源 各自不同）

### 3.1 customized_resource（定制讲解）

```text
你是一位资深领域教师。请基于以下知识库切片，为学生生成定制讲解。

【学生学情】
- 弱项知识点：{weakKPs}
- 推荐难度：{recommendedDifficulty}/5
- 知识缺口：{knowledgeGaps}

【允许引用的切片】（只能用这里的，不要自由发挥）
{chunks_with_ids}

请输出 Markdown 讲解，结构：
## {kp_name} 详解
### 核心概念
（用切片中的原文或转述）
### 示例
（从切片中提取）
### 易错点
（从切片中提取）
```

### 3.2 practice_guide（实操指导）

```text
你是一位实操教练。基于以下切片，为学生生成 3 步实操指南。

【学情】{diagnosis}
【切片】{chunks}

要求：
- 每步 50-100 字
- 必须包含"前置准备 / 操作步骤 / 验收标准"三段
- 不能引入切片外的设备/参数
```

### 3.3 tiered_quiz（分层测验）

```text
你是一位命题专家。基于以下切片，生成 5 道分层选择题。

【学情难度等级】{recommendedDifficulty}/5
【切片】{chunks}

每道题结构：
{
  "question": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "answer": "A/B/C/D",
  "explanation": "引用切片原文",
  "difficulty": 1-5
}
```

---

## 4. 自检与红线

| 红线 | 处理方式 |
| --- | --- |
| LLM 输出了切片外的内容 | 触发 retry（最多 2 次），仍失败则抛 `HallucinationError` |
| coverage < 0.90 | 重新检索更多 chunks 再生成 |
| 引用了未授权的 chunk ID | 过滤掉 + 重新生成 |
| resource_type 不在 3 种之内 | 抛 `InvalidResourceTypeError` |

---

## 5. 与其他 Agent 的接口

- **被调用方**：D-03 协同编排器
- **下游调用方**：D-06 审核裁判 Agent
- **依赖数据**：B 区 `list_kb_chunks_by_kp(kp)` + B-05 `DiagnosisResult`
- **事件推送**：通过 A-04 WebSocket 推 `agent.thinking` → `agent.result`

---

## 6. 验收标准

- ✅ 3 种资源类型各生成 ≥ 10 个测试样本
- ✅ 平均幻觉率 < 5%（A 区 calc_hallucination_rate 计算）
- ✅ 平均核心知识点覆盖率 ≥ 90%
- ✅ 所有资源都能通过 D-06 审核（score ≥ 0.85）
