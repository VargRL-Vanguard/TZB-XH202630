# 任务清单 — 成员 1：a_用户与聊天/

> **比赛目标**：XH-202630 挑战杯"领域知识个性化生成与多智能体协同决策系统研究"，奔着夺奖（擂主 12 万）去。
> **你（成员 1/A）负责**：`公共/` + `a_用户与聊天/`，是系统的**地基 + 实时推送通道**，所有 Agent 的过程可视化都依赖你的 WebSocket。
> **目录约定**：`backend/概览.md` ｜ **协议**：`backend/协作协议.md` ｜ **总览**：`backend/任务总看板.md`
> **3 项硬指标**（你直接负责 0 个，但你的实时通道质量影响"用户体验"15 分的可视化效果）：
> - 幻觉率 < 5%　|　画像-难度适配准确率 ≥ 85%　|　核心知识点覆盖率 ≥ 90%
> **倒推时间线**：报名 2026-05-30～06-30 → 提交 2026-09-05 → 初审 2026-09-20 → 决赛 2026-11

---

# 任务 1：公共基础工具 + 评估指标计算器

**ID**：S-01
**负责人**：A（你）
**状态**：✅ 已完成
**依赖**：无
**优先级**：P0
**归属目录**：`backend/公共/`
**Owner**: @A
**Started**: 2026-08-11

## 涉及文件
- `backend/公共/response.py`（新建）— 统一响应封装 `{code, message, data}` ✅
- `backend/公共/logger.py`（新建）— 统一 logger，按模块命名 ✅
- `backend/公共/errors.py`（新建）— `BizError` / `AuthError` / `NotFoundError` / `AgentError` / `QualityError` ✅
- `backend/公共/config.py`（新建）— 基础配置（**不含** `*_DB_URL`） ✅
- `backend/公共/metrics.py`（新建）— **3 项硬指标计算器**（见验收标准） ✅
- `backend/公共/__init__.py`（新建）— 统一导出 ✅
- `backend/公共/tests/`（新建）— 5 个单测文件 + `__init__.py` ✅
- `backend/docs/decisions/0001-S01技术选型.md`（新建）— 技术选型决策记录 ✅
- `backend/docs/decisions/README.md`（新建）— ADR 索引 ✅
- `backend/docs/dev_notes/S01-实施日志.md`（新建）— S-01 实施过程记录 ✅
- `backend/docs/progress/项目进度.md`（新建）— 项目每日进度同步 ✅

## 描述
为 4 个业务区提供**跨区通用且无状态**的基础工具 + **夺奖硬指标计算器**。后者是验收"实用价值 30 分"的核心工具。

## 验收标准（每项必须 ✅，量化）
- [x] `response.py.ok(data=None, message="success")` / `.fail(code, message)` 输出 `api-doc.js` 中规定的 `{code, message, data}` 结构
- [x] `logger.py` 支持按模块命名，输出含 `timestamp / level / module / trace_id`
- [x] `errors.py` 定义 5 类异常：`BizError` / `AuthError` / `NotFoundError` / `AgentError`（Agent 调度失败） / `QualityError`（指标不达标）
- [x] `config.py` 导出 `PORT` / `LOG_LEVEL` / `ENV` / `JWT_SECRET` / `AGENT_TIMEOUT_SEC=30` / `QUALITY_THRESHOLD`；**不**包含任何 `*_DB_URL`
- [x] **`metrics.py` 提供 3 个纯函数**（挑战杯核心指标）：
  - `calc_hallucination_rate(generated: str, ground_truth: list[str]) -> float` — 返回 [0,1] 浮点，**必须 < 0.05**（关键词匹配算法）
  - `calc_match_accuracy(profile: dict, resource_difficulty: int) -> float` — 返回 [0,1] 浮点，**必须 ≥ 0.85**（完全相等算法）
  - `calc_coverage(generated: str, required_kps: list[str]) -> float` — 返回 [0,1] 浮点，**必须 ≥ 0.90**（kp_tags 字段对比算法）
  - 每个函数有 ≥ 3 个单测（含边界值 0、1、空输入）
- [x] `__init__.py` 全部导出，B/C/D 可 `from backend.公共 import response, logger, errors, metrics`
- [x] 在群里公告 `config.py` 字段清单 + 3 个指标函数的输入输出签名

