<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import router from '@/router'

/**
 * 路由切换顶部进度条（NProgress 风格，无第三方依赖）
 * - beforeEach 启动：快速推进到 ~80% 制造加载感
 * - afterEach 完成：冲到 100% 后淡出
 * - 首屏（组件挂载前的首次导航）不展示
 */
const visible = ref(false)
const width = ref(0)

let timer: number | undefined
let started = false

function start() {
  started = true
  window.clearInterval(timer)
  width.value = 8
  visible.value = true
  let p = 8
  timer = window.setInterval(() => {
    p = Math.min(82, p + 4 + Math.random() * 10)
    width.value = p
  }, 120)
}

function done() {
  if (!started) return
  started = false
  window.clearInterval(timer)
  width.value = 100
  window.setTimeout(() => {
    visible.value = false
  }, 260)
}

const removeBefore = router.beforeEach(start)
const removeAfter = router.afterEach(done)

onMounted(() => {
  /* 挂载即完成首屏导航的进度（不闪） */
})
onBeforeUnmount(() => {
  window.clearInterval(timer)
  removeBefore()
  removeAfter()
})
</script>

<template>
  <div
    class="route-progress"
    :class="{ 'route-progress--on': visible }"
    :style="{ width: width + '%' }"
    aria-hidden="true"
  />
</template>

<style scoped>
.route-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  z-index: 3000; /* 压过 Element 弹层 */
  border-radius: 0 2px 2px 0;
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
  box-shadow: 0 0 8px rgba(79, 110, 247, 0.45);
  opacity: 0;
  pointer-events: none;
  transition:
    width 200ms ease-out,
    opacity 200ms ease-out;
}

.route-progress--on {
  opacity: 1;
}
</style>
