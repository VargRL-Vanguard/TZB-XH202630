import { get, post } from './request'

/**
 * B 区学习记录 api（08 号契约 §2b + 17 号计划 §三实测差异，以实测为准）
 */

export type ActivityStatus = 'completed' | 'in-progress' | 'not-started'
export type ActivityFilter = 'all' | 'in-progress' | 'completed' | 'not-started'

/** 活动条目（courses/recent 共用 Activity.to_dict() 结构） */
export interface ActivityItem {
  activityId: string
  activityType: string
  resourceId: string
  resourceName: string
  status: ActivityStatus | string
  progress: number
  score: number | null
  startTime: string
  durationMinutes: number
  kpTags: string[]
}

/** GET /api/activity/stats — 汇总指标 */
export interface ActivityStats {
  totalActivities: number
  completedActivities: number
  completionRate: number
  avgProgress: number
  totalStudyMinutes: number
  avgScore: number
}

/** GET /api/activity/courses — 课程/活动列表 */
export interface ActivityCourses {
  total: number
  items: ActivityItem[]
}

/** GET /api/activity/recent — 最近活动 */
export interface ActivityRecent {
  count: number
  items: ActivityItem[]
}

/** GET /api/activity/calendar — 学习日历（今天=最后一项） */
export interface CalendarDay {
  date: string
  count: number
  minutes: number
}

export interface ActivityCalendar {
  days: number
  items: CalendarDay[]
}

export function getActivityStats(studentId: string) {
  return get<ActivityStats>('/api/activity/stats', { studentId })
}

export function getActivityCourses(studentId: string, filter: ActivityFilter = 'all') {
  return get<ActivityCourses>('/api/activity/courses', { studentId, filter })
}

export function getActivityRecent(studentId: string, days = 7, limit = 10) {
  return get<ActivityRecent>('/api/activity/recent', { studentId, days, limit })
}

export function getActivityCalendar(studentId: string, days = 28) {
  return get<ActivityCalendar>('/api/activity/calendar', { studentId, days })
}

/** POST /api/activity/record — 上报一条学习活动 */
export function recordActivity(payload: {
  studentId: string
  activityType: string
  resourceId: string
  resourceName: string
  status?: string
  progress?: number
  score?: number | null
  durationMinutes?: number
  kpTags?: string[]
}) {
  return post<{ activityId: string }>('/api/activity/record', payload)
}
