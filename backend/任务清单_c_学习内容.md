# 任务清单 — 成员 3：c_学习内容/

> **比赛目标**：XH-202630 挑战杯「领域知识个性化生成与多智能体协同决策系统研究」，**奔着夺奖（擂主 12 万）去**。
> **你（成员 3/C）负责**：`c_学习内容/`，是**领域专家 Agent** + **3 种形态资源（定制化资源 / 实操指南 / 分阶测试题）**的唯一负责区。
> **目录约定**：`backend/概览.md` ｜ **协议**：`backend/协作协议.md` ｜ **总览**：`backend/任务总看板.md`
> **3 项硬指标**（你直接负责 1 个，间接贡献 1 个）：
> - 幻觉率 `< 5%`　|　画像-难度适配准确率 `≥ 85%`　|　核心知识点覆盖率 `≥ 90%`
> - 你的 3 种形态资源生成质量直接决定「画像-难度适配准确率」是否达标
> **倒推时间线**：报名 2026-05-30～06-30 → 提交 **2026-09-05**（死线）→ 初审 2026-09-20 → 决赛 2026-11
> **每周硬节点**：每周五晚 22:00 在群里同步进度；距提交剩 2 周（8-22）起**每日**同步。

---

# 任务 1：c_学习内容/ 自有数据层

**ID**：C-00
**负责人**：C（你）
**状态**：⬜ 待开始
**依赖**：无
**优先级**：P0
**归属目录**：`backend/c_学习内容/`

## 涉及文件
- `backend/c_学习内容/db.py`（新建）— 连接池 + `get_session()` 上下文管理器
- `backend/c_学习内容/config.py`（新建）— 读取 `LEARNING_CONTENT_DB_URL`
- `backend/c_学习内容/models/`（按表分文件）
  - `learning_path.py` — LearningPath 表
  - `suggestion.py` — Suggestion 表
  - `resource.py`（**挑战杯新增**）— **3 种形态资源表**（resource_id / student_id / type / content / kp_coverage JSON / difficulty / version / generated_at / source_traceId）
    - `type` 枚举：`customized_resource` / `practice_guide` / `tiered_quiz`
  - `resource_version.py`（**挑战杯新增**）— 资源历史版本表（便于回溯 + 演示视频回放）

## 描述
学习内容**自有**的数据层，**不**放在 `公共/`。本任务要一并把挑战杯需要的**3 种形态资源表**和**资源历史版本表**的 schema 落库，避免后续返工。

## 验收标准（每项必须 ✅，量化）
- [ ] `db.get_session()` 上下文管理器，异常自动回滚
- [ ] `config.py` 读取 `LEARNING_CONTENT_DB_URL`
- [ ] `resource` 表字段必须含：`resource_id`(PK) / `student_id` / `type`(枚举 3 种) / `content`(JSON 或 TEXT) / `kp_coverage`(JSON 数组) / `difficulty`(int 1-5) / `version` / `generated_at` / `source_traceId`
- [ ] `resource_version` 表用于**保留每次 AI 生成的历史版本**（演示视频 + 决策回放都要用）
- [ ] 上述 4 张表都有建表 SQL + 单测确认能 CRUD
- [ ] 单测：`db.py` 在测试环境下能连上，建表 SQL 可幂等执行
- [ ] 在群里公告 4 张表 schema 截图

## 一票否决
❌ `resource` 表缺 `type` 枚举 / 缺 `kp_coverage` 字段 → 后续 C-04 领域专家 Agent 无法生成 3 种形态资源，**完整性 30 分必扣**

---

# 任务 2：学习路径 4 个接口

**ID**：C-01
**负责人**：C（你）
**状态**：⬜ 待开始
**依赖**：C-00
**优先级**：P0
**归属目录**：`backend/c_学习内容/`

## 涉及文件
- `backend/c_学习内容/learning_path/overview.py`（新建）
- `backend/c_学习内容/learning_path/timeline.py`（新建）
- `backend/c_学习内容/learning_path/modules.py`（新建）
- `backend/c_学习内容/learning_path/tasks.py`（新建）
- `backend/c_学习内容/models/learning_path.py`（新建）
- `backend/c_学习内容/tests/test_path.py`（新建）

## 描述
实现学习路径模块的 4 个非 AI 接口。

