import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 全局 UI 状态
 * - sideCollapsed：侧栏折叠（从 AppShell 本地状态上提，快捷键 Alt+B 也要控制它）
 *   视口 ≤1200px 自动折叠；手动切换后 manualOverride 优先
 * - shortcutsOpen：快捷键说明面板（Ctrl+/ 唤起）
 */
export const useUiStore = defineStore('ui', () => {
  const sideCollapsed = ref(false)
  let manualOverride = false

  function updateByViewport() {
    if (manualOverride) return
    sideCollapsed.value = window.innerWidth <= 1200
  }

  function toggleSide() {
    manualOverride = true
    sideCollapsed.value = !sideCollapsed.value
  }

  const shortcutsOpen = ref(false)

  return { sideCollapsed, updateByViewport, toggleSide, shortcutsOpen }
})
