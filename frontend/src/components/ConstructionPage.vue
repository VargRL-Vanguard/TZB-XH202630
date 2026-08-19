<script setup lang="ts">
/**
 * 品牌化「建设中」占位页组件（15 号任务书 T2）
 * - 居中卡片：圆角 10px + 卡片阴影变量；顶部品牌渐变条（主→辅，高 4px）
 * - 蓝图风格自绘 SVG 脚手架线稿图标
 * - 文案：标题 + 「建设中 · 预计 {eta} 交付 · {owner}」+ 主色按钮跳 fallbackLink
 * - 背景：低干扰浅色网格（opacity ≤ 0.06）
 * - dark 属性：大屏页占位深色版（背景 --bg-screen，文字 #94A3B8）
 */
withDefaults(
  defineProps<{
    /** 页面标题 */
    title: string
    /** 负责团队，如「B 组」 */
    owner: string
    /** 预计交付日期，如「8-22」 */
    eta: string
    /** 引导跳转链接（如 /chat），不传则不显示按钮 */
    fallbackLink?: string
    /** 引导按钮文案 */
    fallbackText?: string
    /** 深色版（协同大屏用） */
    dark?: boolean
  }>(),
  { fallbackLink: '', fallbackText: '先去消息页' }
)
</script>

<template>
  <div class="construction" :class="{ 'construction--dark': dark }">
    <div class="construction__card">
      <!-- 顶部品牌渐变条 -->
      <div class="construction__brand-bar"></div>

      <!-- 蓝图风格脚手架线稿 -->
      <svg class="construction__icon" viewBox="0 0 96 96" fill="none" aria-hidden="true">
        <!-- 外框蓝图 -->
        <rect
          x="14"
          y="20"
          width="68"
          height="56"
          rx="4"
          stroke="currentColor"
          stroke-width="2"
          stroke-dasharray="5 4"
        />
        <!-- 屋顶吊臂 -->
        <path
          d="M14 44 L48 20 L82 44"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <!-- 内部脚手架网格 -->
        <path
          d="M32 32 L32 76 M64 32 L64 76 M14 58 L82 58"
          stroke="currentColor"
          stroke-width="1.5"
          opacity="0.55"
        />
        <!-- 砖块 -->
        <rect x="40" y="48" width="8" height="8" rx="1" fill="currentColor" opacity="0.85" />
        <rect x="52" y="64" width="8" height="8" rx="1" fill="currentColor" opacity="0.55" />
        <rect x="24" y="64" width="8" height="8" rx="1" fill="currentColor" opacity="0.35" />
        <!-- 吊钩 -->
        <path
          d="M48 20 L48 8 M48 8 L70 8"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        />
        <circle cx="72" cy="8" r="3" stroke="currentColor" stroke-width="2" />
      </svg>

      <!-- 标题与交付信息 -->
      <h2 class="construction__title">{{ title }}</h2>
      <p class="construction__meta">
        <span class="construction__tag">建设中</span>
        <span>预计 {{ eta }} 交付 · {{ owner }}</span>
      </p>
      <p class="construction__desc">该模块正在紧张开发中，交付后将在导航中直接可用。</p>

      <!-- 引导按钮 -->
      <el-button
        v-if="fallbackLink"
        type="primary"
        class="construction__btn"
        @click="$router.push(fallbackLink)"
      >
        {{ fallbackText }} →
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.construction {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-3);
  background:
    /* 低干扰浅色网格，opacity 远低于 0.06 上限 */
    repeating-linear-gradient(0deg, rgba(31, 41, 55, 0.03) 0 1px, transparent 1px 32px),
    repeating-linear-gradient(90deg, rgba(31, 41, 55, 0.03) 0 1px, transparent 1px 32px),
    radial-gradient(circle at 50% 30%, rgba(79, 110, 247, 0.05), transparent 60%), var(--bg-page);
}

/* ===== 深色版（协同大屏占位） ===== */
.construction--dark {
  background:
    repeating-linear-gradient(0deg, rgba(148, 163, 184, 0.04) 0 1px, transparent 1px 32px),
    repeating-linear-gradient(90deg, rgba(148, 163, 184, 0.04) 0 1px, transparent 1px 32px),
    radial-gradient(circle at 50% 30%, rgba(56, 189, 248, 0.05), transparent 60%), var(--bg-screen);
}

/* ===== 居中卡片 ===== */
.construction__card {
  position: relative;
  width: 100%;
  max-width: 420px;
  padding: var(--sp-4) var(--sp-3) var(--sp-3);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: var(--bg-card);
  border-radius: var(--card-radius); /* 10px */
  box-shadow: var(--card-shadow);
  overflow: hidden;
  animation: construction-in 300ms var(--ease-out);
}

.construction--dark .construction__card {
  background: #10182e;
  box-shadow:
    0 0 0 1px rgba(148, 163, 184, 0.15),
    0 8px 32px rgba(0, 0, 0, 0.4);
}

@keyframes construction-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 顶部品牌渐变条：主→辅，高 4px */
.construction__brand-bar {
  position: absolute;
  width: 100%;
  height: 4px;
  margin: calc(-1 * var(--sp-4)) calc(-1 * var(--sp-3)) var(--sp-3);
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
}

/* 蓝图线稿图标 */
.construction__icon {
  width: 96px;
  height: 96px;
  color: var(--color-primary);
}

.construction--dark .construction__icon {
  color: var(--color-agent-blue);
}

.construction__title {
  margin-top: var(--sp-2);
  font-size: 20px;
  font-weight: 600;
  color: var(--text-main);
}

.construction--dark .construction__title {
  color: #e2e8f0;
}

.construction__meta {
  margin-top: var(--sp-1);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-sub);
}

.construction--dark .construction__meta {
  color: #94a3b8; /* 任务书指定深色版文字色 */
}

.construction__tag {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  color: #ffffff;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
}

.construction__desc {
  margin-top: var(--sp-1);
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-sub);
}

.construction--dark .construction__desc {
  color: #94a3b8;
}

.construction__btn {
  margin-top: var(--sp-2);
  min-width: 160px;
}
</style>
