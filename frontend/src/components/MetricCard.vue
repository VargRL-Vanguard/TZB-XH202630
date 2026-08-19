<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

/**
 * 指标卡组件（05 号文档 v1 规格，字段对齐 08 号契约 §2）
 * - props：label 标签 / value 数值 / unit 单位
 *   trend ('up'|'down'|null) ← 对应 GET /api/student/metrics 的 trend 字段
 *   trendValue 变化量数值 ← 对应同接口的 trendValue 字段
 * - 数字进视口滚动增长动画 800ms ease-out（0→目标值）；tabular-nums 不跳动
 * - prefers-reduced-motion 下直接显示终值
 */
const props = withDefaults(
  defineProps<{
    label: string
    value: number
    unit?: string
    trend?: 'up' | 'down' | null
    trendValue?: number | null
    /** 小数位数（默认 0；幻觉率 4.10 需传 2） */
    decimals?: number
  }>(),
  { unit: '', trend: null, trendValue: null, decimals: 0 }
)

const rootEl = ref<HTMLElement | null>(null)
const displayValue = ref(0)

let observer: IntersectionObserver | null = null
let rafId = 0
let animated = false

// 格式化：千分位 + 固定小数位
function format(n: number): string {
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals
  })
}

// 0→目标值 800ms ease-out 滚动
function runCountUp() {
  cancelAnimationFrame(rafId)
  const target = props.value
  if (target <= 0) {
    displayValue.value = target
    return
  }
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduceMotion) {
    displayValue.value = target
    return
  }
  const duration = 800
  const start = performance.now()
  const tick = (now: number) => {
    const p = Math.min(1, (now - start) / duration)
    const eased = 1 - Math.pow(1 - p, 3) // ease-out cubic
    displayValue.value = target * eased
    if (p < 1) rafId = requestAnimationFrame(tick)
    else displayValue.value = target
  }
  rafId = requestAnimationFrame(tick)
}

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((e) => e.isIntersecting) && !animated) {
        animated = true
        runCountUp()
        observer?.disconnect()
      }
    },
    { threshold: 0.3 }
  )
  if (rootEl.value) observer.observe(rootEl.value)
})

// 数值更新时重新滚动（如切换学生画像）
watch(
  () => props.value,
  () => {
    if (animated) runCountUp()
  }
)

onBeforeUnmount(() => {
  observer?.disconnect()
  cancelAnimationFrame(rafId)
})
</script>

<template>
  <div ref="rootEl" class="metric-card" :class="`metric-card--trend-${trend ?? 'none'}`">
    <span class="metric-card__label">{{ label }}</span>
    <div class="metric-card__value-row">
      <span class="metric-card__value num">{{ format(displayValue) }}</span>
      <span v-if="unit" class="metric-card__unit">{{ unit }}</span>
      <span v-if="trend" class="metric-card__trend" :class="`metric-card__trend--${trend}`">
        {{ trend === 'up' ? '↑' : '↓' }}
        <template v-if="trendValue != null">{{ trendValue }}</template>
      </span>
    </div>
    <slot name="foot"></slot>
  </div>
</template>

<style scoped>
.metric-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  transition: box-shadow 200ms var(--ease-out);
}

.metric-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.metric-card__label {
  font-size: 13px;
  color: var(--text-sub);
}

.metric-card__value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}

.metric-card__value {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-main);
  font-variant-numeric: tabular-nums; /* 规范：指标数字等宽，跳动不错位 */
}

.metric-card__unit {
  font-size: 13px;
  color: var(--text-sub);
}

/* 趋势：up 绿 / down 红（08 契约 trend 字段） */
.metric-card__trend {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  font-variant-numeric: tabular-nums;
}

.metric-card__trend--up {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.1);
}

.metric-card__trend--down {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.1);
}
</style>