## 验收标准（严格）
- [ ] `GET /api/learning-path/overview` 字段对齐 `api-doc §3.1`
- [ ] `GET /api/learning-path/timeline` 支持 status 过滤（`completed/current/pending`）
- [ ] `GET /api/learning-path/modules` 返回模块 + 进度
- [ ] `GET /api/learning-path/tasks?studentId=xxx` 返回今日任务清单
- [ ] 单测覆盖 timeline 3 种状态切换，**≥ 6 用例**

---

# 任务 3：学习建议 2 个接口

**ID**：C-02
**负责人**：C（你）
**状态**：⬜ 待开始
**依赖**：C-01
**优先级**：P0
**归属目录**：`backend/c_学习内容/`

## 涉及文件
- `backend/c_学习内容/suggestions/list.py`（新建）
- `backend/c_学习内容/suggestions/read.py`（新建）
- `backend/c_学习内容/models/suggestion.py`（新建）

## 验收标准
- [ ] `GET  /api/suggestions/list?studentId&category` 支持 `all/method/resource/review/practice` 5 种过滤
- [ ] `POST /api/suggestions/read` 入参 `{studentId, suggestionId}` 返回 `{success: true}`
- [ ] 单测覆盖 5 种 category 过滤，**≥ 5 用例**

---

# 任务 4：领域专家 Agent ⭐ 夺奖核心

**ID**：C-04 ⭐ 夺奖专项
**负责人**：C（你）+ D 配合
**状态**：⬜ 待开始
**依赖**：C-00, B-05
**优先级**：P0
**归属目录**：`backend/c_学习内容/agents/`（新建）

## 涉及文件
- `backend/c_学习内容/agents/__init__.py`（新建）
- `backend/c_学习内容/agents/expert_agent.py`（新建）— 领域专家 Agent 主体
- `backend/c_学习内容/agents/expert_prompts.py`（新建）— 领域专家 prompt 模板（顶部注释 `version: 0.1`）
- `backend/c_学习内容/agents/resource_factory.py`（新建）— 3 种形态资源工厂
- `backend/c_学习内容/agents/kp_coverage_check.py`（新建）— **核心知识点覆盖率校验**（对接 A 的 `公共/metrics.py`）
- `backend/c_学习内容/tests/test_expert_agent.py`（新建）

## 描述
**挑战杯 3 个核心 Agent 之一**。领域专家 Agent 的职责：
1. 接 B 的学情诊断结果（`weakKPs` / `knowledgeGaps`）
2. 调 B 的 `list_kb_chunks_by_kp` 检索知识库切片
3. **强制**基于检索到的 chunk 生成内容（不基于自有知识，杜绝幻觉）
4. 调用 D 的 provider 走 3 种形态资源工厂（路径 / 指南 / 题目）
5. 调用 A 的 `公共/metrics.py` 的 `calc_coverage` 自我校验

## 验收标准（一票否决项 - 严格）
- [ ] 模块级函数 `generate_resource(studentId, diagnosis_result, resource_type) -> Resource`：
  - `diagnosis_result` 来自 B 的 `diagnose()` 输出
  - `resource_type` 枚举：`customized_resource` / `practice_guide` / `tiered_quiz`
  - 返回：写入 `resource` 表的 `Resource` 对象 + 同步写入 `resource_version` 历史
- [ ] **3 种形态资源**：
  - `customized_resource`（定制化资源）：Markdown 结构化讲义，含概念/案例/小结
  - `practice_guide`（实操指南）：步骤化操作流程，含前置条件/工具/步骤/排错
  - `tiered_quiz`（分阶测试题）：3-5 题，每题标 `difficulty: 1-5` + 含答案 + 含解析
  - **每种形态的 `kp_coverage` 字段必须非空**（列出覆盖的 kp_id）
- [ ] **必须**通过 WebSocket 推送 `agent.thinking` 事件（调 A-04 的 `ws.emit(agentName='领域专家Agent', ...)`）
- [ ] **必须**调 A 的 `calc_coverage` 校验：覆盖率 `< 0.90` 时**自动重试一次**（扩充检索），仍不达标则抛 `QualityError`
- [ ] **必须**调 A 的 `calc_hallucination_rate` 校验：幻觉率 `> 0.05` 时**自动重试一次**，仍不达标则抛 `QualityError`
- [ ] **必须**保存 traceId 关联 B 的诊断 + D 的 provider 调用日志
- [ ] 单测覆盖 3 种形态 × happy path / 覆盖率不达标 / 幻觉率不达标，**≥ 9 用例**
- [ ] 在 `backend/c_学习内容/概览.md` 中更新「对外约定」

