import axios, { AxiosError, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

/**
 * 统一请求封装（08 号契约 §0 错误处理矩阵的唯一实现点）
 * - 自动带 Authorization: Bearer <token>
 * - 统一解包 {code, message, data}，业务层只拿 data
 * - 401 → 清 token 跳登录（登录/注册接口白名单）
 * - 500 → 统一「服务异常，请稍后重试」，禁止透出后端原文
 * - 网络失败/超时 → 全局断网事件（NetBanner 监听）
 */

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 10_000
})

/** 401 跳转白名单：这些接口本身 401 不触发跳转 */
const AUTH_WHITELIST = ['/api/auth/login', '/api/auth/register']

/** 全局网络状态事件（NetBanner / 断网横幅监听） */
type NetListener = (offline: boolean) => void
const netListeners = new Set<NetListener>()
export function onNetStateChange(fn: NetListener) {
  netListeners.add(fn)
  return () => netListeners.delete(fn)
}
function emitNetState(offline: boolean) {
  netListeners.forEach((fn) => fn(offline))
}

export class BizError extends Error {
  code: number
  constructor(code: number, message: string) {
    super(message)
    this.code = code
  }
}

service.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

service.interceptors.response.use(
  (response) => {
    emitNetState(false)
    const body = response.data
    // 统一响应 {code, message, data}
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 200) {
        return body.data as unknown
      }
      // 业务错误：400/403/404 toast 后端 message 原文（后端已保证中文友好）
      if (body.code === 400 || body.code === 403 || body.code === 404) {
        ElMessage.error(body.message || '请求失败')
        return Promise.reject(new BizError(body.code, body.message))
      }
      if (body.code === 401) {
        handleUnauthorized(response.config.url)
        return Promise.reject(new BizError(401, '未登录或登录已过期'))
      }
      // 其他业务码按 500 处理
      ElMessage.error('服务异常，请稍后重试')
      return Promise.reject(new BizError(body.code, '服务异常，请稍后重试'))
    }
    // 非标准结构直接返回
    return body
  },
  (error: AxiosError<{ message?: string; code?: number }>) => {
    const status = error.response?.status
    const url = error.config?.url ?? ''

    if (status === 401) {
      // 登录/注册接口的 401 不跳转，把后端原文（如「用户名或密码错误」）带给页面内联展示
      if (url && AUTH_WHITELIST.some((w) => url.includes(w))) {
        const msg = error.response?.data?.message || '用户名或密码错误'
        return Promise.reject(new BizError(401, msg))
      }
      handleUnauthorized(url)
      return Promise.reject(new BizError(401, '未登录或登录已过期'))
    }
    if (status === 400 || status === 403 || status === 404) {
      const msg = error.response?.data?.message || '请求失败'
      ElMessage.error(msg)
      return Promise.reject(new BizError(status, msg))
    }
    if (status && status >= 500) {
      // 500 统一文案，禁止透出 detail/堆栈
      ElMessage.error('服务异常，请稍后重试')
      return Promise.reject(new BizError(status, '服务异常，请稍后重试'))
    }
    // 网络失败 / 超时 / 后端挂
    emitNetState(true)
    return Promise.reject(new BizError(-1, '网络异常，请检查网络连接'))
  }
)

let redirecting = false
function handleUnauthorized(url?: string) {
  if (url && AUTH_WHITELIST.some((w) => url.includes(w))) return
  const auth = useAuthStore()
  auth.logout()
  if (redirecting) return
  redirecting = true
  ElMessage.warning('登录已过期，请重新登录')
  // 为避免循环依赖，这里直接操作 hash（本项目为 hash 路由）
  window.location.hash = '#/login'
  setTimeout(() => {
    redirecting = false
  }, 1000)
}

/** 便捷方法（保留完整 data 泛型） */
export function get<T>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig) {
  return service.get(url, { params, ...config }) as Promise<T>
}
export function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
  return service.post(url, data, config) as Promise<T>
}
export function put<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
  return service.put(url, data, config) as Promise<T>
}
export function del<T>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig) {
  return service.delete(url, { params, ...config }) as Promise<T>
}

export default service
