<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { register } from '@/api/auth'

/**
 * 注册页（01 号任务 · 契约 §1.1）
 * - username / password / name / role 下拉三选一 + 可选 education / major
 * - 密码预校验：≥8 位 + 字母 + 数字，不满足按钮置灰 + 具体原因（与后端双保险）
 * - 成功 toast「注册成功」→ 自动跳登录；重复用户名 400 由拦截器 toast 后端原文
 */

const router = useRouter()
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  password: '',
  name: '',
  role: 'student',
  education: '',
  major: ''
})

const loading = ref(false)
const inlineError = ref('')

const roleOptions = [
  { value: 'student', label: '学生' },
  { value: 'teacher', label: '教师' },
  { value: 'admin', label: '管理员' }
]

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 64, message: '用户名 3-64 个字符', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 1, max: 64, message: '姓名 1-64 个字符', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

/** 密码强度预校验（≥8 位 + 字母 + 数字） */
const passwordProblem = computed(() => {
  const p = form.password
  if (!p) return ''
  if (p.length < 8) return '密码不少于 8 位'
  if (!/[A-Za-z]/.test(p)) return '密码需包含字母'
  if (!/\d/.test(p)) return '密码需包含数字'
  return ''
})

const canSubmit = computed(
  () =>
    form.username.trim().length >= 3 &&
    !!form.name.trim() &&
    !!form.role &&
    !!form.password &&
    !passwordProblem.value &&
    !loading.value
)

async function handleSubmit() {
  if (loading.value) return
  if (!canSubmit.value) {
    inlineError.value = passwordProblem.value || '请完整填写必填项'
    return
  }
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  inlineError.value = ''
  try {
    await register({
      username: form.username.trim(),
      password: form.password,
      name: form.name.trim(),
      role: form.role,
      // 选填字段：空串不提交，避免后端存空值
      education: form.education.trim() || undefined,
      major: form.major.trim() || undefined
    })
    ElMessage.success('注册成功，请登录')
    router.replace('/login')
  } catch (e) {
    // 400/403/404（如「用户名已存在」）已由拦截器 toast 后端原文；其余兜底内联提示
    const code = (e as { code?: number }).code
    if (code !== 400 && code !== 403 && code !== 404) {
      inlineError.value = '网络异常，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <div class="register-bg">
      <div class="glow glow--1"></div>
      <div class="glow glow--2"></div>
      <div class="grid-overlay"></div>
    </div>

    <div class="register-card">
      <h1 class="title">创建账号</h1>
      <p class="subtitle">领域知识个性化生成与多智能体协同决策系统</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="3-64 个字符，登录用"
            maxlength="64"
            data-testid="reg-username"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="≥8 位，需包含字母和数字"
            show-password
            maxlength="128"
            data-testid="reg-password"
          />
        </el-form-item>
        <p v-if="passwordProblem" class="field-hint">{{ passwordProblem }}</p>

        <el-form-item label="姓名" prop="name">
          <el-input
            v-model="form.name"
            placeholder="显示名称"
            maxlength="64"
            data-testid="reg-name"
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select
            v-model="form.role"
            placeholder="请选择角色"
            style="width: 100%"
            data-testid="reg-role"
          >
            <el-option v-for="r in roleOptions" :key="r.value" :value="r.value" :label="r.label" />
          </el-select>
        </el-form-item>

        <div v-if="form.role === 'student'" class="optional-row">
          <el-form-item label="学历（选填）">
            <el-input v-model="form.education" placeholder="如：本科应届" maxlength="32" />
          </el-form-item>
          <el-form-item label="专业（选填）">
            <el-input v-model="form.major" placeholder="如：软件工程" maxlength="64" />
          </el-form-item>
        </div>

        <p v-if="inlineError" class="inline-error" role="alert">{{ inlineError }}</p>

        <el-button
          type="primary"
          class="register-btn"
          :loading="loading"
          :disabled="!canSubmit"
          data-testid="reg-submit"
          @click="handleSubmit"
        >
          {{ loading ? '提交中…' : '注 册' }}
        </el-button>

        <div class="register-links">
          <span>已有账号？</span>
          <router-link to="/login" class="link">返回登录</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  position: relative;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  overflow: hidden;
  background: linear-gradient(135deg, #0b1020 0%, #16204a 45%, #2b1b5e 100%);
}

.register-bg {
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
}

.glow--2 {
  background: #7c5cfc;
  bottom: -140px;
  right: -80px;
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

.register-card {
  position: relative;
  z-index: 1;
  width: 440px;
  max-width: 100%;
  padding: 36px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 24px 64px rgba(8, 12, 40, 0.45);
}

.title {
  font-size: 22px;
  text-align: center;
  color: var(--text-main);
}

.subtitle {
  margin: 8px 0 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-sub);
}

.field-hint {
  margin: -12px 0 8px;
  font-size: 12px;
  color: var(--color-warning);
}

.inline-error {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--color-danger);
}

.optional-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 12px;
}

.register-btn {
  width: 100%;
  font-size: 16px;
  letter-spacing: 4px;
}

.register-links {
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
