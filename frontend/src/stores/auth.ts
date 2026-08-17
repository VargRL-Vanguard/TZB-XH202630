import { defineStore } from 'pinia'

/**
 * 认证 store：token / userId / role
 * token 只存内存 + sessionStorage，统一封装，禁止页面裸操作 storage
 */
const STORAGE_KEY = 'xh_auth'

interface AuthState {
  token: string
  userId: string
  role: string
}

function loadFromSession(): AuthState {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as AuthState
      if (parsed.token) return parsed
    }
  } catch {
    /* 解析失败视为未登录 */
  }
  return { token: '', userId: '', role: '' }
}

function saveToSession(state: AuthState) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function clearSession() {
  sessionStorage.removeItem(STORAGE_KEY)
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => loadFromSession(),
  getters: {
    isLoggedIn: (s) => !!s.token
  },
  actions: {
    setAuth(payload: { token: string; userId: string; role: string }) {
      this.token = payload.token
      this.userId = payload.userId
      this.role = payload.role
      saveToSession({ token: this.token, userId: this.userId, role: this.role })
    },
    logout() {
      this.token = ''
      this.userId = ''
      this.role = ''
      clearSession()
    }
  }
})
