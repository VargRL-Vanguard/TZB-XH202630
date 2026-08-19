<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { Monitor, VideoPlay, Back, Setting } from '@element-plus/icons-vue'
import { useAgentEventsStore, MAX_BUBBLES, type AgentEvent } from '@/stores/agentEvents'
import { wsClient, type WsStatus } from '@/ws/client'
import { buildMockTrace, MOCK_TRACE_STEP_TITLES } from '@/mock/fixtures/trace'
import AgentCard from '@/components/AgentCard.vue'
import TypewriterBubble from '@/components/agent/TypewriterBubble.vue'
import ParticleFlow from '@/components/agent/ParticleFlow.vue'
import EventTimeline from '@/components/agent/EventTimeline.vue'
import FinalCard from '@/components/agent/FinalCard.vue'

/**
 * P0-2 多智能体协同大屏（08 号契约 §5 + 05 号文档深色大屏规格）
 * 数据源：
 * - 真实：登录后 App.vue 建 WS → wsClient 把 agent.* 事件写入 agentEvents store，本页纯读
 * - 回放：无 AI Key / 演示场景，用 mock trace 按节奏重演 4 阶段流水线
 */

const store = useAgentEventsStore()

const trace = computed(() => store.activeTrace)

// ===== 3 张 Agent 卡（名称与后端 orchestrator/pipeline.py 一字不差）=====
const AGENTS = [
  { name: '学情诊断Agent', theme: 'var(--color-agent-blue)', role: '画像诊断 · 弱项定位' },
  { name: '领域专家Agent', theme: 'var(--color-agent-purple)', role: '知识检索 · 内容生成' },
  { name: '审核裁判Agent', theme: 'var(--color-agent-gold)', role: '切片比对 · 质量裁决' }
] as const

/** 某卡片的气泡（含 debate 事件），最新在前（条数上限可在大屏设置中调） */
function bubblesOf(agentName: string): AgentEvent[] {
  const list = (trace.value?.events ?? []).filter(
    (e) =>
      e.agentName === agentName ||
      (e.type === 'agent.debate' && (e.agents ?? []).includes(agentName))
  )
  return list.slice(-bubbleLimit.value).reverse()
}

/** 卡片是否处于流水线中（连线流动条件：任意卡 running/debating） */
const flowing = computed(() => {
  const states = Object.values(trace.value?.cardStates ?? {})
  return states.some((s) => s === 'running' || s === 'debating') && !trace.value?.finished
})

// ===== 进度条 1/4 → 4/4 =====
const step = computed(() => trace.value?.step ?? 0)
const steps = MOCK_TRACE_STEP_TITLES

// ===== WS 连接状态 pill =====
const wsStatus = ref<WsStatus>(wsClient.currentStatus)
const offStatus = wsClient.onStatus((s) => {
  wsStatus.value = s
})
const wsStatusText: Record<WsStatus, string> = {
  idle: '未连接',
  connecting: '连接中',
  open: '实时连接',
  reconnecting: '重连中',
  closed: '已断开'
}

// ===== FinalCard =====
const finalDismissed = ref(false)
const showFinal = computed(() => !!trace.value?.finished && !finalDismissed.value)

// ===== 演示回放 =====
const replaying = ref(false)
let replayToken = 0
const timers = new Set<ReturnType<typeof setTimeout>>()

// ===== 大屏快捷设置 =====
const REPLAY_SPEEDS = [
  { label: '0.5×', value: 0.5 },
  { label: '1×', value: 1 },
  { label: '2×', value: 2 }
] as const
const replaySpeed = ref<number>(1) // 回放节奏倍率（值越大越快）
const BUBBLE_LIMITS = [20, 50, 100]
const bubbleLimit = ref<number>(MAX_BUBBLES) // 每卡气泡条数上限
const autoFinal = ref(true) // 回放结束自动弹融合结论

function clearTimers() {
  timers.forEach(clearTimeout)
  timers.clear()
}

function stopReplay() {
  replayToken += 1
  clearTimers()
  replaying.value = false
}

