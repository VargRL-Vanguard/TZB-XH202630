<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { CircleCheckFilled, Collection, Odometer, Timer } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  getPathOverview,
  getPathTimeline,
  getPathTasks,
  type PathOverview,
  type PathTimelineItem,
  type PathTask
} from '@/api/path'
import Skeleton from '@/components/Skeleton.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'

/**
 * P1 学习路径页（C 区真接口：overview + timeline + tasks）
 * - 顶部总览卡：目标 / 总进度 / 预计天数 / 来源（AI 生成）
 * - 左栏：阶段垂直时间线（completed ✓ / current 呼吸蓝 / pending 灰）
 * - 右栏：任务清单（未完成优先，priority 三色标签 + 完成态划线）
 */

const route = useRoute()
const auth = useAuthStore()
const studentId = computed(() => (route.query.studentId as string) || auth.userId)

const loading = ref(true)
const errorMsg = ref('')
const overview = ref<PathOverview | null>(null)
const timeline = ref<PathTimelineItem[]>([])
const tasks = ref<PathTask[]>([])

async function load() {
  if (!studentId.value) return
  loading.value = true
  errorMsg.value = ''
  overview.value = null
  timeline.value = []
  tasks.value = []
  try {
    const [ov, tl, tk] = await Promise.all([
      getPathOverview(studentId.value),
      getPathTimeline(studentId.value),
      getPathTasks(studentId.value)
    ])
    overview.value = ov
    timeline.value = tl
    tasks.value = tk
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(studentId, load)

const hasPath = computed(() => overview.value && overview.value.target !== '暂未配置学习目标')

/** 空态判定：无路径记录 或 时间线全空 */
const isEmpty = computed(() => !hasPath.value && timeline.value.length === 0)

const pendingTasks = computed(() => tasks.value.filter((t) => !t.completed))
const doneTasks = computed(() => tasks.value.filter((t) => t.completed))

const STATUS_META: Record<string, { label: string; type: 'success' | 'primary' | 'info' }> = {
  completed: { label: '已完成', type: 'success' },
  current: { label: '进行中', type: 'primary' },
  pending: { label: '待开始', type: 'info' }
}

function statusMeta(s: string) {
  return STATUS_META[s] ?? { label: s, type: 'info' as const }
}

const PRIORITY_META: Record<string, { label: string; cls: string }> = {
  high: { label: '重要', cls: 'lp-tag--high' },
  medium: { label: '普通', cls: 'lp-tag--medium' },
  low: { label: '可选', cls: 'lp-tag--low' }
}

function priorityMeta(p: string) {
  return PRIORITY_META[p] ?? { label: p, cls: 'lp-tag--low' }
}
</script>

<template>
  <div class="page lp">
    <header class="lp-head">
      <div>
        <h1 class="lp-head__title">学习路径</h1>
        <p class="lp-head__sub">AI 生成的个性化阶段规划 · 目标 → 模块 → 任务三级拆解</p>
      </div>
    </header>

    <!-- 加载态 -->
    <template v-if="loading">
      <Skeleton variant="card" />
      <div class="lp-grid">
        <Skeleton :rows="8" />
        <Skeleton :rows="6" />
      </div>
    </template>

    <!-- 错误态 -->
    <section v-else-if="errorMsg" class="lp-panel">
      <ErrorState :text="`学习路径加载失败：${errorMsg}`" @retry="load" />
    </section>

    <!-- 空态：尚无路径（提示去 AI 辅导触发生成） -->
    <section v-else-if="isEmpty" class="lp-panel">
      <EmptyState
        icon="🗺️"
        text="该学生还没有学习路径。完成画像编辑或通过 AI 辅导对话后，系统将自动生成个性化路径。"
        action-text="去 AI 辅导"
        @action="$router.push('/ai-chat')"
      />
    </section>

    <template v-else>
      <!-- 总览卡 -->
      <section class="lp-overview">
        <div class="lp-overview__main">
          <div class="lp-overview__target">
            <el-icon :size="18" class="lp-overview__icon"><Collection /></el-icon>
            <span>{{ overview?.target }}</span>
            <el-tag
              v-if="overview?.source === 'ai'"
              size="small"
              type="primary"
              effect="plain"
              class="lp-overview__src"
            >
              AI 生成
            </el-tag>
          </div>
          <div class="lp-overview__bar">
            <el-progress
              :percentage="overview?.progress ?? 0"
              :stroke-width="10"
              :show-text="false"
              class="lp-overview__progress"
            />
            <span class="lp-overview__pct num">{{ overview?.progress ?? 0 }}%</span>
          </div>
        </div>
        <div class="lp-overview__stats">
          <div class="lp-stat">
            <el-icon :size="16"><Odometer /></el-icon>
            <div>
              <span class="lp-stat__label">总进度</span>
              <span class="lp-stat__value num">{{ overview?.progress ?? 0 }}%</span>
            </div>
          </div>
          <div class="lp-stat">
            <el-icon :size="16"><Timer /></el-icon>
            <div>
              <span class="lp-stat__label">预计周期</span>
              <span class="lp-stat__value num">{{ overview?.estimatedDays ?? 0 }} 天</span>
            </div>
          </div>
          <div class="lp-stat">
            <el-icon :size="16"><CircleCheckFilled /></el-icon>
            <div>
              <span class="lp-stat__label">已完成模块</span>
              <span class="lp-stat__value num">
                {{ timeline.filter((m) => m.status === 'completed').length }} /
                {{ timeline.length }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- 主体：时间线 + 任务 -->
      <div class="lp-grid">
        <!-- 左：阶段时间线 -->
        <section class="lp-panel">
          <h2 class="lp-panel__title">阶段规划（{{ timeline.length }} 个模块）</h2>
          <el-timeline v-if="timeline.length" class="lp-timeline">
            <el-timeline-item
              v-for="m in timeline"
              :key="m.moduleId"
              :type="statusMeta(m.status).type"
              :hollow="m.status !== 'current'"
              :timestamp="`${m.startDate} ~ ${m.endDate} · ${m.duration}`"
              placement="top"
              :class="{ 'lp-timeline__item--current': m.status === 'current' }"
            >
              <div class="lp-module">
                <div class="lp-module__head">
                  <span class="lp-module__name">{{ m.title }}</span>
                  <el-tag size="small" :type="statusMeta(m.status).type" effect="light">
                    {{ statusMeta(m.status).label }}
                  </el-tag>
                </div>
                <p class="lp-module__desc">{{ m.desc }}</p>
                <div class="lp-module__bar">
                  <el-progress :percentage="m.progress" :stroke-width="6" />
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
          <EmptyState v-else icon="📭" text="暂无阶段数据" />
        </section>

        <!-- 右：任务清单 -->
        <section class="lp-panel">
          <h2 class="lp-panel__title">
            任务清单
            <span class="lp-panel__count num"
              >{{ pendingTasks.length }} 待办 · {{ doneTasks.length }} 已完成</span
            >
          </h2>

          <template v-if="tasks.length">
            <ul v-if="pendingTasks.length" class="lp-tasks">
              <li v-for="t in pendingTasks" :key="t.taskId" class="lp-task">
                <span
                  class="lp-task__check"
                  :class="`lp-tag-prio--${t.priority}`"
                  aria-hidden="true"
                ></span>
                <div class="lp-task__body">
                  <span class="lp-task__title">{{ t.title }}</span>
                  <span class="lp-task__meta">{{ t.meta }}</span>
                </div>
                <span class="lp-tag" :class="priorityMeta(t.priority).cls">{{
                  priorityMeta(t.priority).label
                }}</span>
              </li>
            </ul>
            <EmptyState v-else icon="🎉" text="太棒了，当前没有待办任务" />

            <details v-if="doneTasks.length" class="lp-done">
              <summary>已完成（{{ doneTasks.length }}）</summary>
              <ul class="lp-tasks lp-tasks--done">
                <li v-for="t in doneTasks" :key="t.taskId" class="lp-task">
                  <el-icon class="lp-task__done-icon"><CircleCheckFilled /></el-icon>
                  <div class="lp-task__body">
                    <span class="lp-task__title lp-task__title--done">{{ t.title }}</span>
                    <span class="lp-task__meta">{{ t.meta }}</span>
                  </div>
                </li>
              </ul>
            </details>
          </template>
          <EmptyState v-else icon="📭" text="暂无任务" />
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.lp {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.lp-head__title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}

.lp-head__sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-sub);
}

/* ===== 总览卡 ===== */
.lp-overview {
  display: flex;
  align-items: stretch;
  gap: var(--sp-2);
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  flex-wrap: wrap;
}

.lp-overview__main {
  flex: 1 1 420px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--sp-1);
  min-width: 0;
}

