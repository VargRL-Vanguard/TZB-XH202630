import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/**
 * 全路由表（08 号契约 §7 页面路由约定）
 * - 守卫：未登录访问业务页 → 跳 /login（带 redirect 回跳）
 * - 404 中文页 + 返回首页按钮
 * - 切换路由同步 document.title
 */

/** 按角色跳首页（契约 §1.2：student→仪表盘；teacher→学生列表；admin→质量看板） */
export function roleHome(role: string): string {
  if (role === 'teacher') return '/students'
  if (role === 'admin') return '/quality'
  return '/dashboard'
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', public: true }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '学习仪表盘' }
  },
  {
    path: '/activity',
    name: 'activity',
    component: () => import('@/views/Activity.vue'),
    meta: { title: '学习记录' }
  },
  {
    path: '/resources',
    name: 'resources',
    component: () => import('@/views/Resources.vue'),
    meta: { title: '学习资源' }
  },
  {
    path: '/learning-path',
    name: 'learning-path',
    component: () => import('@/views/LearningPath.vue'),
    meta: { title: '学习路径' }
  },
  {
    path: '/suggestions',
    name: 'suggestions',
    component: () => import('@/views/Suggestions.vue'),
    meta: { title: '学习建议' }
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('@/views/Chat.vue'),
    meta: { title: '消息' }
  },
  {
    path: '/ai-chat',
    name: 'ai-chat',
    component: () => import('@/views/AiChat.vue'),
    meta: { title: 'AI 辅导' }
  },
  {
    path: '/agent-screen',
    name: 'agent-screen',
    component: () => import('@/views/AgentScreen.vue'),
    meta: { title: '多智能体协同大屏' }
  },
  {
    path: '/quality',
    name: 'quality',
    component: () => import('@/views/Quality.vue'),
    meta: { title: '质量看板' }
  },
  {
    path: '/students',
    name: 'students',
    component: () => import('@/views/Students.vue'),
    meta: { title: '学生列表' }
  },
  {
    path: '/404',
    name: 'not-found',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在', public: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  // 已登录访问登录/注册 → 回角色首页
  if (to.meta.public && auth.isLoggedIn && (to.name === 'login' || to.name === 'register')) {
    return { path: roleHome(auth.role), replace: true }
  }
  if (!to.meta.public && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath }, replace: true }
  }
  return true
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || ''
  document.title = title
    ? `${title} · 领域知识个性化生成与多智能体协同决策系统`
    : '领域知识个性化生成与多智能体协同决策系统'
})

export default router
