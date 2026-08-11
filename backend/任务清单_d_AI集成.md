# 任务清单 — 成员 4：d_AI集成/

> **比赛目标**：XH-202630 挑战杯「领域知识个性化生成与多智能体协同决策系统研究」，**奔着夺奖（擂主 12 万）去**。
> **你（成员 4/D）负责**：`d_AI集成/`，是**多智能体协同编排** + **审核裁判 Agent** + **3 个 AI provider** + **可视化事件** + **演示视频 + PPT** 的唯一负责区。
> **目录约定**：`backend/概览.md` ｜ **协议**：`backend/协作协议.md` ｜ **总览**：`backend/任务总看板.md`
> **3 项硬指标**（你直接负责 1 个，间接贡献 2 个）：
> - 幻觉率 `< 5%`　|　画像-难度适配准确率 `≥ 85%`　|　核心知识点覆盖率 `≥ 90%`
> - 你的 3 个 AI 接入质量 + 审核 Agent 直接决定 3 项指标能否达标
> **倒推时间线**：报名 2026-05-30～06-30 → 提交 **2026-09-05**（死线）→ 初审 2026-09-20 → 决赛 2026-11
> **每周硬节点**：每周五晚 22:00 在群里同步进度；距提交剩 2 周（8-22）起**每日**同步。

---

# 任务 1：d_AI集成/ 自有数据层 + 3 个 AI 配置

**ID**：D-00
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：无
**优先级**：P0
**归属目录**：`backend/d_AI集成/`

## 涉及文件
- `backend/d_AI集成/db.py`（新建）— 连接池 + `get_session()` 上下文管理器
- `backend/d_AI集成/config.py`（新建）— 读取 `AI_INTEGRATION_DB_URL` + 3 个 AI 的 `*_API_KEY` / `*_ENDPOINT`
- `backend/d_AI集成/models/`（按表分文件）
  - `ai_conversation.py` — AI 对话历史表
  - `ai_result.py` — AI 生成结果表
  - `agent_log.py`（**挑战杯新增**）— **多 Agent 协同日志表**（trace_id / agent_name / step / event_type / payload JSON / ts）
  - `audit_record.py`（**挑战杯新增**）— **审核裁判 Agent 审核记录表**（audit_id / trace_id / result / issues / score）

## 描述
AI集成**自有**的数据层，**不**放在 `公共/`。`config.py` 同时负责 3 个 AI 服务的连接信息（key / endpoint），属于本区私有。本任务要一并把挑战杯需要的**多 Agent 协同日志表**和**审核记录表**的 schema 落库。

## 验收标准（每项必须 ✅，量化）
- [ ] `db.get_session()` 上下文管理器，异常自动回滚
- [ ] `config.py` 从环境变量读取 `AI_INTEGRATION_DB_URL` + 3 个 AI 的配置（`CHAT_AI_*` / `PATH_AI_*` / `SUGGEST_AI_*`）
- [ ] `agent_log` 表字段必须含：`log_id`(PK) / `trace_id` / `agent_name` / `step` / `event_type`（`start/thinking/result/debate/final`）/ `payload`(JSON) / `ts`
- [ ] `audit_record` 表字段必须含：`audit_id`(PK) / `trace_id` / `result`（`pass/fail/retry`）/ `issues`(JSON) / `score`(浮点 0-1) / `ts`
- [ ] 上述 4 张表都有建表 SQL + 单测确认能 CRUD
- [ ] 单测：`db.py` 在测试环境下能连上
- [ ] 在群里公告 4 张表 schema + 3 个 AI 的环境变量名

## 一票否决
❌ `agent_log` / `audit_record` 缺一 → 后续 D-04/D-06 协同可视化、审核 Agent 全部无法工作

---

# 任务 2：BaseAIProvider 抽象

**ID**：D-01
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-00
**优先级**：P0
**归属目录**：`backend/d_AI集成/`

## 涉及文件
- `backend/d_AI集成/providers/__init__.py`（新建）
- `backend/d_AI集成/providers/base.py`（新建）

## 描述
定义 3 个 AI provider 必须实现的统一接口。后续切换 / 新增 AI 只需替换 provider，业务路由不动。

