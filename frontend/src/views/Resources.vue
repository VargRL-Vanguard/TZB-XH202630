<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  SAMPLE_RESOURCES,
  RESOURCE_TYPE_LABELS,
  deriveEasierVersion,
  type ResourceBase
} from '@/mock/fixtures/resources'
import DifficultyBadge from '@/components/DifficultyBadge.vue'
import CustomizedResource from '@/components/resource/CustomizedResource.vue'
import PracticeGuide from '@/components/resource/PracticeGuide.vue'
import TieredQuiz from '@/components/resource/TieredQuiz.vue'

/**
 * P0-4 学习资源页（3 形态：定制化资源 / 实践指南 / 分层测验）
 * 数据源：fixtures（sample_resources 逐字段搬运）。C 组列表接口 8-26 就绪后，
 * 把 load() 换成真接口调用即可（数据结构已按后端 JSON 分层）。
 * 反馈迭代：「太难了」→ 难度 -1 + 版本 +1 + 新旧对比（真环境走 D 区重生成）。
 */

// ===== 类型过滤 =====
const TYPE_FILTERS = [
  { value: 'all', label: '全部' },
  { value: 'customized_resource', label: '定制化资源' },
  { value: 'practice_guide', label: '实践指南' },
  { value: 'tiered_quiz', label: '分层测验' }
] as const
const filter = ref<string>('all')

// ===== 版本状态（反馈迭代）=====
interface VersionState {
  ver: number
  res: ResourceBase
  /** 历史：[旧版本, 新版本] 用于对比 */
  lastDiff: { from: ResourceBase; to: ResourceBase } | null
}
const versions = ref<Record<string, VersionState>>({})
for (const r of SAMPLE_RESOURCES) {
  versions.value[r.resource_id] = { ver: 1, res: r, lastDiff: null }
}

const list = computed(() =>
  SAMPLE_RESOURCES.map(
    (r) => versions.value[r.resource_id] ?? { ver: 1, res: r, lastDiff: null }
  ).filter((v) => filter.value === 'all' || v.res.type === filter.value)
)

// ===== 展开/收起 =====
const expanded = ref<Record<string, boolean>>({})

// ===== 反馈 =====
const compareVisible = ref(false)
const compareData = ref<{ from: ResourceBase; to: ResourceBase; ver: number } | null>(null)

function feedback(res: ResourceBase, kind: 'too-hard' | 'ok' | 'too-easy') {
  if (kind === 'ok') {
    ElMessage.success('已收到反馈：难度合适')
    return
  }
  const old = res
  let next: ResourceBase
  if (kind === 'too-hard') {
    if (old.difficulty <= 1) {
      ElMessage.info('已是最低难度 L1')
      return
    }
    next = deriveEasierVersion(old)
  } else {
    if (old.difficulty >= 5) {
      ElMessage.info('已是最高难度 L5')
      return
    }
    next = { ...old, difficulty: old.difficulty + 1, trigger_reason: 'feedback_too_easy' }
  }

  const state = versions.value[old.resource_id] ?? { ver: 1, res: old, lastDiff: null }
  const ver = state.ver + 1
  versions.value[old.resource_id] = { ver, res: next, lastDiff: { from: old, to: next } }
  compareData.value = { from: old, to: next, ver }
  compareVisible.value = true
  ElMessage.success(`已触发重生成：v${ver} 版本已生成（演示为本地难度调整）`)
}

function formComponent(type: string) {
  if (type === 'customized_resource') return CustomizedResource
  if (type === 'practice_guide') return PracticeGuide
  return TieredQuiz
}

function fmtPct(v: number) {
  return `${Math.round(v * 100)}%`
}
</script>

