/**
 * 资源 3 形态 fixtures —— 数据逐字段搬自 backend/c_学习内容/sample_resources/*.json（禁止手编数值）。
 * 用途：Resources 资源页（后端列表接口等 C 组 8-26，先用 fixtures 搭页面）。
 * 切换真数据时：改 src/views/Resources.vue 的 load() 指向真接口即可（结构已分层）。
 */

/** 形态一：定制化资源（按知识点分节 + 引用切片） */
export interface CustomizedSection {
  kp_id: string
  heading: string
  body: string
}

export interface CustomizedResourceContent {
  title: string
  sections: CustomizedSection[]
}

/** 形态二：实践指南（分步 + 工具 + 排错） */
export interface GuideStep {
  order: number
  title: string
  content: string
  estimated_min: number
}

export interface GuideTroubleshooting {
  problem: string
  solution: string
}

export interface PracticeGuideContent {
  title: string
  steps: GuideStep[]
  tools: string[]
  troubleshooting: GuideTroubleshooting[]
}

/** 形态三：分层测验（题目 + 选项 + 解析 + 难度分层） */
export interface QuizQuestion {
  question: string
  options: string[]
  answer: string
  explanation: string
  difficulty: number
  kp_id: string
}

export interface TieredQuizContent {
  title: string
  questions: QuizQuestion[]
}

export interface ResourceMetrics {
  coverage: number
  hallucination: number
  matchAccuracy: number
}

export interface ResourceBase {
  resource_id: string
  student_id: string
  type: 'customized_resource' | 'practice_guide' | 'tiered_quiz' | string
  title: string
  content: CustomizedResourceContent | PracticeGuideContent | TieredQuizContent
  kp_coverage: string[]
  cited_chunks: string[]
  difficulty: number
  trigger_reason: string
  source_trace_id: string
  metrics: ResourceMetrics
  generated_at: string
}

