<template>
  <div class="page placeholder">
    <h1>AI 辅导</h1>
    <p>该页面由 D 组负责人开发中（04_D_大屏_AI对话_质量看板）</p>
    <router-link to="/chat">先去消息页 →</router-link>
  </div>
</template>

<style scoped>
.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-sub);
}
h1 {
  color: var(--text-main);
}
a {
  color: var(--color-primary);
  text-decoration: none;
}
</style>