## 接口契约（D 必看）
```python
from backend.c_学习内容.agents import generate_resource

result = generate_resource(
    studentId="s001",
    diagnosis_result=diagnosis_payload,  # 来自 B 的 diagnose()
    resource_type="customized_resource"  # 3 选 1
)
# 返回：写入数据库的 resource_id + 完整内容
```

## 一票否决
❌ 领域专家 Agent 不能跑通 / 不能生成 3 种形态 / 不能调指标自检 → 完整性 30 分必扣、技术创新性 25 分必扣

---

# 任务 5：3 种形态资源的渲染器（前端展示 + 演示视频用）

**ID**：C-05
**负责人**：C（你）
**状态**：⬜ 待开始
**依赖**：C-04
**优先级**：P0
**归属目录**：`backend/c_学习内容/`

## 涉及文件
- `backend/c_学习内容/learning_path/renderers/customized_resource.py`（新建）
- `backend/c_学习内容/learning_path/renderers/practice_guide.py`（新建）
- `backend/c_学习内容/learning_path/renderers/tiered_quiz.py`（新建）
- `backend/c_学习内容/learning_path/renderers/__init__.py`（新建）

## 描述
把 3 种形态资源**统一渲染**为前端可展示的 HTML / Markdown 混合结构（含样式），用于演示视频和前端页面。要求**排版规范、展示清晰**（这是用户体验 15 分的硬要求）。

## 验收标准（严格 - 用户体验 15 分核心）
- [ ] 3 个渲染器输出统一结构 `{html, markdown, structuredData}`
  - `html` 含内联 CSS 样式（前端无需额外样式表即可展示）
  - `markdown` 保留原始结构（备用导出）
  - `structuredData` 含 TOC（目录）+ 元信息（生成时间、kp 列表、难度）
- [ ] `customized_resource` 渲染：含 H1 标题、概念卡片、案例代码块、小结
- [ ] `practice_guide` 渲染：含步骤序号、工具清单、代码块、排错 FAQ
- [ ] `tiered_quiz` 渲染：含题目编号、难度徽章、答案折叠区、解析区
- [ ] **所有代码块语法高亮**（用 Pygments / Prism / highlight.js 任一）
- [ ] **移动端友好**（@media 适配，演示视频可能投屏）
- [ ] 单测：3 种渲染器 × 至少 1 份样本，**≥ 6 用例**
- [ ] 在 `docs/demo_assets/` 提供 3 份**脱敏后**的样例渲染结果 HTML（演示视频用）

## 一票否决
❌ 渲染器输出混乱 / 无样式 / 排版不清晰 → 用户体验 15 分必扣 5-10 分

---

# 任务 6：暴露给 D 的写回方法

**ID**：C-03
**负责人**：C（你）
**状态**：⬜ 待开始
**依赖**：C-01, C-02
**优先级**：P1
**归属目录**：`backend/c_学习内容/`

## 涉及文件
- `backend/c_学习内容/learning_path/__init__.py`（扩展）
- `backend/c_学习内容/suggestions/__init__.py`（扩展）

## 描述
D 在生成 AI 内容后要写回本区数据表。提供**模块级写函数**，D 通过 import 调用，**不**直接操作 C 的 ORM。

## 验收标准
- [ ] `from backend.c_学习内容.learning_path import save_ai_generated_path` 可用
- [ ] `save_ai_generated_path(studentId: str, content: str) -> None` 写入并保留历史版本
- [ ] `from backend.c_学习内容.suggestions import save_ai_generated_suggestions` 可用
- [ ] `save_ai_generated_suggestions(studentId: str, content: str) -> None` 写入
- [ ] **新增** `from backend.c_学习内容.agents import generate_resource`（C-04）
- [ ] 在 `backend/c_学习内容/概览.md` 中更新「写回约定」小节
- [ ] 单测：写后 read 能拿到

---

# 任务 7：基于反馈的动态迭代机制（**创新性 25 分亮点**）

**ID**：C-06 ⭐ 夺奖专项
**负责人**：C（你）
**状态**：⬜ 待开始
**依赖**：C-04, C-05
**优先级**：P0
**归属目录**：`backend/c_学习内容/`

## 涉及文件
- `backend/c_学习内容/learning_path/feedback_adapter.py`（新建）
- `backend/c_学习内容/models/interaction_log.py`（新建）— 交互记录表（question_id / correct / response_time / kp_id）
- `backend/c_学习内容/tests/test_feedback_adapter.py`（新建）

