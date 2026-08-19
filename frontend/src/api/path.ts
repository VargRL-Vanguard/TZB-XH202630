import { get, post } from './request'

/**
 * C 区学习路径 api（/api/learning-path/*）
 * 契约以后端实测为准（learning_path/service.py）：
 * - overview → {target, progress, estimatedDays, source}
 * - timeline → 扁平数组 {id, moduleId, title, desc, status, progress, duration, startDate, endDate}
 * - modules  → 扁平数组 {name, progress, desc}
 * - tasks    → 扁平数组 {id, taskId, title, meta, priority, completed(boolean)}
 * - feedback → 答题反馈（correct/kpId），非「太难/太简单」；触发降维/进阶动态迭代
 */

/** GET /overview — 路径总览 */
export interface PathOverview {
  target: string
  progress: number
  estimatedDays: number
  source: string
}

export type ModuleStatus = 'completed' | 'current' | 'pending'

/** GET /timeline — 阶段时间线（支持 status 过滤） */
export interface PathTimelineItem {
  id: number
  moduleId: string
  title: string
  desc: string
  status: ModuleStatus | string
  progress: number
  duration: string
  startDate: string
  endDate: string
}

/** GET /modules — 模块概要 */
export interface PathModule {
  name: string
  progress: number
  desc: string
}

/** GET /tasks — 任务清单（未完成优先，前 20 条） */
export interface PathTask {
  id: number
  taskId: string
  title: string
  meta: string
  priority: 'high' | 'medium' | 'low' | string
  completed: boolean
}

/** POST /feedback — 答题反馈（C-06 动态迭代入口） */
export interface PathFeedbackResult {
  logged: boolean
  accuracy: number
  samples: number
  action: 'downgrade' | 'upgrade' | 'none' | string
  triggerReason: 'low_accuracy' | 'high_accuracy' | 'stable' | 'insufficient_samples' | string
  resourceId?: string
}

export function getPathOverview(studentId: string) {
  return get<PathOverview>('/api/learning-path/overview', { studentId })
}

export function getPathTimeline(studentId: string, status?: 'completed' | 'current' | 'pending') {
  return get<PathTimelineItem[]>('/api/learning-path/timeline', { studentId, status })
}

export function getPathModules(studentId: string) {
  return get<PathModule[]>('/api/learning-path/modules', { studentId })
}

export function getPathTasks(studentId: string) {
  return get<PathTask[]>('/api/learning-path/tasks', { studentId })
}

/** 答题反馈：样本 ≥3 且正确率极端时自动触发降维解释 / 进阶挑战 */
export function sendPathFeedback(payload: {
  studentId: string
  kpId: string
  questionId?: string
  correct: boolean
  responseTime?: number
  difficulty?: number
  resourceId?: string
}) {
  return post<PathFeedbackResult>('/api/learning-path/feedback', payload)
}