export const SAMPLE_RESOURCES: ResourceBase[] = [
  {
    resource_id: 'res-69fccebff0d14dda',
    student_id: 'demo-mid-002',
    type: 'customized_resource',
    title: 'kp_function_design kp_oop_basics 核心概念',
    content: {
      title: 'kp_function_design kp_oop_basics 核心概念',
      sections: [
        {
          kp_id: 'kp_function_design',
          heading: 'kp_function_design',
          body: '[mock-chunk] 关于知识点 kp_function_design 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。'
        },
        {
          kp_id: 'kp_oop_basics',
          heading: 'kp_oop_basics',
          body: '[mock-chunk] 关于知识点 kp_oop_basics 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。'
        }
      ]
    },
    kp_coverage: ['kp_function_design', 'kp_oop_basics'],
    cited_chunks: [
      'mock-kp_function_design-0',
      'mock-kp_function_design-1',
      'mock-kp_function_design-2',
      'mock-kp_oop_basics-0',
      'mock-kp_oop_basics-1',
      'mock-kp_oop_basics-2'
    ],
    difficulty: 3,
    trigger_reason: 'demo_sample',
    source_trace_id: 'trace-24134dc73089',
    metrics: { coverage: 1.0, hallucination: 0.0, matchAccuracy: 1.0 },
    generated_at: '2026-08-13T17:21:17.566423+00:00'
  },
  {
    resource_id: 'res-b5e3d21a81e746d0',
    student_id: 'demo-mid-002',
    type: 'practice_guide',
    title: 'kp_function_design 核心概念',
    content: {
      title: 'kp_function_design 核心概念',
      steps: [
        {
          order: 1,
          title: '前置',
          content:
            '[mock-chunk] 关于知识点 kp_function_design 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。',
          estimated_min: 5
        },
        {
          order: 2,
          title: '操作',
          content:
            '[mock-chunk] 关于知识点 kp_function_design 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。',
          estimated_min: 20
        },
        {
          order: 3,
          title: '易错点',
          content:
            '[mock-chunk] 关于知识点 kp_function_design 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。',
          estimated_min: 5
        }
      ],
      tools: ['kp_function_design 基础语法'],
      troubleshooting: [
        {
          problem:
            '[mock-chunk] 关于知识点 kp_function_design 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。',
          solution:
            '[mock-chunk] 关于知识点 kp_function_design 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。'
        }
      ]
    },
    kp_coverage: ['kp_function_design', 'kp_oop_basics'],
    cited_chunks: [
      'mock-kp_function_design-0',
      'mock-kp_function_design-1',
      'mock-kp_function_design-2',
      'mock-kp_oop_basics-0',
      'mock-kp_oop_basics-1',
      'mock-kp_oop_basics-2'
    ],
    difficulty: 3,
    trigger_reason: 'demo_sample',
    source_trace_id: 'trace-8a9649ae10dc',
    metrics: { coverage: 1.0, hallucination: 0.0, matchAccuracy: 1.0 },
    generated_at: '2026-08-13T17:21:17.595246+00:00'
  },
  {
    resource_id: 'res-f5df32f433c147fc',
    student_id: 'demo-mid-002',
    type: 'tiered_quiz',
    title: 'kp_function_design kp_oop_basics 核心概念',
    content: {
      title: 'kp_function_design kp_oop_basics 核心概念',
      questions: [
        {
          question: 'kp_oop_basics',
          options: ['基础语法', '边界条件', '异常分支', '按步骤执行'],
          answer: 'A',
          explanation:
            '[mock-chunk] 关于知识点 kp_oop_basics 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。',
          difficulty: 2,
          kp_id: 'kp_oop_basics'
        },
        {
          question: 'kp_function_design',
          options: ['基础语法', '边界条件', '异常分支', '按步骤执行'],
          answer: 'A',
          explanation:
            '[mock-chunk] 关于知识点 kp_function_design 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。',
          difficulty: 3,
          kp_id: 'kp_function_design'
        },
        {
          question: 'kp_oop_basics',
          options: ['基础语法', '边界条件', '异常分支', '按步骤执行'],
          answer: 'A',
          explanation:
            '[mock-chunk] 关于知识点 kp_oop_basics 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。',
          difficulty: 4,
          kp_id: 'kp_oop_basics'
        },
        {
          question: 'kp_function_design',
          options: ['基础语法', '边界条件', '异常分支', '按步骤执行'],
          answer: 'A',
          explanation:
            '[mock-chunk] 关于知识点 kp_function_design 的核心概念：用于演示。\n前置：掌握基础语法。\n操作：按步骤执行，注意边界条件。\n易错点：忽略异常分支。',
          difficulty: 5,
          kp_id: 'kp_function_design'
        }
      ]
    },
    kp_coverage: ['kp_function_design', 'kp_oop_basics'],
    cited_chunks: [
      'mock-kp_function_design-0',
      'mock-kp_function_design-1',
      'mock-kp_function_design-2',
      'mock-kp_oop_basics-0',
      'mock-kp_oop_basics-1',
      'mock-kp_oop_basics-2'
    ],
    difficulty: 3,
    trigger_reason: 'demo_sample',
    source_trace_id: 'trace-536ef96845c1',
    metrics: { coverage: 1.0, hallucination: 0.0, matchAccuracy: 1.0 },
    generated_at: '2026-08-13T17:21:17.624600+00:00'
  }
]

export const RESOURCE_TYPE_LABELS: Record<string, string> = {
  customized_resource: '定制化资源',
  practice_guide: '实践指南',
  tiered_quiz: '分层测验'
}

/** 「太难了」反馈后的本地降级：难度 -1（最低 1），真接口接通后由后端重生成替换 */
export function deriveEasierVersion(res: ResourceBase): ResourceBase {
  return {
    ...res,
    difficulty: Math.max(1, res.difficulty - 1),
    trigger_reason: 'feedback_too_hard',
    resource_id: `${res.resource_id}-v${Math.max(1, res.difficulty - 1)}`
  }
}
