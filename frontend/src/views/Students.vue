<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getStudentInfo, type StudentInfo } from '@/api/student'
import { TEST_PROFILES, type TestProfile } from '@/mock/fixtures/profiles'
import Skeleton from '@/components/Skeleton.vue'

/**
 * P2 学生列表页（教师视角首页）
 * - 在读学生：B 区暂无列表接口，先以 seed 学生清单（u001/u002）逐个拉
 *   GET /api/student/info 聚合基本信息 + 指标；列表接口就绪后替换数据源
 * - 每卡独立容错：student 角色查他人 403 时仅该卡降级，不阻塞整页
 * - 画像演示档案：3 类测试画像（fixtures，逐字段对齐 B 区 test_profiles）
 */
interface StudentRow {
  studentId: string
  name: string
  info: StudentInfo | null
  error: string
}

const STUDENT_SEEDS = [
  { studentId: 'u001', name: '张三' },
  { studentId: 'u002', name: '李四' }
]

const loading = ref(true)
const rows = ref<StudentRow[]>([])

async function load() {
  loading.value = true
  const results = await Promise.allSettled(STUDENT_SEEDS.map((s) => getStudentInfo(s.studentId)))
  rows.value = STUDENT_SEEDS.map((s, i) => {
    const r = results[i]
    return r.status === 'fulfilled'
      ? { studentId: s.studentId, name: s.name, info: r.value, error: '' }
      : { studentId: s.studentId, name: s.name, info: null, error: '加载失败' }
  })
  loading.value = false
}

onMounted(load)

// 画像档案派生指标
function profileStats(p: TestProfile) {
  const scored = p.activityHistory.filter((a) => a.score !== null)
  const avg = scored.length
    ? Math.round(scored.reduce((sum, a) => sum + (a.score ?? 0), 0) / scored.length)
    : 0
  const minutes = p.activityHistory.reduce((sum, a) => sum + a.durationMinutes, 0)
  return {
    activities: p.activityHistory.length,
    avg,
    hours: Math.round(minutes / 60)
  }
}

const profileCards = computed(() => TEST_PROFILES.map((p) => ({ ...p, stats: profileStats(p) })))
</script>

