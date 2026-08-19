<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useUiStore } from '@/stores/ui'
import { wsClient } from '@/ws/client'
import NetBanner from '@/components/NetBanner.vue'
import AppShell from '@/components/AppShell.vue'
import RouteProgress from '@/components/RouteProgress.vue'
import ShortcutsDialog from '@/components/ShortcutsDialog.vue'

const auth = useAuthStore()
const route = useRoute()
const theme = useThemeStore()
const ui = useUiStore()

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

// ============ 全局快捷键 ============
// Alt+T 昼夜切换 / Alt+B 侧栏折叠 / Ctrl+/ 快捷键面板
// 输入框/文本域内不触发（Ctrl+/ 除外），避免打字干扰
function onKeydown(e: KeyboardEvent) {
  // e.code 判物理键位，不受中文输入法/键盘布局影响（e.key 可能是 '?' 或被 IME 拦截）
  if (e.ctrlKey && (e.key === '/' || e.code === 'Slash')) {
    e.preventDefault()
    ui.shortcutsOpen = true
    return
  }
  const target = e.target as HTMLElement | null
  if (target?.closest('input, textarea, [contenteditable="true"]')) return
  if (e.altKey && !e.ctrlKey) {
    const k = e.key.toLowerCase()
    if (k === 't') {
      e.preventDefault()
      theme.toggle()
    } else if (k === 'b') {
      e.preventDefault()
      ui.toggleSide()
    }
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="app-root">
    <RouteProgress />
    <NetBanner />
    <ShortcutsDialog />
    <AppShell v-if="useShell">
      <router-view v-slot="{ Component }">
        <Transition name="page-swap" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </router-view>
    </AppShell>
    <router-view v-else v-slot="{ Component }">
      <Transition name="page-swap" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </router-view>
  </div>
</template>

<style scoped>
.app-root {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
