<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { wsClient } from '@/ws/client'
import NetBanner from '@/components/NetBanner.vue'
import AppShell from '@/components/AppShell.vue'

const auth = useAuthStore()
const route = useRoute()

// 登录后自动建连 WS；登出断开（login 页不需要连接）
watch(
  () => auth.token,
  (token) => {
    if (token) wsClient.connect(token)
    else wsClient.close()
  },
  { immediate: true }
)

// 布局切换（15 号任务书 T1）：
// - /agent-screen（meta.layout: 'full'，大屏要全屏）与登录/注册/404（meta.public）不套 AppShell
const useShell = computed(() => !route.meta.public && route.meta.layout !== 'full')
</script>

<template>
  <div class="app-root">
    <NetBanner />
    <AppShell v-if="useShell">
      <router-view />
    </AppShell>
    <router-view v-else />
  </div>
</template>

<style scoped>
.app-root {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
