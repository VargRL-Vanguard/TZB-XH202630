# A 区对 B / C / D 对接契约（一站式手册）

> **目标读者**：B（学情数据）、C（学习内容）、D（AI 集成）三个区的开发者
>
> **维护者**：A（用户与聊天）
>
> **更新规则**：A 区任何对外接口（HTTP 路由、对外函数、WS 事件协议、metrics 签名）发生变更，**必须**同步更新本文档并在群里通知 B/C/D。

---

## 0. 速查表

| 需求 | 调什么 | 入口模块 |
|------|--------|----------|
| 拿当前登录用户 + 画像 | `Depends(get_current_user)` | `backend.公共.auth_middleware` |
| 路由必须登录 | `dependencies=[Depends(require_auth)]` | 同上 |
| 路由必须指定角色 | `dependencies=[Depends(require_role("admin"))]` | 同上 |
| 按 userId 查用户 | `await get_user_by_id("u001")` | `backend.a_用户与聊天` |
| 按 userId 查画像 | `await get_learner_profile("u001")` | `backend.a_用户与聊天` |
| 回写画像（学情诊断后） | `await upsert_learner_profile("u001", weak_kps=[...])` | `backend.a_用户与聊天.db` |
| 推 Agent 事件给前端 | `await connection_manager.broadcast_to_channel(...)` | `backend.a_用户与聊天.ws.manager` |
| 算 3 项硬指标 | `metrics.calc_hallucination_rate(...)` 等 | `backend.公共.metrics` |
| 统一成功响应 | `return ok(data=...)` | `backend.公共.response` |
| 抛业务异常 | `raise AuthError(...)` / `raise ForbiddenError(...)` | `backend.公共.errors` |
| 写 A 区的 DB | `async with get_session() as session:` | `backend.a_用户与聊天.db` |

---

## 1. 鉴权中间件（`S-02`）

**位置**：`backend.公共.auth_middleware.py`

### 1.1 `get_current_user` — 注入当前用户

```python
from fastapi import Depends
from backend.公共.auth_middleware import get_current_user

@router.get("/api/some_resource")
async def some_handler(user: dict = Depends(get_current_user)):
    user_id = user["userId"]
    role    = user["role"]
    # user["learnerProfile"] 可能是 None（老师/管理员/无画像学生）
```

**返回结构契约**（A 区写、B/C/D **必须按此读取**，否则会出问题）：

```python
{
  "userId": "u001",        # str
  "name":   "张三",         # str
  "role":   "student",     # "student" | "teacher" | "admin"
  "learnerProfile": {      # dict 或 None
    "education":       "本科",
    "theoryTestScore": 78,
    "weakKPs":         ["kp12", "kp15"],
    "strongKPs":       ["kp03"]
  }
}
```

⚠️ **不要假设 learnerProfile 一定有**。**必须**这样写：

```python
profile = user.get("learnerProfile")  # 可能为 None
if profile is None:
    # 老师/管理员/无画像学生分支
    ...
else:
    weak_kps = profile["weakKPs"]
```

### 1.2 `@require_auth` — 路由必须登录

```python
from backend.公共.auth_middleware import require_auth

@router.get("/api/protected", dependencies=[Depends(require_auth)])
async def protected():
    return {"ok": True}
```

### 1.3 `@require_role` — 路由必须指定角色（**工厂**）

```python
from backend.公共.auth_middleware import require_role

# 单角色
@router.post("/api/admin/x", dependencies=[Depends(require_role("admin"))])

# 多角色（任一即可）
@router.post("/api/teacher-or-admin", dependencies=[Depends(require_role("teacher", "admin"))])
```

### 1.4 失败码（**HTTP 状态码 = 业务码**）

| 异常 | HTTP | 含义 |
|------|------|------|
| `AuthError` | 401 | 缺 token / 过期 / 伪造 / 已登出 / 格式错 |
| `ForbiddenError` | 403 | 已登录但角色不符 |