## 技术选型决策（ADR-0001）
- Web 框架：FastAPI
- 日志库：loguru
- 配置管理：pydantic-settings
- 3 项硬指标算法：关键词匹配 / 完全相等 / kp_tags 对比
- 详见：[`docs/decisions/0001-S01技术选型.md`](./docs/decisions/0001-S01技术选型.md)

## 实施日志
- 详见：[`docs/dev_notes/S01-实施日志.md`](./docs/dev_notes/S01-实施日志.md)

## 一票否决
❌ 任何指标函数未提供 / 计算结果与目标值偏差 > 5% → 实用价值 30 分全扣

---

# 任务 2：鉴权中间件 auth_middleware

**ID**：S-02
**负责人**：A（你）
**状态**：✅ 已完成（2026-08-12）
**依赖**：S-01, 任务 3, 任务 4
**优先级**：P0
**归属目录**：`backend/公共/`

## 涉及文件
- `backend/公共/auth_middleware.py`（新建）✅
- `backend/公共/__init__.py`（修改，导出 auth_middleware）✅
- `backend/公共/tests/test_auth_middleware.py`（新建，13 个单测）✅

## 描述
为 B / C / D 提供统一的"解析 token → userId + learnerProfile"能力，**所有业务接口**都依赖它。鉴权过程中需要查 `a_用户与聊天/` 的 User 表 + learner_profile 表，通过 A 暴露的 `get_learner_profile` 函数读取（**不**直连 A 的数据库）。

## 验收标准（严格）
- [x] 提供 `get_current_user(request) -> dict`，返回 `{userId, name, role, learnerProfile{education, theoryTestScore, weakKPs[], strongKPs[]}}`（学情诊断 Agent 必需输入）
- [x] 提供装饰器 `@require_auth` 供路由使用（路由级 dependencies=[Depends(require_auth)]）
- [x] 提供装饰器 `@require_role('teacher' | 'student' | 'admin')` 供权限路由使用（**工厂函数**支持多角色：require_role("teacher", "admin")）
- [x] 缺失 / 过期 / 伪造 token 时抛 `AuthError`（HTTP 401）
- [x] 角色不符时抛 `ForbiddenError`（HTTP 403）
- [x] **单测覆盖** 13 用例 > 6：正常/过期/伪造/缺 header/角色不符/画像缺失/黑名单/格式错/admin 通过/student 被拒/teacher-or-admin 工厂/无参工厂/teacher 无画像
- [x] 在群里公告接口签名，B/C/D 同步（见 auth_middleware.py 顶部 docstring）

## 接口契约
```
请求头：Authorization: Bearer <token>
返回  ：dict  {"userId": "u001", "name": "张三", "role": "student",
              "learnerProfile": {"education": "本科", "theoryTestScore": 78,
                                 "weakKPs": ["kp12","kp15"], "strongKPs": ["kp03"]}}
错误  ：401 {"code": 401, "message": "未登录或token过期"}
```

---

# 任务 3：a_用户与聊天/ 自有数据层

**ID**：A-00
**负责人**：A（你）
**状态**：✅ 已完成
**依赖**：无
**优先级**：P0
**归属目录**：`backend/a_用户与聊天/`
**Owner**: @A
**Started**: 2026-08-11
**Completed**: 2026-08-12

## 涉及文件
- `backend/a_用户与聊天/db.py`（新建）— 连接池 + `get_session()` 上下文管理器
- `backend/a_用户与聊天/config.py`（新建）— 读取 `USER_CHAT_DB_URL`
- `backend/a_用户与聊天/models/`（按表分文件）
  - `user.py` — User 表（id / username / password_hash / name / role / created_at）
  - `learner_profile.py` — **挑战杯新增**：学习者画像（user_id / education / major / theory_test_score / weak_kps JSON / strong_kps JSON / updated_at）

## 描述
自有数据层，**不放**在 `公共/`。`learner_profile` 表是学情诊断 Agent 的**唯一**输入源。

## 验收标准
- [ ] `db.get_session()` 上下文管理器，异常自动回滚
- [ ] `learner_profile` 表字段必须含：`weak_kps`（JSON 数组）、`strong_kps`（JSON 数组），其他区只读
- [ ] `USER_CHAT_DB_URL` 加入项目根 `.env.example`
- [ ] 单测：`db.py` 在测试环境下能连上
- [ ] 暴露模块级函数 `get_user_by_id(user_id) -> dict` 给 S-02 / 任务 6 使用
- [ ] **暴露模块级函数 `get_learner_profile(user_id) -> dict`** 给 B 的学情诊断 Agent 使用