.lp-overview__target {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main);
  flex-wrap: wrap;
}

.lp-overview__icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.lp-overview__src {
  flex-shrink: 0;
}

.lp-overview__bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lp-overview__progress {
  flex: 1;
}

.lp-overview__pct {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-primary);
}

.lp-overview__stats {
  display: flex;
  gap: var(--sp-3);
  align-items: center;
  padding-left: var(--sp-2);
  border-left: 1px solid var(--border-color, var(--border-line));
  flex-wrap: wrap;
}

.lp-stat {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
}

.lp-stat > div {
  display: flex;
  flex-direction: column;
}

.lp-stat__label {
  font-size: 11px;
  color: var(--text-sub);
}

.lp-stat__value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-main);
}

/* ===== 主体两栏 ===== */
.lp-grid {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(0, 5fr);
  gap: var(--sp-2);
  align-items: start;
}

.lp-panel {
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.lp-panel__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: var(--sp-2);
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.lp-panel__count {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-sub);
}

/* ===== 时间线 ===== */
.lp-timeline {
  padding-left: 4px;
}

.lp-module__head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.lp-module__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
}

.lp-module__desc {
  margin: 6px 0;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-sub);
}

.lp-module__bar {
  max-width: 320px;
}

/* 进行中模块：卡片高亮 + 节点呼吸 */
.lp-timeline__item--current :deep(.el-timeline-item__node) {
  animation: lp-breathe 2s ease-in-out infinite;
}

