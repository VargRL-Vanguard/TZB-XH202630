<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { PracticeGuideContent, ResourceBase } from '@/mock/fixtures/resources'

/**
 * 形态二：实践指南（分步可勾选，进度本地持久化）
 */
const props = defineProps<{ resource: ResourceBase }>()

const content = props.resource.content as PracticeGuideContent
const STORE_KEY = `guide-progress-${props.resource.resource_id}`

const doneSteps = ref<number[]>(load())
function load(): number[] {
  try {
    return JSON.parse(sessionStorage.getItem(STORE_KEY) ?? '[]') as number[]
  } catch {
    return []
  }
}

watch(doneSteps, (v) => sessionStorage.setItem(STORE_KEY, JSON.stringify(v)), { deep: true })

function toggle(order: number) {
  doneSteps.value = doneSteps.value.includes(order)
    ? doneSteps.value.filter((o) => o !== order)
    : [...doneSteps.value, order]
}

const progress = computed(() => Math.round((doneSteps.value.length / content.steps.length) * 100))
</script>

<template>
  <div class="guide">
    <!-- 步骤勾选进度 -->
    <div class="guide__progress">
      <span class="guide__progress-label">完成度</span>
      <span class="guide__progress-bar">
        <span class="guide__progress-fill" :style="{ width: progress + '%' }"></span>
      </span>
      <span class="guide__progress-num num">{{ progress }}%</span>
    </div>

    <label
      v-for="step in content.steps"
      :key="step.order"
      class="guide__step"
      :class="{ 'guide__step--done': doneSteps.includes(step.order) }"
    >
      <input
        type="checkbox"
        :checked="doneSteps.includes(step.order)"
        @change="toggle(step.order)"
      />
      <span class="guide__step-main">
        <span class="guide__step-head">
          <span class="guide__step-order">步骤 {{ step.order }}</span>
          <span class="guide__step-title">{{ step.title }}</span>
          <span class="guide__step-min">约 {{ step.estimated_min }} 分钟</span>
        </span>
        <span class="guide__step-content">{{ step.content }}</span>
      </span>
    </label>

    <!-- 工具清单 -->
    <div v-if="content.tools?.length" class="guide__tools">
      <h4 class="guide__sub-title">所需工具</h4>
      <el-tag v-for="t in content.tools" :key="t" size="small" type="info" effect="plain">{{
        t
      }}</el-tag>
    </div>

    <!-- 排错手册 -->
    <div v-if="content.troubleshooting?.length" class="guide__ts">
      <h4 class="guide__sub-title">常见问题排错</h4>
      <details v-for="(t, i) in content.troubleshooting" :key="i" class="guide__ts-item">
        <summary class="guide__ts-problem">问题 {{ i + 1 }}：{{ t.problem }}</summary>
        <p class="guide__ts-solution">解决：{{ t.solution }}</p>
      </details>
    </div>
  </div>
</template>

<style scoped>
.guide {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.guide__progress {
  display: flex;
  align-items: center;
  gap: 10px;
}

.guide__progress-label {
  font-size: 12px;
  color: var(--text-sub);
  flex-shrink: 0;
}

.guide__progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: var(--border-line);
  overflow: hidden;
}

.guide__progress-fill {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
  border-radius: 4px;
  transition: width 400ms var(--ease-out);
}

.guide__progress-num {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.guide__step {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f8f9fc;
  cursor: pointer;
  transition: background 200ms var(--ease-out);
}

.guide__step:hover {
  background: #f0f2fa;
}

.guide__step--done {
  background: rgba(34, 197, 94, 0.06);
}

.guide__step--done .guide__step-title,
.guide__step--done .guide__step-content {
  text-decoration: line-through;
  opacity: 0.55;
}

.guide__step input {
  margin-top: 3px;
  accent-color: var(--color-success);
}

.guide__step-main {
  min-width: 0;
  flex: 1;
}

.guide__step-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.guide__step-order {
  font-size: 11px;
  color: var(--color-primary);
  font-weight: 600;
}

.guide__step-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
}

.guide__step-min {
  font-size: 11px;
  color: var(--text-sub);
  padding: 1px 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.14);
}

.guide__step-content {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-sub);
  white-space: pre-line;
}

.guide__sub-title {
  font-size: 12px;
  color: var(--text-sub);
  margin-bottom: 6px;
}

.guide__tools {
  display: flex;
  flex-direction: column;
}

.guide__ts-item {
  padding: 8px 12px;
  border-radius: 8px;
  background: #fffbeb;
  border: 1px solid rgba(245, 158, 11, 0.25);
  font-size: 13px;
}

.guide__ts-problem {
  cursor: pointer;
  color: #92400e;
  font-weight: 500;
}

.guide__ts-solution {
  margin-top: 6px;
  color: var(--text-main);
  line-height: 1.7;
  white-space: pre-line;
}
</style>