---

# 任务 4：用户注册 / 登录 / 登出

**ID**：A-01
**负责人**：A（你）
**状态**：⬜ 待开始
**依赖**：A-00
**优先级**：P0
**归属目录**：`backend/a_用户与聊天/`

## 涉及文件
- `backend/a_用户与聊天/auth/register.py`（新建）— bcrypt 哈希密码
- `backend/a_用户与聊天/auth/login.py`（新建）— 签发 JWT
- `backend/a_用户与聊天/auth/logout.py`（新建）— token 失效
- `backend/a_用户与聊天/models/user.py`（新建）— User 表
- `backend/a_用户与聊天/tests/test_auth.py`（新建）

## 验收标准（严格量化）
- [ ] `POST /api/auth/register` 入参 `{username, password, name, role, education?, major?}`；**role 必须 ∈ {student, teacher, admin}**；返回 `{code:200, data:{userId}}`
- [ ] `POST /api/auth/login` 入参 `{username, password}`，返回 `{code:200, data:{token, userId, role}}`
- [ ] `POST /api/auth/logout` 鉴权后调用，token 加入黑名单（Redis 或 DB 标记）
- [ ] 重复注册 → 400 + message `"用户名已存在"`
- [ ] 错误密码 → 401 + message `"用户名或密码错误"`（**不**暴露"用户不存在"）
- [ ] **密码强度校验**：≥ 8 位 + 字母 + 数字
- [ ] **JWT 必须**含 `role` 和 `exp`（24h 过期）
- [ ] 单测覆盖：3 接口的 happy path / 异常 path，**共 ≥ 9 用例**

---

# 任务 5：用户信息 + 学习者画像读写

**ID**：A-02
**负责人**：A（你）
**状态**：✅ 已完成（2026-08-12）
**依赖**：A-01
**优先级**：P0
**归属目录**：`backend/a_用户与聊天/`

## 涉及文件
- `backend/a_用户与聊天/user/info.py`（新建）
- `backend/a_用户与聊天/user/profile.py`（新建）— **挑战杯新增** 学习者画像读写
- `backend/a_用户与聊天/models/learner_profile.py`（新建）— LearnerProfile 表
- `backend/a_用户与聊天/tests/test_profile.py`（新建）

## 验收标准
- [ ] `GET  /api/user/info?userId=xxx` 鉴权后返回 User + LearnerProfile 合并结果
- [ ] `PUT  /api/user/profile` 入参 `{education, major, theoryTestScore, weakKPs[], strongKPs[]}` 鉴权后更新；teacher 角色可改任意学生，其他角色只能改自己
- [ ] **越权访问他人信息 → 403**（含 4 个单测：自己 / 跨学生 / 教师读学生 / 管理员读）
- [ ] 返回结构与 `api-doc.js §1.3` 一致 + 扩展字段对齐任务 2 的契约

---

# 任务 6：聊天消息 4 个接口

**ID**：A-03
**负责人**：A（你）
**状态**：⬜ 待开始
**依赖**：A-02
**优先级**：P1
**归属目录**：`backend/a_用户与聊天/`

> 注：聊天功能在挑战杯评分中**非核心**（用户体验 15 分中可由 D 的可视化承担），P1 即可，**不要影响地基与 WebSocket 进度**。

## 涉及文件
- `backend/a_用户与聊天/chat/{send,history,list,read}.py`
- `backend/a_用户与聊天/models/message.py`
- `backend/a_用户与聊天/tests/test_chat.py`

## 验收标准
- [ ] 4 个接口严格按 `api-doc.js §1.1`
- [ ] `POST /api/chat/send` 支持 `text / image / file` 3 种 type
- [ ] 单测覆盖分页、已读、type 枚举

---

# 任务 7：WebSocket 实时通道（**挑战杯核心，影响"可视化"15 分**）

**ID**：A-04
**负责人**：A（你）
**状态**：✅ 已完成（2026-08-12）
**依赖**：A-01
**优先级**：P0 ⭐（与 S-01 同优先级）
**归属目录**：`backend/a_用户与聊天/`

