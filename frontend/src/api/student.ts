import { get } from './request'

/**
 * B 区学情数据 api（08 号契约 §2 + 17 号计划 §三实测差异，以实测为准）
 * 鉴权：student 仅本人，teacher/admin 任意（后端校验，403 走统一 toast）
 */

/** GET /api/student/info — 基本信息 + 画像 + 指标聚合 */
export interface LearnerProfile {
  education: string
  major: string
  theoryTestScore: number | null
  weakKPs: string[]
  strongKPs: string[]
}

export interface StudentMetrics {
  studyHours: number
  completionRate: number
  avgScore: number
  trend: 'up' | 'down'
  trendValue: number
}

export interface StudentInfo {
  studentId: string
  name: string
  learnerProfile: LearnerProfile
  metrics: StudentMetrics
}

/** GET /api/student/dimensions — 六维（0-100 dict，非数组，17 号 §三实测） */
export interface StudentDimensions {
  comprehension: number
  application: number
  analysis: number
  evaluation: number
  creation: number
  collaboration: number
}

/** GET /api/student/behavior — 学习行为统计 */
export interface BehaviorDay {
  date: string
  minutes: number
  count: number
}

export interface StudentBehavior {
  period: string
  startDate: string
  endDate: string
  totalStudyMinutes: number
  activityCount: number
  completedCount: number
  avgScore: number
  activityTypeBreakdown: Record<string, number>
  dailySeries: BehaviorDay[]
  _isMock?: boolean
}

/** GET /api/student/knowledge — 知识点掌握列表 */
export type KpStatus = 'mastered' | 'learning' | 'not-started'

export interface KnowledgePoint {
  kp_id: string
  kp_name: string
  mastery: number
  status: KpStatus
}

export function getStudentInfo(studentId: string) {
  return get<StudentInfo>('/api/student/info', { studentId })
}

export function getStudentMetrics(studentId: string) {
  return get<StudentMetrics>('/api/student/metrics', { studentId })
}

export function getStudentDimensions(studentId: string) {
  return get<StudentDimensions>('/api/student/dimensions', { studentId })
}

export function getStudentBehavior(
  studentId: string,
  period: 'week' | 'month' | 'semester' = 'week'
) {
  return get<StudentBehavior>('/api/student/behavior', { studentId, period })
}

export function getStudentKnowledge(studentId: string) {
  return get<KnowledgePoint[]>('/api/student/knowledge', { studentId })
}
