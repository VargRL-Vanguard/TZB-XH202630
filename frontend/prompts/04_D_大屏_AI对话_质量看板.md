# 04 成员 D：⭐ Agent 协同大屏 + AI 对话 + 质量看板

> 负责人：成员 D　|　死线：**大屏骨架 8-22**、**AI 对话 + 质量看板 8-24**、**大屏完整（含回放器）8-27**
> 你负责的是**全项目最重要页面**——评审看不懂"多智能体协同"，大屏动画就是他们唯一能看见的证据。5 类事件缺一个，用户体验分砍半。值得投 50% 前端工时。

## 复制即用 · 开工提示词

把下面整段复制给你的 AI：

```text
你是本项目的前端工程师，负责多 Agent 协同可视化大屏（全项目最高优先级）、AI 对话页、质量指标看板。项目：挑战杯 XH-202630，前端 frontend/（Vue3+Vite+TS+Element Plus+ECharts），基建与 agentEvents store 由 A 提供，三画像 fixtures 由 B 提供。

请先按顺序完整阅读以下文件（项目根 d:\TZB\TZB-XH202630）：
1. frontend/prompts/00_开工前必读.md（技术栈与纪律）
2. backend/prompts/40_前端开发_提示词.md（最高规范，重点 §4.2 Agent 配色、§5-P0-2/P0-5、§6 WS 协议逐字段、§7 动画、§11 视频画面对齐）
3. frontend/prompts/04_D_大屏_AI对话_质量看板.md（本文档，你的任务清单）
4. backend/a_用户与聊天/ws/events.py（5 类 Agent 事件的字段定义，逐字段照此写）
5. api-doc.js §6（/api/ai-chat/* 契约）
6. docs/quality_reports/ 下最新一份报告（质量看板数据口径：幻觉率 4.10% / 适配 100% / 覆盖 100%）
7. backend/d_AI集成/概览.md 与 orchestrator/event_emitter.py（事件如何产生，便于造逼真的 mock trace）
8. frontend/prompts/08_接口契约速查表_字段级.md（⭐字段级契约+每页 DoD：WS 5 类事件逐字段见 §5、/api/ai-chat/* 见 §4、质量看板数据源见 §6，验收按 §8 AgentScreen/AiChat/Quality DoD）

读完后先回答 00 文档 §7 的 6 道自查题 + 逐字复述 5 类 WS 事件的字段和对应 UI 行为（以 08 号文档 §5 为准），确认无误后按本文档「任务清单」顺序开工。

全程遵守：
- 事件字段以 ws/events.py 为准；/api/visualization、/api/trace 契约发布后第一时间对齐；冲突立即停下提醒我群里 @ 后端负责人（归你），不许猜
- 大屏回放器读 agentEvents store，不重放网络
- AI 生成内容渲染必须 sanitize（DOMPurify），禁 v-html 直插
- 完成每个任务节点后，主动提醒我完成本文档末尾「手操清单」对应事项，给出具体步骤后再继续
```

## 任务清单

### 阶段一：大屏骨架（8-22，mock trace 驱动）

- [ ] `views/AgentScreen.vue` 深色科技风：背景 `#0B1020`，主视觉 `#4F6EF7 → #7C5CFC` 渐变
- [ ] 3 张 AgentCard 横排流水线 + 箭头连线：学情诊断 Agent（蓝 `#38BDF8` 放大镜/仪表盘图标）→ 领域专家 Agent（紫 `#A78BFA` 书本/火花）→ 审核裁判 Agent（金 `#FBBF24` 天平/盾牌）；连线粒子流动画（20-40 粒子，方向 A→B/B→A 交替）
- [ ] 顶部 traceId + 步骤进度条（1/4 → 4/4）
- [ ] mock 一条完整 trace 事件序列（start → thinking×N → result → debate → final，间隔 0.5-1.5s）写入 fixtures 驱动开发

### 阶段二：5 类 WS 事件全量实现（8-27，夺奖红线）

- [ ] `agent.start {agentName, step, traceId, timestamp}` → 对应卡片转「工作中」（转圈/呼吸灯），进度条跳 step
- [ ] `agent.thinking {agentName, step, content, traceId, timestamp}` → **打字机流式追加**（30-50ms/字）到该卡片思考气泡区，逐条追加不是一次性替换
- [ ] `agent.result {..., data}` → 卡片「完成 ✅」，data 暂存待 final
- [ ] `agent.debate {agents[], topic, content, ...}` → 参与卡片间 ⚡ 连线，topic 居中，观点气泡左右对撞交替
- [ ] `agent.final {ok, summary, ...}` → 关全部 loading；ok=true 弹最终资源结果卡，ok=false 错误 + 重试按钮
- [ ] 状态机：idle → running → done → debating → finished；乱序事件容错不白屏；思考/辩论气泡**最多保留 50 条**
- [ ] 事件时间轴侧栏：本次 trace 全事件按时间排列，点击可回看
- [ ] **回放模式**：按钮触发，把 store 内事件序列按原始间隔重放（视频补拍 + 现场二次展示唯一手段）
- [ ] 动画期间帧率 ≥ 50fps；`prefers-reduced-motion` 降级

### 阶段三：AI 对话页（8-24）

- [ ] `views/AiChat.vue` + `src/api/aiChat.ts`：`POST /api/ai-chat/send`、`GET /api/ai-chat/history`、DELETE 清空
- [ ] AI 回复**必须走后端**（对接 D 区 pipeline）；回复渲染 sanitize；流式/打字指示器可复用大屏组件
- [ ] **彻底删除旧版关键词匹配假回复的思路**——那是上一版的穿帮点

### 阶段四：质量指标看板（P0-5，8-24）

- [ ] `views/QualityBoard.vue` 3 张大指标卡：幻觉率 **4.10%**（<5% ✅）/ 适配准确率 **100%**（≥85% ✅）/ 覆盖率 **100%**（≥90% ✅）
- [ ] 数据源 `docs/quality_reports/latest.json`（A-05 每日更新）；达标绿 ✅ / 不达标红 ❌，**页面是活的不是贴图**
- [ ] 附 3 组画像明细表：推荐难度 vs 期望、每组幻觉率、覆盖弱项、审核结论 + 生成时间

## 验收标准

- 5/5 类事件逐一在真实 WS 下触发验证；断网重连横幅出现/消失
- 回放按钮完整重演一次 trace（含 debate 分支）
- 大屏任意时刻截图可当 PPT 素材；连跑 10 次回放内存无持续增长
- 质量看板数值与 latest.json 完全一致

## ⚠️ 手操清单（AI 会提醒你，但必须你亲手做）

| 时机 | 手操内容 |
| --- | --- |
| 大屏每类事件完成 | 真实后端起服务，触发一次生成流程，浏览器录 GIF（打字机特写 + 辩论特写 + final 弹卡）发群 |
| 回放器完成 | 连放 10 次回放，开任务管理器对比内存；录回放 GIF |
| AI 对话联调 | 启动后端 + D 区 pipeline，真实问 3 个问题验证走的是后端 AI 而非前端假回复 |
| 质量看板 | 数值与 docs/quality_reports/ 最新报告肉眼逐项核对一致 |
| 性能自查 | Chrome DevTools Performance 面板跑动画录帧率 ≥ 50fps |
| 每个阶段完成 | git 分支 `feat/fe-agent-screen` 等 → commit → push → PR 带 GIF |
| 每日 18:00 | 群推进度：完成项 + GIF/截图 + 明日计划 + 阻塞 |
