# 02 成员 B：学情仪表盘 + 学习活动 + 三画像 mock

> 负责人：成员 B　|　死线：**三画像 mock fixtures 8-19**（C/D 等着用）、**仪表盘 mock 版 8-22**、**真数据切换 8-25**、**活动页 8-25**
> 你交付的 fixtures 是全队 mock 纪律的基石，最先到期。

## 复制即用 · 开工提示词

把下面整段复制给你的 AI：

```text
你是本项目的前端工程师，负责学情画像仪表盘与学习活动页。项目：挑战杯 XH-202630，前端 frontend/（Vue3+Vite+TS+Element Plus+ECharts 按需引入），基建由 A 提供（request 封装/路由/store）。

请先按顺序完整阅读以下文件（项目根 d:\TZB\TZB-XH202630）：
1. frontend/prompts/00_开工前必读.md（技术栈与纪律）
2. backend/prompts/40_前端开发_提示词.md（最高规范，重点 §4 视觉、§5-P0-3、§7 动画、§8 四态、§10 mock 规范）
3. frontend/prompts/02_B_仪表盘_活动_画像mock.md（本文档，你的任务清单）
4. api-doc.js §2（/api/student/* 契约，一字不差）
5. backend/b_学情数据/test_profiles/profile_01_本科应届生.json、profile_02_高职在读生.json、profile_03_企业转岗人员.json（mock 数据唯一来源，禁止自己编）
6. backend/b_学情数据/概览.md（你自己的后端，回顾字段含义）
7. frontend/prompts/08_接口契约速查表_字段级.md（⭐字段级契约+每页 DoD：/api/student/* 与 /api/activity/* 逐字段照 §2/§2b 核对，三画像数值口径在 §2，验收按 §8 Dashboard/Activity DoD）

读完后先回答 00 文档 §7 的 6 道自查题，确认无误后按本文档「任务清单」顺序开工。

全程遵守：
- mock 数据必须来自上述 3 个画像 JSON，字段名与 api-doc.js 一字不差；契约冲突立即停下提醒我群里 @ 后端负责人（/api/student|activity 归你），不许猜字段
- 图表全部 ECharts 按需引入；数字用 tabular-nums
- 完成每个任务节点后，主动提醒我完成本文档末尾「手操清单」对应事项，给出具体步骤后再继续
```

## 任务清单

### 阶段一：三画像 mock fixtures（8-19，最先到期）

- [ ] `src/mock/fixtures/profiles.ts`：从 3 个画像 JSON 转出前端 fixtures，覆盖 p-001（本科应届生/高分/期望难度5/弱项kp12,kp15/雷达偏满）、p-002（高职在读/低分/期望2/雷达偏低→触发降维解释演示）、p-003（企业转岗/低分/期望2/实操导向→触发 practice_guide 形态）
- [ ] `src/api/student.ts`：`VITE_USE_MOCK=true` 走 fixtures，false 走 `VITE_API_BASE`，**页面代码零修改**
- [ ] 交付：fixtures 完成即群里通知 C/D 取用

### 阶段二：学情画像仪表盘（P0-3，mock 版 8-22）

- [ ] `views/Dashboard.vue`（学生首页）：顶部指标卡 学习时长/完成率/平均分 + 趋势箭头（`GET /api/student/metrics`）；数字进视口滚动增长动画 800ms ease-out
- [ ] ECharts 雷达图：6 能力维度（`GET /api/student/dimensions`）
- [ ] 折线图：学习行为 周/月/学期 切换（`GET /api/student/behavior`），切换 300ms 过渡动画
- [ ] 知识掌握度进度条组（`GET /api/student/knowledge`）：强弱项红绿区分（成功 `#22C55E` / 危险 `#EF4444`），**弱项必须醒目**（它是后续 Agent 链路的触发点）
- [ ] 画像编辑表单：education/major/theoryTestScore/weakKPs/strongKPs → `PUT /api/user/profile`；保存后刷新回显正确
- [ ] 4 态齐全：骨架屏（呼吸 1.5s）/ 错误重试 / 空态引导（"还没有学习记录，去生成你的第一条路径 →"）/ 断网横幅

### 阶段三：真数据切换（8-25）

- [ ] 关 `VITE_USE_MOCK`，连真实后端（student001 画像：本科/机械工程/78分/弱项kp12,kp15），逐接口核对回显
- [ ] 画像编辑真改一次并刷新验证持久化

### 阶段四：学习活动页（P2，8-25）

- [ ] `views/Activity.vue`：统计卡 + 课程进度网格 + 最近记录 + 每周日历热力图（`GET /api/activity/stats|courses|recent|calendar`，mock 数据同样从画像派生，日期用当前周）

## 验收标准

- 3 画像切换时雷达图/指标/强弱项数据**肉眼可辨差异**（评审看的就是这个对比）
- 截图任意时刻可当 PPT 素材；1920×1080 无破版
- `npm run lint` 零 error；四态逐项演示给队长看

## ⚠️ 手操清单（AI 会提醒你，但必须你亲手做）

| 时机 | 手操内容 |
| --- | --- |
| fixtures 完成 | 群发通知 + 3 画像数据结构截图（C/D 要用） |
| 仪表盘 mock 完成 | 浏览器逐页截图（指标卡/雷达/折线/知识掌握度/编辑表单）发群；切 p-001 vs p-002 截对比图 |
| 真数据切换前 | 启动 MySQL + 后端，确认 student001 画像存在；切换后逐接口核对 |
| 视觉自查 | F11 全屏 + 1920×1080 检查无破版无横向滚动条；控制台无红错 |
| 每个阶段完成 | git 分支 `feat/fe-dashboard-radar` 等 → commit → push → PR 带截图 |
| 每日 18:00 | 群推进度：完成项 + 截图 + 明日计划 + 阻塞 |
