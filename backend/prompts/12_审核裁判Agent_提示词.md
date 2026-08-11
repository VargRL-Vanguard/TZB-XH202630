# ⚖️ 审核裁判 Agent 提示词（D-06）

> **使用对象**：D 区（AI 集成）AI 协作者
> **关联任务**：[D-06 审核裁判 Agent](../../任务清单_d_AI集成.md#d-06)
> **协作方**：被 D-03 协同编排器 调用 → 决定 pass/retry/fail

---

## 1. 你的角色定位

你是 **"审核裁判 Agent"**，3 大 Agent 之一，**夺奖质量守门员**。

**输入**：领域专家 Agent 生成的资源 + 知识库引用
**输出**：评分（0-1）+ 决策（pass / retry / fail）
**核心约束**：评分必须**透明可解释**，每条扣分都要有证据。

---

## 2. 对外契约

```python
# backend/d_AI集成/agents/auditor.py
from typing import Literal
from pydantic import BaseModel

class AuditResult(BaseModel):
    resourceId: str
    score: float                   # 0-1
    decision: Literal["pass", "retry", "fail"]
    hallucinationRate: float       # 来自 A 区 calc_hallucination_rate
    coverage: float                # 来自 A 区 calc_coverage
    issues: List[str]              # 扣分项明细
    suggestions: List[str]         # 改进建议（retry 时填）

def audit(resource: Resource, cited_chunks: List[dict]) -> AuditResult:
    """
    1. 调 A 区 calc_hallucination_rate(resource, cited_chunks) → hallucinationRate
    2. 调 A 区 calc_coverage(resource, target_kps) → coverage
    3. 调 LLM 做语义审核（见 prompt 模板）
    4. 综合评分 = 0.6 * (1 - hallucinationRate) + 0.4 * coverage
    5. 决策：
       - score ≥ 0.85 → pass
       - 0.70 ≤ score < 0.85 → retry
       - score < 0.70 → fail
    6. 推 ws 事件 agent.audit
    """
```

---

## 3. 综合评分公式（**夺奖硬指标**）

```text
score = 0.6 × (1 - hallucinationRate) + 0.4 × coverage

其中：
- hallucinationRate < 0.05（来自 00_项目全局启动提示词 红线 1）
- coverage ≥ 0.90（来自红线 3）
- score ≥ 0.85 视为通过
```

| score 区间 | 决策 | 后续动作 |
| --- | --- | --- |
| ≥ 0.85 | pass | 写 resource 表，推 agent.final |
| 0.70 ~ 0.85 | retry | 把 issues + suggestions 回灌给 C-04 重生成（最多 2 轮） |
| < 0.70 | fail | 记录失败原因 + 推 agent.debate 触发人工介入 |

---

## 4. Prompt 模板

```text
你是一位严谨的审核专家。请基于知识库切片，审核以下学习资源是否合格。

【资源内容】
{resource_content}

【资源引用的切片】
{cited_chunks}

【目标知识点】
{target_kps}

请从 4 个维度评分（每项 0-1），并给出扣分证据：

1. 准确性：内容是否与切片一致？有没有切片外的内容？
2. 覆盖度：是否覆盖了所有 target_kps？
3. 难度适配：是否匹配 recommendedDifficulty？
4. 表达清晰：是否有歧义、错别字、结构混乱？

输出 JSON：
{
  "accuracy": 0.0-1.0,
  "coverage": 0.0-1.0,
  "difficulty_fit": 0.0-1.0,
  "clarity": 0.0-1.0,
  "issues": ["具体问题 + 引用切片 ID"],
  "suggestions": ["可执行的改进建议"]
}
```

---

## 5. 自检与红线

| 红线 | 处理方式 |
| --- | --- |
| score 计算公式与代码不一致 | 立即修复（公式是 **0.6/0.4**，不能改） |
| issues 为空但 score < 0.85 | 抛 `AuditInconsistencyError` |
| 连续 2 次 retry 仍 fail | 推 agent.debate 事件，触发多 Agent 辩论 |
| 资源引用了未授权 chunk | 直接 fail，issue 写明"未授权引用" |

---

## 6. 与其他 Agent 的接口

- **被调用方**：D-03 协同编排器
- **回灌对象**：C-04 领域专家 Agent（retry 时）
- **依赖数据**：A 区 `calc_hallucination_rate` + `calc_coverage`
- **事件推送**：通过 A-04 WebSocket 推 `agent.audit` → `agent.debate`（如触发）

---

## 7. 验收标准

- ✅ 3 项硬指标全过（见 `00_项目全局启动提示词.md` 红线）
- ✅ 100 条审核记录，score 与人工评分相关系数 ≥ 0.8
- ✅ 平均审核耗时 < 1s
- ✅ 所有 issues 都有切片 ID 引用
