<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { AgentEvent } from '@/stores/agentEvents'

/**
 * 事件时间轴（大屏右侧，可点定位）
 * - 5 类事件图标/配色区分；点击 emit select（回放器定位到该事件）
 * - 新事件自动滚动到底部
 */
const props = defineProps<{ events: AgentEvent[]; activeSeq: number }>()
const emit = defineEmits<{ (e: 'select', evt: AgentEvent): void }>()

const boxEl = ref<HTMLElement | null>(null)

const META: Record<string, { icon: string; label: string; color: string }> = {
  'agent.start': { icon: '▶', label: '启动', color: 'var(--color-agent-blue)' },
  'agent.thinking': { icon: '⋯', label: '思考', color: 'var(--color-agent-purple)' },
  'agent.result': { icon: '✓', label: '产出', color: 'var(--color-success)' },
  'agent.debate': { icon: '⚡', label: '辩论', color: 'var(--color-agent-gold)' },
  'agent.final': { icon: '★', label: '结论', color: '#f97316' }
}

function metaOf(type: string) {
  return META[type] ?? { icon: '·', label: type, color: 'var(--text-sub)' }
}

function fmtTime(ts: number) {
  const d = new Date(ts * 1000)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

function titleOf(evt: AgentEvent) {
  if (evt.type === 'agent.debate') return `辩论：${evt.topic ?? ''}`
  if (evt.type === 'agent.final') return '决策融合结论'
  return evt.agentName ?? ''
}

watch(
  () => props.events.length,
  async () => {
    await nextTick()
    boxEl.value?.scrollTo({ top: boxEl.value.scrollHeight, behavior: 'smooth' })
  }
)
</script>

<template>
  <div ref="boxEl" class="event-timeline" role="listbox" aria-label="协同事件时间轴">
    <button
      v-for="evt in events"
      :key="evt.seq"
      class="event-timeline__item"
      :class="{ 'event-timeline__item--active': evt.seq === activeSeq }"
      :style="{ '--evt-color': metaOf(evt.type).color }"
      role="option"
      :aria-selected="evt.seq === activeSeq"
      @click="emit('select', evt)"
    >
      <span class="event-timeline__icon">{{ metaOf(evt.type).icon }}</span>
      <span class="event-timeline__body">
        <span class="event-timeline__title">
          <span class="event-timeline__agent">{{ titleOf(evt) }}</span>
          <span class="event-timeline__tag">{{ metaOf(evt.type).label }}</span>
        </span>
        <span v-if="evt.content" class="event-timeline__content">{{ evt.content }}</span>
        <span class="event-timeline__time">#{{ evt.seq }} · {{ fmtTime(evt.timestamp) }}</span>
      </span>
    </button>
    <p v-if="!events.length" class="event-timeline__empty">等待事件…</p>
  </div>
</template>

<style scoped>
.event-timeline {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 4px;
}

.event-timeline__item {
  display: flex;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.04);
  text-align: left;
  cursor: pointer;
  color: inherit;
  transition:
    background 150ms ease-out,
    border-color 150ms ease-out;
}

.event-timeline__item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.event-timeline__item--active {
  border-color: var(--evt-color);
  background: color-mix(in srgb, var(--evt-color) 12%, transparent);
}

.event-timeline__icon {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 12px;
  color: #0b1020;
  background: var(--evt-color);
  font-weight: 700;
}

.event-timeline__body {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event-timeline__title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.event-timeline__agent {
  font-size: 12px;
  font-weight: 600;
  color: #e5e7eb;
}

.event-timeline__tag {
  font-size: 10px;
  padding: 0 6px;
  border-radius: 999px;
  color: var(--evt-color);
  border: 1px solid color-mix(in srgb, var(--evt-color) 45%, transparent);
}

.event-timeline__content {
  font-size: 11px;
  color: #9ca3af;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.event-timeline__time {
  font-size: 10px;
  color: #6b7280;
  font-variant-numeric: tabular-nums;
}

.event-timeline__empty {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  padding: 24px 0;
}
</style>
