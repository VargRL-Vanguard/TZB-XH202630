<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onNetStateChange } from '@/api/request'
import { wsClient, type WsStatus } from '@/ws/client'

/**
 * 全局网络状态横幅（08 号契约 §0 错误矩阵）
 * - HTTP 网络失败/超时 → 黄色「服务暂不可用，已展示缓存数据」
 * - WS 重连中 → 黄色「服务连接中断，正在自动重连…」；恢复后自动消失
 */

const httpOffline = ref(false)
const wsStatus = ref<WsStatus>(wsClient.currentStatus)

let offNet: (() => void) | null = null
let offWs: (() => void) | null = null

onMounted(() => {
  offNet = onNetStateChange((offline) => {
    // 恢复在线时立即收起；掉线时展示（成功响应会持续触发 false，天然自愈）
    httpOffline.value = offline
  })
  offWs = wsClient.onStatus((s) => {
    wsStatus.value = s
  })
})

onUnmounted(() => {
  offNet?.()
  offWs?.()
})

const visible = computed(() => httpOffline.value || wsStatus.value === 'reconnecting')
const text = computed(() =>
  httpOffline.value
    ? '服务暂不可用，已展示缓存数据，恢复后将自动更新'
    : '服务连接中断，正在自动重连…'
)
</script>

<template>
  <transition name="net-banner">
    <div v-if="visible" class="net-banner" role="alert">
      <span class="net-banner__dot"></span>
      <span>{{ text }}</span>
    </div>
  </transition>
</template>

<style scoped>
.net-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  background: #fef3c7;
  border-bottom: 1px solid #f59e0b;
  color: #92400e;
  font-size: 14px;
}

.net-banner__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
  animation: net-pulse 1.2s infinite;
}

@keyframes net-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.net-banner-enter-active,
.net-banner-leave-active {
  transition:
    transform 200ms ease-out,
    opacity 200ms ease-out;
}

.net-banner-enter-from,
.net-banner-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