function startReplay() {
  stopReplay()
  finalDismissed.value = !autoFinal.value
  const token = replayToken
  const { traceId, events } = buildMockTrace()
  store.resetTrace(traceId)
  store.activeTraceId = traceId
  replaying.value = true

  let acc = 0
  events.forEach((e) => {
    acc += e.delayMs / replaySpeed.value // 速度倍率：2× 时延减半
    const t = setTimeout(() => {
      if (token !== replayToken) return
      // 补真实时间戳（回放时按当前时刻计）
      store.pushEvent({ ...e.payload, type: String(e.payload.type), timestamp: Date.now() / 1000 })
      if (e.payload.type === 'agent.final') {
        replaying.value = false
      }
    }, acc)
    timers.add(t)
  })
}

// ===== 时间轴点击定位 =====
const activeSeq = ref(0)
function onTimelineSelect(evt: AgentEvent) {
  activeSeq.value = evt.seq
}

onBeforeUnmount(() => {
  stopReplay()
  offStatus()
})
</script>

<template>
  <div class="screen">
    <!-- ===== 顶栏 ===== -->
    <header class="screen__bar">
      <div class="screen__title-wrap">
        <el-icon :size="22" class="screen__title-icon"><Monitor /></el-icon>
        <div>
          <h1 class="screen__title">多智能体协同决策大屏</h1>
          <p class="screen__sub">学情诊断 → 领域专家生成 → 审核裁判辩论 → 决策融合</p>
        </div>
      </div>

      <div class="screen__bar-right">
        <span class="screen__ws" :class="`screen__ws--${wsStatus}`">
          <span class="screen__ws-dot"></span>
          {{ wsStatusText[wsStatus] }}
        </span>
        <span v-if="trace" class="screen__trace" title="当前 traceId"
          >traceId：{{ trace.traceId }}</span
        >
        <el-button type="primary" :icon="VideoPlay" :disabled="replaying" @click="startReplay">
          {{ replaying ? '回放中…' : '演示回放' }}
        </el-button>
        <el-popover placement="bottom-end" :width="264" trigger="click">
          <template #reference>
            <el-button :icon="Setting" circle title="大屏快捷设置" />
          </template>
          <div class="screen-settings">
            <h4 class="screen-settings__title">大屏快捷设置</h4>
            <div class="screen-settings__row">
              <span class="screen-settings__label">回放速度</span>
              <el-radio-group v-model="replaySpeed" size="small">
                <el-radio-button v-for="s in REPLAY_SPEEDS" :key="s.value" :value="s.value">
                  {{ s.label }}
                </el-radio-button>
              </el-radio-group>
            </div>
            <div class="screen-settings__row">
              <span class="screen-settings__label">气泡条数上限</span>
              <el-select v-model="bubbleLimit" size="small" style="width: 110px">
                <el-option v-for="n in BUBBLE_LIMITS" :key="n" :label="`${n} 条`" :value="n" />
              </el-select>
            </div>
            <div class="screen-settings__row">
              <span class="screen-settings__label">回放结束弹融合结论</span>
              <el-switch v-model="autoFinal" size="small" />
            </div>
            <p class="screen-settings__hint">速度对下一次回放生效；气泡上限即时生效</p>
          </div>
        </el-popover>
        <el-button :icon="Back" text class="screen__back" @click="$router.push('/dashboard')">
          返回系统
        </el-button>
      </div>
    </header>

    <!-- ===== 4 步进度 ===== -->
    <nav class="screen__steps" aria-label="协同阶段进度">
      <template v-for="(title, i) in steps" :key="title">
        <div
          class="step"
          :class="{ 'step--done': step > i + 1, 'step--now': step === i + 1 }"
          :style="{ '--i': i }"
        >
          <span class="step__num">{{ i + 1 }}</span>
          <span class="step__label">{{ title }}</span>
        </div>
        <div
          v-if="i < steps.length - 1"
          class="screen__step-link"
          :class="{ 'screen__step-link--lit': step > i + 1 }"
        ></div>
      </template>
      <span class="screen__step-count num">{{ Math.max(1, step) }}/4</span>
    </nav>

    <!-- ===== 主区：3 卡流水线 + 时间轴 ===== -->
    <main class="screen__main">
      <section class="screen__pipeline" aria-label="智能体流水线">
        <template v-for="(agent, i) in AGENTS" :key="agent.name">
          <div class="screen__card-wrap" :style="{ '--agent-theme': agent.theme }">
            <AgentCard
              :name="agent.name"
              :theme-color="agent.theme"
              :state="trace?.cardStates[agent.name] ?? 'idle'"
            >
              <template #default>
                <p class="screen__role">{{ agent.role }}</p>
                <div v-if="bubblesOf(agent.name).length" class="screen__bubbles">
                  <div
                    v-for="(evt, bi) in bubblesOf(agent.name)"
                    :key="evt.seq"
                    class="screen__bubble"
                  >
                    <TypewriterBubble
                      v-if="bi === 0 && evt.type === 'agent.thinking'"
                      :text="evt.content ?? ''"
                    />
                    <div
                      v-else
                      class="screen__bubble-static"
                      :class="`screen__bubble-static--${evt.type.replace('agent.', '')}`"
                    >
                      <span v-if="evt.type === 'agent.debate'" class="screen__debate-tag"
                        >⚡ 辩论</span
                      >
                      <span v-else-if="evt.type === 'agent.result'" class="screen__result-tag"
                        >✓</span
                      >
                      <span v-else-if="evt.type === 'agent.start'" class="screen__start-tag"
                        >▶</span
                      >
                      <span class="screen__bubble-text">{{ evt.content ?? evt.topic ?? '' }}</span>
                    </div>
                  </div>
                </div>
                <p v-else class="screen__idle">待命，等待任务下发…</p>
              </template>
            </AgentCard>
          </div>
          <ParticleFlow
            v-if="i < AGENTS.length - 1"
            :active="flowing"
            :label="i === 0 ? '诊断结果' : '初稿'"
          />
        </template>
      </section>

      <!-- 右侧时间轴 -->
      <aside class="screen__side" aria-label="事件时间轴">
        <h2 class="screen__side-title">事件时间轴</h2>
        <EventTimeline
          :events="store.replayEvents(trace?.traceId ?? '')"
          :active-seq="activeSeq"
          @select="onTimelineSelect"
        />
      </aside>
    </main>

    <!-- ===== 空态引导 ===== -->
    <div v-if="!trace || trace.events.length === 0" class="screen__empty">
      <p class="screen__empty-title">暂无协同事件</p>
      <p class="screen__empty-sub">等待真实任务下发，或点击「演示回放」查看完整 4 阶段协同过程</p>
      <el-button type="primary" :icon="VideoPlay" @click="startReplay">演示回放</el-button>
    </div>

    <!-- ===== 结论弹卡 ===== -->
    <div v-if="showFinal && trace" class="screen__final-mask" @click.self="finalDismissed = true">
      <FinalCard
        :ok="trace.finalOk ?? false"
        :summary="trace.summary"
        :trace-id="trace.traceId"
        @close="finalDismissed = true"
      />
    </div>
  </div>