## 验收标准
- [ ] `BaseAIProvider` 抽象类定义：
  - `name: str` 属性
  - `async def invoke(self, prompt: str, *, context: dict, **kwargs) -> str`
  - `async def stream(self, prompt: str, *, context: dict, **kwargs) -> AsyncIterator[str]`（任务 6 用）
  - `async def invoke_with_audit(self, prompt: str, *, context: dict, audit_callback=None) -> str`（**挑战杯新增**）— 支持接入审核回调
- [ ] 提供 `register(name, provider)` 全局注册函数
- [ ] 提供 `get_provider(name) -> BaseAIProvider` 工厂
- [ ] 单测：mock 一个 provider 注册后能查到 + invoke_with_audit 能触发回调

---

# 任务 3：3 个 AI provider 实现

**ID**：D-02
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-01
**优先级**：P0
**归属目录**：`backend/d_AI集成/`

## 涉及文件
- `backend/d_AI集成/providers/chat_ai.py`（新建 — AI 1：辅导）
- `backend/d_AI集成/providers/path_ai.py`（新建 — AI 2：路径生成）
- `backend/d_AI集成/providers/suggest_ai.py`（新建 — AI 3：建议生成）
- `backend/d_AI集成/providers/embed_ai.py`（**挑战杯新增** — AI 4：embedding，用于知识库检索）

## 描述
3 个 AI 服务接入层（实际是 4 个，含 embedding），每个 AI 一个文件。配置从本区 `config.py` 读取。具体 AI 服务由团队决定（OpenAI / 智谱 / 通义 / 自建 …）。

## 验收标准
- [ ] 4 个 provider 继承 `BaseAIProvider`
- [ ] 配置走 `config.py` → 环境变量，**不**硬编码 key
- [ ] 每个 provider 至少有 happy-path 单测（用 mock）
- [ ] 错误处理：网络错误 / 超时 / 4xx / 5xx 都要转成统一异常
- [ ] `D-02.1` ChatAI 完成 → D-02.1 ✅
- [ ] `D-02.2` PathAI 完成 → D-02.2 ✅
- [ ] `D-02.3` SuggestAI 完成 → D-02.3 ✅
- [ ] `D-02.4` EmbedAI 完成 → D-02.4 ✅

---

# 任务 4：多智能体协同编排器 ⭐ 夺奖核心

**ID**：D-03 ⭐ 夺奖专项
**负责人**：D（你）+ B/C 配合
**状态**：⬜ 待开始
**依赖**：D-02, B-05, C-04
**优先级**：P0
**归属目录**：`backend/d_AI集成/orchestrator/`（新建）

## 涉及文件
- `backend/d_AI集成/orchestrator/__init__.py`（新建）
- `backend/d_AI集成/orchestrator/pipeline.py`（新建）— **3 Agent 协同编排主体**
- `backend/d_AI集成/orchestrator/debate_engine.py`（**挑战杯核心**）— **辩论与交叉验证引擎**
- `backend/d_AI集成/orchestrator/event_emitter.py`（新建）— 包装 A-04 的 ws.emit，自动落 `agent_log` 表
- `backend/d_AI集成/orchestrator/decision_maker.py`（新建）— 决策选择：pass / retry / 反馈降维
- `backend/d_AI集成/tests/test_orchestrator.py`（新建）

## 描述
**挑战杯 3 个核心 Agent 的"导演"**。协调 3 个 Agent 形成"分析-生成-校验-决策"协同闭环。**所有事件必须**通过 A-04 的 WebSocket 推送 + 同步落 `agent_log` 表，用于前端实时可视化 + 演示视频回放。

## 流程（必须严格按此执行）
```
1. start: emit agent.start("学情诊断Agent", traceId=t)
2. diagnose: B.diagnose(studentId) → emit agent.thinking × N → emit agent.result
3. start: emit agent.start("领域专家Agent", traceId=t)
4. expert: C.generate_resource(studentId, diagnosis, type) → emit agent.thinking × N → emit agent.result
5. start: emit agent.start("审核裁判Agent", traceId=t)
6. audit: 调 audit_agent.score(content, kb_chunks) → emit agent.debate（领域专家 vs 审核）→ emit agent.result
7. decide: 根据 audit.score 选择 pass / retry / 反馈降维
8. emit agent.final(ok=..., traceId=t)
```