## 涉及文件
- `backend/a_用户与聊天/ws/server.py`（新建）
- `backend/a_用户与聊天/ws/handlers.py`（新建）
- `backend/a_用户与聊天/ws/events.py`（新建）— **挑战杯新增**：Agent 协同事件协议
- `backend/a_用户与聊天/tests/test_ws.py`（新建）

## 描述
实现 `ws://host/ws?token=xxx`，**重点支持多智能体协同过程实时推送**，是用户体验 15 分"协同过程可视化"的前端依赖通道。

## 验收标准（严格 - 夺奖关键）
- [ ] 连接握手校验 token，无效立即关闭（401）
- [ ] 客户端 `ping` → 服务端 30s 内回 `pong`（含超时测试）
- [ ] **Agent 协同事件协议**（这是挑战杯核心，前端可视化要靠它）：
  - 服务端推送 `agent.start` / `agent.thinking` / `agent.result` / `agent.debate` / `agent.final` 5 类事件
  - 事件 payload 含 `{agentName, step, content, timestamp, traceId}`
  - 客户端可订阅 `agent:<name>` 频道
- [ ] **断线重连**：服务端保留最近 50 条事件，新连接重放（前端刷新不丢可视化进度）
- [ ] 收到 `chat` 消息持久化并广播给 `targetId` 在线连接
- [ ] 客户端断线后服务端清理连接（5min 心跳超时）
- [ ] **单测 ≥ 8 用例**：握手 / 心跳 / 5 类事件 / 重连重放 / 断线清理 / 鉴权失败 / 频道订阅 / 跨用户隔离
- [ ] 用 `websockets` / `FastAPI WebSocket` 任一框架，自行记录选择到 `ws/README.md`

## 接口契约（前端必看）
```json
// 服务端 → 客户端
{"type":"agent.start",   "agentName":"学情诊断Agent", "step":1, "traceId":"t-001", "ts":1720000000}
{"type":"agent.thinking","agentName":"学情诊断Agent", "step":2, "content":"正在匹配知识盲区...", "traceId":"t-001", "ts":1720000001}
{"type":"agent.debate",  "agents":["领域专家Agent","审核裁判Agent"], "topic":"该知识点是否准确", "traceId":"t-001", "ts":1720000002}
{"type":"agent.result",  "agentName":"领域专家Agent", "step":3, "content":"...", "traceId":"t-001", "ts":1720000003}
{"type":"agent.final",   "ok":true, "traceId":"t-001", "ts":1720000004}
```

---

# 任务 8：3 项硬指标的工程化验证脚本（**夺奖前必跑**）

**ID**：A-05 ⭐ 夺奖专项
**负责人**：A（你）+ B/C/D 配合
**状态**：⬜ 待开始
**依赖**：所有 Agent 任务完成
**优先级**：P0
**归属目录**：`backend/公共/`

## 涉及文件
- `backend/公共/quality_check.py`（新建）— 端到端跑 3 项指标
- `backend/tests/test_quality_e2e.py`（新建）— e2e 验收测试

## 描述
**夺奖前最后一道关卡**。在提交作品（2026-09-05）前，必须用 B 准备的 ≥3 组测试画像，跑通 3 项指标，**全部达标**才提交。

## 验收标准（一票否决）
- [ ] `quality_check.py` 接受 `--profiles`（测试画像 JSON 路径）+ `--kb`（知识库路径）参数
- [ ] 跑完输出报告 `quality_report_{ts}.json`，含 3 项指标实际值 + 是否达标
- [ ] **3 项硬指标必须同时达标**：
  - 幻觉率 `< 0.05`
  - 画像-难度适配准确率 `≥ 0.85`
  - 核心知识点覆盖率 `≥ 0.90`
- [ ] **未达标 → 阻塞提交，必须迭代到达标为止**
- [ ] 报告归档到 `docs/quality_reports/`

---

## 你的交付物清单（提交前自检）

- [ ] S-01 / S-02 公共工具（带 3 项指标计算器）
- [ ] A-00 ~ A-05 全部 ✅
- [ ] `get_user_by_id` / `get_learner_profile` 模块级函数暴露
- [ ] WebSocket 5 类 Agent 事件协议稳定
- [ ] `quality_check.py` 跑通 3 项指标达标
- [ ] 你这部分的 `tests/` 覆盖率 ≥ 70%