<template>
  <div class="page resources">
    <header class="res-head">
      <div>
        <h1 class="res-head__title">学习资源</h1>
        <p class="res-head__sub">按画像个性化生成的 3 形态资源 · 内容均附引用切片可溯源</p>
      </div>
      <el-radio-group v-model="filter" size="small">
        <el-radio-button v-for="f in TYPE_FILTERS" :key="f.value" :value="f.value">{{
          f.label
        }}</el-radio-button>
      </el-radio-group>
    </header>

    <!-- ===== 资源卡列表 ===== -->
    <section v-for="state in list" :key="state.res.resource_id" class="res-card">
      <div
        class="res-card__head"
        @click="expanded[state.res.resource_id] = !expanded[state.res.resource_id]"
      >
        <div class="res-card__title-wrap">
          <el-tag
            size="small"
            effect="dark"
            :type="
              state.res.type === 'tiered_quiz'
                ? 'warning'
                : state.res.type === 'practice_guide'
                  ? 'success'
                  : 'primary'
            "
          >
            {{ RESOURCE_TYPE_LABELS[state.res.type] ?? state.res.type }}
          </el-tag>
          <h2 class="res-card__title">{{ state.res.title }}</h2>
          <span v-if="state.ver > 1" class="res-card__ver">v{{ state.ver }}</span>
        </div>
        <div class="res-card__meta">
          <DifficultyBadge :level="state.res.difficulty" />
          <span class="res-card__metric">覆盖 {{ fmtPct(state.res.metrics.coverage) }}</span>
          <span class="res-card__metric">幻觉 {{ fmtPct(state.res.metrics.hallucination) }}</span>
          <span class="res-card__metric">匹配 {{ fmtPct(state.res.metrics.matchAccuracy) }}</span>
          <span class="res-card__expand">{{
            expanded[state.res.resource_id] ? '收起 ▲' : '展开使用 ▼'
          }}</span>
        </div>
      </div>

      <div class="res-card__tags">
        <el-tag v-for="kp in state.res.kp_coverage" :key="kp" size="small" effect="plain">{{
          kp
        }}</el-tag>
        <span class="res-card__trace">来源 trace：{{ state.res.source_trace_id }}</span>
      </div>

      <!-- 展开使用 -->
      <div v-if="expanded[state.res.resource_id]" class="res-card__body">
        <component :is="formComponent(state.res.type)" :resource="state.res" />
      </div>

      <!-- 反馈条 -->
      <div class="res-card__feedback">
        <span class="res-card__feedback-label">这份资源难度如何？</span>
        <el-button size="small" plain type="danger" @click="feedback(state.res, 'too-hard')"
          >太难了</el-button
        >
        <el-button size="small" plain type="success" @click="feedback(state.res, 'ok')"
          >正合适</el-button
        >
        <el-button size="small" plain type="warning" @click="feedback(state.res, 'too-easy')"
          >太简单了</el-button
        >
      </div>
    </section>

    <p v-if="!list.length" class="res-empty">该形态暂无资源</p>

    <!-- ===== 新旧版本对比对话框 ===== -->
    <el-dialog v-model="compareVisible" title="资源已重生成 · 新旧版本对比" width="480px">
      <template v-if="compareData">
        <div class="cmp">
          <div class="cmp__row cmp__row--old">
            <span class="cmp__tag">旧 v{{ compareData.ver - 1 }}</span>
            <span>难度 L{{ compareData.from.difficulty }}</span>
            <span class="cmp__id">{{ compareData.from.resource_id }}</span>
          </div>
          <div class="cmp__arrow">
            ↓ 反馈「{{
              compareData.to.trigger_reason === 'feedback_too_easy' ? '太简单了' : '太难了'
            }}」触发重生成
          </div>
          <div class="cmp__row cmp__row--new">
            <span class="cmp__tag cmp__tag--new">新 v{{ compareData.ver }}</span>
            <span>难度 L{{ compareData.to.difficulty }}</span>
            <span class="cmp__id">{{ compareData.to.resource_id }}</span>
          </div>
          <p class="cmp__note">
            质量指标保持达标：覆盖 {{ fmtPct(compareData.to.metrics.coverage) }} · 幻觉
            {{ fmtPct(compareData.to.metrics.hallucination) }} · 匹配
            {{ fmtPct(compareData.to.metrics.matchAccuracy) }}
          </p>
        </div>
      </template>
      <template #footer>
        <el-button type="primary" @click="compareVisible = false">知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.resources {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.res-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.res-head__title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}

.res-head__sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-sub);
}

/* ===== 资源卡 ===== */
.res-card {
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.res-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  flex-wrap: wrap;
  cursor: pointer;
}

.res-card__title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.res-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.res-card__ver {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  color: #ffffff;
  background: var(--color-primary);
  border-radius: 999px;
  padding: 1px 8px;
}

.res-card__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.res-card__metric {
  font-size: 12px;
  color: var(--text-sub);
}

.res-card__expand {
  font-size: 12px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.res-card__tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.res-card__trace {
  font-size: 11px;
  color: #9ca3af;
  margin-left: auto;
}

.res-card__body {
  padding: var(--sp-1) 0;
  border-top: 1px dashed var(--border-line);
  animation: res-expand 250ms var(--ease-out);
}

@keyframes res-expand {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.res-card__feedback {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: var(--sp-1);
  border-top: 1px solid #f3f4f6;
}

.res-card__feedback-label {
  font-size: 12px;
  color: var(--text-sub);
  margin-right: 4px;
}

.res-empty {
  text-align: center;
  padding: var(--sp-4);
  color: var(--text-sub);
  font-size: 13px;
}

/* ===== 对比对话框 ===== */
.cmp {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cmp__row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
}

.cmp__row--old {
  background: #f8f9fc;
  color: var(--text-sub);
}

.cmp__row--new {
  background: rgba(79, 110, 247, 0.07);
  color: var(--text-main);
  border: 1px solid rgba(79, 110, 247, 0.3);
}

.cmp__tag {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
  color: var(--text-sub);
  flex-shrink: 0;
}

.cmp__tag--new {
  background: var(--color-primary);
  color: #ffffff;
}

.cmp__id {
  font-size: 11px;
  color: #9ca3af;
  font-variant-numeric: tabular-nums;
}

.cmp__arrow {
  text-align: center;
  font-size: 12px;
  color: var(--color-warning);
}

.cmp__note {
  font-size: 12px;
  color: var(--text-sub);
  text-align: center;
}
</style>
