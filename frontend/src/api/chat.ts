import { get, post } from './request'

/** ============ A 区：聊天（契约 08 号 §1.6-1.9，字段一字不差） ============ */

export interface ChatMessage {
  id: number
  userId: string
  targetId: string
  content: string
  type: 'text' | 'image' | 'file'
  timestamp: string
  status: 'sent' | 'read'
}

export interface ChatHistoryResp {
  list: ChatMessage[]
  total: number
  hasMore: boolean
}

export interface Conversation {
  targetId: string
  name: string
  lastMessage: string
  lastTime: string
  unread: number
}

/** POST /api/chat/send */
export function sendMessage(payload: {
  userId: string
  targetId: string
  content: string
  type?: 'text' | 'image' | 'file'
}) {
  return post<Pick<ChatMessage, 'id' | 'timestamp' | 'status'>>('/api/chat/send', {
    type: 'text',
    ...payload
  })
}

/** GET /api/chat/history?userId=&targetId=&limit=&offset= */
export function getHistory(params: {
  userId: string
  targetId: string
  limit?: number
  offset?: number
}) {
  return get<ChatHistoryResp>('/api/chat/history', params)
}

/** GET /api/chat/list?userId= — 后端 userId 为必填 Query（缺参 422） */
export function getConversationList(userId: string) {
  return get<Conversation[]>('/api/chat/list', { userId })
}

/** POST /api/chat/read */
export function markRead(payload: { userId: string; targetId: string }) {
  return post<{ success: boolean; markedCount: number }>('/api/chat/read', payload)
}
