<script setup lang="ts">
withDefaults(
  defineProps<{
    /** 图标（emoji 或单字符），默认空盒子 */
    icon?: string
    /** 引导文案 */
    text?: string
    /** 行动按钮文案；不传则不显示按钮 */
    actionText?: string
  }>(),
  { icon: '📭', text: '暂无数据', actionText: '' }
)

const emit = defineEmits<{ (e: 'action'): void }>()
</script>

<template>
  <div class="empty-state">
    <!-- 低干扰插画：虚线托盘 + 图标 -->
    <div class="empty-state__figure">
      <svg class="empty-state__tray" viewBox="0 0 120 80" fill="none" aria-hidden="true">
        <ellipse
          cx="60"
          cy="66"
          rx="44"
          ry="8"
          stroke="currentColor"
          stroke-width="2"
          opacity="0.35"
        />
        <path
          d="M32 62 L38 40 L82 40 L88 62"
          stroke="currentColor"
          stroke-width="2"
          stroke-linejoin="round"
          stroke-dasharray="5 4"
          opacity="0.6"
        />
        <path
          d="M44 40 L44 30 Q60 20 76 30 L76 40"
          stroke="currentColor"
          stroke-width="2"
          stroke-linejoin="round"
          opacity="0.5"
        />
      </svg>
      <span class="empty-state__icon">{{ icon }}</span>
    </div>

    <p class="empty-state__text">{{ text }}</p>

    <el-button v-if="actionText" type="primary" plain size="small" @click="emit('action')">
      {{ actionText }}
    </el-button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-1);
  padding: var(--sp-4) var(--sp-3);
  text-align: center;
  animation: empty-in 200ms var(--ease-out);
}

@keyframes empty-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 图标叠在插画上方 */
.empty-state__figure {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--sp-1);
}

.empty-state__tray {
  width: 120px;
  height: 80px;
  color: var(--color-primary);
}

.empty-state__icon {
  position: absolute;
  bottom: 18px;
  font-size: 32px;
  line-height: 1;
  filter: grayscale(0.1);
}

.empty-state__text {
  font-size: 14px;
  color: var(--text-sub);
  max-width: 320px;
}
</style>
