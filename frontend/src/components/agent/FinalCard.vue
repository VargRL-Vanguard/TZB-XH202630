<script setup lang="ts">
/**
 * 决策融合结论弹卡（agent.final 后弹出）
 * - ok：融合是否通过；summary：结论文本；traceId：可复制
 * - 弹入动画（scale+fade），深色大屏风格
 */
defineProps<{ ok: boolean; summary: string; traceId: string }>()
const emit = defineEmits<{ (e: 'close'): void }>()

async function copyTrace(id: string) {
  try {
    await navigator.clipboard.writeText(id)
    const { ElMessage } = await import('element-plus')
    ElMessage.success('traceId 已复制')
  } catch {
    /* 剪贴板不可用时静默 */
  }
}
</script>

<template>
  <div class="final-card" role="dialog" aria-label="决策融合结论">
    <div class="final-card__glow" aria-hidden="true"></div>
    <div class="final-card__head">
      <span
        class="final-card__badge"
        :class="ok ? 'final-card__badge--ok' : 'final-card__badge--fail'"
      >
        {{ ok ? '✓ 融合通过' : '✕ 融合未通过' }}
      </span>
      <button class="final-card__close" aria-label="关闭" @click="emit('close')">✕</button>
    </div>
    <p class="final-card__summary">{{ summary }}</p>
    <div class="final-card__foot">
      <button class="final-card__trace" title="点击复制" @click="copyTrace(traceId)">
        traceId：{{ traceId }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.final-card {
  position: relative;
  max-width: 520px;
  padding: 20px 24px;
  border-radius: 14px;
  background: rgba(17, 24, 39, 0.92);
  border: 1px solid rgba(56, 189, 248, 0.35);
  box-shadow: 0 12px 48px rgba(56, 189, 248, 0.18);
  backdrop-filter: blur(6px);
}

.final-card__glow {
  position: absolute;
  inset: -1px;
  border-radius: 14px;
  padding: 1px;
  background: linear-gradient(
    120deg,
    rgba(56, 189, 248, 0.5),
    rgba(167, 139, 250, 0.5),
    rgba(251, 191, 36, 0.5)
  );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.final-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.final-card__badge {
  font-size: 14px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 999px;
}

.final-card__badge--ok {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.45);
}

.final-card__badge--fail {
  color: #f87171;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.45);
}

.final-card__close {
  border: none;
  background: transparent;
  color: #9ca3af;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
}

.final-card__close:hover {
  color: #e5e7eb;
  background: rgba(255, 255, 255, 0.08);
}

.final-card__summary {
  font-size: 14px;
  line-height: 1.8;
  color: #e5e7eb;
}

.final-card__foot {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.final-card__trace {
  font-size: 11px;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 6px;
  padding: 3px 10px;
  cursor: pointer;
  font-variant-numeric: tabular-nums;
}

.final-card__trace:hover {
  color: #e5e7eb;
  border-color: rgba(148, 163, 184, 0.5);
}

/* 进场动画（父组件 v-if 控制显隐，这里只负责弹入） */
.final-card {
  animation: final-in 300ms var(--ease-out);
}

@keyframes final-in {
  from {
    opacity: 0;
    transform: scale(0.92) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>
