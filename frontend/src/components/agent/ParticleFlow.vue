<script setup lang="ts">
/**
 * 卡片间粒子流动连线（纯 CSS/SVG 粒子，无图片资源）
 * - active：当前阶段是否处于流动状态（对应卡片 running/debating 时点亮）
 * - label：连线中点标签（如「诊断结果」）
 */
withDefaults(defineProps<{ active?: boolean; label?: string }>(), { active: false, label: '' })
</script>

<template>
  <div class="p-flow" :class="{ 'p-flow--active': active }" aria-hidden="true">
    <svg class="p-flow__svg" viewBox="0 0 120 12" preserveAspectRatio="none">
      <line x1="0" y1="6" x2="120" y2="6" class="p-flow__line" />
      <polygon points="112,1 120,6 112,11" class="p-flow__arrow" />
    </svg>
    <span
      v-for="n in 3"
      :key="n"
      class="p-flow__particle"
      :style="{ '--p-delay': (n - 1) * 0.55 + 's' }"
    ></span>
    <span v-if="label" class="p-flow__label">{{ label }}</span>
  </div>
</template>

<style scoped>
.p-flow {
  position: relative;
  flex: 1;
  min-width: 48px;
  height: 36px;
  display: flex;
  align-items: center;
}

.p-flow__svg {
  width: 100%;
  height: 12px;
}

.p-flow__line {
  stroke: rgba(148, 163, 184, 0.35);
  stroke-width: 2;
  stroke-dasharray: 6 6;
  transition: stroke 300ms ease-out;
}

.p-flow__arrow {
  fill: rgba(148, 163, 184, 0.45);
  transition: fill 300ms ease-out;
}

.p-flow--active .p-flow__line {
  stroke: var(--color-agent-blue);
  animation: dash-move 1s linear infinite;
}

.p-flow--active .p-flow__arrow {
  fill: var(--color-agent-blue);
}

@keyframes dash-move {
  to {
    stroke-dashoffset: -12;
  }
}

/* 粒子：沿线流动的小圆点，激活时可见 */
.p-flow__particle {
  position: absolute;
  top: 50%;
  left: 0;
  width: 5px;
  height: 5px;
  margin-top: -2.5px;
  border-radius: 50%;
  background: var(--color-agent-blue);
  box-shadow: 0 0 8px var(--color-agent-blue);
  opacity: 0;
}

.p-flow--active .p-flow__particle {
  animation: particle-run 1.65s linear infinite;
  animation-delay: var(--p-delay);
}

@keyframes particle-run {
  0% {
    left: 0;
    opacity: 0;
  }
  12% {
    opacity: 1;
  }
  88% {
    opacity: 1;
  }
  100% {
    left: calc(100% - 8px);
    opacity: 0;
  }
}

.p-flow__label {
  position: absolute;
  top: -14px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  white-space: nowrap;
  color: #64748b;
}

.p-flow--active .p-flow__label {
  color: var(--color-agent-blue);
}
</style>