> 前端按 HTTP 状态码处理；B/C/D 调中间件时不用自己 try AuthError，会被全局 handler 转 JSON。

### 1.5 已知坑

1. **`Authorization` 头必须 `Bearer` 开头**，大小写不敏感但必须有 `Bearer ` 前缀。
2. **不要自己解 JWT**，让中间件做 — 里面还做了黑名单 + 画像合并。
3. **老师/管理员 `learnerProfile` 永远是 None**，别忘了 `if profile is None` 判空。

---

## 2. A 区业务函数（数据访问）

**位置**：`backend.a_用户与聊天.db` / `backend.a_用户与聊天`

### 2.1 `get_user_by_id`

```python
from backend.a_用户与聊天 import get_user_by_id

user = await get_user_by_id("u001")
# -> {"userId": "u001", "name": "张三", "role": "student"} 或 None
```

### 2.2 `get_learner_profile`（**学情诊断 Agent 唯一输入**）

```python
from backend.a_用户与聊天 import get_learner_profile

profile = await get_learner_profile("u001")
# -> {
#      "education": "本科",
#      "major":     "机械工程",
#      "theoryTestScore": 78,
#      "weakKPs":   ["kp12", "kp15"],
#      "strongKPs": ["kp03", "kp07"],
#      "updatedAt": "2026-08-12T10:00:00"
#    } 或 None
```

### 2.3 `upsert_learner_profile`（**学情诊断后回写**）

```python
from backend.a_用户与聊天.db import upsert_learner_profile

result = await upsert_learner_profile(
    user_id="u001",
    weak_kps=["kp12", "kp15", "kp18"],     # 任意字段可选
    strong_kps=["kp03"],
    theory_test_score=80,
    # education=..., major=...   # 这些也能改
)
# result 字段同 get_learner_profile
```

⚠️ **坑**：传入 `None` 的字段**不更新**（保留旧值）。要"清空"传 `[]` / `0` / `""`。

### 2.4 `get_session`（**B/C/D 调 A 区 DB 唯一合法入口**）

```python
from backend.a_用户与聊天.db import get_session

async with get_session() as session:
    # 用 SQLAlchemy 2.0 async 风格
    result = await session.execute(select(MyModel).where(...))
    rows = result.scalars().all()
```

**禁止**：
- ❌ `from backend.a_用户与聊天.db import engine` 然后自己 `AsyncSession(engine)`
- ❌ `from backend.a_用户与聊天.models import Message`（直接读模型）— 应通过函数层
- ❌ B 区创建自己的表指向 A 的库（隔离归 A，B 自己开库）

---

## 3. WebSocket Agent 事件通道（`A-04`）

**位置**：`backend.a_用户与聊天.ws.manager`、`backend.a_用户与聊天.ws.events`

### 3.1 B/C/D 推事件

```python
from backend.a_用户与聊天.ws.manager import connection_manager
from backend.a_用户与聊天.ws.events import AgentEventType
import time

# 1) 广播到频道（所有订阅者收到）
await connection_manager.broadcast_to_channel(
    channel="agent:学情诊断Agent",
    event={
        "type":       AgentEventType.THINKING.value,  # "agent.thinking"
        "agentName":  "学情诊断Agent",
        "step":       1,
        "content":    "正在匹配知识盲区...",
        "traceId":    "trace-2026-08-15-001",
        "timestamp":  time.time(),
    },
)

# 2) 推给指定用户
await connection_manager.send_to_user(
    user_id="u001",
    event={"type": "chat", "data": {...}},
)
```

### 3.2 5 类事件（**前端可视化状态机必看**）

| 事件 type | 何时发 | 关键字段 |
|-----------|--------|----------|
| `agent.start` | Agent 开始工作 | `agentName`, `step`, `traceId` |
| `agent.thinking` | Agent 思考中（可多次） | `agentName`, `step`, `content` |
| `agent.result` | Agent 输出结果 | `agentName`, `step`, `content`, `data` |
| `agent.debate` | 多 Agent 辩论 | `agents[]`, `topic`, `content` |
| `agent.final` | 协同结束 | `ok`, `summary`, `traceId` |

