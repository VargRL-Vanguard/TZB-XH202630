/**
 * Mock 协同 trace 回放数据 —— 事件结构对齐 ws/events.py（08 号契约 §5.2），
 * Agent 名称与后端 orchestrator/pipeline.py 一致：学情诊断Agent / 领域专家Agent / 审核裁判Agent。
 * 用途：AgentScreen 大屏「演示回放」（无 AI Key 时也能完整演示 4 阶段流水线）。
 */

export interface MockTraceEvent {
  /** WS 原始 payload（与真实事件同构，直接喂 agentEvents.pushEvent） */
  payload: Record<string, unknown>
  /** 回放时距上一条的建议间隔 ms */
  delayMs: number
}

export const MOCK_TRACE_STEP_TITLES = [
  '学情诊断',
  '领域专家生成',
  '审核裁判辩论',
  '决策融合'
] as const

let traceSeq = 0

/** 每次生成新 traceId，避免与真实 WS trace 冲突 */
export function buildMockTrace(): { traceId: string; events: MockTraceEvent[] } {
  const traceId = `trace-mock-${Date.now().toString(36)}-${(traceSeq += 1)}`
  const ev = (
    type: string,
    delayMs: number,
    extra: Record<string, unknown> = {}
  ): MockTraceEvent => ({
    payload: { type, traceId, timestamp: 0, ...extra },
    delayMs
  })

  const events: MockTraceEvent[] = [
    // ===== Phase 1：学情诊断 Agent（step 1/4）=====
    ev('agent.start', 400, {
      agentName: '学情诊断Agent',
      step: 1,
      content: '开始解析学习者画像与最近学习行为'
    }),
    ev('agent.thinking', 900, {
      agentName: '学情诊断Agent',
      content: '读取画像：教育层次 / 理论模考分 / 强弱知识点清单…'
    }),
    ev('agent.thinking', 1100, {
      agentName: '学情诊断Agent',
      content: '比对近 10 条学习记录，定位弱项：kp12d、kp22c，置信度 0.87'
    }),
    ev('agent.result', 800, {
      agentName: '学情诊断Agent',
      content: '诊断完成：建议优先补强「逆运动学」与「顺控程序」，理论基线 82 分'
    }),

    // ===== Phase 2：领域专家 Agent（step 2/4）=====
    ev('agent.start', 600, {
      agentName: '领域专家Agent',
      step: 2,
      content: '接收诊断结果，检索知识库切片'
    }),
    ev('agent.thinking', 1000, {
      agentName: '领域专家Agent',
      content: '检索到 6 条相关切片：kp12d ×3、kp22c ×3，开始生成定制化内容…'
    }),
    ev('agent.thinking', 1200, {
      agentName: '领域专家Agent',
      content: '生成实践指南初稿：3 步（前置 5min / 操作 20min / 易错点 5min）'
    }),
    ev('agent.result', 800, {
      agentName: '领域专家Agent',
      content: '产出 res-69fcce 资源初稿，难度 L3，覆盖 2 个弱项知识点'
    }),

    // ===== Phase 3：审核裁判 Agent + 辩论（step 3/4）=====
    ev('agent.start', 600, {
      agentName: '审核裁判Agent',
      step: 3,
      content: '启动质量审核：逐条比对引用切片'
    }),
    ev('agent.thinking', 900, {
      agentName: '审核裁判Agent',
      content: '审核评分 0.78 < 0.85 阈值，触发辩论：要求领域专家修正'
    }),
    ev('agent.result', 700, { agentName: '审核裁判Agent', content: '完成第 1 轮审核：retry' }),
    ev('agent.debate', 400, {
      agents: ['领域专家Agent', '审核裁判Agent'],
      topic: 'kp22c 切片引用与原文一致性'
    }),
    ev('agent.thinking', 1100, {
      agentName: '领域专家Agent',
      content: '辩论回应：替换 2 条存疑表述，补齐缺失边界条件说明…'
    }),
    ev('agent.thinking', 900, {
      agentName: '审核裁判Agent',
      content: '复审通过：幻觉率 0.8%、匹配准确率 96%、覆盖率 100%'
    }),
    ev('agent.result', 700, { agentName: '审核裁判Agent', content: '第 2 轮辩论通过，判定 pass' }),

    // ===== Phase 4：决策融合（step 4/4）=====
    ev('agent.final', 900, {
      step: 4,
      ok: true,
      summary:
        '融合结论：为该学习者交付「定制化资源 + 实践指南 + 分层测验」三形态资源包，难度 L3，弱项覆盖率 100%，幻觉率 0.8%（阈值内）'
    })
  ]

  return { traceId, events }
}
