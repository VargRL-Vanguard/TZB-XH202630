import { get, post, put } from './request'

/** ============ A 区：鉴权（契约 08 号 §1） ============ */

export interface LoginResp {
  token: string
  userId: string
  role: string
}

export function login(payload: { username: string; password: string }) {
  return post<LoginResp>('/api/auth/login', payload)
}

export function register(payload: {
  username: string
  password: string
  name: string
  role: string
  education?: string
  major?: string
}) {
  return post<{ userId: string }>('/api/auth/register', payload)
}

export function logout() {
  return post<{ ok: boolean }>('/api/auth/logout')
}

/** ============ A 区：用户 ============ */

export interface UserInfo {
  userId: string
  username: string
  name: string
  role: string
  education: string | null
  major: string | null
  theoryTestScore: number | null
  weakKPs: string[] | null
  strongKPs: string[] | null
  profileUpdatedAt: string | null
}

/** ⚠️ 必带 userId query */
export function getUserInfo(userId: string) {
  return get<UserInfo>('/api/user/info', { userId })
}

export function updateProfile(payload: {
  education?: string
  major?: string
  theoryTestScore?: number
  weakKPs?: string[]
  strongKPs?: string[]
}) {
  return put<UserInfo>('/api/user/profile', payload)
}