</template>

<style scoped>
.screen {
  height: 100vh; /* 大屏锁一屏：内部各区域自行滚动，页面不出滚动条 */
  overflow: hidden;
  background:
    radial-gradient(1200px 500px at 15% -10%, rgba(56, 189, 248, 0.08), transparent),
    radial-gradient(1000px 480px at 85% -10%, rgba(167, 139, 250, 0.08), transparent),
    var(--bg-screen);
  color: #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: var(--sp-3);
  gap: var(--sp-2);
}

/* ===== 顶栏 ===== */
.screen__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.screen__title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-agent-blue);
}

.screen__title {
  font-size: 20px;
  font-weight: 700;
  color: #f8fafc;
}

.screen__sub {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.screen__bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* ===== 大屏快捷设置 popover 内容 ===== */
.screen-settings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.screen-settings__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.screen-settings__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.screen-settings__label {
  font-size: 12px;
  color: var(--text-sub);
}

.screen-settings__hint {
  font-size: 11px;
  color: var(--text-sub);
  border-top: 1px dashed var(--border-line);
  padding-top: 8px;
}

.screen__ws {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  color: #94a3b8;
}

.screen__ws-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #64748b;
}

.screen__ws--open .screen__ws-dot {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.8);
  animation: ws-breathe 1.6s infinite;
}

.screen__ws--reconnecting .screen__ws-dot {
  background: #f59e0b;
  animation: ws-breathe 0.8s infinite;
}

.screen__ws--open {
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.4);
}

.screen__ws--reconnecting {
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.4);
}

@keyframes ws-breathe {
  50% {
    opacity: 0.35;
  }
}