## 验收标准（一票否决项 - 严格）
- [ ] 模块级函数 `orchestrate(studentId, resource_type) -> dict`：
  - 串起 3 个 Agent（B 诊断 → C 生成 → D 审核）
  - 同步通过 A-04 的 ws.emit 推送 5 类事件
  - 同步落 `agent_log` 表（每步一行）
  - 同步落 `audit_record` 表（审核结果）
  - 返回：`{traceId, resourceId, auditScore, finalStatus}`
- [ ] **辩论与交叉验证**（技术创新性 25 分核心）：
  - 当 audit.score `< 0.85` 时，触发 `agent.debate` 事件：领域专家 Agent 与审核裁判 Agent 交叉质询
  - 辩论最多 2 轮，2 轮后仍未达 0.85 → 抛 `QualityError` 并将 trace 标记为 fail
  - 辩论内容**全部**落 `agent_log` 表
- [ ] 决策选择：
  - audit.score `≥ 0.95` → pass，直接返回
  - audit.score `0.85 ~ 0.95` → pass，标记 `confidence: medium`
  - audit.score `< 0.85` → 触发辩论
- [ ] 失败重试：编排器内任意 Agent 抛 `QualityError` → 自动重试 1 次，仍失败 → 返回 `finalStatus: fail` + 详细错误
- [ ] 单测覆盖：happy path / 审核不达标触发辩论 / 辩论 2 轮未达 0.85 / 事件推送至少 5 次 / 日志表写入完整，**≥ 10 用例**
- [ ] 在 `backend/d_AI集成/概览.md` 中更新「对外约定」

## 接口契约（C/B 必看）
```python
from backend.d_AI集成.orchestrator import orchestrate

result = orchestrate(
    studentId="s001",
    resource_type="customized_resource"
)
# {
#   "traceId": "trace-2026-08-15-001",
#   "resourceId": "r-001",
#   "auditScore": 0.92,
#   "finalStatus": "pass",
#   "duration": 12.3
# }
```

## 一票否决
❌ 协同闭环断裂（任一 Agent 未串起来）→ 完整性 30 分全扣、技术创新性 25 分扣 10-15 分

---

# 任务 5：审核裁判 Agent ⭐ 夺奖核心

**ID**：D-06 ⭐ 夺奖专项
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-02, B-06
**优先级**：P0
**归属目录**：`backend/d_AI集成/audit/`（新建）

## 涉及文件
- `backend/d_AI集成/audit/__init__.py`（新建）
- `backend/d_AI集成/audit/audit_agent.py`（新建）— 审核裁判 Agent 主体
- `backend/d_AI集成/audit/audit_prompts.py`（新建）— 审核 prompt 模板（顶部注释 `version: 0.1`）
- `backend/d_AI集成/audit/groundness_check.py`（新建）— **幻觉率校验**（基于 B 的 `list_kb_chunks_by_kp` + A 的 `calc_hallucination_rate`）
- `backend/d_AI集成/audit/coverage_check.py`（新建）— **核心知识点覆盖率校验**
- `backend/d_AI集成/tests/test_audit_agent.py`（新建）

## 描述
**挑战杯 3 个核心 Agent 之一**。审核裁判 Agent 是与领域专家 Agent **辩论**的对方，职责：
1. 把领域专家生成的内容**严格**与知识库切片做比对
2. 计算幻觉率（`calc_hallucination_rate`）、覆盖率（`calc_coverage`）
3. 输出结构化审核结果（pass / fail / retry + 详细 issues）

## 验收标准（一票否决项 - 严格）
- [ ] 模块级函数 `audit(studentId, content, kp_ids) -> AuditResult`：
  - `content` 来自 C 的 `generate_resource` 输出
  - `kp_ids` 是 C 声称覆盖的 kp 列表
  - 返回：`{auditId, traceId, score, result, issues[], metrics: {hallucinationRate, coverage}, ts}`
- [ ] **幻觉率校验**（基于知识库检索）：
  - 把 content 拆句 → 每句调 B 的 `list_kb_chunks_by_kp` 检索 → 句与检索结果的相似度
  - 相似度 `< 0.5` 的句子视为幻觉
  - `hallucinationRate = 幻觉句数 / 总句数`
