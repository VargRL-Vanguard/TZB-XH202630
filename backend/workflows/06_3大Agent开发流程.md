# 工作流程 06：3 大 Agent 开发流程（**B-05 / C-04 / D-06 通用**）

> 3 大 Agent 都遵循同一个开发模式（输入输出不同，但步骤一样）。
> 本流程适用于：B-05 学情诊断 / C-04 领域专家 / D-06 审核裁判。

---

## 前置条件

- 对应区的 00 任务（数据层）已完成
- A-04 WebSocket 已就绪
- A 区 `公共/metrics` 3 个函数已发布
- D 区 `ai_service` 已就绪
- B-06 知识库切片已就绪（仅 C-04 / D-06）

---

## 步骤 1：明确 Agent 的"输入 / 输出 / 契约"

**输入**：对应的提示词文档
- B-05 → [`prompts/10_学情诊断Agent_提示词.md`](../prompts/10_学情诊断Agent_提示词.md) 第 2 节
- C-04 → [`prompts/11_领域专家Agent_提示词.md`](../prompts/11_领域专家Agent_提示词.md) 第 2 节
- D-06 → [`prompts/12_审核裁判Agent_提示词.md`](../prompts/12_审核裁判Agent_提示词.md) 第 2 节

**操作**：
1. **抄下来** 提示词第 2 节的"对外契约"代码
2. 把 schema（`DiagnosisResult` / `Resource` / `AuditResult`）放到 `models.py`
3. 函数签名照抄

**输出**：1 个 Pydantic 模型 + 1 个函数签名

**验证**：
- [ ] 函数签名与提示词一致（**不要**自己加字段）
- [ ] 字段名 / 类型与 `api-doc.js` 一致

**失败处理**：字段不匹配 → 查提示词 + `api-doc.js`，**不要**自己改

---

## 步骤 2：实现 Agent 函数（按提示词流程）

**输入**：步骤 1 的契约

**操作**：严格按提示词第 2 节的"伪代码"实现

通用模板（**所有 Agent 都要做的事**）：

```python
def agent_xxx(...):
    traceId = get_current_traceId()  # 从上下文拿
    
    # 1. 推 ws: agent.start
    emit_agent_start(traceId, "<agent_name>", "start", payload)
    
    # 2. 拉数据（业务相关）
    data = get_xxx(...)
    emit_agent_thinking(traceId, "<agent_name>", "data_loaded", {"count": len(data)})
    
    # 3. 拼 prompt（**只引用检索到的数据，不要自由发挥**）
    prompt = build_prompt(data)
    
    # 4. 调 D 区 ai_service
    raw = chat_with_prompt(prompt, system=SYSTEM_PROMPT)
    emit_agent_thinking(traceId, "<agent_name>", "llm_called", {"raw_len": len(raw)})
    
    # 5. 解析 + 校验
    result = parse_and_validate(raw, expected_schema)
    
    # 6. 调 A 区 metrics 自检
    metrics = {
        "hallucination": calc_hallucination_rate(result, cited),
        "coverage": calc_coverage(result, target_kps),
    }
    emit_agent_thinking(traceId, "<agent_name>", "metrics_checked", metrics)
    
    # 7. 推 ws: agent.result
    emit_agent_result(traceId, "<agent_name>", "result", result.dict())
    
    # 8. 落 agent_log
    log_agent_event(traceId, "<agent_name>", "result", result.dict())
    
    return result
```

**输出**：1 个 Agent 函数

**验证**：
- [ ] 推了 4 类事件：start / thinking / result / log
- [ ] 调了 metrics 自检
- [ ] 解析失败有重试（最多 2 次）

**失败处理**：
- LLM 解析失败 → retry 1 次 + fallback 到默认值
- metrics 不达标 → 抛 `QualityError`（**不要**静默通过）

---

## 步骤 3：写 Prompt 模板

**输入**：提示词第 3 节

**操作**：
1. 把提示词第 3 节的 prompt 模板**直接复制**到代码里
2. 用 Python f-string 或 Jinja2 填变量
3. **不要**自己改 prompt 结构

**输出**：1 个 `build_prompt()` 函数

**验证**：
- [ ] prompt 字符串与提示词第 3 节**完全一致**（变量部分用占位符）
- [ ] 单元测试：填入测试数据 → 生成的 prompt 字符串与人工填的一致

**失败处理**：AI 改了 prompt → 删掉改回原版，**不要**让 AI "优化"

---

## 步骤 4：写自检逻辑

**输入**：提示词第 4 节"自检与红线"

**操作**：把红线表**逐条**写成 if/else

**通用自检模式**：

```python
def self_check(result) -> List[str]:
    issues = []
    # 红线 1：字段必须在白名单内
    if not all(kp in ALLOWED_KPS for kp in result.weakKPs):
        issues.append("weakKPs 含非法 kp_id")
    # 红线 2：必须引用切片
    if not result.cited_chunks:
        issues.append("未引用任何切片（幻觉风险）")
    # 红线 3：数值范围
    if not (1 <= result.recommendedDifficulty <= 5):
        issues.append(f"难度 {result.recommendedDifficulty} 越界")
    return issues
```

**输出**：1 个 `self_check()` 函数

**验证**：
- [ ] 红线条数与提示词第 4 节一致
- [ ] 单元测试覆盖每个红线

**失败处理**：漏红线 → 查提示词第 4 节，**不要**自己加

---

## 步骤 5：写单元测试

**输入**：B-07 测试画像（仅 C-04 / D-06 用，B-05 用真实学生数据）

**操作**：
1. `tests/test_<agent>.py`
2. 准备 3-5 组测试输入（包含正常 / 边界 / 异常）
3. 断言：
   - 输出 schema 正确
   - 调过 4 类 WebSocket 事件（用 mock）
   - metrics 在合理范围
   - 红线触发时有 `issues`

**输出**：1 个测试文件

**验证**：
- [ ] `pytest tests/test_<agent>.py` 全过
- [ ] 覆盖率 ≥ 80%

**详细提示**：[`prompts/<对应提示词>.md`](../prompts/) 验收标准节

---

## 步骤 6：与其他 Agent 联调

**输入**：本 Agent 完成 + 上下游 Agent 完成

**操作**：
1. 上下游约定一个 `traceId`
2. 跑完整链路：B-05 → C-04 → D-06
3. 检查 agent_log 表 → 事件流是否完整
4. 检查 WebSocket → 前端能否看到完整流程

**输出**：1 份联调报告（事件流截图 + agent_log 记录）

**验证**：
- [ ] agent_log 表里本 Agent 的所有事件都在
- [ ] traceId 能串联 B-05 → C-04 → D-06
- [ ] 3 项硬指标不倒退

**失败处理**：事件缺失 → 检查是否每个函数入口都 `emit_*`

---

## Agent 通用验收清单

- [ ] 步骤 1：契约 schema + 函数签名与提示词一致
- [ ] 步骤 2：Agent 函数实现完整（4 类事件 + metrics + log）
- [ ] 步骤 3：Prompt 模板与提示词第 3 节**完全一致**
- [ ] 步骤 4：自检逻辑覆盖提示词第 4 节**所有红线**
- [ ] 步骤 5：单元测试全过，覆盖率 ≥ 80%
- [ ] 步骤 6：与其他 Agent 联调通过

**任何一步不过 → 不要往下做，先修**
