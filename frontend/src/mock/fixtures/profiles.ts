/**
 * 3 画像 fixtures —— 数据逐字段搬自 backend/b_学情数据/test_profiles/*.json（禁止手编数值）。
 * 用途：Students 学生列表页（后端无列表接口）+ 大屏 demo 选择画像。
 * 真接口就绪后：本文件保留作为回退数据源。
 */

export interface ProfileActivity {
  activityType: string
  resourceName: string
  status: string
  progress: number
  score: number | null
  kpTags: string[]
  startTime: string
  durationMinutes: number
}

export interface TestProfile {
  profile_id: string
  label: string
  learnerProfile: {
    education: string
    major: string
    theoryTestScore: number
    weakKPs: string[]
    strongKPs: string[]
  }
  activityHistory: ProfileActivity[]
  interactionGoal: string
}

export const TEST_PROFILES: TestProfile[] = [
  {
    profile_id: 'p-001',
    label: '本科应届生',
    learnerProfile: {
      education: '本科',
      major: '智能制造工程',
      theoryTestScore: 82,
      weakKPs: ['kp12d', 'kp22c'],
      strongKPs: ['kp01', 'kp02', 'kp03', 'kp15']
    },
    activityHistory: [
      {
        activityType: 'test',
        resourceName: '工业机器人坐标系单元测试',
        status: 'completed',
        progress: 100,
        score: 85,
        kpTags: ['kp02', 'kp12'],
        startTime: '2026-08-12T14:30:00',
        durationMinutes: 45
      },
      {
        activityType: 'course',
        resourceName: 'D-H参数法建模精讲',
        status: 'completed',
        progress: 100,
        score: 78,
        kpTags: ['kp12d', 'kp12c'],
        startTime: '2026-08-11T09:00:00',
        durationMinutes: 60
      },
      {
        activityType: 'exercise',
        resourceName: 'PLC梯形图编程练习',
        status: 'completed',
        progress: 100,
        score: 88,
        kpTags: ['kp22a', 'kp03'],
        startTime: '2026-08-10T16:20:00',
        durationMinutes: 50
      },
      {
        activityType: 'test',
        resourceName: '顺控程序SFC概念测验',
        status: 'completed',
        progress: 100,
        score: 68,
        kpTags: ['kp22c'],
        startTime: '2026-08-09T10:15:00',
        durationMinutes: 30
      },
      {
        activityType: 'course',
        resourceName: '工业机器人路径规划',
        status: 'completed',
        progress: 100,
        score: 90,
        kpTags: ['kp15'],
        startTime: '2026-08-08T13:00:00',
        durationMinutes: 55
      },
      {
        activityType: 'exercise',
        resourceName: '传感器选型综合实训',
        status: 'completed',
        progress: 100,
        score: 86,
        kpTags: ['kp04', 'kp04a'],
        startTime: '2026-08-06T15:00:00',
        durationMinutes: 70
      },
      {
        activityType: 'test',
        resourceName: '工业机器人基础理论测验',
        status: 'completed',
        progress: 100,
        score: 92,
        kpTags: ['kp01', 'kp01d'],
        startTime: '2026-08-05T09:30:00',
        durationMinutes: 40
      },
      {
        activityType: 'course',
        resourceName: '坐标系变换与齐次矩阵',
        status: 'completed',
        progress: 100,
        score: 80,
        kpTags: ['kp12', 'kp02'],
        startTime: '2026-08-03T14:00:00',
        durationMinutes: 65
      },
      {
        activityType: 'discussion',
        resourceName: '离线编程与路径优化讨论',
        status: 'completed',
        progress: 100,
        score: null,
        kpTags: ['kp15', 'kp18'],
        startTime: '2026-08-01T19:00:00',
        durationMinutes: 35
      },
      {
        activityType: 'exercise',
        resourceName: 'PLC程序调试与故障诊断',
        status: 'in-progress',
        progress: 60,
        score: null,
        kpTags: ['kp22d'],
        startTime: '2026-07-30T16:30:00',
        durationMinutes: 40
      }
    ],
    interactionGoal: '希望深入学习工业机器人离线编程与路径规划，准备智能制造工程师认证'
  },
  {
    profile_id: 'p-002',
    label: '高职在读生',
    learnerProfile: {
      education: '高职',
      major: '工业机器人技术',
      theoryTestScore: 58,
      weakKPs: ['kp12', 'kp12c', 'kp22', 'kp22a', 'kp04c', 'kp05b'],
      strongKPs: ['kp01']
    },
    activityHistory: [
      {
        activityType: 'test',
        resourceName: '坐标系变换单元测验',
        status: 'completed',
        progress: 100,
        score: 48,
        kpTags: ['kp12'],
        startTime: '2026-08-12T10:00:00',
        durationMinutes: 35
      },
      {
        activityType: 'exercise',
        resourceName: '逆运动学基础练习',
        status: 'completed',
        progress: 100,
        score: 52,
        kpTags: ['kp12c'],
        startTime: '2026-08-11T14:30:00',
        durationMinutes: 40
      },
      {
        activityType: 'course',
        resourceName: '工业机器人入门基础',
        status: 'completed',
        progress: 100,
        score: 70,
        kpTags: ['kp01'],
        startTime: '2026-08-10T09:00:00',
        durationMinutes: 45
      },
      {
        activityType: 'test',
        resourceName: '模拟量信号处理小测',
        status: 'completed',
        progress: 100,
        score: 45,
        kpTags: ['kp22'],
        startTime: '2026-08-09T15:00:00',
        durationMinutes: 30
      },
      {
        activityType: 'exercise',
        resourceName: '梯形图编程入门练习',
        status: 'completed',
        progress: 100,
        score: 58,
        kpTags: ['kp22a'],
        startTime: '2026-08-08T13:30:00',
        durationMinutes: 50
      },
      {
        activityType: 'course',
        resourceName: '编码器原理与应用',
        status: 'in-progress',
        progress: 65,
        score: null,
        kpTags: ['kp04c'],
        startTime: '2026-08-07T10:30:00',
        durationMinutes: 35
      },
      {
        activityType: 'test',
        resourceName: '工业以太网协议测验',
        status: 'completed',
        progress: 100,
        score: 50,
        kpTags: ['kp05b'],
        startTime: '2026-08-05T14:00:00',
        durationMinutes: 25
      },
      {
        activityType: 'exercise',
        resourceName: 'PLC数字量IO接线实训',
        status: 'completed',
        progress: 100,
        score: 62,
        kpTags: ['kp03b'],
        startTime: '2026-08-03T16:00:00',
        durationMinutes: 60
      },
      {
        activityType: 'course',
        resourceName: 'PLC工作原理基础',
        status: 'completed',
        progress: 100,
        score: 55,
        kpTags: ['kp03'],
        startTime: '2026-08-01T09:30:00',
        durationMinutes: 40
      },
      {
        activityType: 'discussion',
        resourceName: '传感器分类学习讨论',
        status: 'in-progress',
        progress: 40,
        score: null,
        kpTags: ['kp04'],
        startTime: '2026-07-30T18:00:00',
        durationMinutes: 30
      }
    ],
    interactionGoal: '需要从基础补起，希望获得适合高职层次的入门学习资源'
  },
  {
    profile_id: 'p-003',
    label: '企业转岗人员',
    learnerProfile: {
      education: '本科',
      major: '机械设计制造及其自动化',
      theoryTestScore: 55,
      weakKPs: ['kp03', 'kp22', 'kp22b', 'kp05', 'kp05a', 'kp12c'],
      strongKPs: ['kp01d', 'kp04', 'kp06b']
    },
    activityHistory: [
      {
        activityType: 'exercise',
        resourceName: '气动执行元件调试实操',
        status: 'completed',
        progress: 100,
        score: 88,
        kpTags: ['kp06b'],
        startTime: '2026-08-12T09:00:00',
        durationMinutes: 80
      },
      {
        activityType: 'exercise',
        resourceName: '传感器选型与接线实操',
        status: 'completed',
        progress: 100,
        score: 85,
        kpTags: ['kp04', 'kp04a'],
        startTime: '2026-08-11T14:00:00',
        durationMinutes: 65
      },
      {
        activityType: 'test',
        resourceName: 'PLC工作原理理论测验',
        status: 'completed',
        progress: 100,
        score: 48,
        kpTags: ['kp03'],
        startTime: '2026-08-10T10:30:00',
        durationMinutes: 35
      },
      {
        activityType: 'exercise',
        resourceName: '机器人本体结构拆装实操',
        status: 'completed',
        progress: 100,
        score: 90,
        kpTags: ['kp01d'],
        startTime: '2026-08-09T13:30:00',
        durationMinutes: 90
      },
      {
        activityType: 'test',
        resourceName: '模拟量信号处理理论测验',
        status: 'completed',
        progress: 100,
        score: 42,
        kpTags: ['kp22'],
        startTime: '2026-08-08T15:00:00',
        durationMinutes: 30
      },
      {
        activityType: 'course',
        resourceName: 'STL/ST文本编程入门',
        status: 'in-progress',
        progress: 55,
        score: null,
        kpTags: ['kp22b'],
        startTime: '2026-08-07T09:30:00',
        durationMinutes: 45
      },
      {
        activityType: 'test',
        resourceName: '工业通信网络分层测验',
        status: 'completed',
        progress: 100,
        score: 50,
        kpTags: ['kp05'],
        startTime: '2026-08-05T14:30:00',
        durationMinutes: 25
      },
      {
        activityType: 'exercise',
        resourceName: 'Modbus协议调试实操',
        status: 'completed',
        progress: 100,
        score: 75,
        kpTags: ['kp05a'],
        startTime: '2026-08-04T16:00:00',
        durationMinutes: 70
      },
      {
        activityType: 'course',
        resourceName: '逆运动学概念复习',
        status: 'completed',
        progress: 100,
        score: 55,
        kpTags: ['kp12c'],
        startTime: '2026-08-02T10:00:00',
        durationMinutes: 50
      },
      {
        activityType: 'exercise',
        resourceName: '产线协同控制综合实训',
        status: 'completed',
        progress: 100,
        score: 82,
        kpTags: ['kp06a', 'kp06b'],
        startTime: '2026-07-31T13:00:00',
        durationMinutes: 95
      }
    ],
    interactionGoal:
      '有机械行业实战经验，需要补齐PLC编程和工业通信理论，目标是转型智能制造系统集成岗位'
  }
]

export function getProfileById(profileId: string): TestProfile | undefined {
  return TEST_PROFILES.find((p) => p.profile_id === profileId)
}
