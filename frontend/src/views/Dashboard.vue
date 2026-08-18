<script setup lang="ts">
import { computed } from 'vue'
import {
  Guide,
  Reading,
  MagicStick,
  Calendar,
  ChatDotRound,
  Bell,
  Monitor
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

/**
 * 学习仪表盘占位页（15 号任务书 T2 特殊处理）
 * B 组开工前它是学生登录首页，不能像坏页：
 * - 顶部欢迎语 + 「学情仪表盘建设中」提示条
 * - 指标卡骨架屏示意（模拟真实仪表盘布局，呼吸 1.5s 循环）
 * - 常用功能导航卡（学生可见的页面入口，避免迷路）
 */

const auth = useAuthStore()
const greeting = computed(() => `你好，${auth.userId || '同学'}`)

// 学生常用入口（均为现有路由，不含学生列表）
const entries = [
  { path: '/learning-path', title: '学习路径', desc: '个性化学习路线规划', icon: Guide },
  { path: '/resources', title: '学习资源', desc: '按画像推荐的资源', icon: Reading },
  { path: '/suggestions', title: '学习建议', desc: '针对弱项的改进建议', icon: MagicStick },
  { path: '/activity', title: '学习记录', desc: '学习行为与日历', icon: Calendar },
  { path: '/ai-chat', title: 'AI 辅导', desc: '一对一智能答疑', icon: ChatDotRound },
  { path: '/chat', title: '消息', desc: '与系统的会话消息', icon: Bell },
  { path: '/agent-screen', title: '协同大屏', desc: '多智能体协同演示', icon: Monitor }
]
</script>

<template>
  <div class="page dashboard-ph">
    <!-- 欢迎区 -->
    <section class="dashboard-ph__hero">
      <h1 class="dashboard-ph__title">{{ greeting }}</h1>
      <p class="dashboard-ph__sub">领域知识个性化生成与多智能体协同决策系统</p>
      <div class="dashboard-ph__notice">
        <span class="dashboard-ph__notice-dot"></span>
        <span>学情仪表盘建设中 · B 组预计 8-24 交付，下方功能已可用</span>
      </div>
    </section>

    <!-- 指标卡骨架屏示意：模拟真实仪表盘首屏（4 张指标卡 + 2 张图表位） -->
    <section class="dashboard-ph__skeleton" aria-label="仪表盘骨架屏示意">
      <div v-for="n in 4" :key="`m${n}`" class="sk sk--metric">
        <div class="sk__line sk__line--sm"></div>
        <div class="sk__line sk__line--num num"></div>
        <div class="sk__line sk__line--xs"></div>
      </div>
      <div class="sk sk--chart">
        <div class="sk__line sk__line--sm"></div>
        <div class="sk__chart-body"></div>
      </div>
      <div class="sk sk--chart">
        <div class="sk__line sk__line--sm"></div>
        <div class="sk__chart-body sk__chart-body--bars"></div>
      </div>
    </section>

    <!-- 常用功能导航 -->
    <section class="dashboard-ph__nav">
      <h2 class="dashboard-ph__section-title">常用功能</h2>
      <div class="dashboard-ph__grid">
        <router-link v-for="e in entries" :key="e.path" :to="e.path" class="entry-card">
          <span class="entry-card__icon">
            <el-icon :size="20"><component :is="e.icon" /></el-icon>
          </span>
          <span class="entry-card__text">
            <span class="entry-card__title">{{ e.title }}</span>
            <span class="entry-card__desc">{{ e.desc }}</span>
          </span>
        </router-link>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard-ph {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

/* ===== 欢迎区 ===== */
.dashboard-ph__hero {
  padding: var(--sp-3);
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  color: #ffffff;
}

.dashboard-ph__title {
  font-size: 22px;
  font-weight: 600;
}

.dashboard-ph__sub {
  margin-top: 8px;
  font-size: 13px;
  opacity: 0.85;
}

.dashboard-ph__notice {
  margin-top: var(--sp-2);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 13px;
}

.dashboard-ph__notice-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-warning);
  animation: notice-pulse 1.5s infinite;
}

@keyframes notice-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.35;
  }
}

/* ===== 骨架屏示意 ===== */
.dashboard-ph__skeleton {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
}

.sk {
  padding: var(--sp-2);
  background: #ffffff;
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.sk__line {
  height: 12px;
  border-radius: 6px;
  background: #e5e7eb;
  animation: sk-breathe 1.5s infinite ease-in-out; /* 规范：骨架呼吸 1.5s */
}

.sk__line--sm {
  width: 40%;
  margin-bottom: 12px;
}

.sk__line--num {
  width: 64%;
  height: 26px;
  margin-bottom: 12px;
}

.sk__line--xs {
  width: 56%;
  height: 10px;
}

.sk--chart {
  grid-column: span 2;
}

.sk__chart-body {
  height: 140px;
  border-radius: 8px;
  background:
    linear-gradient(#e5e7eb 1px, transparent 1px) 0 100% / 100% 33.3%,
    #eef0f4;
  animation: sk-breathe 1.5s infinite ease-in-out;
}

.sk__chart-body--bars {
  background:
    repeating-linear-gradient(90deg, #e5e7eb 0 18px, transparent 18px 36px) 0 100% / 100% 70%,
    #eef0f4;
}

@keyframes sk-breathe {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.45;
  }
}

/* ===== 导航区 ===== */
.dashboard-ph__section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
}

.dashboard-ph__grid {
  margin-top: var(--sp-2);
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--sp-2);
}

.entry-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: var(--sp-2);
  background: #ffffff;
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  text-decoration: none;
  transition:
    box-shadow 200ms var(--ease-out),
    transform 200ms var(--ease-out);
}

.entry-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.entry-card:active {
  transform: scale(0.98); /* 点击反馈：微缩 */
}

.entry-card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.entry-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  flex-shrink: 0;
  color: var(--color-primary);
  background: rgba(79, 110, 247, 0.08);
}

.entry-card__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.entry-card__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
}

.entry-card__desc {
  font-size: 12px;
  color: var(--text-sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 窄屏适配：指标卡两列 */
@media (max-width: 900px) {
  .dashboard-ph__skeleton {
    grid-template-columns: repeat(2, 1fr);
  }

  .sk--chart {
    grid-column: span 2;
  }
}
</style>
