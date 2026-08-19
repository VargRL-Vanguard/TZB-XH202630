<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, UploadFilled } from '@element-plus/icons-vue'
import {
  getConversationList,
  getHistory,
  markRead,
  sendMessage,
  type ChatMessage,
  type Conversation
} from '@/api/chat'
import { useAuthStore } from '@/stores/auth'
import { wsClient } from '@/ws/client'
import ChatQuickPanel from '@/components/chat/ChatQuickPanel.vue'

/**
 * 聊天页（01 号任务阶段三 · 契约 §1.6-1.9 + DoD）
 * - 会话列表：未读红点，进入会话调 /api/chat/read 清零
 * - 历史分页：滑到顶加载更多，hasMore=false 停止
 * - WS 实时接收：契约 type:"message"{from,content,timestamp}；
 *   兼容后端 ws/handlers.py 实际推送的 type:"chat"{fromId,content,timestamp(秒)}
 * - 发送：乐观插入 pending 气泡；失败变红 + 重发按钮，消息永不消失
 * - 4 态：骨架屏 / 错误重试 / 空态引导 / 断网横幅（全局 NetBanner）
 */

const auth = useAuthStore()
const me = computed(() => auth.userId)

const PAGE_SIZE = 20

/** 本地消息（含发送中间态，比契约多 pending/failed 两个客户端态） */
interface LocalMessage {
  localId: string
  id: number | null
  userId: string
  targetId: string
  content: string
  type: ChatMessage['type']
  timestamp: string
  status: 'pending' | 'failed' | 'sent' | 'read'
}

let localSeq = 0
function toLocal(m: ChatMessage): LocalMessage {
  return {
    localId: `srv-${m.id}-${++localSeq}`,
    id: m.id,
    userId: m.userId,
    targetId: m.targetId,
    content: m.content,
    type: m.type,
    timestamp: m.timestamp,
    status: m.status
  }
}

// ============ 会话列表 ============
const conversations = ref<Conversation[]>([])
const convLoading = ref(false)
const convError = ref(false)
const activeTargetId = ref('')

const activeConversation = computed(
  () => conversations.value.find((c) => c.targetId === activeTargetId.value) ?? null
)

async function loadConversations() {
  convLoading.value = true
  convError.value = false
  try {
    conversations.value = await getConversationList(me.value)
  } catch {
    convError.value = true
  } finally {
    convLoading.value = false
  }
}

// ============ 历史消息 ============
const messages = ref<LocalMessage[]>([])
const msgLoading = ref(false)
const msgError = ref(false)
const hasMore = ref(false)
const loadingMore = ref(false)
const offset = ref(0)

const scrollRef = ref<HTMLElement>()

async function openConversation(targetId: string) {
  if (targetId === activeTargetId.value) return
  activeTargetId.value = targetId
  messages.value = []
  offset.value = 0
  hasMore.value = false
  await loadMessages(true)
  // 进入会话即上报已读（契约 §1.9），本地清零红点
  const conv = conversations.value.find((c) => c.targetId === targetId)
  if (conv && conv.unread > 0) {
    conv.unread = 0
    markRead({ userId: me.value, targetId }).catch(() => {
      /* 已读失败不打扰用户，下次进入重试 */
    })
  }
}

async function loadMessages(first = false) {
  msgLoading.value = true
  msgError.value = false
  try {
    const resp = await getHistory({
      userId: me.value,
      targetId: activeTargetId.value,
      limit: PAGE_SIZE,
      offset: 0
    })
    // 后端按时间倒序/正序未定：统一按时间戳升序渲染（旧→新）
    const list = [...resp.list]
      .map(toLocal)
      .sort((a, b) => +new Date(a.timestamp) - +new Date(b.timestamp))
    messages.value = list
    hasMore.value = resp.hasMore
    offset.value = list.length
    if (first) await scrollToBottom()
  } catch {
    msgError.value = true
  } finally {
    msgLoading.value = false
  }
}

