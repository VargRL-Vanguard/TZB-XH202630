<script setup lang="ts">
import { computed } from 'vue'

/**
 * 难度徽章组件（05 号文档 v1 规格）
 * - props：level(1-5) 资源实际难度；expected 可选学生期望难度（画像字段）
 * - 颜色梯度绿→红：1-2 绿（易）· 3 黄（中）· 4-5 红（难），全部走 CSS 变量
 * - expected 传入时显示一致性标识：一致 ✅ / 实际偏高 ↑ / 实际偏低 ↓
 */
const props = withDefaults(
  defineProps<{
    level: number
    expected?: number | null
    /** 是否显示文字标签「难度」 */
    showLabel?: boolean
  }>(),
  { expected: null, showLabel: true }
)

// 难度色阶（仅用全局语义色变量，禁写死色值）
const levelClass = computed(() => `difficulty-badge--l${Math.min(5, Math.max(1, props.level))}`)

// 一致性标识：level 对比 expected
const consistency = computed<'ok' | 'higher' | 'lower' | null>(() => {
  if (props.expected == null) return null
  if (props.level === props.expected) return 'ok'
  return props.level > props.expected ? 'higher' : 'lower'
})

const consistencyText = computed(() => {
  switch (consistency.value) {
    case 'ok':
      return '✅'
    case 'higher':
      return '偏高 ↑'
    case 'lower':
      return '偏低 ↓'
    default:
      return ''
  }
})
</script>

<template>
  <span class="difficulty-badge" :class="levelClass" :title="`难度 ${level}/5`">
    <span v-if="showLabel" class="difficulty-badge__label">难度</span>
    <span class="difficulty-badge__dots" aria-hidden="true">
      <span
        v-for="n in 5"
        :key="n"
        class="difficulty-badge__dot"
        :class="{ 'difficulty-badge__dot--on': n <= level }"
      ></span>
    </span>
    <span class="difficulty-badge__num num">{{ level }}</span>
    <span
      v-if="consistency"
      class="difficulty-badge__consistency"
      :class="`difficulty-badge__consistency--${consistency}`"
    >
      {{ consistencyText }}
    </span>
  </span>
</template>

<style scoped>
.difficulty-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid currentColor;
  background: color-mix(in srgb, currentColor 8%, transparent);
  transition: transform 200ms var(--ease-out);
}

.difficulty-badge:hover {
  transform: scale(1.04);
}

/* ===== 色阶：绿(易)→黄(中)→红(难)，语义色变量 ===== */
.difficulty-badge--l1,
.difficulty-badge--l2 {
  color: var(--color-success);
}

.difficulty-badge--l2 {
  opacity: 0.92;
}

.difficulty-badge--l3 {
  color: var(--color-warning);
}

.difficulty-badge--l4,
.difficulty-badge--l5 {
  color: var(--color-danger);
}

.difficulty-badge--l4 {
  opacity: 0.92;
}

.difficulty-badge__label {
  color: var(--text-sub);
}

.difficulty-badge__dots {
  display: inline-flex;
  gap: 2px;
}

.difficulty-badge__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.2;
}

.difficulty-badge__dot--on {
  opacity: 1;
}

.difficulty-badge__num {
  font-weight: 600;
}

/* ===== 一致性标识 ===== */
.difficulty-badge__consistency {
  padding-left: 6px;
  border-left: 1px solid color-mix(in srgb, currentColor 30%, transparent);
  white-space: nowrap;
}

.difficulty-badge__consistency--ok {
  color: var(--color-success);
}

.difficulty-badge__consistency--higher {
  color: var(--color-danger); /* 偏难：对低画像学生是风险 */
}

.difficulty-badge__consistency--lower {
  color: var(--color-warning); /* 偏易：提示不够挑战 */
}
</style>
