<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  getStudentInfo,
  getStudentDimensions,
  getStudentBehavior,
  getStudentKnowledge,
  type StudentInfo,
  type StudentDimensions,
  type StudentBehavior,
  type KnowledgePoint
} from '@/api/student'
import { updateProfile } from '@/api/auth'
import { useThemeStore } from '@/stores/theme'
import {
  useChart,
  CHART_COLORS,
  chartTextColor,
  chartSplitColor,
  type EChartsOption
} from '@/utils/echarts'
import MetricCard from '@/components/MetricCard.vue'
import Skeleton from '@/components/Skeleton.vue'
import ErrorState from '@/components/ErrorState.vue'

/**
 * P0-3 学情仪表盘（B 区真接口）
 * - 指标卡（MetricCard 800ms 滚动 + tabular-nums）
 * - 六维雷达 + 每日学习时长折线（周/月/学期切换）
 * - 知识点掌握列表（弱项红色醒目）
 * - 画像编辑（A 区 PUT /api/user/profile，保存后刷新回显）
 */

const route = useRoute()
const auth = useAuthStore()
const studentId = computed(() => (route.query.studentId as string) || auth.userId)

// ===== 数据状态 =====
const loading = ref(true)
const errorMsg = ref('')
const info = ref<StudentInfo | null>(null)
const dims = ref<StudentDimensions | null>(null)
const behavior = ref<StudentBehavior | null>(null)
const knowledge = ref<KnowledgePoint[]>([])

async function load() {
  if (!studentId.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    const [infoRes, dimsRes, behRes, kpRes] = await Promise.all([
      getStudentInfo(studentId.value),
      getStudentDimensions(studentId.value),
      getStudentBehavior(studentId.value, period.value),
      getStudentKnowledge(studentId.value)
    ])
    info.value = infoRes
    dims.value = dimsRes
    behavior.value = behRes
    knowledge.value = kpRes
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(studentId, load)

// ===== 周期切换（周/月/学期，300ms 过渡由图表 css transition 承担）=====
const period = ref<'week' | 'month' | 'semester'>('week')
const periodLabel: Record<typeof period.value, string> = {
  week: '本周',
  month: '本月',
  semester: '本学期'
}
const periodSwitching = ref(false)

watch(period, async () => {
  periodSwitching.value = true
  try {
    behavior.value = await getStudentBehavior(studentId.value, period.value)
  } finally {
    periodSwitching.value = false
  }
})

// ===== 指标 =====
const metrics = computed(() => info.value?.metrics ?? null)
const weakCount = computed(() => info.value?.learnerProfile.weakKPs.length ?? 0)

// ===== 雷达图 =====
const DIM_NAMES: Array<[keyof StudentDimensions, string]> = [
  ['comprehension', '理解'],
  ['application', '应用'],
  ['analysis', '分析'],
  ['evaluation', '评价'],
  ['creation', '创造'],
  ['collaboration', '协作']
]

const radarEl = ref<HTMLElement | null>(null)

function renderRadar() {
  if (!dims.value || loading.value) return
  const d = dims.value
  setRadar({
    tooltip: {},
    radar: {
      indicator: DIM_NAMES.map(([, name]) => ({ name, max: 100 })),
      radius: '68%',
      axisName: { color: chartTextColor() },
      splitArea: {
        areaStyle: {
          color: useThemeStore().isDark
            ? ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.05)']
            : ['#ffffff', '#f8f9fc']
        }
      },
      axisLine: { lineStyle: { color: chartSplitColor() } },
      splitLine: { lineStyle: { color: chartSplitColor() } }
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: DIM_NAMES.map(([k]) => d[k]),
            name: '能力维度',
            areaStyle: { color: 'rgba(79, 110, 247, 0.25)' },
            lineStyle: { color: CHART_COLORS.primary, width: 2 },
            itemStyle: { color: CHART_COLORS.primary }
          }
        ]
      }
    ]
  } as EChartsOption)
}

const { setOption: setRadar } = useChart(radarEl, renderRadar)

watch([dims, loading], renderRadar, { immediate: true })