/** 滑到顶加载更多（保留原阅读位置） */
async function loadMore() {
  if (!hasMore.value || loadingMore.value || msgLoading.value) return
  loadingMore.value = true
  const el = scrollRef.value
  const prevHeight = el?.scrollHeight ?? 0
  try {
    const resp = await getHistory({
      userId: me.value,
      targetId: activeTargetId.value,
      limit: PAGE_SIZE,
      offset: offset.value
    })
    const older = resp.list
      .map(toLocal)
      .sort((a, b) => +new Date(a.timestamp) - +new Date(b.timestamp))
    // 去重（按服务端 id）
    const existIds = new Set(messages.value.map((m) => m.id))
    const fresh = older.filter((m) => m.id === null || !existIds.has(m.id))
    messages.value = [...fresh, ...messages.value]
    offset.value += resp.list.length
    hasMore.value = resp.hasMore
    await nextTick()
    if (el) el.scrollTop = el.scrollHeight - prevHeight
  } catch {
    ElMessage.error('加载历史消息失败，请重试')
  } finally {
    loadingMore.value = false
  }
}

function onScroll() {
  const el = scrollRef.value
  if (el && el.scrollTop <= 40) void loadMore()
}

async function scrollToBottom() {
  await nextTick()
  const el = scrollRef.value
  if (el) el.scrollTop = el.scrollHeight
}

// ============ 发送（乐观更新 + 失败重发，消息不消失） ============
const draft = ref('')
const sending = ref(false)

async function doSend() {
  const content = draft.value.trim()
  if (!content || !activeTargetId.value || sending.value) return
  if (content.length > 2000) {
    ElMessage.warning('消息不能超过 2000 字')
    return
  }
  draft.value = ''
  sending.value = true

  const local: LocalMessage = {
    localId: `local-${Date.now()}-${++localSeq}`,
    id: null,
    userId: me.value,
    targetId: activeTargetId.value,
    content,
    type: 'text',
    timestamp: new Date().toISOString(),
    status: 'pending'
  }
  messages.value.push(local)
  void scrollToBottom()
  // 同步会话列表最后一条
  bumpConversation(activeTargetId.value, content)

  try {
    const resp = await sendMessage({ userId: me.value, targetId: activeTargetId.value, content })
    local.id = resp.id
    local.timestamp = resp.timestamp
    local.status = resp.status
  } catch {
    // 失败：气泡变红 + 重发按钮，消息保留
    local.status = 'failed'
  } finally {
    sending.value = false
  }
}

async function resend(m: LocalMessage) {
  m.status = 'pending'
  try {
    const resp = await sendMessage({ userId: me.value, targetId: m.targetId, content: m.content })
    m.id = resp.id
    m.timestamp = resp.timestamp
    m.status = resp.status
  } catch {
    m.status = 'failed'
    ElMessage.error('重发失败，请检查网络')
  }
}

// ============ WS 实时接收 ============
function normalizeIncoming(
  payload: Record<string, unknown>
): { from: string; content: string; timestamp: string } | null {
  const from = (payload.from ?? payload.fromId) as string | undefined
  const content = payload.content as string | undefined
  if (!from || !content) return null
  const rawTs = payload.timestamp as string | number | undefined
  let timestamp = new Date().toISOString()
  if (typeof rawTs === 'number') timestamp = new Date(rawTs * 1000).toISOString()
  else if (typeof rawTs === 'string' && rawTs) timestamp = rawTs
  return { from, content, timestamp }
}

function onWsMessage(payload: Record<string, unknown>) {
  const incoming = normalizeIncoming(payload)
  if (!incoming) return

  if (incoming.from === activeTargetId.value) {
    // 当前会话：直接追加左侧气泡 + 已读回执 + 对端在线则我方 sent 升级为 read（✓✓）
    messages.value.push({
      localId: `ws-${Date.now()}-${++localSeq}`,
      id: null,
      userId: incoming.from,
      targetId: me.value,
      content: incoming.content,
      type: 'text',
      timestamp: incoming.timestamp,
      status: 'sent'
    })
    messages.value.forEach((m) => {
      if (m.userId === me.value && m.status === 'sent') m.status = 'read'
    })
    void scrollToBottom()
    markRead({ userId: me.value, targetId: incoming.from }).catch(() => {})
    bumpConversation(incoming.from, incoming.content, true)
  } else {
    // 其他会话：未读 +1，列表最后一条同步更新
    bumpConversation(incoming.from, incoming.content, true)
  }
}

/** 更新会话列表 lastMessage/unread（不存在则补一条） */
function bumpConversation(targetId: string, content: string, unreadPlus = false) {
  let conv = conversations.value.find((c) => c.targetId === targetId)
  if (!conv) {
    conv = { targetId, name: targetId, lastMessage: '', lastTime: '', unread: 0 }
    conversations.value.unshift(conv)
  }
  conv.lastMessage = content
  conv.lastTime = new Date().toISOString()
  if (unreadPlus && targetId !== activeTargetId.value) conv.unread += 1
}

