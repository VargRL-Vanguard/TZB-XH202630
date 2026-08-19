<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  getActivityStats,
  getActivityCalendar,
  getActivityRecent,
  getActivityCourses,
  type ActivityStats,
  type ActivityItem,
  type CalendarDay,
  type ActivityFilter
} from '@/api/activity'
import MetricCard from '@/components/MetricCard.vue'
import Skeleton from '@/components/Skeleton.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'

/**
 * P2 学习记录页（B 区真接口：stats / calendar / recent / courses）
 * - 顶部 4 指标卡：活动总数 / 完成率 / 学习时长 / 平均分
 * - 左栏：课程活动列表（all/进行中/已完成/未开始 筛选）
 * - 右栏：4 周学习日历热力 + 最近活动
 */

const route = useRoute()
const auth = useAuthStore()
const studentId = computed(() => (route.query.studentId as string) || auth.userId)

const loading = ref(true)
const errorMsg = ref('')
const stats = ref<ActivityStats | null>(null)
const calendar = ref<CalendarDay[]>([])
const recent = ref<ActivityItem[]>([])

const filter = ref<ActivityFilter>('all')
const coursesLoading = ref(false)
const courses = ref<ActivityItem[]>([])

async function load() {
  if (!studentId.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    const [st, cal, rec] = await Promise.all([
      getActivityStats(studentId.value),
      getActivityCalendar(studentId.value, 28),
      getActivityRecent(studentId.value, 7, 8)
    ])
    stats.value = st
    calendar.value = cal.items ?? []
    recent.value = rec.items ?? []
    await loadCourses()
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadCourses() {
  coursesLoading.value = true
  try {
    const res = await getActivityCourses(studentId.value, filter.value)
    courses.value = res.items ?? []
  } catch {
    courses.value = []
  } finally {
    coursesLoading.value = false
  }
}

onMounted(load)
watch(studentId, load)
watch(filter, loadCourses)

const TYPE_META: Record<string, { label: string; cls: string }> = {
  course: { label: '课程', cls: 'act-type--course' },
  exercise: { label: '练习', cls: 'act-type--exercise' },
  test: { label: '测验', cls: 'act-type--test' },
  discussion: { label: '讨论', cls: 'act-type--discussion' }
}

function typeMeta(t: string) {
  return TYPE_META[t] ?? { label: t, cls: 'act-type--course' }
}

const STATUS_META: Record<string, { label: string; cls: string }> = {
  completed: { label: '已完成', cls: 'act-status--done' },
  'in-progress': { label: '进行中', cls: 'act-status--doing' },
  'not-started': { label: '未开始', cls: 'act-status--todo' }
}

function statusMeta(s: string) {
  return STATUS_META[s] ?? { label: s, cls: 'act-status--todo' }
}

/** 日历热力：按分钟分 4 档 */
const maxMinutes = computed(() => Math.max(1, ...calendar.value.map((d) => d.minutes)))

function heatLevel(d: CalendarDay) {
  if (!d.minutes) return 0
  const ratio = d.minutes / maxMinutes.value
  if (ratio > 0.66) return 3
  if (ratio > 0.33) return 2
  return 1
}

function fmtDateShort(iso: string) {
  return iso ? iso.slice(5).replace('-', '/') : ''
}

/** 一行 7 格（周） */
const calendarWeeks = computed(() => {
  const weeks: CalendarDay[][] = []
  for (let i = 0; i < calendar.value.length; i += 7) {
    weeks.push(calendar.value.slice(i, i + 7))
  }
  return weeks
})

const todayIso = new Date().toISOString().slice(0, 10)

const FILTER_TABS: { value: ActivityFilter; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'in-progress', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'not-started', label: '未开始' }
]
</script>

<template>
  <div class="page act">
    <header class="act-head">
      <div>
        <h1 class="act-head__title">学习记录</h1>
        <p class="act-head__sub">活动完成情况 · 学习时长 · 最近 4 周日历热力</p>
      </div>
    </header>

    <!-- 加载态 -->
    <template v-if="loading">
      <section class="act-metrics">
        <Skeleton v-for="n in 4" :key="n" variant="card" />
      </section>
      <div class="act-grid">
        <Skeleton :rows="7" />
        <Skeleton :rows="6" />
      </div>
    </template>

    <!-- 错误态 -->
    <section v-else-if="errorMsg" class="act-panel">
      <ErrorState :text="`学习记录加载失败：${errorMsg}`" @retry="load" />
    </section>

    <template v-else>
      <!-- 指标卡 -->
      <section class="act-metrics">
        <MetricCard label="活动总数" :value="stats?.totalActivities ?? 0" unit="次" />
        <MetricCard label="完成率" :value="stats?.completionRate ?? 0" unit="%" />
        <MetricCard
          label="累计学习"
          :value="Math.round((stats?.totalStudyMinutes ?? 0) / 60)"
          unit="小时"
        />
        <MetricCard label="平均分" :value="stats?.avgScore ?? 0" unit="分" />
      </section>

      <div class="act-grid">
        <!-- 左：课程活动列表 -->
        <section class="act-panel">
          <div class="act-panel__head">
            <h2 class="act-panel__title">课程与活动</h2>
            <nav class="act-filter">
              <button
                v-for="t in FILTER_TABS"
                :key="t.value"
                class="act-filter__btn"
                :class="{ 'act-filter__btn--on': filter === t.value }"
                @click="filter = t.value"
              >
                {{ t.label }}
              </button>
            </nav>
          </div>

          <div v-if="coursesLoading" class="act-list">
            <Skeleton v-for="n in 4" :key="n" :rows="2" />
          </div>
          <EmptyState v-else-if="courses.length === 0" icon="📭" text="该筛选下暂无活动记录" />
          <ul v-else class="act-list">
            <li v-for="a in courses" :key="a.activityId" class="act-item">
              <div class="act-item__main">
                <div class="act-item__titleline">
                  <span class="act-type" :class="typeMeta(a.activityType).cls">{{
                    typeMeta(a.activityType).label
                  }}</span>
                  <span class="act-item__name">{{ a.resourceName }}</span>
                  <span class="act-status" :class="statusMeta(a.status).cls">{{
                    statusMeta(a.status).label
                  }}</span>
                </div>
                <div class="act-item__meta">
                  <span class="num">{{ fmtDateShort(a.startTime) }}</span>
                  <span>· {{ a.durationMinutes }} 分钟</span>
                  <template v-if="a.score != null">
                    <span
                      >· 得分 <span class="num act-item__score">{{ a.score }}</span></span
                    >
                  </template>
                  <span class="act-item__kps">
                    <span v-for="kp in a.kpTags.slice(0, 3)" :key="kp" class="act-kp">{{
                      kp
                    }}</span>
                  </span>
                </div>
                <el-progress
                  v-if="a.status !== 'not-started'"
                  :percentage="a.progress"
                  :stroke-width="5"
                  :show-text="false"
                  class="act-item__bar"
                />
              </div>
            </li>
          </ul>
        </section>

        <!-- 右：日历 + 最近活动 -->
        <div class="act-side">
          <!-- 4 周热力日历 -->
          <section class="act-panel">
            <h2 class="act-panel__title">学习日历（近 4 周）</h2>
            <div class="act-calendar" role="img" aria-label="近 4 周学习日历热力图">
              <div v-for="(week, wi) in calendarWeeks" :key="wi" class="act-calendar__week">
                <div
                  v-for="d in week"
                  :key="d.date"
                  class="act-calendar__cell"
                  :class="[
                    `act-calendar__cell--l${heatLevel(d)}`,
                    { 'act-calendar__cell--today': d.date === todayIso }
                  ]"
                  :title="`${d.date}：学习 ${d.minutes} 分钟 · ${d.count} 次活动`"
                ></div>
              </div>
            </div>
            <div class="act-calendar__legend">
              <span>少</span>
              <span class="act-calendar__cell act-calendar__cell--l0"></span>
              <span class="act-calendar__cell act-calendar__cell--l1"></span>
              <span class="act-calendar__cell act-calendar__cell--l2"></span>
              <span class="act-calendar__cell act-calendar__cell--l3"></span>
              <span>多</span>
            </div>
          </section>

          <!-- 最近活动 -->
          <section class="act-panel">
            <h2 class="act-panel__title">最近活动</h2>
            <EmptyState v-if="recent.length === 0" icon="📭" text="近 7 天暂无活动" />
            <ul v-else class="act-recent">
              <li v-for="a in recent" :key="a.activityId" class="act-recent__item">
                <span class="act-type" :class="typeMeta(a.activityType).cls">{{
                  typeMeta(a.activityType).label
                }}</span>
                <span class="act-recent__name">{{ a.resourceName }}</span>
                <span class="act-recent__time num">{{ fmtDateShort(a.startTime) }}</span>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.act {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.act-head__title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}

