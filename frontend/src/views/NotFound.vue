<template>
  <div class="page notfound">
    <div class="notfound__card">
      <p class="notfound__code num">404</p>
      <h1>页面不存在</h1>
      <p class="notfound__desc">您访问的页面不存在或已被移除</p>
      <el-button type="primary" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { roleHome } from '@/router'

const router = useRouter()
const auth = useAuthStore()

function goHome() {
  router.push(auth.isLoggedIn ? roleHome(auth.role) : '/login')
}
</script>

<style scoped>
.notfound {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}

.notfound__card {
  text-align: center;
  padding: 48px 64px;
  background: #fff;
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
}

.notfound__code {
  font-size: 64px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}

h1 {
  margin: 16px 0 8px;
  font-size: 20px;
  color: var(--text-main);
}

.notfound__desc {
  margin-bottom: 24px;
  font-size: 14px;
  color: var(--text-sub);
}
</style>