**典型事件流**：
```
agent.start → agent.thinking (N次) → agent.result → agent.debate (可选) → agent.final
```

### 3.3 频道命名约定

- 前缀：`agent:`
- 示例：`agent:学情诊断Agent`、`agent:资源匹配Agent`、`agent:路径规划Agent`
- 客户端订阅：`{"type": "subscribe", "channel": "agent:学情诊断Agent"}`

### 3.4 已知坑

1. **同一 traceId 的事件发给同一频道**，前端按 traceId 串成一次协同会话。
2. **断线重连会重放最近 50 条**事件，所以不要担心临时掉线。
3. **如果用户没订阅频道，`broadcast_to_channel` 返回 0**，不报错，正常。

---

## 4. 3 项硬指标（`S-01`，B/C/D **禁止重写**）

**位置**：`backend.公共.metrics`

```python
from backend.公共 import metrics

# 1. 幻觉率（越小越好，< 0.05 达标）
hr = metrics.calc_hallucination_rate(
    generated="生成的资源文本...",
    ground_truth=["知识库切片1", "知识库切片2"],
)

# 2. 画像-难度适配准确率（越大越好，≥ 0.85 达标）
# 单次返回 0/1，多组调用方聚合后除以总数
ma = metrics.calc_match_accuracy(
    profile={"expected": {"recommendedDifficulty": 3}},
    resource_difficulty=3,
)

# 3. 核心知识点覆盖率（越大越好，≥ 0.90 达标）
cov = metrics.calc_coverage(
    generated={"kp_coverage": ["kp12", "kp15"]},  # dict 形式
    # 或 generated=["kp12", "kp15"],              # list 形式
    required_kps=["kp12", "kp15", "kp18"],
)
```

⚠️ **A-05 端到端验收时**，B/C/D 必须能被 `公共/quality_check.py` 自动跑这 3 项达标。

---

## 5. 统一响应 / 异常

### 5.1 响应格式（**所有 A 区 API 都用**）

```json
{ "code": 200, "message": "ok", "data": { ... } }
```

```python
from backend.公共.response import ok, fail

return ok(data={"id": 1}, message="已发送")
return fail(code=400, message="参数错误", data={"field": "userId"})
```

### 5.2 异常类（**A 区、B/C/D 也可用**）

```python
from backend.公共.errors import (
    BizError,         # 基类 400
    AuthError,        # 401 鉴权失败
    ForbiddenError,   # 403 越权
    NotFoundError,    # 404 不存在
    AgentError,       # 500 Agent 调度失败
    QualityError,     # 422 硬指标不达标
)

raise AuthError("token 过期")
raise ForbiddenError("无权访问他人")
raise NotFoundError(f"用户 {user_id} 不存在")
```

全局 handler 会自动把异常转成上面的 JSON 响应，**B/C/D 直接 raise 即可**。

---

## 6. HTTP API 速查（A 区暴露的所有路由）

| 方法 | 路径 | 用途 | 鉴权 |
|------|------|------|------|
| POST | `/api/auth/register` | 注册 | 无 |
| POST | `/api/auth/login` | 登录 | 无 |
| POST | `/api/auth/logout` | 登出 | 登录 |
| GET  | `/api/user/info?userId=` | 读用户+画像 | 登录（越权规则见下） |
| PUT  | `/api/user/profile` | 更新画像 | 登录（越权规则见下） |
| POST | `/api/chat/send` | 发消息 | 登录 |
| GET  | `/api/chat/history?userId=&targetId=&limit=&offset=` | 历史 | 登录 |
| GET  | `/api/chat/list?userId=` | 会话列表 | 登录 |
| POST | `/api/chat/read` | 标已读 | 登录 |
| WS   | `/ws?token=` | 实时通道 | token 握手 |

### 6.1 `/api/user/info` 越权规则

| 调用方 | target = 自己 | target = 他人 |
|--------|---------------|---------------|
| student | ✅ 200 | ❌ 403 |
| teacher | ✅ 200 | ✅ 200 |
| admin | ✅ 200 | ✅ 200 |

