import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useThemeStore } from '@/stores/theme'
import '@/styles/index.css'
// Element Plus 暗色变量：html.dark 时 el-* 组件自动切换暗色（配 stores/theme.ts）
import 'element-plus/theme-chalk/dark/css-vars.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// 主题初始化（挂载前 apply，避免暗色用户看到闪白）
useThemeStore()

app.mount('#app')
