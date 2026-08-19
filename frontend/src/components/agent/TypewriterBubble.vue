<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'

/**
 * 打字机气泡（大屏 thinking 事件逐字显示）
 * - text 变化时从头逐字打出（30ms/字，长文本自动加速保证 3s 内完成）
 * - prefers-reduced-motion 直接显示全文
 * - 完成后 emit('done')
 */
const props = defineProps<{ text: string; speed?: number }>()
const emit = defineEmits<{ (e: 'done'): void }>()

const shown = ref('')
const typing = ref(false)

let timer: ReturnType<typeof setInterval> | null = null

function stop() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  typing.value = false
}

function run() {
  stop()
  const full = props.text ?? ''
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduce || !full) {
    shown.value = full
    emit('done')
    return
  }
  shown.value = ''
  typing.value = true
  // 每字步进间隔：默认 30ms，超过 100 字自动压缩到 3s 内打完
  const step = Math.max(props.speed ?? 30, Math.ceil(3000 / full.length))
  let i = 0
  timer = setInterval(() => {
    i += 1
    shown.value = full.slice(0, i)
    if (i >= full.length) {
      stop()
      emit('done')
    }
  }, step)
}

watch(() => props.text, run, { immediate: true })

onBeforeUnmount(stop)
</script>

<template>
  <div class="tw-bubble" :class="{ 'tw-bubble--typing': typing }">
    <span class="tw-bubble__text">{{ shown }}</span>
    <span v-if="typing" class="tw-bubble__caret" aria-hidden="true"></span>
  </div>
</template>

<style scoped>
.tw-bubble {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.6;
  background: color-mix(in srgb, var(--agent-theme, #38bdf8) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--agent-theme, #38bdf8) 22%, transparent);
  word-break: break-all;
}

.tw-bubble__caret {
  width: 2px;
  height: 14px;
  background: var(--agent-theme, #38bdf8);
  animation: caret-blink 0.7s step-end infinite;
}

@keyframes caret-blink {
  50% {
    opacity: 0;
  }
}
</style>