### 6.2 `PUT /api/user/profile` 越权规则

- `student` → 只能改自己（body 不传 userId）
- `teacher` / `admin` → 可指定 query `?userId=xxx` 改任意人
- 不存在的 userId → 404

### 6.3 聊天 userId 规则（**重要**）

所有 `/api/chat/*` 接口的 `userId` 字段**必须等于当前登录用户**，否则 400（防冒用身份）。`teacher` / `admin` 例外。

---

## 7. 数据库与初始化

### 7.1 A 区自有数据库

- **库名**：`tzb_user_chat`（环境变量 `USER_CHAT_DB_URL` 配置）
- **驱动**：`mysql+aiomysql`
- **B/C/D 不允许直连**，只能通过 `get_session()` 共享 session。

### 7.2 启动顺序（新机器部署）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配 .env（参考 .env.example）
cp .env.example .env
# 编辑 USER_CHAT_DB_URL / JWT_SECRET

# 3. 建库 + 建表
python -m backend.a_用户与聊天.init_db

# 4. 灌种子数据（4 个测试账号）
python -m backend.a_用户与聊天.seed_data

# 5. 启动
uvicorn backend.main:app --reload --port 8000
```

### 7.3 测试账号

| userId | username | password | role | 画像 |
|--------|----------|----------|------|------|
| u001 | student001 | Test@1234 | student | ✅ |
| u002 | student002 | Test@1234 | student | ✅ |
| t001 | teacher001 | Test@1234 | teacher | — |
| a001 | admin001 | Test@1234 | admin | — |

---

## 8. 常见问题（FAQ）

### Q1: `learnerProfile` 字段都有哪些？找不到字段怎么办？
A: 严格按 [§1.1 返回结构契约](#11-get_current_user--注入当前用户)。**没有** `major` 字段在 `learnerProfile` 里（要查画像详细信息用 `get_learner_profile`）。

### Q2: 我能在 B 区创建一个新表指向 A 的库吗？
A: **不能**。B 区用自己独立的库（`tzb_student_data`），跨区只走函数。

### Q3: WS 推事件给"不在线的用户"会怎样？
A: 不会保存离线消息。`send_to_user` 直接返回 0，B/C/D 应保证用户**在线**（agent 处理时让用户保持 WS 连接）。

### Q4: 我在 B 区想读自己创建的资源，能用 A 的 `get_session` 吗？
A: 不能。B 区用 B 自己的 session（`from backend.b_学情数据.db import get_session`）。A 的 `get_session` 只对 A 的库有效。

### Q5: 硬指标在 B 区 / C 区算都行吗？
A: 都可以，但**结果必须 3 项都达标**（A-05 会端到端校验）。建议在 B 的学情诊断后、C 的资源生成后**都算一遍**做 early check。

### Q6: token 多久过期？
A: 默认 7 天（`JWT_EXPIRE_HOURS=168`），在 `.env` 配。

### Q7: 我能用 `sub` 字段当 userId 吗？
A: `S-02` 新中间件返回的是 `userId` 字段（不是 JWT 的 `sub`）。**A-02 老路由**（`/api/user/info`）内部可能用 `sub`，但 B/C/D 调新中间件都用 `userId`。

---

## 9. 变更日志

| 日期 | 变更 | 影响 |
|------|------|------|
| 2026-08-12 | 新增 A-02 越权 + 画像读写 | B-05 学情诊断可读 / 回写 |
| 2026-08-12 | 新增 S-02 统一鉴权 | B/C/D **所有**业务接口必须用 |
| 2026-08-12 | 新增 A-03 聊天 4 接口 | 挑战杯非核心，可不接 |
| 2026-08-12 | 5 类 Agent WS 事件协议 | B-05/C-04/D-03 必须用 |

---

## 10. 联系 / 反馈

A 区（你）→ 在群里 @ 我，或者在 PR 中 @ 评审人。
