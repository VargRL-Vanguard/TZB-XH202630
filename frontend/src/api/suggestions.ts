import { get, post } from './request'

/**
 * C 区学习建议 api（/api/suggestions/*）
 * 契约以后端实测为准（suggestions/service.py）：
 * - list → 扁平数组 {id, title, content, category, categoryLabel, priority, priorityLabel, source, isRead(boolean), createdAt}
 * - read → body {studentId, suggestionId}（缺 studentId 会 422，注意必传）
 */

export type SuggestionCategory = 'all' | 'method' | 'resource' | 'review' | 'practice'
export type SuggestionPriority = 'high' | 'medium' | 'low'

export interface Suggestion {
  id: string
  title: string
  content: string
  category: SuggestionCategory | string
  categoryLabel: string
  priority: SuggestionPriority | string
  priorityLabel: string
  source: string
  isRead: boolean
  createdAt: string
}

export function getSuggestions(studentId: string, category: SuggestionCategory = 'all') {
  return get<Suggestion[]>('/api/suggestions/list', { studentId, category })
}

/** POST /read — 标记已读（studentId 必传，student 仅能标记自己） */
export function markSuggestionRead(studentId: string, suggestionId: string) {
  return post<{ success: boolean }>('/api/suggestions/read', { studentId, suggestionId })
}