- [ ] **核心知识点覆盖率校验**：
  - 调 A 的 `calc_coverage(content, kp_ids)` → 返回值
  - `coverage < 0.90` → 列入 issues
- [ ] 评分公式（0-1）：
  - `score = 0.6 * (1 - hallucinationRate) + 0.4 * coverage`
  - `score ≥ 0.85` → pass
  - `0.70 ≤ score < 0.85` → retry（标"可优化"）
  - `score < 0.70` → fail
- [ ] **必须**通过 WebSocket 推送 `agent.thinking` + `agent.result` 事件
- [ ] 单测覆盖：完全正确内容 / 含幻觉内容 / 覆盖率不达标 / 边界 score，**≥ 8 用例**
- [ ] 写审核日志到 `audit_record` 表

## 一票否决
❌ 审核 Agent 不能跑通 / 不能给 0-1 评分 → 完整性 30 分必扣、辩论机制无法工作

---

# 任务 6：统一 AI 服务 ai_service

**ID**：D-04
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-02, B-04, C-03
**优先级**：P0
**归属目录**：`backend/d_AI集成/`

## 涉及文件
- `backend/d_AI集成/ai_service.py`（新建）
- `backend/d_AI集成/prompt_templates.py`（新建）
- `backend/d_AI集成/chat/__init__.py`（新建）
- `backend/d_AI集成/path/__init__.py`（新建）
- `backend/d_AI集成/suggest/__init__.py`（新建）

## 描述
业务路由不直接调 provider，而是调 `ai_service`：
1. 从 B 拉 `get_student_snapshot` 拼上下文
2. 从 `prompt_templates` 取模板
3. 选 provider → invoke
4. 调 C 的 `save_ai_generated_*` 写回

## 验收标准
- [ ] `ai_service.chat(studentId, message) -> str` 实现
- [ ] `ai_service.generate_path(studentId) -> str` 实现，调用 C 的 `save_ai_generated_path`
- [ ] `ai_service.generate_suggestions(studentId) -> str` 实现，调用 C 的 `save_ai_generated_suggestions`
- [ ] 3 类 prompt 模板放在 `prompt_templates.py`，顶部注释 `version: 0.1`
- [ ] 单测：snapshot 拼装正确、provider 选错时报错、写回调用 1 次
- [ ] **不**直接 import B / C 的 models，只调用 概览 中声明的对外函数

---

# 任务 7：WebSocket 协同事件 + 可视化数据接口（**用户体验 15 分核心**）

**ID**：D-07 ⭐ 夺奖专项
**负责人**：D（你）+ A 配合
**状态**：⬜ 待开始
**依赖**：D-03
**优先级**：P0
**归属目录**：`backend/d_AI集成/`

## 涉及文件
- `backend/d_AI集成/ws_bridge.py`（新建）— 把编排器的 event_emitter 桥接到 A-04 的 ws
- `backend/d_AI集成/api/visualization.py`（新建）— **可视化数据接口**（用于前端大屏）
- `backend/d_AI集成/api/trace.py`（新建）— **trace 回放接口**（演示视频用）
- `backend/d_AI集成/tests/test_ws_bridge.py`（新建）

## 描述
**用户体验 15 分的硬要求**：「多智能体协同调度过程与决策逻辑可视化交互流畅」。本任务确保 A-04 的 5 类事件能稳定推送到前端 + 提供可视化数据接口 + 提供 trace 回放接口（演示视频用）。

## 验收标准（一票否决项 - 严格）
- [ ] `ws_bridge.py` 把 D 的 event_emitter 输出**实时**桥接到 A-04 的 ws（无延迟）
- [ ] 5 类事件必须**全部**推送：`agent.start` / `agent.thinking` / `agent.result` / `agent.debate` / `agent.final`
- [ ] 事件 payload 格式**严格**与 A-04 文档一致：`{type, agentName, step, content, traceId, ts}` + `agent.debate` 额外含 `agents` 列表和 `topic`
- [ ] `GET /api/visualization/agent-graph?studentId=xxx` 返回 3 Agent 的实时状态（含最近 10 个事件）
- [ ] `GET /api/visualization/recent-traces?limit=20` 返回最近 20 个 trace 摘要（用于演示视频首页大屏）
- [ ] `GET /api/trace/{traceId}` 返回完整 trace 详情（含所有 agent_log + audit_record，按 ts 升序）
- [ ] 单测覆盖：5 类事件全部推送 / 可视化接口数据完整 / trace 回放按时间顺序，**≥ 8 用例**
- [ ] 在群里公告：ws 桥接测试截图 + 可视化接口截图

