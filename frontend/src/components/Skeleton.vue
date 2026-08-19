<script setup lang="ts">
import { computed } from 'vue'

/**
 * 骨架屏组件（05 号文档 v1 规格）
 * - props：rows 行数（默认 3）；variant 'card' | 'text' | 'chart'
 * - 呼吸动画 1.5s 循环（全局 prefers-reduced-motion 已自动降级）
 * - 结构模拟真实内容布局：text=多行文本 / card=头像+标题+正文+按钮 / chart=标题+图区
 */
const props = withDefaults(
  defineProps<{
    /** 骨架行数 */
    rows?: number
    /** 骨架形态 */
    variant?: 'card' | 'text' | 'chart'
  }>(),
  { rows: 3, variant: 'text' }
)

// 文本形态：最后一行短一些，贴近真实段落收尾
const textRows = computed<number[]>(() => {
  const n = Math.max(1, props.rows)
  const list: number[] = []
  for (let i = 0; i < n; i++) {
    list.push(i === n - 1 && n > 1 ? 55 : 100)
  }
  return list
})
</script>

<template>
  <!-- 文本形态：模拟一段文章 -->
  <div
    v-if="variant === 'text'"
    class="skeleton skeleton--text"
    aria-busy="true"
    aria-hidden="true"
  >
    <div
      v-for="(w, i) in textRows"
      :key="i"
      class="skeleton__bar"
      :style="{ width: w + '%' }"
    ></div>
  </div>

  <!-- 卡片形态：头像 + 标题 + 两行正文 + 底部操作条 -->
  <div
    v-else-if="variant === 'card'"
    class="skeleton skeleton--card"
    aria-busy="true"
    aria-hidden="true"
  >
    <div class="skeleton__head">
      <div class="skeleton__avatar"></div>
      <div class="skeleton__head-lines">
        <div class="skeleton__bar" style="width: 60%"></div>
        <div class="skeleton__bar skeleton__bar--thin" style="width: 35%"></div>
      </div>
    </div>
    <div class="skeleton__bar" style="width: 100%"></div>
    <div class="skeleton__bar" style="width: 92%"></div>
    <div class="skeleton__card-actions">
      <div class="skeleton__chip"></div>
      <div class="skeleton__chip skeleton__chip--wide"></div>
    </div>
  </div>

  <!-- 图表形态：标题 + 图表主体（折线占位） -->
  <div v-else class="skeleton skeleton--chart" aria-busy="true" aria-hidden="true">
    <div class="skeleton__bar skeleton__bar--title" style="width: 40%"></div>
    <div class="skeleton__chart">
      <div class="skeleton__grid-lines">
        <div v-for="n in 4" :key="n" class="skeleton__grid-line"></div>
      </div>
      <div class="skeleton__area"></div>
    </div>
    <div class="skeleton__legend">
      <div v-for="n in 3" :key="n" class="skeleton__chip"></div>
    </div>
  </div>
</template>

<style scoped>
/* ===== 公共：呼吸动画 1.5s 循环 ===== */
.skeleton__bar,
.skeleton__avatar,
.skeleton__chip,
.skeleton__area {
  background: #e5e7eb;
  animation: skeleton-breathe 1.5s infinite ease-in-out;
}

@keyframes skeleton-breathe {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.45;
  }
}

/* ===== 文本形态 ===== */
.skeleton--text {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  width: 100%;
}

.skeleton__bar {
  height: 14px;
  border-radius: 7px;
}

.skeleton__bar--thin {
  height: 10px;
}

.skeleton__bar--title {
  height: 16px;
  margin-bottom: var(--sp-1);
}

/* ===== 卡片形态 ===== */
.skeleton--card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.skeleton__head {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  margin-bottom: var(--sp-1);
}

.skeleton__avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  flex-shrink: 0;
}

.skeleton__head-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skeleton__card-actions {
  display: flex;
  gap: var(--sp-1);
  margin-top: var(--sp-1);
}

.skeleton__chip {
  width: 72px;
  height: 26px;
  border-radius: 13px;
}

.skeleton__chip--wide {
  width: 108px;
}

/* ===== 图表形态 ===== */
.skeleton--chart {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.skeleton__chart {
  position: relative;
  height: 160px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-page);
}

/* 网格线：贴近 ECharts 默认网格观感 */
.skeleton__grid-lines {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  padding: 12px 0;
}

.skeleton__grid-line {
  height: 1px;
  background: #e5e7eb;
}

/* 面积占位：模拟折线图主体 */
.skeleton__area {
  position: absolute;
  left: 8%;
  right: 12%;
  bottom: 16px;
  height: 62%;
  border-radius: 8px 20px 6px 4px / 12px 30px 4px 4px;
  opacity: 0.8;
}

.skeleton__legend {
  display: flex;
  gap: var(--sp-1);
}
</style>