// ===== 折线图（每日学习分钟）=====
const lineEl = ref<HTMLElement | null>(null)

function renderLine() {
  if (!behavior.value || loading.value) return
  const series = behavior.value.dailySeries ?? []
  setLine({
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 分钟` },
    grid: { left: 44, right: 16, top: 24, bottom: 28 },
    xAxis: {
      type: 'category',
      data: series.map((d) => d.date.slice(5)),
      axisLabel: { color: chartTextColor(), fontSize: 11 },
      axisLine: { lineStyle: { color: chartSplitColor() } }
    },
    yAxis: {
      type: 'value',
      name: '分钟',
      nameTextStyle: { color: chartTextColor() },
      axisLabel: { color: chartTextColor(), fontSize: 11 },
      splitLine: { lineStyle: { color: chartSplitColor() } }
    },
      series: [
        {
          type: 'line',
          smooth: true,
          symbolSize: 6,
          data: series.map((d) => d.minutes),
          lineStyle: { color: CHART_COLORS.primary, width: 2.5 },
          itemStyle: { color: CHART_COLORS.primary },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(79, 110, 247, 0.28)' },
                { offset: 1, color: 'rgba(79, 110, 247, 0.02)' }
              ]
            }
          }
        }
      ]
  } as EChartsOption)
}

const { setOption: setLine } = useChart(lineEl, renderLine)

watch([behavior, loading, periodSwitching], renderLine, { immediate: true })

// ===== 知识点（弱项红色醒目）=====
function kpTone(kp: KnowledgePoint): 'weak' | 'mid' | 'ok' {
  if (kp.mastery < 60 || kp.status === 'not-started') return 'weak'
  if (kp.mastery < 85 || kp.status === 'learning') return 'mid'
  return 'ok'
}
const kpToneText: Record<string, string> = { weak: '薄弱', mid: '巩固中', ok: '已掌握' }

// ===== 画像编辑 =====
const dialogVisible = ref(false)
const saving = ref(false)
const form = ref({
  education: '',
  major: '',
  theoryTestScore: null as number | null,
  weakKPs: [] as string[],
  strongKPs: [] as string[]
})
const kpInput = ref<'weak' | 'strong' | null>(null)
const kpInputValue = ref('')

function openEdit() {
  const p = info.value?.learnerProfile
  form.value = {
    education: p?.education ?? '',
    major: p?.major ?? '',
    theoryTestScore: p?.theoryTestScore ?? null,
    weakKPs: [...(p?.weakKPs ?? [])],
    strongKPs: [...(p?.strongKPs ?? [])]
  }
  dialogVisible.value = true
}

function addKp(list: 'weakKPs' | 'strongKPs') {
  const v = kpInputValue.value.trim()
  if (v && !form.value[list].includes(v)) form.value[list].push(v)
  kpInputValue.value = ''
}

async function saveProfile() {
  saving.value = true
  try {
    await updateProfile({
      education: form.value.education || undefined,
      major: form.value.major || undefined,
      theoryTestScore: form.value.theoryTestScore ?? undefined,
      weakKPs: form.value.weakKPs,
      strongKPs: form.value.strongKPs
    })
    ElMessage.success('画像已更新')
    dialogVisible.value = false
    await load() // 保存后刷新回显
  } catch {
    /* request.ts 已统一 toast */
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page dashboard">
    <!-- ===== 欢迎区 ===== -->
    <section class="dash-hero">
      <div>
        <h1 class="dash-hero__title">你好，{{ info?.name || auth.userId }}</h1>
        <p class="dash-hero__sub">
          {{ info?.learnerProfile.education }} · {{ info?.learnerProfile.major || '未设置专业' }}
          <template v-if="info?.learnerProfile.theoryTestScore != null">
            · 理论模考 {{ info.learnerProfile.theoryTestScore }} 分
          </template>
        </p>
      </div>
      <el-button type="primary" plain :icon="Edit" @click="openEdit">编辑画像</el-button>
    </section>

    <!-- ===== 加载态 ===== -->
    <template v-if="loading">
      <section class="dash-metrics">
        <Skeleton v-for="n in 4" :key="n" variant="card" />
      </section>
      <section class="dash-charts">
        <Skeleton variant="chart" />
        <Skeleton variant="chart" />
      </section>
    </template>

    <!-- ===== 错误态 ===== -->
    <section v-else-if="errorMsg" class="dash-panel">
      <ErrorState text="学情数据加载失败，请稍后重试" @retry="load" />
    </section>

    <template v-else>
      <!-- ===== 指标卡 ===== -->
      <section class="dash-metrics">
        <MetricCard
          v-if="metrics"
          label="累计学习时长"
          :value="metrics.studyHours"
          unit="小时"
          :trend="metrics.trend"
          :trend-value="metrics.trendValue"
        />
        <MetricCard v-if="metrics" label="任务完成率" :value="metrics.completionRate" unit="%" />
        <MetricCard v-if="metrics" label="平均分" :value="metrics.avgScore" unit="分" />
        <MetricCard label="薄弱知识点" :value="weakCount" unit="个">
          <template #foot>
            <span class="dash-weak-foot">建议优先补强（点击列表定位）</span>
          </template>
        </MetricCard>
      </section>

      <!-- ===== 图表区 ===== -->
      <section class="dash-charts">
        <div class="dash-panel">
          <h2 class="dash-panel__title">能力维度画像</h2>
          <div ref="radarEl" class="dash-chart dash-chart--radar"></div>
        </div>
        <div class="dash-panel">
          <div class="dash-panel__head">
            <h2 class="dash-panel__title">每日学习时长</h2>
            <el-radio-group v-model="period" size="small">
              <el-radio-button value="week">周</el-radio-button>
              <el-radio-button value="month">月</el-radio-button>
              <el-radio-button value="semester">学期</el-radio-button>
            </el-radio-group>
          </div>
          <div
            ref="lineEl"
            class="dash-chart"
            :class="{ 'dash-chart--switching': periodSwitching }"
          ></div>
          <p v-if="behavior" class="dash-panel__foot">
            {{ periodLabel[period] }}：共 {{ behavior.activityCount }} 次活动 · 完成
            {{ behavior.completedCount }} 次 · 累计
            {{ Math.round(behavior.totalStudyMinutes / 60) }} 小时
          </p>
        </div>
      </section>

      <!-- ===== 知识点掌握 ===== -->
      <section class="dash-panel">
        <h2 class="dash-panel__title">知识点掌握（{{ knowledge.length }}）</h2>
        <div v-if="knowledge.length" class="dash-kps">
          <div
            v-for="kp in knowledge"
            :key="kp.kp_id"
            class="kp"
            :class="`kp--${kpTone(kp)}`"
            :title="`${kp.kp_name} · 掌握度 ${kp.mastery}%`"
          >
            <span class="kp__name">{{ kp.kp_name }}</span>
            <span class="kp__bar">
              <span class="kp__bar-fill" :style="{ width: kp.mastery + '%' }"></span>
            </span>
            <span class="kp__pct num">{{ kp.mastery }}%</span>
            <span class="kp__tag">{{ kpToneText[kpTone(kp)] }}</span>
          </div>
        </div>
        <p v-else class="dash-empty">暂无知识点数据</p>
      </section>
    </template>

    <!-- ===== 画像编辑对话框 ===== -->
    <el-dialog v-model="dialogVisible" title="编辑学习者画像" width="520px">
      <el-form label-width="92px">
        <el-form-item label="教育层次">
          <el-select v-model="form.education" placeholder="选择教育层次" clearable>
            <el-option label="本科" value="本科" />
            <el-option label="高职" value="高职" />
            <el-option label="硕士" value="硕士" />
            <el-option label="在职" value="在职" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业">
          <el-input v-model="form.major" placeholder="如：智能制造工程" maxlength="32" />
        </el-form-item>
        <el-form-item label="理论模考分">
          <el-input-number v-model="form.theoryTestScore" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="薄弱知识点">
          <div class="kp-editor">
            <el-tag
              v-for="kp in form.weakKPs"
              :key="kp"
              type="danger"
              closable
              @close="form.weakKPs = form.weakKPs.filter((k) => k !== kp)"
            >
              {{ kp }}
            </el-tag>
            <el-input
              v-if="kpInput === 'weak'"
              v-model="kpInputValue"
              size="small"
              class="kp-editor__input"
              placeholder="输入 kp 编号回车添加"
              @keyup.enter="addKp('weakKPs')"
              @blur="addKp('weakKPs'); kpInput = null"
            />
            <el-button
              v-else
              size="small"
              @click="kpInput = 'weak'; kpInputValue = ''"
              >+ 添加</el-button
            >
          </div>
        </el-form-item>
        <el-form-item label="优势知识点">
          <div class="kp-editor">
            <el-tag
              v-for="kp in form.strongKPs"
              :key="kp"
              type="success"
              closable
              @close="form.strongKPs = form.strongKPs.filter((k) => k !== kp)"
            >
              {{ kp }}
            </el-tag>
            <el-input
              v-if="kpInput === 'strong'"
              v-model="kpInputValue"
              size="small"
              class="kp-editor__input"
              placeholder="输入 kp 编号回车添加"
              @keyup.enter="addKp('strongKPs')"
              @blur="addKp('strongKPs'); kpInput = null"
            />
            <el-button
              v-else
              size="small"
              @click="kpInput = 'strong'; kpInputValue = ''"
              >+ 添加</el-button
            >
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

/* ===== 欢迎区 ===== */
.dash-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  color: #ffffff;
}

.dash-hero__title {
  font-size: 20px;
  font-weight: 600;
}

.dash-hero__sub {
  margin-top: 6px;
  font-size: 13px;
  opacity: 0.88;
}

/* ===== 指标卡 ===== */
.dash-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
}

.dash-weak-foot {
  font-size: 12px;
  color: var(--color-danger);
}

/* ===== 图表区 ===== */
.dash-charts {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: var(--sp-2);
}

.dash-panel {
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.dash-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--sp-1);
}

.dash-panel__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: var(--sp-1);
}

.dash-panel__foot {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-sub);
  text-align: right;
}

.dash-chart {
  height: 260px;
  transition: opacity 300ms var(--ease-out);
}

.dash-chart--switching {
  opacity: 0.35;
}

.dash-chart--radar {
  height: 300px;
}

/* ===== 知识点 ===== */
.dash-kps {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--sp-1) var(--sp-2);
}

.kp {
  display: grid;
  grid-template-columns: 88px 1fr 48px 52px;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 12px;
}

.kp__name {
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kp__bar {
  height: 6px;
  border-radius: 3px;
  background: var(--border-line);
  overflow: hidden;
}

.kp__bar-fill {
  display: block;
  height: 100%;
  border-radius: 3px;
  background: var(--color-success);
  transition: width 600ms var(--ease-out);
}

.kp__pct {
  text-align: right;
  color: var(--text-sub);
  font-variant-numeric: tabular-nums;
}

.kp__tag {
  text-align: center;
  font-size: 11px;
  padding: 1px 0;
  border-radius: 999px;
}

/* 弱项红色醒目 */
.kp--weak {
  background: rgba(239, 68, 68, 0.06);
}

.kp--weak .kp__name {
  color: var(--color-danger);
  font-weight: 600;
}

.kp--weak .kp__bar-fill {
  background: var(--color-danger);
}

.kp--weak .kp__tag {
  color: #ffffff;
  background: var(--color-danger);
}

.kp--mid .kp__bar-fill {
  background: var(--color-warning);
}

.kp--mid .kp__tag {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.12);
}

.kp--ok .kp__tag {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.12);
}

.dash-empty {
  padding: var(--sp-2);
  font-size: 13px;
  color: var(--text-sub);
  text-align: center;
}

/* ===== kp 标签编辑器 ===== */
.kp-editor {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.kp-editor__input {
  width: 180px;
}

/* ===== 窄屏 ===== */
@media (max-width: 900px) {
  .dash-metrics {
    grid-template-columns: repeat(2, 1fr);
  }

  .dash-charts {
    grid-template-columns: 1fr;
  }
}
</style>