## 一票否决
❌ 协同过程无可视化 → 用户体验 15 分扣 5-10 分

---

# 任务 8：3 个 AI 业务接口

**ID**：D-05
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-04
**优先级**：P0
**归属目录**：`backend/d_AI集成/`

## 涉及文件
- `backend/d_AI集成/chat/send.py`（新建）— `/api/ai-chat/send`
- `backend/d_AI集成/chat/history.py`（新建）— `/api/ai-chat/history`
- `backend/d_AI集成/chat/clear.py`（新建）— `/api/ai-chat/history` (DELETE)
- `backend/d_AI集成/path/ai_result.py`（新建）— `/api/learning-path/ai-result`
- `backend/d_AI集成/suggest/ai_result.py`（新建）— `/api/suggestions/ai-result`
- `backend/d_AI集成/models/ai_conversation.py`（新建）
- `backend/d_AI集成/models/ai_result.py`（新建）

## 验收标准
- [ ] `POST   /api/ai-chat/send` 入参 `api-doc §6.1`，返回 `{reply, conversationId}`
- [ ] `GET    /api/ai-chat/history?studentId&limit` 返回对话历史
- [ ] `DELETE /api/ai-chat/history?studentId` 清空
- [ ] `send` 内调 `ai_service.chat`
- [ ] `POST /api/learning-path/ai-result` 入参 `{studentId, content}`，保存入参 content
- [ ] `GET  /api/learning-path/ai-result?studentId=xxx` 返回 `{content, generatedAt}`
- [ ] `POST /api/suggestions/ai-result` 入参 `{studentId, content}`，保存
- [ ] `GET  /api/suggestions/ai-result?studentId=xxx` 返回 `{content, generatedAt}`
- [ ] 单测覆盖 3 个接口，**≥ 6 用例**

---

# 任务 9：演示视频录制（≤10 分钟）⭐ 9-5 必交

**ID**：D-08 ⭐ 夺奖专项
**负责人**：D（你）+ 全员
**状态**：⬜ 待开始
**依赖**：D-03, D-07, C-08
**优先级**：P0
**归属目录**：`backend/d_AI集成/demo_video/`（新建）→ 最终归档到 `docs/demo_video/`

## 涉及文件
- `backend/d_AI集成/demo_video/script.md`（**先写脚本**）— 10 分钟逐字稿
- `backend/d_AI集成/demo_video/recording_notes.md` — 录制注意事项
- `backend/d_AI集成/demo_video/raw/`（新建）— 原始视频 + 工程文件
- `backend/d_AI集成/demo_video/final.mp4`（**最终交付物**）

## 描述
**演示视频是 9-5 必交材料**。挑战杯要求 ≤10 分钟，清晰展示：差异化学习者学情画像输入 + 多智能体协同调度与交互过程可视化 + 最终个性化领域知识资源生成。

## 视频结构（必须覆盖，**严格 ≤ 10 分钟**）
```
0:00 - 0:30  开场：项目名称 + 团队介绍
0:30 - 1:30  背景与痛点（30s，配 3 张图）
1:30 - 3:00  多智能体架构 + 3 Agent 介绍（90s）
3:00 - 4:30  演示：3 组测试画像输入（90s）
4:30 - 7:00  演示：3 Agent 协同过程（前端大屏 90s + 实时生成 60s）
7:00 - 8:30  演示：3 种形态资源最终输出（90s）
8:30 - 9:30  演示：动态迭代机制（降维解释 + 进阶挑战，60s）
9:30 - 10:00 收尾：3 项硬指标 + 商业价值（30s）
```

