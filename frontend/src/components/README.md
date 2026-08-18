# 组件库 v1（05 号文档规格 · F1 交付）

组件全部在 `src/components/`，**unplugin-vue-components 自动按需引入，模板里直接写标签即可，无需 import**。
色值一律用 `styles/index.css` 全局变量；数字用 `.num`（tabular-nums）。
演示页：`/#/demo`（逐态可看）。

---

## Skeleton 骨架屏

数据未到时必须有，不许白块（呼吸 1.5s 循环）。

```vue
<Skeleton :rows="3" variant="text" />   <!-- 文章段落 -->
<Skeleton variant="card" />             <!-- 卡片：头像+标题+正文+按钮 -->
<Skeleton variant="chart" />            <!-- 图表：标题+图区+图例 -->
```

| prop | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| rows | number | 3 | 行数（仅 text 形态） |
| variant | 'card' \| 'text' \| 'chart' | 'text' | 形态 |

---

## EmptyState 空态

```vue
<EmptyState icon="📚" text="还没有学习资源" action-text="去触发生成" @action="onGen" />
```

| prop | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| icon | string | '📭' | emoji 图标 |
| text | string | '暂无数据' | 引导文案 |
| actionText | string | ''（不显示按钮） | 行动按钮文案 |

事件：`@action` 按钮点击。

---

## ErrorState 错误态

绝不显示堆栈 / code 原文（组件不接受 detail 字段，从设计上杜绝）。

```vue
<ErrorState text="学习路径加载失败，请检查网络" @retry="reload" />
```

| prop | 类型 | 默认 |
| --- | --- | --- |
| text | string | '加载失败，请稍后重试' |
| retryText | string | '重试' |

事件：`@retry`。

---

## NetBanner 断网横幅（基建已交付）

由 `onNetStateChange` + `wsClient.onStatus` 驱动，页面无需传参，App.vue 已全局挂载。

---

## MetricCard 指标卡

字段对齐 08 契约 `GET /api/student/metrics`：`trend("up"/"down")`、`trendValue(number)`。

```vue
<MetricCard label="学习时长" :value="128" unit="小时" trend="up" :trend-value="12.5" />
<MetricCard label="幻觉率" :value="4.1" unit="%" :decimals="2" />
```

| prop | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| label | string | 必填 | 指标名 |
| value | number | 必填 | 数值（进视口 0→value 800ms ease-out 滚动） |
| unit | string | '' | 单位 |
| trend | 'up' \| 'down' \| null | null | 趋势（绿 ↑ / 红 ↓） |
| trendValue | number \| null | null | 变化量 |
| decimals | number | 0 | 小数位（4.10 传 2） |

插槽：`#foot` 底部补充行（如达标线）。

---

## DifficultyBadge 难度徽章

对接资源难度字段；`expected` 对接画像期望难度。

```vue
<DifficultyBadge :level="3" />
<DifficultyBadge :level="5" :expected="2" />  <!-- 显示「偏高 ↑」 -->
```

| prop | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| level | number | 必填 | 实际难度 1-5（绿→黄→红色阶） |
| expected | number \| null | null | 期望难度；传入显示 一致 ✅ / 偏高 ↑ / 偏低 ↓ |
| showLabel | boolean | true | 是否显示「难度」文字 |

---

## AgentCard 大屏 Agent 卡片

状态机对齐 `stores/agentEvents.ts` 的 `AgentCardState`，由 WS 事件驱动（start→running / thinking→running / result→done / debate→debating / final→finished）。

```vue
<AgentCard
  name="学情诊断Agent"
  theme-color="var(--color-agent-blue)"
  :icon="Search"
  :state="cardStates[name]"
>
  <TypewriterBubble :content="evt.content" />  <!-- D 区塞打字机内容 -->
</AgentCard>
```

| prop | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| name | string | 必填 | 与 WS `agentName` 一致 |
| themeColor | string | var(--color-primary) | 主题色（蓝/紫/金见 40 号 §4.2） |
| icon | Component \| null | null | 图标组件 |
| state | AgentCardState | 'idle' | idle/running/done/debating/finished |

插槽：默认 = 思考气泡区（**最多保留 50 条**，超出滚动销毁，防内存膨胀）。

---

## ConstructionPage 建设中占位（15 号 T2，组件库第七个）

```vue
<ConstructionPage title="学习资源" owner="C 组" eta="8-23" fallback-link="/chat" />
<ConstructionPage title="协同大屏" owner="D 组" eta="8-24" dark />
```

| prop | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| title | string | 必填 | 页面标题 |
| owner | string | 必填 | 负责组 |
| eta | string | 必填 | 预计交付 |
| fallbackLink | string | '' | 引导跳转（空则无按钮） |
| fallbackText | string | '先去消息页' | 按钮文案 |
| dark | boolean | false | 深色版（大屏） |