// ============ 工具 ============
/** 快捷短语/表情插入：追加到草稿末尾（可继续编辑后发送） */
function onQuickInsert(text: string) {
  draft.value = draft.value + text
}

// ============ 自定义聊天背景 ============
// 预设渐变 + 本地图片上传，localStorage 持久化（key: tzb:chat-bg）
const BG_STORAGE_KEY = 'tzb:chat-bg'
const PRESET_BGS = [
  { id: 'default', label: '默认', css: '' },
  {
    id: 'aurora',
    label: '极光',
    css: 'linear-gradient(160deg, #e0e7ff 0%, #eef2ff 45%, #ecfeff 100%)'
  },
  {
    id: 'sakura',
    label: '樱粉',
    css: 'linear-gradient(160deg, #fdf2f8 0%, #fff1f2 50%, #fef3c7 100%)'
  },
  {
    id: 'mint',
    label: '抹茶',
    css: 'linear-gradient(160deg, #ecfdf5 0%, #f0fdfa 50%, #f0f9ff 100%)'
  },
  {
    id: 'night',
    label: '夜幕',
    css: 'linear-gradient(160deg, #0f172a 0%, #1e1b4b 55%, #312e81 100%)'
  },
  {
    id: 'peach',
    label: '蜜桃',
    css: 'linear-gradient(160deg, #fff7ed 0%, #ffe4e6 55%, #fae8ff 100%)'
  }
] as const

const bgId = ref(localStorage.getItem(BG_STORAGE_KEY) ?? 'default')
/** 自定义图片（dataURL，优先于预设） */
const bgImage = ref<string | null>(
  (() => {
    try {
      return localStorage.getItem(`${BG_STORAGE_KEY}:img`)
    } catch {
      return null
    }
  })()
)