## 验收标准（一票否决 - 9-5 必交）
- [ ] 时长 **严格 ≤ 10 分钟**（多 1 秒也不行）
- [ ] 视频清晰度 ≥ 1080p
- [ ] **必须**展示前端大屏（多 Agent 协同可视化界面，含 5 类事件流）
- [ ] **必须**展示 3 组差异化测试画像
- [ ] **必须**展示 3 种形态资源最终输出（用 C-08 的 3 套脱敏样例）
- [ ] **必须**展示动态迭代机制（任一画像触发降维或进阶）
- [ ] **必须**在视频内显示 3 项硬指标实际值
- [ ] 字幕 + 配音清晰（任选其一即可）
- [ ] 原始视频归档到 `raw/`，最终视频放到 `docs/demo_video/final.mp4`
- [ ] 9-1 前完成初剪，9-3 前完成终剪（留 2 天 buffer）

## 一票否决
❌ 视频缺失 / 超时 / 未覆盖必展示项 → **直接失去参赛资格**

---

# 任务 10：PPT（路演 + 答辩用）⭐ 9-5 必交

**ID**：D-09 ⭐ 夺奖专项
**负责人**：D（你）+ 全员
**状态**：⬜ 待开始
**依赖**：D-08
**优先级**：P0
**归属目录**：`backend/d_AI集成/ppt/`（新建）→ 最终归档到 `docs/ppt/`

## 涉及文件
- `backend/d_AI集成/ppt/slides.md`（新建）— 逐页大纲
- `backend/d_AI集成/ppt/final.pptx`（**最终交付物**）

## 描述
PPT 用于路演 / 答辩，**重点**是讲清楚：背景痛点 → 解决方案（多 Agent 协同）→ 3 项硬指标 → 商业价值。

## 验收标准（一票否决 - 9-5 必交）
- [ ] **页数 15-20 页**（太多讲不完）
- [ ] **必须**含：项目封面、团队介绍、痛点、解决方案架构、3 Agent 职责、3 项硬指标实测值、3 种形态资源样例、动态迭代机制、商业价值、致谢
- [ ] 风格统一，配色专业，**不**用花哨模板
- [ ] 关键页（架构 / 硬指标）配示意图
- [ ] 9-1 前完成初版，9-3 前完成终版

## 一票否决
❌ PPT 缺失 / 超过 20 页 / 不含硬指标实测值 → 路演分大扣

---

# 任务 11：联调 AI集成 全部接口

**ID**：D-10（可选，里程碑 M3 后做）
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-05
**优先级**：P1
**归属目录**：`backend/d_AI集成/`

## 涉及文件
- `backend/d_AI集成/tests/test_e2e.py`（新建）

## 验收标准
- [ ] 启动后端，模拟前端调用 3 个 AI 路径，全程不报错
- [ ] AI 返回内容正确写入 C 的表
- [ ] 3 个 AI 的真实 / mock 切换只改 `providers/`

---

# 任务 12：参与 A-05 端到端验收

**ID**：D-11
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：A-05, D-03
**优先级**：P0
**归属目录**：`backend/d_AI集成/`

## 涉及文件
- `backend/d_AI集成/tests/test_e2e_quality.py`（新建）

## 验收标准
- [ ] 配合 A 跑通 A-05 的 `quality_check.py`
- [ ] 3 个 Agent 协同闭环跑通
- [ ] 辩论机制在 score < 0.85 时触发
- [ ] 3 项硬指标全部达标
- [ ] 任一项不达标 → 阻塞提交，立即进入迭代

---

## 你的交付物清单（提交前自检）

- [ ] D-00 ~ D-11 全部 ✅
- [ ] 3 Agent 协同闭环跑通（分析-生成-校验-决策）+ 辩论机制可演示
- [ ] 3 个 AI provider（含 embedding）可切换
- [ ] 审核裁判 Agent 输出 0-1 评分
- [ ] WebSocket 5 类事件稳定推送 + 可视化数据接口 + trace 回放
- [ ] **演示视频 ≤ 10 分钟 + PPT 15-20 页 全部就绪**
- [ ] `orchestrate()` / `audit()` / `ws_bridge` 模块级函数暴露
- [ ] D 的 `tests/` 覆盖率 ≥ 70%
- [ ] 配合 A-05 跑通 3 项硬指标达标
