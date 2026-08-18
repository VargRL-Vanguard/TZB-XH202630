<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Reading, Timer } from '@element-plus/icons-vue'
import type { AgentCardState } from '@/stores/agentEvents'

/**
 * 组件库 v1 演示页（05 号文档：Storybook 式，逐态可看）
 * 访问：/#/demo（内部演示路由，不在侧栏菜单）
 */

// AgentCard 状态轮播：点按钮按 状态机顺序推进
const stateOrder: AgentCardState[] = ['idle', 'running', 'done', 'debating', 'finished']
const agentStateIdx = ref(1)
const agentState = ref<AgentCardState>('running')
function nextAgentState() {
  agentStateIdx.value = (agentStateIdx.value + 1) % stateOrder.length
  agentState.value = stateOrder[agentStateIdx.value]
}

// MetricCard 重播：改 key 触发重建 → 数字重新滚动
const metricKey = ref(0)
const metricValue = ref(128)
function replayMetric() {
  metricValue.value = 80 + Math.floor(Math.random() * 400)
  metricKey.value++
}
</script>

<template>
  <div class="page demo">
    <h1 class="demo__h1">组件库 v1 演示</h1>
    <p class="demo__desc">F1 公共组件逐态展示 · 悬停/点击/Tab 体验交互</p>

    <!-- 1. Skeleton -->
    <section class="demo__section">
      <h2 class="demo__h2">Skeleton 骨架屏（text / card / chart，呼吸 1.5s）</h2>
      <div class="demo__grid demo__grid--3">
        <div class="demo__cell"><Skeleton :rows="3" variant="text" /></div>
        <div class="demo__cell"><Skeleton variant="card" /></div>
        <div class="demo__cell"><Skeleton variant="chart" /></div>
      </div>
    </section>

    <!-- 2. EmptyState / ErrorState -->
    <section class="demo__section">
      <h2 class="demo__h2">EmptyState 空态 / ErrorState 错误态</h2>
      <div class="demo__grid demo__grid--2">
        <div class="demo__cell">
          <EmptyState
            icon="📚"
            text="还没有学习资源，等 AI 为你生成第一份"
            action-text="去触发生成"
            @action="ElMessage.info('action 事件触发')"
          />
        </div>
        <div class="demo__cell">
          <ErrorState
            text="学习路径加载失败，请检查网络"
            @retry="ElMessage.success('retry 事件触发')"
          />
        </div>
      </div>
    </section>

    <!-- 3. MetricCard -->
    <section class="demo__section">
      <h2 class="demo__h2">
        MetricCard 指标卡（进视口 800ms 滚动 · trend 对齐 metrics 接口）
        <el-button size="small" @click="replayMetric">重播动画</el-button>
      </h2>
      <div :key="metricKey" class="demo__grid demo__grid--4">
        <MetricCard
          label="学习时长"
          :value="metricValue"
          unit="小时"
          trend="up"
          :trend-value="12.5"
        />
        <MetricCard label="完成率" :value="86" unit="%" />
        <MetricCard label="平均分" :value="78" trend="down" :trend-value="3.2" />
        <MetricCard label="幻觉率" :value="4.1" unit="%" :decimals="2">
          <template #foot><span class="demo__foot">达标线 &lt;5%</span></template>
        </MetricCard>
      </div>
    </section>

    <!-- 4. DifficultyBadge -->
    <section class="demo__section">
      <h2 class="demo__h2">DifficultyBadge 难度徽章（1-5 色阶 + 一致性标识）</h2>
      <div class="demo__row">
        <DifficultyBadge :level="1" />
        <DifficultyBadge :level="2" />
        <DifficultyBadge :level="3" />
        <DifficultyBadge :level="4" />
        <DifficultyBadge :level="5" />
        <DifficultyBadge :level="5" :expected="5" />
        <DifficultyBadge :level="5" :expected="2" />
        <DifficultyBadge :level="2" :expected="4" />
      </div>
    </section>

    <!-- 5. AgentCard -->
    <section class="demo__section">
      <h2 class="demo__h2">
        AgentCard 状态机（idle→running→done→debating→finished）
        <el-button size="small" @click="nextAgentState">推进状态：{{ agentState }}</el-button>
      </h2>
      <div class="demo__grid demo__grid--3">
        <AgentCard
          name="学情诊断Agent"
          theme-color="var(--color-agent-blue)"
          :icon="Search"
          :state="agentState"
        >
          <p>正在分析画像：本科应届 · 机械工程 · 78 分…</p>
        </AgentCard>
        <AgentCard
          name="领域专家Agent"
          theme-color="var(--color-agent-purple)"
          :icon="Reading"
          state="idle"
        />
        <AgentCard
          name="审核裁判Agent"
          theme-color="var(--color-agent-gold)"
          :icon="Timer"
          state="finished"
        >
          <p>审核通过：幻觉率 4.10%，达标。</p>
        </AgentCard>
      </div>
    </section>

    <!-- 6. ConstructionPage -->
    <section class="demo__section">
      <h2 class="demo__h2">ConstructionPage 建设中占位（浅色/深色）</h2>
      <div class="demo__grid demo__grid--2">
        <div class="demo__cell demo__cell--flat">
          <ConstructionPage title="示例页面" owner="演示" eta="8-22" />
        </div>
        <div class="demo__cell demo__cell--flat demo__cell--dark">
          <ConstructionPage title="示例大屏" owner="演示" eta="8-22" dark />
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.demo {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.demo__h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-main);
}

.demo__desc {
  font-size: 13px;
  color: var(--text-sub);
  margin-top: -12px;
}

.demo__section {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.demo__h2 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.demo__grid {
  display: grid;
  gap: var(--sp-2);
}

.demo__grid--2 {
  grid-template-columns: repeat(2, 1fr);
}

.demo__grid--3 {
  grid-template-columns: repeat(3, 1fr);
}

.demo__grid--4 {
  grid-template-columns: repeat(4, 1fr);
}

.demo__cell {
  padding: var(--sp-2);
  background: var(--bg-page);
  border-radius: var(--card-radius);
}

/* ConstructionPage 自带整页背景，演示格里压扁展示 */
.demo__cell--flat {
  height: 320px;
  overflow: hidden;
  display: flex;
}

.demo__cell--flat :deep(.construction) {
  flex: 1;
  min-height: 100%;
}

.demo__cell--dark {
  background: var(--bg-screen);
}

.demo__row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  align-items: center;
}

.demo__foot {
  font-size: 12px;
  color: var(--text-sub);
}

@media (max-width: 900px) {
  .demo__grid--3,
  .demo__grid--4 {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
