/**
 * ECharts 按需注册（控制包体积，只注册项目用到的图表类型）
 * - Dashboard：雷达（六维）+ 折线（每日学习时长）
 * - Activity：柱状（活动类型分布）
 * - 暗色：图表色走 chartTextColor()/chartSplitColor()（随主题 store），
 *   主题切换时 useChart 自动 clear + 重调 render（canvas 不吃 CSS 变量，必须重绘）
 * 用法：import { useChart, CHART_COLORS, chartTextColor, chartSplitColor } from '@/utils/echarts'
 */
import { onBeforeUnmount, onMounted, shallowRef, watch, type Ref } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, RadarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import { useThemeStore } from '@/stores/theme'

echarts.use([
  LineChart,
  BarChart,
  RadarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer
])

export type { EChartsOption }

/** 图表用色（页面拼 option 时引用，避免散落硬编码） */
export const CHART_COLORS = {
  primary: '#4f6ef7',
  secondary: '#7c5cfc',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444'
}

/** 轴/图例文字色随主题 */
export function chartTextColor(): string {
  return useThemeStore().isDark ? '#9ca3af' : '#6b7280'
}

/** 轴分隔线色随主题 */
export function chartSplitColor(): string {
  return useThemeStore().isDark ? '#262b40' : '#eef0f4'
}

/**
 * 图表 composable：init + setOption + 尺寸自适应 + 主题切换重绘 + 卸载 dispose
 * @param elRef 图表容器 ref（须有确定高度）
 * @param render 页面渲染函数（内部调 setOption），主题切换时自动重调
 */
export function useChart(elRef: Ref<HTMLElement | null>, render?: () => void) {
  const chart = shallowRef<echarts.ECharts | null>(null)
  let observer: ResizeObserver | null = null

  onMounted(() => {
    if (!elRef.value) return
    chart.value = echarts.init(elRef.value)
    observer = new ResizeObserver(() => chart.value?.resize())
    observer.observe(elRef.value)
  })

  const theme = useThemeStore()
  watch(
    () => theme.isDark,
    () => {
      chart.value?.clear()
      render?.()
    }
  )

  onBeforeUnmount(() => {
    observer?.disconnect()
    chart.value?.dispose()
    chart.value = null
  })

  function setOption(option: EChartsOption) {
    chart.value?.setOption(option, { notMerge: false })
  }

  return { chart, setOption }
}
