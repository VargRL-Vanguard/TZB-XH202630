<script setup lang="ts">
import { ref } from 'vue'
import { ChatLineSquare, Pointer } from '@element-plus/icons-vue'

/**
 * 聊天输入区功能分页：快捷短语 + 表情
 * - 组件自带开合；父组件监听 @insert 接收待插入文本
 * - 快捷短语按教学场景分组；表情为 emoji 字符集（走 text 消息，无后端改动）
 */
defineEmits<{ (e: 'insert', text: string): void }>()

type TabKey = 'phrase' | 'emoji'
const activeTab = ref<TabKey>('phrase')
const open = ref(false)

const PHRASE_GROUPS: { label: string; items: string[] }[] = [
  { label: '问候', items: ['老师好！', '同学你好！', '早上好！', '下午好！'] },
  { label: '请教', items: ['我想请教一个问题：', '这个知识点我不太理解', '能再讲一遍吗？', '有没有推荐的资料？'] },
  { label: '汇报', items: ['我的作业已完成', '实验报告已提交', '本周学习计划已执行', '测验成绩已出'] },
  { label: '反馈', items: ['谢谢老师！', '明白了，感谢！', '辛苦了！', '收到！'] }
]

const EMOJI_GROUPS: { label: string; items: string[] }[] = [
  { label: '常用', items: ['😀', '😁', '😂', '🤣', '😊', '😍', '🤔', '😅', '😏', '🙄'] },
  { label: '手势', items: ['👍', '👎', '👏', '🙏', '💪', '🤝', '✌️', '👌', '🫶', '👋'] },
  { label: '学习', items: ['📚', '✏️', '📝', '💡', '🔥', '⭐', '🎯', '✅', '❌', '📌'] },
  { label: '心情', items: ['❤️', '😢', '😭', '😥', '😤', '🥳', '😴', '🤯', '😌', '🎊'] }
]

function toggle() {
  open.value = !open.value
}

function switchTab(tab: TabKey) {
  activeTab.value = tab
  open.value = true
}
</script>

<template>
  <div class="chat-quick" :class="{ 'chat-quick--open': open }">
    <!-- 功能分页条 -->
    <div class="chat-quick__tabs">
      <button
        class="chat-quick__tab"
        :class="{ 'chat-quick__tab--on': open && activeTab === 'phrase' }"
        title="快捷短语"
        @click="switchTab('phrase')"
      >
        <el-icon :size="14"><Pointer /></el-icon>
        <span>快捷短语</span>
      </button>
      <button
        class="chat-quick__tab"
        :class="{ 'chat-quick__tab--on': open && activeTab === 'emoji' }"
        title="表情"
        @click="switchTab('emoji')"
      >
        <el-icon :size="14"><ChatLineSquare /></el-icon>
        <span>表情</span>
      </button>
      <button class="chat-quick__fold" :title="open ? '收起面板' : '展开面板'" @click="toggle">
        {{ open ? '收起 ▴' : '展开 ▾' }}
      </button>
    </div>

    <!-- 面板（Transition 高度自适应） -->
    <Transition name="quick-slide">
      <div v-if="open" class="chat-quick__panel">
        <!-- 快捷短语页 -->
        <template v-if="activeTab === 'phrase'">
          <div v-for="g in PHRASE_GROUPS" :key="g.label" class="chat-quick__group">
            <span class="chat-quick__group-label">{{ g.label }}</span>
            <div class="chat-quick__chips">
              <button
                v-for="p in g.items"
                :key="p"
                class="chat-quick__chip"
                :title="`点击填入：${p}`"
                @click="$emit('insert', p)"
              >
                {{ p }}
              </button>
            </div>
          </div>
        </template>

        <!-- 表情页 -->
        <template v-else>
          <div v-for="g in EMOJI_GROUPS" :key="g.label" class="chat-quick__group">
            <span class="chat-quick__group-label">{{ g.label }}</span>
            <div class="chat-quick__emoji-grid">
              <button
                v-for="e in g.items"
                :key="e"
                class="chat-quick__emoji"
                :title="`插入 ${e}`"
                @click="$emit('insert', e)"
              >
                {{ e }}
              </button>
            </div>
          </div>
        </template>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.chat-quick {
  border-bottom: 1px solid var(--border-line);
  background: var(--bg-card);
}

/* ===== 分页条 ===== */
.chat-quick__tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
}

.chat-quick__tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-sub);
  font-size: 12px;
  cursor: pointer;
  transition:
    background-color 200ms var(--ease-out),
    color 200ms var(--ease-out);
}

.chat-quick__tab:hover {
  color: var(--color-primary);
  background: rgba(79, 110, 247, 0.08);
}

.chat-quick__tab--on {
  color: var(--color-primary);
  background: rgba(79, 110, 247, 0.12);
  font-weight: 600;
}

.chat-quick__tab:active {
  transform: scale(0.95);
}

.chat-quick__fold {
  margin-left: auto;
  padding: 4px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-sub);
  font-size: 12px;
  cursor: pointer;
}

.chat-quick__fold:hover {
  color: var(--color-primary);
}

/* ===== 面板 ===== */
.chat-quick__panel {
  max-height: 168px;
  overflow-y: auto;
  padding: 8px 12px 10px;
  border-top: 1px dashed var(--border-line);
  background: var(--bg-soft);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-quick__group {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.chat-quick__group-label {
  flex-shrink: 0;
  width: 34px;
  padding-top: 5px;
  font-size: 11px;
  color: var(--text-sub);
}

.chat-quick__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chat-quick__chip {
  padding: 4px 10px;
  border: 1px solid var(--border-line);
  border-radius: 999px;
  background: var(--bg-card);
  color: var(--text-main);
  font-size: 12px;
  cursor: pointer;
  transition:
    border-color 200ms var(--ease-out),
    color 200ms var(--ease-out),
    transform 150ms var(--ease-out);
}

.chat-quick__chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.chat-quick__chip:active {
  transform: scale(0.94);
}

.chat-quick__emoji-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chat-quick__emoji {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
  transition:
    background-color 150ms var(--ease-out),
    transform 150ms var(--ease-out);
}

.chat-quick__emoji:hover {
  background: rgba(79, 110, 247, 0.1);
}

.chat-quick__emoji:active {
  transform: scale(0.88);
}

/* ===== 面板展开动画 ===== */
.quick-slide-enter-active,
.quick-slide-leave-active {
  transition:
    max-height 220ms var(--ease-out),
    opacity 180ms var(--ease-out);
  overflow: hidden;
}
.quick-slide-enter-from,
.quick-slide-leave-to {
  max-height: 0;
  opacity: 0;
}
.quick-slide-enter-to,
.quick-slide-leave-from {
  max-height: 168px;
  opacity: 1;
}
</style>
