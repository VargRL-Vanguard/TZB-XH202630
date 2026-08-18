<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'
import type { AgentCardState } from '@/stores/agentEvents'

/**
 * 大屏 Agent 卡片（05 号文档 v1 规格，状态机对齐 08 号契约 §5.2 / stores/agentEvents.ts）
 * - props：name（与 WS agentName 一致，如「学情诊断Agent」）、themeColor、icon、state
 * - 状态：idle 空闲 / running 转圈+呼吸边框 / done ✅ / debating ⚡ 边框 / finished 收尾
 * - 默认插槽：思考气泡区（D 区往里塞打字机内容，最多保留 50 条由调用方控制）
 */
withDefaults(
  defineProps<{
    name: string
    /** 主题色（40 号文档 §4.2：诊断蓝 / 专家紫 / 裁判金） */
    themeColor?: string
    /** 图标组件（Element 图标或自绘 SVG 组件） */
    icon?: Component | null
    state?: AgentCardState
  }>(),
  { themeColor: 'var(--color-primary)', icon: null, state: 'idle' }
)

const stateText = computed<Record<AgentCardState, string>>(() => ({
  idle: '待命',
  running: '分析中',
  done: '已完成',
  debating: '辩论中',
  finished: '已交付'
}))
</script>

<template>
  <div class="agent-card" :class="`agent-card--${state}`" :style="{ '--agent-theme': themeColor }">
    <!-- 卡头：图标 + 名称 + 状态徽标 -->
    <div class="agent-card__head">
      <span class="agent-card__icon">
        <span v-if="state === 'running'" class="agent-card__spinner" aria-hidden="true"></span>
        <span v-else-if="state === 'done'" class="agent-card__check">✅</span>
        <span v-else-if="state === 'debating'" class="agent-card__bolt">⚡</span>
        <component :is="icon" v-else-if="icon" class="agent-card__icon-svg" />
        <span v-else class="agent-card__icon-fallback">🤖</span>
      </span>
      <span class="agent-card__name">{{ name }}</span>
      <span class="agent-card__state">{{ stateText[state] }}</span>
    </div>

    <!-- 思考气泡区：D 区塞打字机内容 -->
    <div class="agent-card__body">
      <slot>
        <p class="agent-card__placeholder">等待任务下发…</p>
      </slot>
    </div>
  </div>
</template>

<style scoped>
.agent-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-2);
  min-width: 0;
  border-radius: var(--card-radius);
  background: #ffffff;
  box-shadow: var(--card-shadow);
  border: 1px solid color-mix(in srgb, var(--agent-theme) 25%, transparent);
  transition:
    border-color 200ms var(--ease-out),
    box-shadow 200ms var(--ease-out);
}

/* ===== running：呼吸灯 + 转圈 ===== */
.agent-card--running {
  animation: agent-breathe 1.6s infinite ease-in-out;
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--agent-theme) 45%, transparent),
    0 4px 16px color-mix(in srgb, var(--agent-theme) 25%, transparent);
}

@keyframes agent-breathe {
  0%,
  100% {
    box-shadow:
      0 0 0 1px color-mix(in srgb, var(--agent-theme) 45%, transparent),
      0 4px 16px color-mix(in srgb, var(--agent-theme) 12%, transparent);
  }
  50% {
    box-shadow:
      0 0 0 1px color-mix(in srgb, var(--agent-theme) 70%, transparent),
      0 4px 24px color-mix(in srgb, var(--agent-theme) 35%, transparent);
  }
}

/* ===== debating：⚡ 高亮边框 ===== */
.agent-card--debating {
  border-color: var(--color-agent-gold);
  box-shadow:
    0 0 0 1px var(--color-agent-gold),
    0 0 20px color-mix(in srgb, var(--color-agent-gold) 35%, transparent);
}

/* ===== finished：收敛态 ===== */
.agent-card--finished {
  opacity: 0.92;
}

/* ===== 卡头 ===== */
.agent-card__head {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}

.agent-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  flex-shrink: 0;
  color: var(--agent-theme);
  background: color-mix(in srgb, var(--agent-theme) 12%, transparent);
}

.agent-card__icon-svg {
  width: 20px;
  height: 20px;
}

.agent-card__spinner {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid color-mix(in srgb, var(--agent-theme) 25%, transparent);
  border-top-color: var(--agent-theme);
  animation: agent-spin 0.9s linear infinite;
}

@keyframes agent-spin {
  to {
    transform: rotate(360deg);
  }
}

.agent-card__check,
.agent-card__bolt {
  font-size: 18px;
  line-height: 1;
}

.agent-card__name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-card__state {
  flex-shrink: 0;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--agent-theme);
  background: color-mix(in srgb, var(--agent-theme) 10%, transparent);
}

/* ===== 气泡区 ===== */
.agent-card__body {
  min-height: 72px;
  max-height: 200px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-sub);
}

.agent-card__placeholder {
  color: var(--text-sub);
  opacity: 0.7;
}
</style>
