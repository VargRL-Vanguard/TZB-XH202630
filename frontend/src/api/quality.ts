import { get } from './request'

/**
 * 质量报告 api（/api/quality/latest，读 docs/quality_reports/latest.json）
 * 3 项硬指标：幻觉率 <5% / 匹配准确率 ≥85% / 知识点覆盖率 ≥90%
 */

export interface QualityThresholds {
  hallucination_max: number
  match_accuracy_min: number
  coverage_min: number
}

export interface QualityMetrics {
  hallucination_rate: number
  match_accuracy: number
  hallucination_pass: boolean
  match_accuracy_pass: boolean
  soft_metrics_pass: boolean
  profile_count: number
  coverage: number
  coverage_pass: boolean
  passed: boolean
}

export interface QualityDetail {
  profile_id: string
  label: string
  source_file: string
  elapsed_sec: number
  trace_id: string
  weak_kps: string[]
  strong_kps: string[]
  confidence: number
  expected_difficulty: number
  resource_difficulty: number
  resource_id: string
  cited_chunks: number
  hallucination_rate: number
  match_accuracy: number
  resource_vs_weak_coverage: number
  audit_verdict: string
  audit_score: number
}

export interface QualityReport {
  generated_at: string
  mode: string
  kb_chunk_count: number
  kb_covered_kp_count: number
  thresholds: QualityThresholds
  metrics: QualityMetrics
  details: QualityDetail[]
  passed: boolean
  warnings: string[]
}

export function getQualityLatest() {
  return get<QualityReport>('/api/quality/latest')
}
