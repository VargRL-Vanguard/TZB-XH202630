<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { CircleCheckFilled, CircleCloseFilled, WarningFilled } from '@element-plus/icons-vue'
import { getQualityLatest, type QualityReport } from '@/api/quality'
import MetricCard from '@/components/MetricCard.vue'
import Skeleton from '@/components/Skeleton.vue'
import ErrorState from '@/components/ErrorState.vue'

/**
 * P0-5 质量看板（GET /api/quality/latest，读 docs/quality_reports/latest.json）
 * 3 项硬指标数值与报告逐项一致（禁止写死）：幻觉率 / 匹配准确率 / 知识点覆盖率
 */

const loading = ref(true)
const errorMsg = ref('')
const report = ref<QualityReport | null>(null)

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    report.value = await getQualityLatest()
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const m = computed(() => report.value?.metrics)
const thresholds = computed(() => report.value?.thresholds)

/** 0.041 → 4.1 */
function pct(v: number, digits = 1) {
  return +(v * 100).toFixed(digits)
}

const verdicts: Record<string, { text: string; tone: 'ok' | 'fail' }> = {
  pass: { text: '通过', tone: 'ok' },
  retry: { text: '待优化', tone: 'fail' },
  fail: { text: '未通过', tone: 'fail' }
}
</script>

<template>
  <div class="page quality">
    <header class="q-head">
      <div>
        <h1 class="q-head__title">内容质量看板</h1>
        <p class="q-head__sub">
          3 项硬指标（幻觉率 / 匹配准确率 / 覆盖率）· 数据源：最近一次 quality_check 报告
        </p>
      </div>
      <span v-if="report" class="q-head__time">报告生成时间：{{ report.generated_at }}</span>
    </header>

    <!-- 加载态 -->
    <template v-if="loading">
      <section class="q-metrics">
        <Skeleton v-for="n in 3" :key="n" variant="card" />
      </section>
      <Skeleton :rows="6" />
    </template>

    <!-- 错误态（含 404 暂无报告） -->
    <section v-else-if="errorMsg" class="q-panel">
      <ErrorState
        :text="`质量报告加载失败：${errorMsg}（可先运行 A-05 quality_check 生成报告）`"
        @retry="load"
      />
    </section>

    <template v-else-if="report && m">
      <!-- 总体结论 -->
      <div class="q-verdict" :class="m.passed ? 'q-verdict--pass' : 'q-verdict--fail'">
        <el-icon :size="18">
          <CircleCheckFilled v-if="m.passed" />
          <CircleCloseFilled v-else />
        </el-icon>
        <span>{{ m.passed ? '本次质量检查全部通过' : '存在未达标指标，需要处理' }}</span>
        <span class="q-verdict__meta"
          >画像 {{ m.profile_count }} 组 · 知识库切片 {{ report.kb_chunk_count }} 条 · 覆盖知识点
          {{ report.kb_covered_kp_count }} 个</span
        >
      </div>

      <!-- 3 项硬指标卡（数值直接来自报告，禁止写死） -->
      <section class="q-metrics">
        <MetricCard label="幻觉率" :value="pct(m.hallucination_rate, 2)" unit="%" :decimals="2">
          <template #foot>
            <span class="q-foot" :class="m.hallucination_pass ? 'q-foot--ok' : 'q-foot--fail'">
              {{ m.hallucination_pass ? '✓' : '✕' }} 阈值 &lt;
              {{ pct(thresholds?.hallucination_max ?? 0) }}%
            </span>
          </template>
        </MetricCard>

        <MetricCard label="匹配准确率" :value="pct(m.match_accuracy)" unit="%">
          <template #foot>
            <span class="q-foot" :class="m.match_accuracy_pass ? 'q-foot--ok' : 'q-foot--fail'">
              {{ m.match_accuracy_pass ? '✓' : '✕' }} 阈值 ≥
              {{ pct(thresholds?.match_accuracy_min ?? 0) }}%
            </span>
          </template>
        </MetricCard>

        <MetricCard label="知识点覆盖率" :value="pct(m.coverage)" unit="%">
          <template #foot>
            <span class="q-foot" :class="m.coverage_pass ? 'q-foot--ok' : 'q-foot--fail'">
              {{ m.coverage_pass ? '✓' : '✕' }} 阈值 ≥ {{ pct(thresholds?.coverage_min ?? 0) }}%
            </span>
          </template>
        </MetricCard>
      </section>

      <!-- 3 画像明细表 -->
      <section class="q-panel">
        <h2 class="q-panel__title">画像级明细（{{ report.details.length }} 组）</h2>
        <el-table :data="report.details" stripe style="width: 100%">
          <el-table-column prop="label" label="画像" min-width="110" fixed>
            <template #default="{ row }">
              <span class="q-cell-strong">{{ row.label }}</span>
              <span class="q-cell-sub">{{ row.profile_id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="弱项知识点" min-width="180">
            <template #default="{ row }">
              <el-tag
                v-for="kp in row.weak_kps.slice(0, 3)"
                :key="kp"
                size="small"
                type="danger"
                effect="plain"
                class="q-kp-tag"
              >
                {{ kp }}
              </el-tag>
              <span v-if="row.weak_kps.length > 3" class="q-cell-sub"
                >+{{ row.weak_kps.length - 3 }}</span
              >
            </template>
          </el-table-column>
          <el-table-column label="诊断置信度" width="110" align="center">
            <template #default="{ row }">
              <span class="num">{{ row.confidence }}</span>
            </template>
          </el-table-column>
          <el-table-column label="难度 期望/实际" width="110" align="center">
            <template #default="{ row }">
              <span class="num"
                >L{{ row.expected_difficulty }} / L{{ row.resource_difficulty }}</span
              >
            </template>
          </el-table-column>
          <el-table-column label="引用切片" width="90" align="center">
            <template #default="{ row }">
              <span class="num">{{ row.cited_chunks }}</span>
            </template>
          </el-table-column>
          <el-table-column label="幻觉率" width="90" align="center">
            <template #default="{ row }">
              <span class="num">{{ pct(row.hallucination_rate, 2) }}%</span>
            </template>
          </el-table-column>
          <el-table-column label="弱项覆盖" width="90" align="center">
            <template #default="{ row }">
              <span class="num">{{ pct(row.resource_vs_weak_coverage) }}%</span>
            </template>
          </el-table-column>
          <el-table-column label="D-06 审核" width="100" align="center">
            <template #default="{ row }">
              <span
                class="q-audit"
                :class="`q-audit--${verdicts[row.audit_verdict]?.tone ?? 'fail'}`"
              >
                {{ verdicts[row.audit_verdict]?.text ?? row.audit_verdict }}
                <span class="num">{{ row.audit_score }}</span>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="trace" min-width="150">
            <template #default="{ row }">
              <span class="q-trace" :title="row.trace_id">{{ row.trace_id }}</span>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <!-- 警告 -->
      <section v-if="report.warnings?.length" class="q-warnings">
        <h2 class="q-panel__title">
          <el-icon class="q-warn-icon"><WarningFilled /></el-icon>
          非阻塞警告（{{ report.warnings.length }}）
        </h2>
        <ul class="q-warn-list">
          <li v-for="(w, i) in report.warnings" :key="i">{{ w }}</li>
        </ul>
      </section>
    </template>
  </div>
</template>

<style scoped>
.quality {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.q-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.q-head__title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}

.q-head__sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-sub);
}

