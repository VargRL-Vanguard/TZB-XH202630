import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

/**
 * 昼夜主题 store
 * - isDark 切换 → html 根节点挂/摘 `dark` class
 *   - Element Plus：main.ts 已引入 dark/css-vars.css，html.dark 下组件自动换暗色变量
 *   - 项目样式：styles/index.css 的 html.dark 块覆盖全局 CSS 变量
 * - localStorage 持久化；首次进入跟随系统 prefers-color-scheme
 */
const KEY = 'tzb-theme'

function initial(): boolean {
  const saved = localStorage.getItem(KEY)
  if (saved === 'dark') return true
  if (saved === 'light') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(initial())

  function apply(dark: boolean) {
    document.documentElement.classList.toggle('dark', dark)
  }

  // 立即应用一次（store 建立时机在 main.ts 挂载前，避免暗色闪白）
  apply(isDark.value)

  watch(
    isDark,
    (dark) => {
      apply(dark)
      localStorage.setItem(KEY, dark ? 'dark' : 'light')
    },
    { immediate: false }
  )

  function toggle() {
    isDark.value = !isDark.value
  }

  return { isDark, toggle }
})