.lp-timeline__item--current .lp-module {
  padding: 8px 12px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-primary) 25%, transparent);
}

@keyframes lp-breathe {
  0%,
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-primary) 35%, transparent);
  }
  50% {
    box-shadow: 0 0 0 6px color-mix(in srgb, var(--color-primary) 0%, transparent);
  }
}

/* ===== 任务清单 ===== */
.lp-tasks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lp-task {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #f0f1f3;
  border-radius: 8px;
  background: var(--bg-soft);
  transition: border-color 200ms var(--ease-out);
}

.lp-task:hover {
  border-color: color-mix(in srgb, var(--color-primary) 35%, transparent);
}

/* 优先级色点（未完成）：high 红 / medium 黄 / low 灰 */
.lp-task__check {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.lp-tag-prio--high {
  background: var(--color-danger);
}

.lp-tag-prio--medium {
  background: var(--color-warning);
}

.lp-tag-prio--low {
  background: #d1d5db;
}

.lp-task__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.lp-task__title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-main);
}

.lp-task__title--done {
  text-decoration: line-through;
  color: var(--text-sub);
}

.lp-task__meta {
  font-size: 11px;
  color: var(--text-sub);
}

.lp-tag {
  flex-shrink: 0;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.lp-tag--high {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.08);
}

.lp-tag--medium {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.1);
}

.lp-tag--low {
  color: var(--text-sub);
  background: #f3f4f6;
}

.lp-task__done-icon {
  color: var(--color-success);
  flex-shrink: 0;
}

.lp-done {
  margin-top: var(--sp-2);
  font-size: 12px;
  color: var(--text-sub);
}

.lp-done summary {
  cursor: pointer;
  user-select: none;
  padding: 4px 0;
}

@media (max-width: 900px) {
  .lp-grid {
    grid-template-columns: 1fr;
  }

  .lp-overview__stats {
    border-left: none;
    padding-left: 0;
  }
}
</style>
