<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { login } from '@/api/auth'
import { BizError } from '@/api/request'
import { useAuthStore } from '@/stores/auth'
import { roleHome } from '@/router'

/**
 * 登录页（01 号任务 · DoD 逐条对应）
 * - 品牌首屏：项目名 + 副标题 + 科技感渐变背景（录屏第一画面）
 * - 错误内联红字，禁 alert；连点只发 1 个请求（loading + disabled）
 * - 回车提交；密码预校验（≥8 位 + 字母 + 数字）不满足按钮置灰 + 具体原因
 * - 成功存 token/userId/role，按角色跳转
 */

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const form = reactive({ username: '', password: '' })
const loading = ref(false)
/** 内联错误（服务端返回或提交异常） */
const inlineError = ref('')

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

/** 密码强度预校验：≥8 位 + 字母 + 数字（与后端双保险） */
const passwordProblem = computed(() => {
  const p = form.password
  if (!p) return ''
  if (p.length < 8) return '密码不少于 8 位'
  if (!/[A-Za-z]/.test(p)) return '密码需包含字母'
  if (!/\d/.test(p)) return '密码需包含数字'
  return ''
})

const canSubmit = computed(
  () => !!form.username && !!form.password && !passwordProblem.value && !loading.value
)

async function handleSubmit() {
  if (loading.value) return // 连点防护：只发 1 个请求
  if (!form.username || !form.password) {
    inlineError.value = '请输入用户名和密码'
    return
  }
  if (passwordProblem.value) {
    inlineError.value = passwordProblem.value
    return
  }
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  inlineError.value = ''
  try {
    const data = await login({ username: form.username.trim(), password: form.password })
    auth.setAuth({ token: data.token, userId: data.userId, role: data.role })
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    router.replace(redirect || roleHome(data.role))
  } catch (e) {
    // 内联展示：401 用后端原文「用户名或密码错误」；网络/服务异常给兜底文案
    inlineError.value = e instanceof BizError ? e.message : '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="glow glow--1"></div>
      <div class="glow glow--2"></div>
      <div class="grid-overlay"></div>
    </div>

    <div class="login-card">
      <div class="brand">
        <div class="brand__logo">智</div>
        <h1 class="brand__name">领域知识个性化生成与<br />多智能体协同决策系统</h1>
        <p class="brand__subtitle">挑战杯 XH-202630 · 多智能体协同 · 防幻觉 · 个性化导学</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        size="large"
        @submit.prevent
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名（如 student001）"
            autocomplete="username"
            data-testid="login-username"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            show-password
            autocomplete="current-password"
            data-testid="login-password"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <!-- 密码预校验具体原因（按钮置灰依据） -->
        <p v-if="passwordProblem" class="field-hint">{{ passwordProblem }}</p>

        <!-- 服务端错误内联红字：不跳页、不 alert -->
        <p v-if="inlineError" class="inline-error" data-testid="login-error" role="alert">
          {{ inlineError }}
        </p>

        <el-button
          type="primary"
          class="login-btn"
          :loading="loading"
          :disabled="!canSubmit"
          data-testid="login-submit"
          @click="handleSubmit"
        >
          {{ loading ? '登录中…' : '登 录' }}
        </el-button>

        <div class="login-links">
          <span>还没有账号？</span>
          <router-link to="/register" class="link">立即注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(135deg, #0b1020 0%, #16204a 45%, #2b1b5e 100%);
}

/* 科技感背景装饰 */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.glow {
  position: absolute;
  width: 480px;
  height: 480px;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.35;
}

.glow--1 {
  background: #4f6ef7;
  top: -120px;
  left: -100px;
  animation: drift 12s ease-in-out infinite alternate;
}

.glow--2 {
  background: #7c5cfc;
  bottom: -140px;
  right: -80px;
  animation: drift 14s ease-in-out infinite alternate-reverse;
}

@keyframes drift {
  from {
    transform: translate(0, 0) scale(1);
  }
  to {
    transform: translate(40px, 30px) scale(1.12);
  }
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 75%);
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  max-width: calc(100vw - 32px);
  padding: 40px 36px 32px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 24px 64px rgba(8, 12, 40, 0.45);
  animation: card-in 400ms ease-out;
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.brand {
  text-align: center;
  margin-bottom: 28px;
}

.brand__logo {
  width: 56px;
  height: 56px;
  margin: 0 auto 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  box-shadow: 0 8px 20px rgba(79, 110, 247, 0.4);
}

.brand__name {
  font-size: 20px;
  line-height: 1.45;
  color: var(--text-main);
  font-weight: 700;
}

.brand__subtitle {
  margin-top: 10px;
  font-size: 13px;
  color: var(--text-sub);
  letter-spacing: 0.5px;
}

.field-hint {
  margin: -8px 0 8px;
  font-size: 12px;
  color: var(--color-warning);
}

.inline-error {
  margin: -4px 0 12px;
  font-size: 13px;
  color: var(--color-danger);
  font-weight: 500;
}

.login-btn {
  width: 100%;
  font-size: 16px;
  letter-spacing: 4px;
}

.login-links {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--text-sub);
}

.link {
  color: var(--color-primary);
  text-decoration: none;
  margin-left: 4px;
}

.link:hover {
  text-decoration: underline;
}
</style>