.act-head__sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-sub);
}

.act-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
}

.act-grid {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(0, 5fr);
  gap: var(--sp-2);
  align-items: start;
}

.act-side {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.act-panel {
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.act-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-1);
  flex-wrap: wrap;
  margin-bottom: var(--sp-2);
}

.act-panel__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
}

/* ===== 筛选 ===== */
.act-filter {
  display: inline-flex;
  border: 1px solid var(--border-line);
  border-radius: 999px;
  overflow: hidden;
}

.act-filter__btn {
  padding: 5px 12px;
  font-size: 12px;
  border: none;
  background: transparent;
  color: var(--text-sub);
  cursor: pointer;
  transition: all 200ms var(--ease-out);
}

.act-filter__btn--on {
  background: var(--color-primary);
  color: #ffffff;
  font-weight: 600;
}

/* ===== 活动列表 ===== */
.act-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.act-item {
  padding: 10px 12px;
  border: 1px solid #f0f1f3;
  border-radius: 8px;
  background: var(--bg-soft);
}

.act-item__titleline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.act-item__name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.act-item__meta {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-sub);
  flex-wrap: wrap;
}

.act-item__score {
  font-weight: 600;
  color: var(--color-primary);
}

.act-item__kps {
  margin-left: auto;
  display: inline-flex;
  gap: 4px;
}

