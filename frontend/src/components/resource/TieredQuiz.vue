<script setup lang="ts">
import { computed, reactive } from 'vue'
import type { ResourceBase, TieredQuizContent } from '@/mock/fixtures/resources'

/**
 * 形态三：分层测验（可作答：选选项 → 提交 → 判分 + 解析）
 * - 难度分层徽标（DifficultyBadge 由题目行内展示难度等级数字）
 */
const props = defineProps<{ resource: ResourceBase }>()

const content = props.resource.content as TieredQuizContent
const OPTION_KEYS = ['A', 'B', 'C', 'D']

/** answers[qIndex] = 选中选项 key；submitted[qIndex] = 是否已提交 */
const answers = reactive<Record<number, string>>({})
const submitted = reactive<Record<number, boolean>>({})

function submit(qi: number) {
  if (!answers[qi] || submitted[qi]) return
  submitted[qi] = true
}

const correctCount = computed(
  () => content.questions.filter((q, i) => submitted[i] && answers[i] === q.answer).length
)
const submittedCount = computed(
  () => Object.keys(submitted).filter((k) => submitted[Number(k)]).length
)
</script>

<template>
  <div class="quiz">
    <div class="quiz__summary">
      <span>已完成 {{ submittedCount }}/{{ content.questions.length }}</span>
      <span v-if="submittedCount" class="quiz__score num">答对 {{ correctCount }} 题</span>
    </div>

    <div v-for="(q, qi) in content.questions" :key="qi" class="quiz__q">
      <div class="quiz__q-head">
        <span class="quiz__q-num">第 {{ qi + 1 }} 题</span>
        <span class="quiz__q-diff" :class="`quiz__q-diff--d${q.difficulty}`"
          >难度 L{{ q.difficulty }}</span
        >
        <el-tag size="small" effect="plain" type="info">{{ q.kp_id }}</el-tag>
      </div>

      <p class="quiz__q-title">{{ q.question }}</p>

      <div class="quiz__options">
        <button
          v-for="(opt, oi) in q.options"
          :key="oi"
          class="quiz__opt"
          :class="{
            'quiz__opt--picked': answers[qi] === OPTION_KEYS[oi],
            'quiz__opt--right': submitted[qi] && OPTION_KEYS[oi] === q.answer,
            'quiz__opt--wrong':
              submitted[qi] && answers[qi] === OPTION_KEYS[oi] && OPTION_KEYS[oi] !== q.answer
          }"
          :disabled="submitted[qi]"
          @click="answers[qi] = OPTION_KEYS[oi]"
        >
          <span class="quiz__opt-key">{{ OPTION_KEYS[oi] }}</span>
          <span class="quiz__opt-text">{{ opt }}</span>
          <span v-if="submitted[qi] && OPTION_KEYS[oi] === q.answer" class="quiz__opt-mark">✓</span>
          <span
            v-else-if="
              submitted[qi] && answers[qi] === OPTION_KEYS[oi] && OPTION_KEYS[oi] !== q.answer
            "
            class="quiz__opt-mark quiz__opt-mark--wrong"
          >
            ✕
          </span>
        </button>
      </div>

      <div class="quiz__q-foot">
        <el-button
          v-if="!submitted[qi]"
          size="small"
          type="primary"
          plain
          :disabled="!answers[qi]"
          @click="submit(qi)"
        >
          提交本题
        </el-button>
        <p v-else class="quiz__explain"><strong>解析：</strong>{{ q.explanation }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quiz {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.quiz__summary {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-sub);
}

.quiz__score {
  color: var(--color-primary);
  font-weight: 600;
}

.quiz__q {
  padding: 12px var(--sp-2);
  border-radius: 10px;
  background: #f8f9fc;
}

.quiz__q-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quiz__q-num {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.quiz__q-diff {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.quiz__q-diff--d1,
.quiz__q-diff--d2 {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.1);
}

.quiz__q-diff--d3 {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.1);
}

.quiz__q-diff--d4,
.quiz__q-diff--d5 {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.1);
}

.quiz__q-title {
  margin: 8px 0;
  font-size: 14px;
  color: var(--text-main);
}

.quiz__options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 8px;
}

.quiz__opt {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--border-line);
  background: var(--bg-card);
  cursor: pointer;
  text-align: left;
  transition: all 150ms var(--ease-out);
}

.quiz__opt:hover:not(:disabled) {
  border-color: var(--color-primary);
}

.quiz__opt:disabled {
  cursor: default;
}

.quiz__opt--picked {
  border-color: var(--color-primary);
  background: rgba(79, 110, 247, 0.06);
}

.quiz__opt--right {
  border-color: var(--color-success);
  background: rgba(34, 197, 94, 0.08);
}

.quiz__opt--wrong {
  border-color: var(--color-danger);
  background: rgba(239, 68, 68, 0.06);
}

.quiz__opt-key {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid currentColor;
  color: var(--text-sub);
}

.quiz__opt--picked .quiz__opt-key {
  color: #ffffff;
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.quiz__opt-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-main);
}

.quiz__opt-mark {
  color: var(--color-success);
  font-weight: 700;
}

.quiz__opt-mark--wrong {
  color: var(--color-danger);
}

.quiz__q-foot {
  margin-top: 8px;
}

.quiz__explain {
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-sub);
  background: rgba(79, 110, 247, 0.05);
  border-radius: 6px;
  padding: 8px 10px;
  white-space: pre-line;
}
</style>
