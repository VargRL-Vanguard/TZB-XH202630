"""
学情诊断 Agent 使用的 prompt 模板。
version: 0.1 — 每次更新必须递增（B-05 验收标准）。

说明：
- MVP 阶段 Agent 是"确定性规则引擎 + 知识库检索"的混合，不依赖外部 LLM
- 这里的 prompt 模板是为后续接入 LLM 准备的，规则引擎也会引用其中的关键词
- prompt 版本号写入 diagnosis_record.prompt_version，便于回放追踪
"""

VERSION = "0.1"  # ⭐ B-05 验收：每次更新必须递增

# === agent.start 时发送的开场描述 ===
START_STEP_CONTENT = (
    "【学情诊断Agent】启动：正在加载学生画像 + 最近活动数据..."
)

# === 思考步骤（agent.thinking 事件按 step 递增发送）===
THINKING_STEPS = [
    "步骤 1/4：合并 A 区 learnerProfile 与 B 区学习指标...",
    "步骤 2/4：从最近 30 天活动中统计各知识模块得分分布...",
    "步骤 3/4：匹配弱知识证据，补全画像未覆盖的 blind spot...",
    "步骤 4/4：计算诊断置信度，低于 0.6 则抛 QualityError...",
]

# === 知识盲区证据生成模板 ===
# severity: high (测试分<60) / medium (60-75) / low (75-85)
EVIDENCE_TEMPLATES = {
    "high": "该知识点近 {n} 次活动平均得分 {score:.1f}，低于掌握阈值 60 分，判定为重度盲区。",
    "medium": "该知识点活动得分 {score:.1f}，处于 60-75 区间，需要加强练习。",
    "low": "该知识点掌握度尚可（{score:.1f}），但低于强知识阈值 85 分，建议复习。",
}

# === 最终诊断摘要（agent.result 发送）===
RESULT_SUMMARY_TEMPLATE = (
    "诊断完成：共识别 {n_weak} 个弱知识点、{n_strong} 个强知识点、"
    "{n_gap} 个知识盲区，置信度 {conf:.2f}。"
)
