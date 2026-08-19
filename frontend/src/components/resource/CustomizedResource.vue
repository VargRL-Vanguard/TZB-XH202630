<script setup lang="ts">
import { ref } from 'vue'
import type { CustomizedResourceContent, ResourceBase } from '@/mock/fixtures/resources'

/**
 * 形态一：定制化资源（按知识点分节渲染）
 * - cited_chunks 可点开：点击引用切片 chip → 展开该切片原文（溯源演示）
 */
const props = defineProps<{ resource: ResourceBase }>()

const content = props.resource.content as CustomizedResourceContent
const openChunk = ref('')

function toggleChunk(id: string) {
  openChunk.value = openChunk.value === id ? '' : id
}

function chunkText(id: string) {
  return `[mock-chunk] ${id}：知识点切片原文，用于演示内容溯源（真实环境为知识库切片全文）。`
}
</script>

<template>
  <div class="cres">
    <section v-for="sec in content.sections" :key="sec.kp_id" class="cres__section">
      <h4 class="cres__heading">{{ sec.heading }}</h4>
      <p class="cres__body">{{ sec.body }}</p>
    </section>

    <!-- 引用切片（可点开溯源） -->
    <div class="cres__chunks">
      <h4 class="cres__chunks-title">
        引用切片（{{ resource.cited_chunks.length }}，点击查看原文）
      </h4>
      <div class="cres__chips">
        <button
          v-for="c in resource.cited_chunks"
          :key="c"
          class="cres__chip"
          :class="{ 'cres__chip--open': openChunk === c }"
          @click="toggleChunk(c)"
        >
          {{ c }}
        </button>
      </div>
      <transition name="chunk-expand">
        <pre v-if="openChunk" class="cres__chunk-body">{{ chunkText(openChunk) }}</pre>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.cres {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.cres__section {
  padding: var(--sp-1) var(--sp-2);
  border-left: 3px solid var(--color-primary);
  background: rgba(79, 110, 247, 0.04);
  border-radius: 0 8px 8px 0;
}

.cres__heading {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
}

.cres__body {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-main);
  white-space: pre-line;
}

.cres__chunks {
  margin-top: var(--sp-1);
}

.cres__chunks-title {
  font-size: 12px;
  color: var(--text-sub);
  margin-bottom: 6px;
}

.cres__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.cres__chip {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 999px;
  border: 1px dashed rgba(79, 110, 247, 0.5);
  color: var(--color-primary);
  background: transparent;
  cursor: pointer;
  transition: all 150ms var(--ease-out);
}

.cres__chip:hover {
  background: rgba(79, 110, 247, 0.08);
}

.cres__chip--open {
  border-style: solid;
  background: rgba(79, 110, 247, 0.14);
}

.cres__chunk-body {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f6f8ff;
  border: 1px solid rgba(79, 110, 247, 0.2);
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-main);
  white-space: pre-wrap;
  font-family: inherit;
}

.chunk-expand-enter-active {
  transition:
    opacity 200ms var(--ease-out),
    transform 200ms var(--ease-out);
}

.chunk-expand-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
