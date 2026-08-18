<script setup lang="ts">
withDefaults(
  defineProps<{
    /** 一句话原因（禁止传堆栈/code 原文，组件本身也不接受 detail 字段） */
    text?: string
    /** 重试按钮文案；不传则不显示按钮 */
    retryText?: string
  }>(),
  { text: '加载失败，请稍后重试', retryText: '重试' }
)

const emit = defineEmits<{ (e: 'retry'): void }>()
</script>

<template>
  <div class="error-state" role="alert">
    <!-- 插画：断线插头 -->
    <div class="error-state__figure">
      <svg viewBox="0 0 96 72" fill="none" aria-hidden="true">
        <!-- 左右两段断开的线缆 -->
        <path
          d="M8 36 H34"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          opacity="0.8"
        />
        <path
          d="M62 36 H88"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          opacity="0.8"
        />
        <!-- 插头（左）与插座（右） -->
        <rect x="32" y="26" width="14" height="20" rx="3" fill="currentColor" opacity="0.85" />
        <rect
          x="50"
          y="24"
          width="14"
          height="24"
          rx="3"
          stroke="currentColor"
          stroke-width="2"
          opacity="0.6"
        />
        <!-- 断开火花 -->
        <path
          d="M48 22 L46 14 M48 50 L46 58"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        />
      </svg>
    </div>

    <p class="error-state__text">{{ text }}</p>

    <el-button v-if="retryText" size="small" @click="emit('retry')">{{ retryText }}</el-button>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-1);
  padding: var(--sp-4) var(--sp-3);
  text-align: center;
  animation: error-in 200ms var(--ease-out);
}

@keyframes error-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-state__figure {
  color: var(--color-danger);
}

.error-state__figure svg {
  width: 96px;
  height: 72px;
}

.error-state__text {
  font-size: 14px;
  color: var(--text-sub);
  max-width: 320px;
}
</style>
