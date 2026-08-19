<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import SideNav from '@/components/SideNav.vue'
import TopBar from '@/components/TopBar.vue'
import { useUiStore } from '@/stores/ui'

/**
 * 全局导航壳（15 号任务书 T1）
 * - 布局：左侧 SideNav 固定 220px + 右侧（TopBar 56px + 内容区）
 * - 折叠状态存 ui store（快捷键 Alt+B 同源控制）：视口 ≤1200px 自动折叠，手动优先
 * - 右内容区背景 --bg-page，与侧栏 1px 分隔线 --border-line
 */
const ui = useUiStore()

onMounted(() => {
  ui.updateByViewport()
  window.addEventListener('resize', ui.updateByViewport)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', ui.updateByViewport)
})
</script>

<template>
  <div class="app-shell">
    <SideNav :collapsed="ui.sideCollapsed" />
    <div class="app-shell__main">
      <TopBar :collapsed="ui.sideCollapsed" @toggle="ui.toggleSide()" />
      <main class="app-shell__content">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden; /* 滚动交给内容区，整页无横向滚动条 */
}

.app-shell__main {
  flex: 1;
  min-width: 0; /* 防止内容撑破布局产生横向滚动 */
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
  border-left: 1px solid var(--border-line); /* 任务书指定分隔线 */
}

.app-shell__content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
</style>