<template>
  <div class="page">
    <header class="stu-head">
      <h1 class="stu-head__title">学生列表</h1>
      <p class="stu-head__sub">查看在读学生学情概况，点击卡片进入对应学生的分析页面</p>
    </header>

    <!-- 加载态 -->
    <div v-if="loading" class="stu-grid">
      <Skeleton v-for="n in STUDENT_SEEDS.length" :key="n" variant="card" />
    </div>

    <template v-else>
      <!-- 在读学生 -->
      <section class="stu-panel">
        <h2 class="stu-panel__title">在读学生</h2>
        <div class="stu-grid">
          <article v-for="row in rows" :key="row.studentId" class="stu-card">
            <div class="stu-card__head">
              <div class="stu-avatar">{{ row.name.slice(0, 1) }}</div>
              <div>
                <div class="stu-card__name">{{ row.name }}</div>
                <div class="stu-card__id">{{ row.studentId }}</div>
              </div>
            </div>

            <template v-if="row.info">
              <div class="stu-card__meta">
                <span>{{ row.info.learnerProfile.education }}</span>
                <span class="stu-dot">·</span>
                <span>{{ row.info.learnerProfile.major }}</span>
              </div>
              <div class="stu-card__metrics">
                <div class="stu-metric">
                  <span class="stu-metric__val">{{ Math.round(row.info.metrics.studyHours) }}</span>
                  <span class="stu-metric__label">学习时长(h)</span>
                </div>
                <div class="stu-metric">
                  <span class="stu-metric__val">{{ row.info.metrics.completionRate }}%</span>
                  <span class="stu-metric__label">完成率</span>
                </div>
                <div class="stu-metric">
                  <span class="stu-metric__val">{{ row.info.metrics.avgScore }}</span>
                  <span class="stu-metric__label">平均分</span>
                </div>
              </div>
              <div v-if="row.info.learnerProfile.weakKPs.length" class="stu-kps">
                <span class="stu-kps__label">薄弱项</span>
                <el-tag
                  v-for="kp in row.info.learnerProfile.weakKPs.slice(0, 4)"
                  :key="kp"
                  size="small"
                  type="danger"
                  effect="plain"
                >
                  {{ kp }}
                </el-tag>
              </div>
              <div class="stu-card__actions">
                <router-link :to="`/dashboard?studentId=${row.studentId}`" class="stu-link">
                  学情详情
                </router-link>
                <router-link :to="`/learning-path?studentId=${row.studentId}`" class="stu-link">
                  学习路径
                </router-link>
                <router-link :to="`/suggestions?studentId=${row.studentId}`" class="stu-link">
                  学习建议
                </router-link>
              </div>
            </template>
            <p v-else class="stu-card__error">{{ row.error }}（可能无权查看该学生）</p>
          </article>
        </div>
      </section>

      <!-- 画像演示档案 -->
      <section class="stu-panel">
        <h2 class="stu-panel__title">画像演示档案</h2>
        <p class="stu-panel__sub">B 区三类典型学习者画像，用于系统演示与算法验证</p>
        <div class="stu-grid stu-grid--3">
          <article v-for="p in profileCards" :key="p.profile_id" class="stu-card stu-card--profile">
            <div class="stu-card__head">
              <div class="stu-avatar stu-avatar--alt">{{ p.label.slice(0, 2) }}</div>
              <div>
                <div class="stu-card__name">{{ p.label }}</div>
                <div class="stu-card__meta">
                  <span>{{ p.learnerProfile.education }}</span>
                  <span class="stu-dot">·</span>
                  <span>{{ p.learnerProfile.major }}</span>
                </div>
              </div>
            </div>
            <div class="stu-card__metrics">
              <div class="stu-metric">
                <span class="stu-metric__val">{{ p.learnerProfile.theoryTestScore }}</span>
                <span class="stu-metric__label">模考分</span>
              </div>
              <div class="stu-metric">
                <span class="stu-metric__val">{{ p.stats.activities }}</span>
                <span class="stu-metric__label">活动数</span>
              </div>
              <div class="stu-metric">
                <span class="stu-metric__val">{{ p.stats.avg }}</span>
                <span class="stu-metric__label">平均分</span>
              </div>
            </div>
            <div class="stu-kps">
              <span class="stu-kps__label">薄弱 {{ p.learnerProfile.weakKPs.length }} 项</span>
              <el-tag
                v-for="kp in p.learnerProfile.weakKPs.slice(0, 3)"
                :key="kp"
                size="small"
                type="danger"
                effect="plain"
              >
                {{ kp }}
              </el-tag>
              <el-tag
                v-if="p.learnerProfile.weakKPs.length > 3"
                size="small"
                type="info"
                effect="plain"
              >
                +{{ p.learnerProfile.weakKPs.length - 3 }}
              </el-tag>
            </div>
            <p class="stu-goal">{{ p.interactionGoal }}</p>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.stu-head__title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-main);
}

.stu-head__sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-sub);
}

.stu-panel {
  padding: var(--sp-2);
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.stu-panel__title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main);
}

.stu-panel__sub {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--text-sub);
}

.stu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--sp-2);
}

.stu-grid--3 {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.stu-panel .stu-grid {
  margin-top: 12px;
}

.stu-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border-line);
  border-radius: 10px;
  background: var(--bg-soft);
}

.stu-card--profile {
  background: var(--bg-card);
}

.stu-card__head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stu-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--el-color-primary-light-8, #d9ecff);
  color: var(--el-color-primary, #409eff);
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
}

.stu-avatar--alt {
  font-size: 13px;
}

.stu-card__name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
}

.stu-card__id {
  font-size: 12px;
  color: var(--text-sub);
}

.stu-card__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-sub);
}

.stu-dot {
  color: var(--text-sub);
}

.stu-card__metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.stu-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 0;
  background: var(--bg-card);
  border-radius: 8px;
}

.stu-card--profile .stu-metric {
  background: var(--bg-soft);
}

.stu-metric__val {
  font-size: 18px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--text-main);
}

.stu-metric__label {
  font-size: 11px;
  color: var(--text-sub);
}

.stu-kps {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.stu-kps__label {
  font-size: 12px;
  color: var(--text-sub);
}

.stu-card__actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
  padding-top: 4px;
  border-top: 1px dashed var(--border-line);
}

.stu-link {
  font-size: 13px;
  color: var(--el-color-primary, #409eff);
  text-decoration: none;
}

.stu-link:hover {
  text-decoration: underline;
}

.stu-card__error {
  margin: 0;
  font-size: 13px;
  color: var(--text-sub);
}

.stu-goal {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-sub);
}
</style>
