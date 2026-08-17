import { defineStore } from 'pinia'

/**
 * Agent 事件 store：WS 事件流按 traceId 分组，供大屏与回放器共享读取
 * 事件字段以 08 号契约 §5.2 为准（ws/events.py）
 */

export type AgentEventType =
  'agent.start' | 'agent.thinking' | 'agent.result' | 'agent.debate' | 'agent.final'

export interface AgentEvent {
  type: AgentEventType
  agentName?: string
  step?: number
  content?: string
  data?: Record<string, unknown>
  agents?: string[]
  topic?: string
  ok?: boolean
  summary?: string
  traceId: string
  timestamp: number
  /** 本地记录的接收顺序（回放用） */
  seq: number
}

export type AgentCardState = 'idle' | 'running' | 'done' | 'debating' | 'finished'

/** 气泡最多保留条数（夺奖红线：硬性容错） */
export const MAX_BUBBLES = 50

interface TraceGroup {
  traceId: string
  events: AgentEvent[]
  /** 各 agent 卡片状态 */
  cardStates: Record<string, AgentCardState>
  /** 当前步骤 1-4 */
  step: number
  finished: boolean
  finalOk: boolean | null
  summary: string
}

interface AgentEventsState {
  /** 当前活跃 traceId */
  activeTraceId: string
  traces: Record<string, TraceGroup>
  seq: number
}

function newTrace(traceId: string): TraceGroup {
  return {
    traceId,
    events: [],
    cardStates: {},
    step: 0,
    finished: false,
    finalOk: null,
    summary: ''
  }
}

export const useAgentEventsStore = defineStore('agentEvents', {
  state: (): AgentEventsState => ({
    activeTraceId: '',
    traces: {},
    seq: 0
  }),
  getters: {
    activeTrace(s): TraceGroup | null {
      return s.traces[s.activeTraceId] ?? null
    },
    /** 回放用：取某 trace 的完整事件序列（按 seq 排序） */
    replayEvents(s) {
      return (traceId: string): AgentEvent[] => {
        const t = s.traces[traceId]
        if (!t) return []
        return [...t.events].sort((a, b) => a.seq - b.seq)
      }
    }
  },
  actions: {
    /**
     * 处理一条服务端事件（乱序容错：不白屏，只按到达顺序记录）
     */
    pushEvent(raw: { type: string; traceId?: string } & Record<string, unknown>) {
      const traceId = (raw.traceId as string) || `unknown-${Date.now()}`
      if (!this.traces[traceId]) this.traces[traceId] = newTrace(traceId)
      const trace = this.traces[traceId]
      this.activeTraceId = traceId

      const evt: AgentEvent = {
        type: raw.type as AgentEventType,
        agentName: raw.agentName as string | undefined,
        step: raw.step as number | undefined,
        content: raw.content as string | undefined,
        data: raw.data as Record<string, unknown> | undefined,
        agents: raw.agents as string[] | undefined,
        topic: raw.topic as string | undefined,
        ok: raw.ok as boolean | undefined,
        summary: raw.summary as string | undefined,
        traceId,
        timestamp: (raw.timestamp as number) ?? Date.now() / 1000,
        seq: ++this.seq
      }
      trace.events.push(evt)

      // 硬性容错：事件数组同样限制规模（气泡 50 条的红线由视图层遵循，事件流这里防内存膨胀放大上限）
      if (trace.events.length > 500) trace.events.splice(0, trace.events.length - 500)

      // 状态机推进
      switch (evt.type) {
        case 'agent.start': {
          if (evt.agentName) trace.cardStates[evt.agentName] = 'running'
          if (evt.step) trace.step = Math.max(trace.step, evt.step)
          break
        }
        case 'agent.thinking': {
          if (evt.agentName) {
            // thinking 期间保持 running（除非已在辩论）
            if (trace.cardStates[evt.agentName] !== 'debating') {
              trace.cardStates[evt.agentName] = 'running'
            }
          }
          break
        }
        case 'agent.result': {
          if (evt.agentName) trace.cardStates[evt.agentName] = 'done'
          break
        }
        case 'agent.debate': {
          const names = evt.agents ?? []
          names.forEach((n) => {
            trace.cardStates[n] = 'debating'
          })
          break
        }
        case 'agent.final': {
          Object.keys(trace.cardStates).forEach((n) => {
            trace.cardStates[n] = 'finished'
          })
          trace.finished = true
          trace.finalOk = evt.ok ?? false
          trace.summary = evt.summary ?? ''
          break
        }
        default:
          break
      }
    },

    /** 重置某 trace（回放前调用） */
    resetTrace(traceId: string) {
      this.traces[traceId] = newTrace(traceId)
    }
  }
})