const usingCustomImage = computed(() => !!bgImage.value)
const chatBodyStyle = computed(() => {
  if (bgImage.value) {
    // veil 遮罩层（--chat-bg-veil 随昼夜主题变化）保证气泡可读；遮罩叠在背景图上、内容下方
    return {
      backgroundImage: `linear-gradient(var(--chat-bg-veil), var(--chat-bg-veil)), url(${bgImage.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  const preset = PRESET_BGS.find((p) => p.id === bgId.value)
  return preset?.css ? { background: preset.css } : {}
})

function applyBg(id: string) {
  bgId.value = id
  bgImage.value = null
  localStorage.setItem(BG_STORAGE_KEY, id)
  localStorage.removeItem(`${BG_STORAGE_KEY}:img`)
}

const bgFileRef = ref<HTMLInputElement>()
function onPickBgFile() {
  bgFileRef.value?.click()
}
function onBgFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 4 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 4MB，请压缩后再试')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    bgImage.value = String(reader.result)
    try {
      localStorage.setItem(`${BG_STORAGE_KEY}:img`, String(reader.result))
    } catch {
      // 存储超限（dataURL 过大）时仅本次会话生效
      ElMessage.warning('图片较大，仅本次会话生效')
    }
    ElMessage.success('聊天背景已更新')
  }
  reader.readAsDataURL(file)
  ;(e.target as HTMLInputElement).value = ''
}

function fmtTime(ts: string): string {
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return ''
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}

function fmtListTime(ts: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return ''
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  return sameDay ? fmtTime(ts) : `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')}`
}

const totalUnread = computed(() => conversations.value.reduce((s, c) => s + c.unread, 0))

// ============ 生命周期 ============
const offMessage = wsClient.on('message', onWsMessage)
// 兼容后端 ws/handlers.py 实际推送 type:"chat"（fromId 字段）
const offChat = wsClient.on('chat', onWsMessage)

onMounted(() => {
  void loadConversations()
})

onUnmounted(() => {
  offMessage()
  offChat()
})
</script>

<template>
  <div class="chat-page page">
    <div class="chat-shell">
      <!-- ============ 左：会话列表 ============ -->
      <aside class="conv-panel">
        <header class="conv-panel__header">
          <h2>消息</h2>
          <span v-if="totalUnread > 0" class="conv-panel__total-unread"
            >{{ totalUnread }} 条未读</span
          >
        </header>

        <!-- 骨架屏 -->
        <div v-if="convLoading" class="conv-panel__body">
          <el-skeleton v-for="i in 6" :key="i" class="conv-skeleton" animated>
            <template #template>
              <div class="conv-skeleton__row">
                <el-skeleton-item variant="circle" style="width: 40px; height: 40px" />
                <div class="conv-skeleton__lines">
                  <el-skeleton-item variant="text" style="width: 55%" />
                  <el-skeleton-item variant="text" style="width: 85%" />
                </div>
              </div>
            </template>
          </el-skeleton>
        </div>

        <!-- 错误重试 -->
        <div v-else-if="convError" class="state-block">
          <p class="state-block__icon">⚠️</p>
          <p>会话列表加载失败</p>
          <el-button size="small" type="primary" plain @click="loadConversations">重试</el-button>
        </div>

        <!-- 空态引导 -->
        <div v-else-if="conversations.length === 0" class="state-block">
          <p class="state-block__icon">📭</p>
          <p>暂无会话</p>
          <p class="state-block__hint">与其他用户开始交流后，会话将显示在这里</p>
        </div>

        <!-- 列表 -->
        <div v-else class="conv-panel__body">
          <div
            v-for="conv in conversations"
            :key="conv.targetId"
            class="conv-item"
            :class="{ 'conv-item--active': conv.targetId === activeTargetId }"
            role="button"
            tabindex="0"
            @click="openConversation(conv.targetId)"
            @keyup.enter="openConversation(conv.targetId)"
          >
            <div class="conv-item__avatar">{{ (conv.name || conv.targetId).slice(0, 1) }}</div>
            <div class="conv-item__main">
              <div class="conv-item__row">
                <span class="conv-item__name">{{ conv.name || conv.targetId }}</span>
                <span class="conv-item__time num">{{ fmtListTime(conv.lastTime) }}</span>
              </div>
              <div class="conv-item__row">
                <span class="conv-item__last">{{ conv.lastMessage }}</span>
                <span v-if="conv.unread > 0" class="conv-item__badge num">{{
                  conv.unread > 99 ? '99+' : conv.unread
                }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- ============ 右：聊天面板 ============ -->
      <section class="chat-panel">
        <template v-if="activeConversation || activeTargetId">
          <header class="chat-panel__header">
            <div class="chat-panel__title">
              <span class="chat-panel__name">{{ activeConversation?.name || activeTargetId }}</span>
              <span class="chat-panel__id">（{{ activeTargetId }}）</span>
            </div>

            <!-- 聊天背景设置 -->
            <el-popover placement="bottom-end" :width="236" trigger="click">
              <template #reference>
                <el-button :icon="Picture" circle size="small" title="聊天背景" />
              </template>
              <div class="bg-picker">
                <h4 class="bg-picker__title">聊天背景</h4>
                <div class="bg-picker__grid">
                  <button
                    v-for="p in PRESET_BGS"
                    :key="p.id"
                    class="bg-picker__swatch"
                    :class="{
                      'bg-picker__swatch--on': bgId === p.id && !usingCustomImage
                    }"
                    :style="p.css ? { background: p.css } : {}"
                    :title="p.label"
                    @click="applyBg(p.id)"
                  >
                    <span v-if="!p.css" class="bg-picker__default">默认</span>
                    <span v-if="bgId === p.id && !usingCustomImage" class="bg-picker__check"
                      >✓</span
                    >
                  </button>
                </div>
                <el-button
                  class="bg-picker__upload"
                  size="small"
                  :icon="UploadFilled"
                  @click="onPickBgFile"
                >
                  {{ usingCustomImage ? '更换自定义图片' : '上传自定义图片' }}
                </el-button>
                <p class="bg-picker__hint">选择即时生效，本地保存（≤4MB）</p>
                <input
                  ref="bgFileRef"
                  type="file"
                  accept="image/*"
                  style="display: none"
                  @change="onBgFileChange"
                />
              </div>
            </el-popover>
          </header>

          <!-- 消息区 4 态 -->
          <div
            ref="scrollRef"
            class="chat-panel__body"
            :class="{ 'chat-panel__body--bg': bgId !== 'default' || usingCustomImage }"
            :style="chatBodyStyle"
            @scroll.passive="onScroll"
          >
            <!-- 加载更多提示 -->
            <div v-if="loadingMore" class="load-more-tip">加载历史消息…</div>
            <div v-else-if="hasMore && messages.length" class="load-more-tip">上滑加载更多</div>

            <!-- 骨架屏 -->
            <div v-if="msgLoading" class="msg-skeleton">
              <el-skeleton v-for="i in 5" :key="i" animated>
                <template #template>
                  <div
                    :class="[
                      'msg-skeleton__row',
                      i % 2 ? 'msg-skeleton__row--left' : 'msg-skeleton__row--right'
                    ]"
                  >
                    <el-skeleton-item variant="circle" style="width: 32px; height: 32px" />
                    <el-skeleton-item
                      variant="text"
                      :style="{ width: 30 + ((i * 13) % 30) + '%' }"
                    />
                  </div>
                </template>
              </el-skeleton>
            </div>

            <!-- 错误重试 -->
            <div v-else-if="msgError" class="state-block">
              <p class="state-block__icon">⚠️</p>
              <p>消息加载失败</p>
              <el-button size="small" type="primary" plain @click="loadMessages(true)"
                >重试</el-button
              >
            </div>

            <!-- 空态引导 -->
            <div v-else-if="messages.length === 0" class="state-block">
              <p class="state-block__icon">💬</p>
              <p>还没有消息</p>
              <p class="state-block__hint">发送第一条消息，开始交流吧</p>
            </div>

            <!-- 消息列表 -->
            <template v-else>
              <div
                v-for="m in messages"
                :key="m.localId"
                class="bubble-row"
                :class="m.userId === me ? 'bubble-row--right' : 'bubble-row--left'"
              >
                <div class="bubble-row__avatar">
                  {{ (m.userId === me ? '我' : activeConversation?.name || m.userId).slice(0, 1) }}
                </div>
                <div class="bubble-wrap">
                  <div class="bubble" :class="{ 'bubble--failed': m.status === 'failed' }">
                    <span class="bubble__text">{{ m.content }}</span>
                  </div>
                  <div class="bubble-row__meta">
                    <span class="num">{{ fmtTime(m.timestamp) }}</span>
                    <!-- 已读回执：sent ✓ → read ✓✓（契约 §1.7） -->
                    <span v-if="m.userId === me && m.status === 'sent'" class="tick" title="已发送"
                      >✓</span
                    >
                    <span
                      v-else-if="m.userId === me && m.status === 'read'"
                      class="tick tick--read"
                      title="已读"
                      >✓✓</span
                    >
                    <span
                      v-else-if="m.status === 'pending'"
                      class="tick tick--pending"
                      title="发送中"
                      >···</span
                    >
                    <button
                      v-else-if="m.status === 'failed'"
                      class="resend-btn"
                      title="发送失败，点击重发"
                      @click="resend(m)"
                    >
                      重发
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- 输入区 -->
          <footer class="chat-panel__footer">
            <ChatQuickPanel @insert="onQuickInsert" />
            <el-input
              v-model="draft"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 5 }"
              placeholder="输入消息，Enter 发送，Shift+Enter 换行"
              maxlength="2000"
              resize="none"
              data-testid="chat-input"
              @keydown.enter.exact.prevent="doSend"
            />
            <div class="chat-panel__footer-bar">
              <span class="chat-panel__count num">{{ draft.length }}/2000</span>
              <el-button
                type="primary"
                :loading="sending"
                :disabled="!draft.trim()"
                data-testid="chat-send"
                @click="doSend"
              >
                发送
              </el-button>
            </div>
          </footer>
        </template>

        <!-- 未选会话空态 -->
        <div v-else class="chat-panel__placeholder state-block">
          <p class="state-block__icon">🗣️</p>
          <p>选择左侧会话开始聊天</p>
          <p class="state-block__hint">实时消息将通过 WebSocket 推送，无需刷新</p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-shell {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: var(--sp-2);
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}

/* ============ 会话列表 ============ */
.conv-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  overflow: hidden;
}