## 描述
**挑战杯创新性要求**：「提供基于学习交互反馈的动态迭代机制，如根据答题正确率，多智能体协同决策是否对知识点进行"降维解释"或生成"进阶挑战任务"」。本任务实现反馈接入 + 触发规则。

## 验收标准（严格 - 创新性 25 分核心）
- [ ] `POST /api/learning-path/feedback` 入参 `{studentId, kpId, questionId, correct, responseTime}`
  - 写 `interaction_log` 表
  - 当某 kp 正确率 `< 0.6` 且样本数 ≥ 3 → **自动**重新调 `generate_resource` 生成 `difficulty-1` 的 `customized_resource`（**降维解释**）
  - 当某 kp 正确率 `> 0.9` 且样本数 ≥ 3 → **自动**调 `generate_resource` 生成 `difficulty+1` 的 `tiered_quiz`（**进阶挑战**）
- [ ] **必须**通过 WebSocket 推送 `agent.start` + `agent.thinking` + `agent.final` 事件（前端实时看到「AI 正在为你降维解释」）
- [ ] **必须**记录 `trigger_reason` 到 `resource` 表（如 `low_accuracy` / `high_accuracy`）
- [ ] 单测覆盖：低正确率触发降维 / 高正确率触发进阶 / 样本不足不触发，**≥ 6 用例**
- [ ] 在 `docs/demo_assets/interaction_scenarios.md` 写 2 个**脱敏的**端到端场景案例（演示视频用）

## 一票否决
❌ 动态迭代机制缺失 → 技术创新性 25 分扣 10-15 分

---

# 任务 8：参与 A-05 端到端验收 + 3 种形态资源达标

**ID**：C-07
**负责人**：C（你）
**状态**：⬜ 待开始
**依赖**：A-05, C-04, C-05
**优先级**：P0
**归属目录**：`backend/c_学习内容/`

## 涉及文件
- `backend/c_学习内容/tests/test_e2e_quality.py`（新建）

## 验收标准
- [ ] 配合 A 跑通 A-05 的 `quality_check.py`
- [ ] 3 种形态资源全部能生成
- [ ] **画像-难度适配准确率 ≥ 0.85**（C-04 调 A 的 `calc_match_accuracy` 自动跑）
- [ ] 渲染器输出符合演示视频要求
- [ ] 任一项不达标 → 阻塞提交，立即进入迭代

---

# 任务 9：演示视频用的 3 套脱敏样例资源

**ID**：C-08
**负责人**：C（你）
**状态**：⬜ 待开始
**依赖**：C-04, C-05
**优先级**：P0（**演示视频是 9-5 必交材料**）
**归属目录**：`backend/c_学习内容/sample_resources/`（新建）

## 涉及文件
- `backend/c_学习内容/sample_resources/customized_resource_sample.html`
- `backend/c_学习内容/sample_resources/practice_guide_sample.html`
- `backend/c_学习内容/sample_resources/tiered_quiz_sample.html`
- `backend/c_学习内容/sample_resources/README.md`（**脱敏声明** + 选用画像说明）

## 描述
**演示视频 10 分钟**要展示 3 种形态资源的完整效果，团队必须**预先**渲染好 3 套**脱敏**样例（基于 B-07 的 3 组测试画像生成）。脱敏后归档，避免泄露真实用户信息。

## 验收标准（一票否决 - 9-5 必交）
- [ ] 3 套 HTML 样例资源，**完全脱敏**（无真实姓名/学号/邮箱）
- [ ] 选用 B-07 的 3 组测试画像作为输入（保证可复现）
- [ ] 每套含：完整内容 + 渲染截图（用 Playwright 截）
- [ ] `README.md` 含：脱敏声明 + 选用画像说明 + 截图清单
- [ ] 在群里公告 3 套样例的访问路径

## 一票否决
❌ 演示视频缺 3 套样例 / 未脱敏 → 9-5 提交材料不完整，**直接失去参赛资格**

---

## 你的交付物清单（提交前自检）

- [ ] C-00 ~ C-08 全部 ✅
- [ ] 领域专家 Agent 可独立调用，能生成 3 种形态资源 + 自动调指标自检
- [ ] 3 个渲染器输出排版规范、样式统一
- [ ] 动态迭代机制（降维解释 / 进阶挑战）可演示
- [ ] 3 套脱敏样例资源就绪
- [ ] `save_ai_generated_*` + `generate_resource` 模块级函数暴露
- [ ] C 的 `tests/` 覆盖率 ≥ 70%
- [ ] 配合 A-05 跑通 3 项硬指标达标
