# 任务清单 — 成员 4：4_AI集成/

> **打开这一份就够了**。本文件包含你（成员 4/D）负责的所有任务，按 1/2/3 顺序排好。
> 目录约定见 `backend/概览.md`；协作规范见 `backend/协作协议.md`；状态总览见 `backend/任务总看板.md`。

---

# 任务 1：4_AI集成/ 自有数据层

**ID**：D-00
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：无
**优先级**：P0
**归属目录**：`backend/4_AI集成/`

## 涉及文件
- `backend/4_AI集成/db.py` (新建)
- `backend/4_AI集成/config.py` (新建，读取 `AI_INTEGRATION_DB_URL` 与 3 个 AI 的 `*_API_KEY` / `*_ENDPOINT`)
- `backend/4_AI集成/models/` (目录已建)

## 描述
AI集成 自有的数据库 / 配置 / ORM。**不放**在 `公共/`，避免与 A/B/C 撞车。

`config.py` 同时负责 3 个 AI 服务的连接信息（key / endpoint），属于本区私有。

## 验收标准
- [ ] `db.py` 提供本区数据库连接
- [ ] `config.py` 从环境变量读取 `AI_INTEGRATION_DB_URL` + 3 个 AI 的配置（`CHAT_AI_*` / `PATH_AI_*` / `SUGGEST_AI_*`）
- [ ] ORM 模型放在 `models/` 子目录下
- [ ] 本区所有后续任务都依赖本任务
- [ ] 单元测试：`db.py` 在测试环境下能连上
- [ ] 在群里公告 `db.get_session()` 接口签名
- [ ] 把 `AI_INTEGRATION_DB_URL` + 3 个 AI 的环境变量加入项目根 `.env.example` 模板

---

# 任务 2：BaseAIProvider 抽象

**ID**：D-01
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-00
**优先级**：P0
**归属目录**：`backend/4_AI集成/`

## 涉及文件
- `backend/4_AI集成/providers/__init__.py` (新建)
- `backend/4_AI集成/providers/base.py` (新建)

## 描述
定义 3 个 AI provider 必须实现的统一接口。后续切换 / 新增 AI 只需替换 provider，业务路由不动。

## 验收标准
- [ ] `BaseAIProvider` 抽象类定义：
  - `name: str` 属性
  - `async def invoke(self, prompt: str, *, context: dict, **kwargs) -> str`
  - `async def stream(self, prompt: str, *, context: dict, **kwargs) -> AsyncIterator[str]`（任务 5 用）
- [ ] 提供 `register(name, provider)` 全局注册函数
- [ ] 提供 `get_provider(name) -> BaseAIProvider` 工厂
- [ ] 单测：mock 一个 provider 注册后能查到

---

# 任务 3：3 个 AI provider 实现

**ID**：D-02
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-01
**优先级**：P0
**归属目录**：`backend/4_AI集成/`

## 涉及文件
- `backend/4_AI集成/providers/chat_ai.py` (新建 — AI 1：辅导)
- `backend/4_AI集成/providers/path_ai.py` (新建 — AI 2：路径生成)
- `backend/4_AI集成/providers/suggest_ai.py` (新建 — AI 3：建议生成)

## 描述
3 个 AI 服务接入层，每个 AI 一个文件。配置从本区 `config.py` 读取。具体 AI 服务由团队决定（OpenAI / 智谱 / 通义 / 自建 …）。

## 验收标准
- [ ] 3 个 provider 继承 `BaseAIProvider`
- [ ] 配置走 `config.py` → 环境变量，**不**硬编码 key
- [ ] 每个 provider 至少有 happy-path 单测（用 mock）
- [ ] 错误处理：网络错误 / 超时 / 4xx / 5xx 都要转成统一异常
- [ ] `D-02.1` ChatAI 完成 → D-02.1 ✅
- [ ] `D-02.2` PathAI 完成 → D-02.2 ✅
- [ ] `D-02.3` SuggestAI 完成 → D-02.3 ✅

---

# 任务 4：统一 AI 服务 ai_service

**ID**：D-03
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-02, B-04, C-03
**优先级**：P0
**归属目录**：`backend/4_AI集成/`

## 涉及文件
- `backend/4_AI集成/ai_service.py` (新建)
- `backend/4_AI集成/prompt_templates.py` (新建)
- `backend/4_AI集成/chat/__init__.py` (新建)
- `backend/4_AI集成/path/__init__.py` (新建)
- `backend/4_AI集成/suggest/__init__.py` (新建)

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

# 任务 5：/api/ai-chat 三个接口

**ID**：D-04
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-03, A-01（token 鉴权）
**优先级**：P0
**归属目录**：`backend/4_AI集成/`

## 涉及文件
- `backend/4_AI集成/chat/send.py` (新建)
- `backend/4_AI集成/chat/history.py` (新建)
- `backend/4_AI集成/chat/clear.py` (新建)
- `backend/4_AI集成/models/ai_conversation.py` (新建)

## 验收标准
- [ ] `POST   /api/ai-chat/send` 入参 `api-doc §6.1`，返回 `{reply, conversationId}`
- [ ] `GET    /api/ai-chat/history?studentId&limit` 返回对话历史
- [ ] `DELETE /api/ai-chat/history?studentId` 清空
- [ ] `send` 内调 `ai_service.chat`
- [ ] 单测覆盖 3 个接口

---

# 任务 6：/api/learning-path/ai-result

**ID**：D-05
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-03, C-03
**优先级**：P0
**归属目录**：`backend/4_AI集成/`

## 涉及文件
- `backend/4_AI集成/path/ai_result.py` (新建)

## 验收标准
- [ ] `POST /api/learning-path/ai-result` 入参 `{studentId, content}`，保存入参 content（C 那边已经会被调用一次，这里再写一次做兜底）
- [ ] `GET  /api/learning-path/ai-result?studentId=xxx` 返回 `{content, generatedAt}`
- [ ] 字段命名与 `api-doc §3.5 / §3.6` 一致

---

# 任务 7：/api/suggestions/ai-result

**ID**：D-06
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-03, C-03
**优先级**：P0
**归属目录**：`backend/4_AI集成/`

## 涉及文件
- `backend/4_AI集成/suggest/ai_result.py` (新建)

## 验收标准
- [ ] `POST /api/suggestions/ai-result` 入参 `{studentId, content}`，保存
- [ ] `GET  /api/suggestions/ai-result?studentId=xxx` 返回 `{content, generatedAt}`
- [ ] 字段命名与 `api-doc §4.2` 一致
- [ ] 单测覆盖 POST/GET

---

# 任务 8：联调 AI集成 全部接口

**ID**：D-07（可选，里程碑 M3 后做）
**负责人**：D（你）
**状态**：⬜ 待开始
**依赖**：D-04, D-05, D-06
**优先级**：P1
**归属目录**：`backend/4_AI集成/`

## 涉及文件
- `backend/4_AI集成/tests/test_e2e.py` (新建)

## 验收标准
- [ ] 启动后端，模拟前端调用 3 个 AI 路径，全程不报错
- [ ] AI 返回内容正确写入 C 的表
- [ ] 3 个 AI 的真实 / mock 切换只改 `providers/`