.conv-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--border-line);
}

.conv-panel__header h2 {
  font-size: 16px;
}

.conv-panel__total-unread {
  font-size: 12px;
  color: var(--color-danger);
  background: color-mix(in srgb, var(--color-danger) 12%, transparent);
  border-radius: 10px;
  padding: 2px 8px;
}

.conv-panel__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px;
}

.conv-skeleton {
  padding: 10px 8px;
}

.conv-skeleton__row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.conv-skeleton__lines {
  flex: 1;
}

.conv-item {
  display: flex;
  gap: 12px;
  padding: 12px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background var(--dur-fast);
}

.conv-item:hover {
  background: var(--bg-soft);
}

.conv-item--active,
.conv-item--active:hover {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.conv-item__avatar {
  flex: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
}

.conv-item__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conv-item__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.conv-item__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-item__time {
  flex: none;
  font-size: 12px;
  color: var(--text-sub);
}

.conv-item__last {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  color: var(--text-sub);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-item__badge {
  flex: none;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--color-danger);
  color: #fff;
  font-size: 11px;
  line-height: 18px;
  text-align: center;
}

/* ============ 聊天面板 ============ */
.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-card);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  overflow: hidden;
}

.chat-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-line);
}

.chat-panel__title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-panel__name {
  font-size: 16px;
  font-weight: 600;
}

