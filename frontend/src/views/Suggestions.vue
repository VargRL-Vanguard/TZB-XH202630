<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  getSuggestions,
  markSuggestionRead,
  type Suggestion,
  type SuggestionCategory
} from '@/api/suggestions'
import Skeleton from '@/components/Skeleton.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'

/**
 * P1 学习建议页（C 区真接口：list + read）
 * - 分类筛选：全部 / 方法 / 资源 / 复习 / 练习（各 tab 显示未读数）
 * - 未读卡：主色左边框 + 高亮圆点 + 标题加粗；已读卡置灰
 * - 点击未读卡或「标记已读」→ POST /api/suggestions/read
 */

const route = useRoute()
const auth = useAuthStore()
const studentId = computed(() => (route.query.studentId as string) || auth.userId)

const loading = ref(true)
const errorMsg = ref('')
const items = ref<Suggestion[]>([])
const category = ref<SuggestionCategory>('all')
const readPending = ref('')

async function load() {
  if (!studentId.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    items.value = await getSuggestions(studentId.value, category.value)
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(studentId, load)

const CATEGORY_TABS: { value: SuggestionCategory; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'method', label: '方法建议' },
  { value: 'resource', label: '资源推荐' },
  { value: 'review', label: '复习建议' },
  { value: 'practice', label: '练习推荐' }
]

/** 全量拉取后按 tab 前端过滤（避免 5 次请求；未读数也需要全量口径） */
const filtered = computed(() =>
  category.value === 'all' ? items.value : items.value.filter((s) => s.category === category.value)
)

const unreadOf = (cat: SuggestionCategory) =>
  items.value.filter((s) => !s.isRead && (cat === 'all' || s.category === cat)).length

const totalUnread = computed(() => unreadOf('all'))

const PRIORITY_CLS: Record<string, string> = {
  high: 'sg-prio--high',
  medium: 'sg-prio--medium',
  low: 'sg-prio--low'
}

async function markRead(s: Suggestion) {
  if (s.isRead || readPending.value) return
  readPending.value = s.id
  try {
    await markSuggestionRead(studentId.value, s.id)
    s.isRead = true
    ElMessage.success('已标记为已读')
  } catch {
    /* request.ts 已统一 toast，这里静默 */
  } finally {
    readPending.value = ''
  }
}

/** createdAt（UTC iso）→ 「今天 HH:mm」/「MM-DD HH:mm」 */
function fmtTime(iso: string) {
  if (!iso) return ''
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
  if (Number.isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  const now = new Date()
  const hm = `${pad(d.getHours())}:${pad(d.getMinutes())}`
  const sameDay = d.toDateString() === now.toDateString()
  return sameDay ? `今天 ${hm}` : `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${hm}`
}
</script>

<template>
  <div class="page sg">
    <header class="sg-head">
      <div>
        <h1 class="sg-head__title">学习建议</h1>
        <p class="sg-head__sub">
          基于学情诊断的个性化建议
          <template v-if="totalUnread > 0">
            · <span class="sg-head__unread num">{{ totalUnread }} 条未读</span>
          </template>
        </p>
      </div>
    </header>

    <!-- 分类筛选 -->
    <nav v-if="!loading && !errorMsg" class="sg-tabs" role="tablist">
      <button
        v-for="t in CATEGORY_TABS"
        :key="t.value"
        role="tab"
        :aria-selected="category === t.value"
        class="sg-tab"
        :class="{ 'sg-tab--active': category === t.value }"
        @click="category = t.value"
      >
        {{ t.label }}
        <span v-if="unreadOf(t.value) > 0" class="sg-tab__badge num">{{ unreadOf(t.value) }}</span>
      </button>
    </nav>

    <!-- 加载态 -->
    <template v-if="loading">
      <Skeleton v-for="n in 4" :key="n" variant="card" class="sg-skeleton" />
    </template>

    <!-- 错误态 -->
    <section v-else-if="errorMsg" class="sg-panel">
      <ErrorState :text="`学习建议加载失败：${errorMsg}`" @retry="load" />
    </section>

    <!-- 空态 -->
    <section v-else-if="filtered.length === 0" class="sg-panel">
      <EmptyState
        icon="💡"
        :text="
          category === 'all'
            ? '暂无学习建议。完成测验或学习活动后，系统将自动生成。'
            : '该分类下暂无建议，看看其他分类吧。'
        "
      />
    </section>

    <!-- 建议列表 -->
    <transition-group v-else name="sg-list" tag="div" class="sg-list">
      <article
        v-for="s in filtered"
        :key="s.id"
        class="sg-card"
        :class="{ 'sg-card--unread': !s.isRead }"
        @click="!s.isRead && markRead(s)"
      >
        <div class="sg-card__head">
          <div class="sg-card__titleline">
            <span v-if="!s.isRead" class="sg-card__dot" aria-label="未读"></span>
            <h3 class="sg-card__title" :class="{ 'sg-card__title--read': s.isRead }">
              {{ s.title }}
            </h3>
          </div>
          <div class="sg-card__tags">
            <span class="sg-cat sg-cat--primary">{{ s.categoryLabel || s.category }}</span>
            <span class="sg-prio" :class="PRIORITY_CLS[s.priority] ?? 'sg-prio--low'">{{
              s.priorityLabel || s.priority
            }}</span>
          </div>
        </div>

        <p class="sg-card__content" :class="{ 'sg-card__content--read': s.isRead }">
          {{ s.content }}
        </p>

        <footer class="sg-card__foot">
          <span class="sg-card__meta"
            >来源：{{ s.source === 'ai' ? 'AI 学情诊断' : s.source }}</span
          >
          <span class="sg-card__time num">{{ fmtTime(s.createdAt) }}</span>
          <el-button
            v-if="!s.isRead"
            size="small"
            type="primary"
            plain
            :loading="readPending === s.id"
            class="sg-card__read-btn"
            @click.stop="markRead(s)"
          >
            标记已读
          </el-button>
          <span v-else class="sg-card__readflag">已读</span>
        </footer>
      </article>
    </transition-group>
  </div>
</template>

<style scoped>
.sg {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.sg-head__title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}

.sg-head__sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-sub);
}

