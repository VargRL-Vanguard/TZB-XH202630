<script setup lang="ts">
import { watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { wsClient } from '@/ws/client'
import NetBanner from '@/components/NetBanner.vue'

const auth = useAuthStore()

// 登录后自动建连 WS；登出断开（login 页不需要连接）
watch(
  () => auth.token,
  (token) => {
    if (token) wsClient.connect(token)
    else wsClient.close()
  },
  { immediate: true }
)
</script>

<template>
  <div class="app-root">
    <NetBanner />
    <router-view />
  </div>
</template>

<style scoped>
.app-root {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
