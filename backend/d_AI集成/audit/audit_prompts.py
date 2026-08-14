"""
审核裁判 Agent prompt 模板（D-06 ⭐）。

version: 0.1
"""
VERSION = "0.1"

# 审核 Agent 启动时的内容
START_STEP_CONTENT = "审核裁判Agent启动，开始对生成内容进行质量审核..."

# 思考步骤（通过 WS 推送）
THINKING_STEPS = [
    "正在拆分生成内容为句子单元...",
    "正在逐句检索知识库切片进行幻觉率比对...",
    "正在计算核心知识点覆盖率...",
    "正在综合评分并生成审核结论...",
]

# 审核结果摘要模板
RESULT_SUMMARY_TEMPLATE = (
    "审核完成：幻觉率={hr:.1%}，覆盖率={cov:.1%}，综合评分={score:.2f}，结论={result}"
)

# 审核结论描述
RESULT_LABELS = {
    "pass": "通过 — 内容质量达标，幻觉率与覆盖率均符合要求",
    "retry": "可优化 — 内容基本可用，但存在可改进项，建议领域专家Agent优化后重新提交",
    "fail": "不通过 — 内容质量不达标，幻觉率过高或覆盖率不足，需重新生成",
}

# Issue 模板
ISSUE_HALLUCINATION = "幻觉句：句子「{sentence}」与知识库相似度仅 {similarity:.2f}，疑似无依据内容"
ISSUE_COVERAGE_LOW = "知识点覆盖率不足：当前覆盖 {covered}/{total}（{ratio:.1%}），未达标（需 ≥ 90%）"
ISSUE_KP_MISSING = "缺失知识点：{kp_id}（{kp_name}）未在生成内容中覆盖"