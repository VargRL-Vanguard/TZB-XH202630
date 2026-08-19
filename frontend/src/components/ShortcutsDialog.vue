<script setup lang="ts">
import { useUiStore } from '@/stores/ui'

/**
 * 快捷键说明面板（Ctrl+/ 唤起，Esc/点遮罩关闭）
 */
const ui = useUiStore()

const GROUPS: { title: string; items: { keys: string[]; desc: string }[] }[] = [
  {
    title: '全局',
    items: [
      { keys: ['Alt', 'T'], desc: '切换 白天 / 夜间模式' },
      { keys: ['Alt', 'B'], desc: '折叠 / 展开左侧导航' },
      { keys: ['Ctrl', '/'], desc: '打开本快捷键面板' }
    ]
  },
  {
    title: '聊天与输入',
    items: [
      { keys: ['Enter'], desc: '发送消息' },
      { keys: ['Shift', 'Enter'], desc: '输入框内换行' }
    ]
  },
  {
    title: '弹窗',
    items: [{ keys: ['Esc'], desc: '关闭当前弹窗 / 面板' }]
  }
]
</script>

<template>
  <el-dialog
    :model-value="ui.shortcutsOpen"
    title="键盘快捷键"
    width="420px"
    align-center
    append-to-body
    @update:model-value="ui.shortcutsOpen = $event"
  >
    <div class="sk-dialog">
      <section v-for="g in GROUPS" :key="g.title" class="sk-group">
        <h4 class="sk-group__title">{{ g.title }}</h4>
        <div v-for="item in g.items" :key="item.desc" class="sk-row">
          <span class="sk-row__keys">
            <kbd v-for="(k, i) in item.keys" :key="k + i" class="sk-kbd">
              {{ k }}<span v-if="i < item.keys.length - 1" class="sk-plus">+</span>
            </kbd>
          </span>
          <span class="sk-row__desc">{{ item.desc }}</span>
        </div>
      </section>
    </div>
  </el-dialog>
</template>

<style scoped>
.sk-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sk-group__title {
  font-size: 13px;
  color: var(--text-sub);
  margin-bottom: 8px;
  font-weight: 600;
}

.sk-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.sk-row__keys {
  display: flex;
  align-items: center;
  gap: 2px;
}

.sk-kbd {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border: 1px solid var(--border-line);
  border-bottom-width: 2px; /* 键帽立体感 */
  border-radius: 6px;
  background: var(--bg-soft);
  color: var(--text-main);
  font-family: inherit;
  font-size: 12px;
}

.sk-plus {
  margin: 0 2px;
  color: var(--text-sub);
  font-size: 11px;
}

.sk-row__desc {
  font-size: 13px;
  color: var(--text-main);
}
</style>