.screen__trace {
  font-size: 12px;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.screen__back {
  color: #94a3b8;
}

/* ===== 4 步进度 ===== */
.screen__steps {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px var(--sp-2);
  border-radius: var(--card-radius);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(148, 163, 184, 0.15);
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step__num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(148, 163, 184, 0.08);
  transition: all 250ms var(--ease-out);
}

.step__label {
  font-size: 13px;
  color: #94a3b8;
}

.step--now .step__num {
  color: #0b1020;
  background: var(--color-agent-blue);
  border-color: var(--color-agent-blue);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.55);
}

.step--now .step__label {
  color: #f8fafc;
  font-weight: 600;
}

.step--done .step__num {
  color: #0b1020;
  background: #22c55e;
  border-color: #22c55e;
}

.step--done .step__label {
  color: #86efac;
}

.screen__step-link {
  flex: 1;
  min-width: 24px;
  height: 2px;
  border-radius: 1px;
  background: rgba(148, 163, 184, 0.3);
}

.screen__step-link--lit {
  background: linear-gradient(90deg, #22c55e, var(--color-agent-blue));
}

.screen__step-count {
  font-size: 14px;
  font-weight: 700;
  color: #f8fafc;
}

/* ===== 主区 ===== */
.screen__main {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: var(--sp-2);
  min-height: 0;
}

.screen__pipeline {
  display: flex;
  align-items: stretch;
  gap: 0;
  min-height: 0; /* 高度交给 screen__main 的 flex 分配，卡片等高不撑破一屏 */
}

.screen__card-wrap {
  flex: 1.6;
  min-width: 0;
  min-height: 0;
  display: flex;
}

/* 深色大屏下卡片改暗色玻璃（覆盖 AgentCard 默认白底） */
.screen__card-wrap :deep(.agent-card) {
  flex: 1;
  min-height: 0; /* 允许在锁高布局中收缩，气泡区自行内滚 */
  background: rgba(17, 24, 39, 0.75);
  border-color: color-mix(in srgb, var(--agent-theme) 25%, transparent);
}

.screen__card-wrap :deep(.agent-card__body) {
  flex: 1;
  min-height: 56px;
  max-height: none; /* 解除 200px 上限：高度随卡片自适应，三卡保持等高 */
  overflow-y: auto;
}

.screen__card-wrap :deep(.agent-card__name) {
  color: #f1f5f9;
}

.screen__card-wrap :deep(.agent-card__state) {
  color: var(--agent-theme);
}

.screen__role {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 8px;
}

.screen__bubbles {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.screen__bubble-static {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 12px;
  line-height: 1.6;
  color: #cbd5e1;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
}

.screen__bubble-static--result {
  color: #86efac;
}

.screen__bubble-static--debate {
  color: #fcd34d;
}

.screen__debate-tag,
.screen__start-tag {
  flex-shrink: 0;
  font-size: 11px;
}

.screen__result-tag {
  flex-shrink: 0;
  color: #22c55e;
  font-weight: 700;
}

.screen__idle {
  font-size: 12px;
  color: #475569;
}

/* ===== 右侧时间轴 ===== */
.screen__side {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-2);
  border-radius: var(--card-radius);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(148, 163, 184, 0.15);
  min-height: 0;
}

.screen__side-title {
  font-size: 13px;
  font-weight: 600;
  color: #cbd5e1;
}

.screen__side :deep(.event-timeline) {
  flex: 1;
}

/* ===== 空态 ===== */
.screen__empty {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(11, 16, 32, 0.72);
  backdrop-filter: blur(3px);
  z-index: 100;
  text-align: center;
}

.screen__empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #e2e8f0;
}

.screen__empty-sub {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 8px;
}

/* ===== FinalCard 遮罩 ===== */
.screen__final-mask {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(11, 16, 32, 0.55);
  backdrop-filter: blur(2px);
  z-index: 200;
}

/* ===== 窄屏 ===== */
@media (max-width: 1100px) {
  .screen {
    height: auto; /* 窄屏纵向排布放不进一屏，恢复页面滚动 */
    min-height: 100vh;
    overflow: visible;
  }

  .screen__main {
    grid-template-columns: 1fr;
  }

  .screen__pipeline {
    flex-direction: column;
  }

  .screen__card-wrap :deep(.agent-card__body) {
    max-height: 260px; /* 窄屏卡片纵排，限制单卡高度避免过长 */
  }

  .screen__side {
    max-height: 320px;
  }
}
</style>
