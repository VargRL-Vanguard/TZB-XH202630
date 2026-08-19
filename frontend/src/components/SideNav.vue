<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Odometer,
  Guide,
  Reading,
  MagicStick,
  Calendar,
  ChatDotRound,
  Bell,
  Monitor,
  DataAnalysis,
  User
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

/**
 * 全局侧边导航（15 号任务书 T1）
 * - 固定宽度 220px，折叠态 64px（icon-only，由父级 AppShell 控制）
 * - 菜单分组：学习中心 / 智能服务 / 演示支持
 * - 按角色显隐：student 隐藏「学生列表」；teacher 隐藏「协同大屏」；admin 全显
 * - 当前路由高亮：主色左边条 3px + 浅蓝底；hover 200ms 过渡
 */

interface MenuItem {
  path: string
  title: string
  icon: unknown
  /** 需要隐藏此菜单的角色列表 */
  hiddenFor?: string[]
}

interface MenuGroup {
  label: string
  items: MenuItem[]
}

// 菜单结构（路由一律用现有路由表，08 号契约 §7，不新增不重命名）
const menuGroups: MenuGroup[] = [
  {
    label: '学习中心',
    items: [
      { path: '/dashboard', title: '仪表盘', icon: Odometer },
      { path: '/learning-path', title: '学习路径', icon: Guide },
      { path: '/resources', title: '学习资源', icon: Reading },
      { path: '/suggestions', title: '学习建议', icon: MagicStick },
      { path: '/activity', title: '学习记录', icon: Calendar }
    ]
  },
  {
    label: '智能服务',
    items: [
      { path: '/ai-chat', title: 'AI 辅导', icon: ChatDotRound },
      { path: '/chat', title: '消息', icon: Bell }
    ]
  },
  {
    label: '演示支持',
    items: [
      { path: '/agent-screen', title: '协同大屏', icon: Monitor, hiddenFor: ['teacher'] },
      { path: '/quality', title: '质量看板', icon: DataAnalysis },
      { path: '/students', title: '学生列表', icon: User, hiddenFor: ['student'] }
    ]
  }
]

// 折叠状态由父级 AppShell 统一控制（≤1200px 自动折叠 / 手动切换）
defineProps<{ collapsed?: boolean }>()

const route = useRoute()
const auth = useAuthStore()

// 按角色过滤菜单组（组内全被过滤时整组隐藏）
const visibleGroups = computed(() =>
  menuGroups
    .map((g) => ({
      ...g,
      items: g.items.filter((it) => !it.hiddenFor?.includes(auth.role))
    }))
    .filter((g) => g.items.length > 0)
)

// 是否为当前激活菜单（前缀匹配，兼容未来子路由）
function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <aside class="side-nav" :class="{ 'side-nav--collapsed': collapsed }">
    <!-- 品牌区：折叠时只显示 logo -->
    <div class="side-nav__brand">
      <span class="side-nav__logo" aria-hidden="true"></span>
      <span v-if="!collapsed" class="side-nav__brand-text">
        <span class="side-nav__brand-name">XH-202630</span>
        <span class="side-nav__brand-sub">挑战杯项目</span>
      </span>
    </div>

    <!-- 菜单：分组标题 + 菜单项 -->
    <nav class="side-nav__menu">
      <div v-for="group in visibleGroups" :key="group.label" class="side-nav__group">
        <div v-if="!collapsed" class="side-nav__group-label">{{ group.label }}</div>
        <router-link
          v-for="item in group.items"
          :key="item.path"
          :to="item.path"
          class="side-nav__item"
          :class="{ 'side-nav__item--active': isActive(item.path) }"
          :title="collapsed ? item.title : undefined"
        >
          <el-icon class="side-nav__item-icon" :size="18">
            <component :is="item.icon" />
          </el-icon>
          <span v-if="!collapsed" class="side-nav__item-text">{{ item.title }}</span>
        </router-link>
      </div>
    </nav>

    <!-- 底部版本信息 -->
    <div v-if="!collapsed" class="side-nav__footer">v1.0 · F1 前端</div>
  </aside>
</template>

<style scoped>
.side-nav {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-card); /* 任务书指定：侧栏白底 */
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 200ms var(--ease-out); /* 折叠动画 200ms ease-out */
}

.side-nav--collapsed {
  width: 64px;
}

/* ===== 品牌区 ===== */
.side-nav__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  min-height: 56px; /* 与 TopBar 等高对齐 */
  border-bottom: 1px solid var(--border-line);
}

.side-nav--collapsed .side-nav__brand {
  justify-content: center;
  padding: 14px 0;
}

.side-nav__logo {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  flex-shrink: 0;
  /* 主→辅品牌渐变 + 网络节点造型，呼应“多智能体协同” */
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.9) 0 2px, transparent 3px),
    radial-gradient(circle at 70% 65%, rgba(255, 255, 255, 0.55) 0 2px, transparent 3px),
    linear-gradient(135deg, var(--color-primary), var(--color-secondary));
}

.side-nav__brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  white-space: nowrap;
}

.side-nav__brand-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: 0.5px;
}

.side-nav__brand-sub {
  font-size: 11px;
  color: var(--text-sub);
}

/* ===== 菜单 ===== */
.side-nav__menu {
  flex: 1;
  padding: 8px;
}

.side-nav__group {
  margin-bottom: 4px;
}

.side-nav__group-label {
  padding: 12px 12px 6px;
  font-size: 11px;
  color: var(--text-sub);
  letter-spacing: 1px;
}

.side-nav__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 2px;
  border-radius: 8px;
  color: var(--text-main);
  text-decoration: none;
  font-size: 14px;
  transition:
    background-color 200ms var(--ease-out),
    color 200ms var(--ease-out);
}

.side-nav--collapsed .side-nav__item {
  justify-content: center;
  padding: 10px 0;
}

/* 键盘可达性：focus 可见描边 */
.side-nav__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.side-nav__item:hover {
  background: rgba(79, 110, 247, 0.08); /* 任务书指定浅蓝底 */
}

/* 激活态：主色左边条 3px + 浅蓝底 */
.side-nav__item--active {
  background: rgba(79, 110, 247, 0.08);
  color: var(--color-primary);
  font-weight: 600;
}

.side-nav__item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 2px;
  background: var(--color-primary);
}

.side-nav__item-icon {
  flex-shrink: 0;
}

.side-nav__item-text {
  white-space: nowrap;
}

/* ===== 底部 ===== */
.side-nav__footer {
  padding: 12px 16px;
  font-size: 11px;
  color: var(--text-sub);
  border-top: 1px solid var(--border-line);
}
</style>
