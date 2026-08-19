<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Fold, Expand, SwitchButton, Sunny, Moon } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

/**
 * 顶部栏（15 号任务书 T1）
 * - 高 56px：左侧折叠按钮 + 当前页标题（route.meta.title）
 * - 右侧用户胶囊：首字圆形头像 + 用户名 + 角色徽章（学生/教师/管理员）+ 登出按钮
 * - 登出：Confirm 二次确认 → auth.logout() → 跳 /login
 *   （token 清空后 App.vue 的 watch 会自动断开 WS，无需在此处理）
 */

defineProps<{ collapsed?: boolean }>()
const emit = defineEmits<{ (e: 'toggle'): void }>()

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()

// 当前页标题（路由 meta.title，守卫已保证存在）
const pageTitle = computed(() => (route.meta.title as string) || '')

// 角色徽章文案映射
const roleText = computed(() => {
  if (auth.role === 'teacher') return '教师'
  if (auth.role === 'admin') return '管理员'
  return '学生'
})

// 头像取用户 ID 首字符（auth store 无昵称字段，用 userId 展示）
const avatarChar = computed(() => (auth.userId || '?').charAt(0).toUpperCase())

// 登出（带二次确认）
async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning'
    })
    auth.logout() // 清 token → App.vue watch 自动 wsClient.close()
    router.push('/login')
  } catch {
    /* 用户取消，不做任何事 */
  }
}
</script>

<template>
  <header class="top-bar">
    <!-- 左侧：折叠开关 + 当前页标题 -->
    <div class="top-bar__left">
      <button
        class="top-bar__fold-btn"
        :title="collapsed ? '展开侧栏' : '折叠侧栏'"
        :aria-label="collapsed ? '展开侧栏' : '折叠侧栏'"
        @click="emit('toggle')"
      >
        <el-icon :size="18">
          <Expand v-if="collapsed" />
          <Fold v-else />
        </el-icon>
      </button>
      <h1 class="top-bar__title">{{ pageTitle }}</h1>
    </div>

    <!-- 右侧：主题切换 + 用户胶囊 + 登出 -->
    <div class="top-bar__right">
      <button
        class="top-bar__icon-btn"
        :title="theme.isDark ? '切换到白天模式（Alt+T）' : '切换到夜间模式（Alt+T）'"
        :aria-label="theme.isDark ? '切换到白天模式' : '切换到夜间模式'"
        @click="theme.toggle()"
      >
        <el-icon :size="18">
          <Sunny v-if="theme.isDark" />
          <Moon v-else />
        </el-icon>
      </button>
      <div class="top-bar__user" :title="auth.userId">
        <span class="top-bar__avatar">{{ avatarChar }}</span>
        <span class="top-bar__name">{{ auth.userId }}</span>
        <span class="top-bar__role" :class="`top-bar__role--${auth.role || 'student'}`">
          {{ roleText }}
        </span>
      </div>
      <button class="top-bar__logout" title="退出登录" @click="handleLogout">
        <el-icon :size="16"><SwitchButton /></el-icon>
        <span>退出</span>
      </button>
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  height: 56px; /* 任务书指定高度 */
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-line); /* 与侧栏分隔线同色 */
}

/* 图标按钮（主题切换等）：与折叠按钮同规格 */
.top-bar__icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-sub);
  cursor: pointer;
  transition:
    background-color 200ms var(--ease-out),
    color 200ms var(--ease-out),
    transform 150ms var(--ease-out);
}

.top-bar__icon-btn:hover {
  background: rgba(79, 110, 247, 0.08);
  color: var(--color-primary);
}

.top-bar__icon-btn:active {
  transform: scale(0.92) rotate(-12deg); /* 点击反馈：微缩+微转 */
}

.top-bar__icon-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

/* ===== 左侧 ===== */
.top-bar__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.top-bar__fold-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-sub);
  cursor: pointer;
  transition:
    background-color 200ms var(--ease-out),
    color 200ms var(--ease-out);
}

.top-bar__fold-btn:hover {
  background: rgba(79, 110, 247, 0.08);
  color: var(--color-primary);
}

.top-bar__fold-btn:active {
  transform: scale(0.97); /* 点击反馈：微缩，不允许位移 */
}

.top-bar__fold-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.top-bar__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ===== 右侧 ===== */
.top-bar__right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.top-bar__user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 4px;
  border-radius: 999px;
  background: var(--bg-page);
  border: 1px solid var(--border-line);
}

.top-bar__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
}

.top-bar__name {
  font-size: 13px;
  color: var(--text-main);
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-bar__role {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
}

/* 角色徽章配色（沿用语义色变量） */
.top-bar__role--student {
  color: var(--color-primary);
  background: rgba(79, 110, 247, 0.1);
}

.top-bar__role--teacher {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.1);
}

.top-bar__role--admin {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.12);
}

.top-bar__logout {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-sub);
  font-size: 13px;
  cursor: pointer;
  transition:
    background-color 200ms var(--ease-out),
    color 200ms var(--ease-out);
}

.top-bar__logout:hover {
  background: rgba(239, 68, 68, 0.08);
  color: var(--color-danger);
}

.top-bar__logout:active {
  transform: scale(0.97);
}

.top-bar__logout:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}
</style>