.sg-head__unread {
  color: var(--color-danger);
  font-weight: 600;
}

/* ===== 分类 tab ===== */
.sg-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.sg-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--border-line);
  background: var(--bg-card);
  font-size: 13px;
  color: var(--text-sub);
  cursor: pointer;
  transition: all 200ms var(--ease-out);
}

.sg-tab:hover {
  border-color: color-mix(in srgb, var(--color-primary) 45%, transparent);
  color: var(--color-primary);
}

.sg-tab--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #ffffff;
  font-weight: 600;
}

.sg-tab__badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #ef4444;
  color: #ffffff;
  font-size: 11px;
  line-height: 18px;
  text-align: center;
}

.sg-tab--active .sg-tab__badge {
  background: rgba(255, 255, 255, 0.25);
}

.sg-skeleton {
  display: block;
}

/* ===== 列表 ===== */
.sg-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.sg-panel {
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.sg-card {
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid #f0f1f3;
  border-left: 3px solid transparent;
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  transition:
    border-color 200ms var(--ease-out),
    transform 200ms var(--ease-out);
}

.sg-card--unread {
  border-left-color: var(--color-primary);
  cursor: pointer;
}

.sg-card--unread:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 30%, transparent);
  border-left-color: var(--color-primary);
}

.sg-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.sg-card__titleline {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.sg-card__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-danger);
  flex-shrink: 0;
}

.sg-card__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
}

.sg-card__title--read {
  color: var(--text-sub);
  font-weight: 500;
}

.sg-card__tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.sg-cat,
.sg-prio {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.sg-cat--primary {
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 8%, transparent);
}

.sg-prio--high {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.08);
}

.sg-prio--medium {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.1);
}

.sg-prio--low {
  color: var(--text-sub);
  background: #f3f4f6;
}

.sg-card__content {
  margin: 8px 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-main);
}

.sg-card__content--read {
  color: var(--text-sub);
}

.sg-card__foot {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-sub);
}

.sg-card__time {
  font-variant-numeric: tabular-nums;
}

.sg-card__read-btn {
  margin-left: auto;
}

.sg-card__readflag {
  margin-left: auto;
  color: var(--color-success);
  font-size: 12px;
}

/* 列表项进出场 */
.sg-list-enter-active,
.sg-list-leave-active {
  transition: all 200ms var(--ease-out);
}

.sg-list-enter-from,
.sg-list-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.sg-list-move {
  transition: transform 200ms var(--ease-out);
}
</style>
