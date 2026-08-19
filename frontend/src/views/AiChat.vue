<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Delete, Promotion, User, ChatDotRound } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { BizError } from '@/api/request'
import { sendAiChat, getAiChatHistory, clearAiChatHistory, type AiChatMessage } from '@/api/aiChat'
import Skeleton from '@/components/Skeleton.vue'
import ErrorState from '@/components/ErrorState.vue'

/**
 * P1 AI 辅导对话页（D 区真接口：send / history / clear）
 * - 气泡对话：user 右主色 / ai 左白卡
 * - AI 未配置 Key（HTTP 503）→ 顶部降级横幅，禁止假回复（穿帮）
 * - 空态：欢迎引导 + 领域快捷提问
 */

const route = useRoute()
const auth = useAuthStore()
const studentId = computed(() => (route.query.studentId as string) || auth.userId)

const loading = ref(true)
const errorMsg = ref('')
const messages = ref<AiChatMessage[]>([])
const input = ref('')
const sending = ref(false)
const clearing = ref(false)
const degraded = ref(false)

const listRef = ref<HTMLElement>()

async function load() {
  if (!studentId.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    messages.value = await getAiChatHistory(studentId.value, 30)
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(studentId, load)

function scrollToBottom() {
  nextTick(() => {
    const el = listRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
watch(() => messages.value.length, scrollToBottom)

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  degraded.value = false
  sending.value = true
  input.value = ''

  // 乐观追加 user 消息
  const localId = Date.now()
  messages.value.push({
    id: localId,
    role: 'user',
    content: text,
    timestamp: new Date().toISOString()
  })
  scrollToBottom()

  try {
    const res = await sendAiChat({ studentId: studentId.value, message: text })
    messages.value.push({
      id: localId + 1,
      role: 'ai',
      content: res.reply,
      timestamp: new Date().toISOString()
    })
  } catch (e) {
    // AI 无 Key / 服务不可用：503 明确降级；回滚刚发出的消息
    messages.value = messages.value.filter((m) => m.id !== localId)
    if (e instanceof BizError && e.code === 503) {
      degraded.value = true
    }
    input.value = text
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

async function clearAll() {
  if (clearing.value) return
  try {
    await ElMessageBox.confirm('确定清空全部 AI 辅导对话记录？该操作不可恢复。', '清空对话', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  clearing.value = true
  try {
    await clearAiChatHistory(studentId.value)
    messages.value = []
  } catch {
    /* request.ts 已统一 toast */
  } finally {
    clearing.value = false
  }
}

const QUICK_ASKS = [
  'D-H 参数法建系有什么口诀？',
  '梯形图启保停电路怎么写？',
  '常用传感器怎么选型？',
  '机器人路径规划入门看什么？'
]

function askQuick(q: string) {
  input.value = q
  send()
}

function fmtTime(ts: string) {
  if (!ts) return ''
  const d = new Date(ts.endsWith('Z') || ts.includes('+') ? ts : `${ts}Z`)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<template>
  <div class="page ac">
    <header class="ac-head">
      <div class="ac-head__left">
        <el-icon :size="20" class="ac-head__icon"><ChatDotRound /></el-icon>
        <div>
          <h1 class="ac-head__title">AI 辅导</h1>
          <p class="ac-head__sub">基于你的学习者画像与知识库的个性化答疑</p>
        </div>
      </div>
      <el-button
        v-if="messages.length"
        size="small"
        plain
        type="danger"
        :loading="clearing"
        :icon="Delete"
        @click="clearAll"
      >
        清空记录
      </el-button>
    </header>

    <!-- 降级横幅：AI 未配置 Key，明确提示而非假回复 -->
    <div v-if="degraded" class="ac-degraded" role="alert">
      AI 服务暂不可用（可能未配置 AI Key）。请联系管理员在 D
      区配置后重试，或先使用学习资源页的定制化内容。
    </div>

    <!-- 消息区 -->
    <section class="ac-board">
      <!-- 加载态 -->
      <div v-if="loading" class="ac-board__inner">
        <Skeleton :rows="4" />
      </div>

      <!-- 错误态 -->
      <div v-else-if="errorMsg" class="ac-board__inner">
        <ErrorState :text="`对话记录加载失败：${errorMsg}`" @retry="load" />
      </div>

      <div v-else ref="listRef" class="ac-board__scroll">
        <!-- 空态：欢迎引导 -->
        <div v-if="messages.length === 0" class="ac-welcome">
          <div class="ac-welcome__figure" aria-hidden="true">
            <svg viewBox="0 0 48 48" width="44" height="44">
              <defs>
                <linearGradient id="ai-spark" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#8ab4ff" />
                  <stop offset="100%" stop-color="#a78bfa" />
                </linearGradient>
              </defs>
              <!-- 主星（四角光核） -->
              <path
                d="M24 6 C26.5 16 32 21.5 42 24 C32 26.5 26.5 32 24 42 C21.5 32 16 26.5 6 24 C16 21.5 21.5 16 24 6 Z"
                fill="url(#ai-spark)"
              />
              <!-- 右上伴星 -->
              <path
                d="M37 8 C38 12 40 14 44 15 C40 16 38 18 37 22 C36 18 34 16 30 15 C34 14 36 12 37 8 Z"
                fill="#c7d6ff"
                opacity="0.9"
              />
              <!-- 左下伴星 -->
              <circle cx="11" cy="36" r="3" fill="#a78bfa" opacity="0.75" />
            </svg>
          </div>
          <h2 class="ac-welcome__title">你好，我是你的 AI 学习助手</h2>
          <p class="ac-welcome__text">可以问我工业机器人领域的知识点，例如：</p>
          <div class="ac-welcome__chips">
            <button
              v-for="q in QUICK_ASKS"
              :key="q"
              class="ac-chip"
              :disabled="sending"
              @click="askQuick(q)"
            >
              {{ q }}
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <template v-else>
          <div
            v-for="m in messages"
            :key="m.id"
            class="ac-msg"
            :class="m.role === 'user' ? 'ac-msg--user' : 'ac-msg--ai'"
          >
            <div
              class="ac-msg__avatar"
              :class="m.role === 'user' ? 'ac-msg__avatar--user' : 'ac-msg__avatar--ai'"
            >
              <el-icon v-if="m.role === 'user'" :size="14"><User /></el-icon>
              <span v-else class="ac-msg__bot">AI</span>
            </div>
            <div class="ac-msg__body">
              <div class="ac-msg__bubble">{{ m.content }}</div>
              <span v-if="fmtTime(m.timestamp)" class="ac-msg__time num" :title="m.timestamp">
                {{ fmtTime(m.timestamp) }}
              </span>
            </div>
          </div>
        </template>

        <!-- AI 思考中 -->
        <div v-if="sending" class="ac-msg ac-msg--ai">
          <div class="ac-msg__avatar ac-msg__avatar--ai"><span class="ac-msg__bot">AI</span></div>
          <div class="ac-msg__body">
            <div class="ac-msg__bubble ac-typing" aria-label="AI 正在输入">
              <span class="ac-typing__dot"></span>
              <span class="ac-typing__dot"></span>
              <span class="ac-typing__dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <footer class="ac-input">
        <textarea
          v-model="input"
          class="ac-input__area"
          :disabled="sending"
          rows="2"
          maxlength="2000"
          placeholder="输入你的问题…（Enter 发送，Shift + Enter 换行）"
          @keydown="onKeydown"
        ></textarea>
        <div class="ac-input__side">
          <span class="ac-input__count num">{{ input.length }}/2000</span>
          <el-button
            type="primary"
            :loading="sending"
            :disabled="!input.trim()"
            :icon="Promotion"
            @click="send"
          >
            发送
          </el-button>
        </div>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.ac {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  height: calc(100vh - 140px);
  min-height: 480px;
}

.ac-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
}

.ac-head__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ac-head__icon {
  color: var(--color-primary);
}

.ac-head__title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.2;
}

.ac-head__sub {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-sub);
}

/* ===== 降级横幅 ===== */
.ac-degraded {
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid rgba(245, 158, 11, 0.35);
}

/* ===== 消息板 ===== */
.ac-board {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  overflow: hidden;
}

.ac-board__inner {
  flex: 1;
  padding: var(--sp-2);
  display: flex;
  align-items: center;
}

.ac-board__scroll {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-2);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ===== 空态欢迎 ===== */
.ac-welcome {
  margin: auto;
  text-align: center;
  padding: var(--sp-3) var(--sp-2);
  animation: ac-in 250ms var(--ease-out);
}

@keyframes ac-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ac-welcome__figure {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 20px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 14%, transparent), color-mix(in srgb, var(--color-secondary) 14%, transparent));
  border: 1px solid color-mix(in srgb, var(--color-primary) 25%, transparent);
  animation: ai-figure-breathe 3s infinite ease-in-out;
}

@keyframes ai-figure-breathe {
  0%,
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-primary) 18%, transparent);
  }
  50% {
    box-shadow: 0 0 18px 2px color-mix(in srgb, var(--color-secondary) 22%, transparent);
  }
}

.ac-welcome__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main);
}