.q-head__time {
  font-size: 12px;
  color: var(--text-sub);
  font-variant-numeric: tabular-nums;
}

/* ===== 总体结论 ===== */
.q-verdict {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px var(--sp-2);
  border-radius: var(--card-radius);
  font-size: 14px;
  font-weight: 600;
}

.q-verdict--pass {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.08);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.q-verdict--fail {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.q-verdict__meta {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
  color: var(--text-sub);
}

/* ===== 指标卡 ===== */
.q-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-2);
}

.q-foot {
  font-size: 12px;
}

.q-foot--ok {
  color: var(--color-success);
}

.q-foot--fail {
  color: var(--color-danger);
}

/* ===== 明细表 ===== */
.q-panel {
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.q-panel__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: var(--sp-1);
  display: flex;
  align-items: center;
  gap: 6px;
}

.q-cell-strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.q-cell-sub {
  font-size: 11px;
  color: #9ca3af;
}

.q-kp-tag {
  margin-right: 4px;
}

.q-audit {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.q-audit--ok {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.1);
}

.q-audit--fail {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.12);
}

.q-trace {
  font-size: 11px;
  color: #9ca3af;
  font-variant-numeric: tabular-nums;
}

/* ===== 警告 ===== */
.q-warnings {
  padding: var(--sp-2);
  background: #fffbeb;
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: var(--card-radius);
}

.q-warn-icon {
  color: var(--color-warning);
}

.q-warn-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  line-height: 1.9;
  color: #92400e;
}

@media (max-width: 900px) {
  .q-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