.act-kp {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #eef1f7;
  color: var(--text-sub);
}

.act-item__bar {
  margin-top: 6px;
  max-width: 360px;
}

/* ===== 类型 / 状态标签 ===== */
.act-type {
  flex-shrink: 0;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.act-type--course {
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 9%, transparent);
}

.act-type--exercise {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.1);
}

.act-type--test {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.08);
}

.act-type--discussion {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.12);
}

.act-status {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.act-status--done {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.1);
}

.act-status--doing {
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 9%, transparent);
}

.act-status--todo {
  color: var(--text-sub);
  background: #f3f4f6;
}

/* ===== 日历热力 ===== */
.act-calendar {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.act-calendar__week {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.act-calendar__cell {
  aspect-ratio: 1;
  border-radius: 4px;
  background: #f1f2f4;
}

.act-calendar__cell--l1 {
  background: color-mix(in srgb, var(--color-primary) 28%, #f1f2f4);
}

.act-calendar__cell--l2 {
  background: color-mix(in srgb, var(--color-primary) 58%, #ffffff);
}

.act-calendar__cell--l3 {
  background: var(--color-primary);
}

.act-calendar__cell--today {
  outline: 2px solid var(--color-warning);
  outline-offset: 1px;
}

.act-calendar__legend {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-sub);
  justify-content: flex-end;
}

.act-calendar__legend .act-calendar__cell {
  width: 12px;
  aspect-ratio: 1;
}

/* ===== 最近活动 ===== */
.act-recent {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.act-recent__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 2px;
  border-bottom: 1px dashed #f0f1f3;
  font-size: 12px;
}

.act-recent__item:last-child {
  border-bottom: none;
}

.act-recent__name {
  flex: 1;
  min-width: 0;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.act-recent__time {
  color: var(--text-sub);
  font-size: 11px;
}

@media (max-width: 900px) {
  .act-grid {
    grid-template-columns: 1fr;
  }

  .act-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