.ac-welcome__text {
  margin: 8px 0 14px;
  font-size: 13px;
  color: var(--text-sub);
}

.ac-welcome__chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.ac-chip {
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid var(--border-line);
  background: var(--bg-soft);
  font-size: 13px;
  color: var(--text-main);
  cursor: pointer;
  transition: all 200ms var(--ease-out);
}

.ac-chip:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 5%, transparent);
}

.ac-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== 消息 ===== */
.ac-msg {
  display: flex;
  gap: 8px;
  max-width: 86%;
}

.ac-msg--user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.ac-msg--ai {
  align-self: flex-start;
}

.ac-msg__avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.ac-msg__avatar--ai {
  background: linear-gradient(
    135deg,
    var(--color-primary),
    color-mix(in srgb, var(--color-primary) 60%, #7c3aed)
  );
  color: #ffffff;
}

.ac-msg__avatar--user {
  background: #f3f4f6;
  color: var(--text-sub);
}

.ac-msg__bot {
  font-size: 11px;
  font-weight: 700;
}

.ac-msg__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.ac-msg--user .ac-msg__body {
  align-items: flex-end;
}

.ac-msg__bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.ac-msg--ai .ac-msg__bubble {
  background: #f6f7f9;
  color: var(--text-main);
  border-top-left-radius: 4px;
}

.ac-msg--user .ac-msg__bubble {
  background: var(--color-primary);
  color: #ffffff;
  border-top-right-radius: 4px;
}

.ac-msg__time {
  font-size: 11px;
  color: #b6bcc4;
  font-variant-numeric: tabular-nums;
}

/* ===== 打字指示 ===== */
.ac-typing {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  padding: 14px 16px !important;
}

.ac-typing__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  animation: ac-bounce 1.2s ease-in-out infinite;
}

.ac-typing__dot:nth-child(2) {
  animation-delay: 0.15s;
}

.ac-typing__dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes ac-bounce {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

/* ===== 输入区 ===== */
.ac-input {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 12px 16px;
  border-top: 1px solid #f0f1f3;
  background: var(--bg-card);
}

.ac-input__area {
  flex: 1;
  resize: none;
  border: 1px solid var(--border-line);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.6;
  color: var(--text-main);
  outline: none;
  transition: border-color 200ms var(--ease-out);
}

.ac-input__area:focus {
  border-color: var(--color-primary);
}

.ac-input__area:disabled {
  background: var(--bg-soft);
  cursor: not-allowed;
}

.ac-input__side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.ac-input__count {
  font-size: 11px;
  color: #b6bcc4;
}
</style>