.chat-panel__id {
  font-size: 12px;
  color: var(--text-sub);
}

.chat-panel__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
  background: var(--bg-soft);
}

.chat-panel__placeholder {
  height: 100%;
}

.load-more-tip {
  text-align: center;
  font-size: 12px;
  color: var(--text-sub);
  padding: 4px 0 12px;
}

.msg-skeleton__row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.msg-skeleton__row--right {
  flex-direction: row-reverse;
}

/* ============ 气泡 ============ */
.bubble-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  animation: bubble-in 200ms var(--ease-out);
}

@keyframes bubble-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.bubble-row--right {
  flex-direction: row-reverse;
}

.bubble-row__avatar {
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, var(--color-agent-blue), var(--color-primary));
}

.bubble-row--right .bubble-row__avatar {
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
}

.bubble-wrap {
  max-width: 62%;
  display: flex;
  flex-direction: column;
}

.bubble-row--right .bubble-wrap {
  align-items: flex-end;
}

.bubble {
  padding: 9px 14px;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-line);
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.bubble-row--right .bubble {
  background: linear-gradient(135deg, var(--color-primary), #6d8bff);
  border: none;
  color: #fff;
}

.bubble--failed {
  background: color-mix(in srgb, var(--color-danger) 14%, var(--bg-card)) !important;
  border: 1px solid var(--color-danger) !important;
  color: var(--color-danger) !important;
}

.bubble-row__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-sub);
}

.tick {
  letter-spacing: -1px;
}

.tick--read {
  color: var(--color-primary);
  font-weight: 700;
}

.tick--pending {
  color: var(--text-sub);
}

.resend-btn {
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  background: var(--bg-card);
  border-radius: 4px;
  font-size: 11px;
  padding: 0 8px;
  line-height: 18px;
  cursor: pointer;
}

.resend-btn:hover {
  background: var(--color-danger);
  color: #fff;
}

/* ============ 输入区 ============ */
.chat-panel__footer {
  padding: 12px 16px 14px;
  border-top: 1px solid var(--border-line);
}

.chat-panel__footer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.chat-panel__count {
  font-size: 12px;
  color: var(--text-sub);
}

/* ============ 通用状态块 ============ */
.state-block {
  flex: 1;
  min-height: 160px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  text-align: center;
  color: var(--text-sub);
  font-size: 14px;
}

.state-block__icon {
  font-size: 34px;
  margin: 0;
}

.state-block__hint {
  font-size: 12px;
  color: var(--text-sub);
}

/* ============ 聊天背景选择器（popover 内） ============ */
.bg-picker {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bg-picker__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.bg-picker__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.bg-picker__swatch {
  position: relative;
  height: 44px;
  border-radius: 8px;
  border: 1px solid var(--border-line);
  cursor: pointer;
  transition:
    transform var(--dur-fast) var(--ease-out),
    border-color var(--dur-fast) var(--ease-out),
    box-shadow var(--dur-fast) var(--ease-out);
}

.bg-picker__swatch:hover {
  transform: translateY(-1px);
  border-color: var(--color-primary);
}

.bg-picker__swatch--on {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 25%, transparent);
}

.bg-picker__default {
  font-size: 12px;
  color: var(--text-sub);
}

.bg-picker__check {
  position: absolute;
  right: 4px;
  bottom: 2px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  text-shadow: 0 0 4px rgba(255, 255, 255, 0.8);
}

.bg-picker__upload {
  width: 100%;
}

.bg-picker__hint {
  font-size: 11px;
  color: var(--text-sub);
}
</style>
