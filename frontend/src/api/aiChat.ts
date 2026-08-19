import { get, post, del } from './request'

/**
 * D 区 AI 辅导对话 api（/api/ai-chat/*，本次后端新增路由，对齐 08 号契约 §4）
 */

export interface AiChatSendResult {
  reply: string
  conversationId: string
  usage?: Record<string, unknown>
  model?: string
}

export interface AiChatMessage {
  id: number
  role: 'user' | 'ai'
  content: string
  timestamp: string
}

export function sendAiChat(payload: {
  studentId: string
  message: string
  context?: Record<string, unknown>
}) {
  // AI 无 Key 时后端返回 503 业务码，request.ts 统一 toast；页面捕获 BizError 展示降级态
  return post<AiChatSendResult>('/api/ai-chat/send', payload)
}

export function getAiChatHistory(studentId: string, limit = 20) {
  return get<AiChatMessage[]>('/api/ai-chat/history', { studentId, limit })
}

export function clearAiChatHistory(studentId: string) {
  return del<{ success: boolean; deleted: number }>('/api/ai-chat/history', { studentId })
}
