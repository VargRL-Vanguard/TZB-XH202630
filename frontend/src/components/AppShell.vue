<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import SideNav from '@/components/SideNav.vue'
import TopBar from '@/components/TopBar.vue'

/**
 * 全局导航壳（15 号任务书 T1）
 * - 布局：左侧 SideNav 固定 220px + 右侧（TopBar 56px + 内容区）
 * - 内容区渲染默认插槽（App.vue 传入 <router-view>，页面自带 page-in 过渡）
 * - 折叠：视口 ≤1200px 自动折叠成 64px icon-only；手动切换优先级更高
 * - 侧栏与内容区之间 1px 分隔线 #EEF0F4；右内容区背景 --bg-page
 */

// 折叠状态：manualOverride 为 true 时以手动操作为准，不再跟随窗口宽度
const collapsed = ref(false)
let manualOverride = false

function updateByViewport() {
  if (manualOverride) return
  collapsed.value = window.innerWidth <= 1200
}

function toggleCollapse() {
  manualOverride = true
  collapsed.value = !collapsed.value
}

onMounted(() => {
  updateByViewport()
  window.addEventListener('resize', updateByViewport)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateByViewport)
})
</script>

<template>
  <div class="app-shell">
    <SideNav :collapsed="collapsed" />
    <div class="app-shell__main">
      <TopBar :collapsed="collapsed" @toggle="toggleCollapse" />
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
  border-left: 1px solid #eef0f4; /* 任务书指定分隔线 */
}

.app-shell__content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
</style>
