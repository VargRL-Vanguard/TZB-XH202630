# 工作流程 08：WebSocket 接入流程（**A-04 专用 + B/C/D 接入**）

> A-04 负责**建通道**；B / C / D 负责**接通道**。本流程定义两边。
> 5 类事件（agent.start / thinking / result / debate / final）是**夺奖可视化核心**。

---

## A 区侧：建通道（A-04 任务）

### 步骤 A1：创建连接管理器

**输入**：`fastapi` / `flask-socketio` 等 WebSocket 框架

**操作**：`backend/a_用户与聊天/ws/manager.py`
```python
class WSManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
    
    async def connect(self, userId: str, ws: WebSocket):
        await ws.accept()
        self.connections[userId] = ws
    
    def disconnect(self, userId: str):
        self.connections.pop(userId, None)
    
    async def send_to_user(self, userId: str, event: dict):
        ws = self.connections.get(userId)
        if ws:
            await ws.send_json(event)

manager = WSManager()
```

**输出**：1 个连接管理器

**验证**：
- [ ] 两个客户端连同一 userId → 后者覆盖前者（**不要**两个并存）
- [ ] 断开后能清理

---

### 步骤 A2：暴露 5 类事件发送函数

**输入**：manager 实例

**操作**：`backend/a_用户与聊天/ws/emit.py`
```python
from backend.a_用户与聊天.ws.manager import manager
import json
from datetime import datetime

def emit_agent_start(traceId, agentName, step, payload):
    return _emit("agent.start", traceId, agentName, step, payload)

def emit_agent_thinking(traceId, agentName, step, content):
    return _emit("agent.thinking", traceId, agentName, step, content)

def emit_agent_result(traceId, agentName, step, content):
    return _emit("agent.result", traceId, agentName, step, content)

def emit_agent_debate(traceId, agents, topic):
    return _emit("agent.debate", traceId, "debate", "topic", {"agents": agents, "topic": topic})

def emit_agent_final(traceId, ok, summary=None):
    return _emit("agent.final", traceId, "orchestrator", "final", {"ok": ok, "summary": summary})

def _emit(event_type, traceId, agentName, step, payload):
    event = {
        "type": event_type,
        "traceId": traceId,
        "agentName": agentName,
        "step": step,
        "payload": payload,
        "ts": datetime.utcnow().isoformat(),
    }
    # 1. 推 WebSocket（发给当前连上的客户端）
    # 2. 落 event_store（Redis），用于断线重连回放
    # 3. 落 agent_log（D 区表）
    return event
```

**输出**：5 个公开函数 + 1 个内部 `_emit`

**验证**：
- [ ] B / C / D 都能 `from backend.a_用户与聊天.ws.emit import emit_agent_xxx`
- [ ] 每条事件都有 type / traceId / agentName / ts

---

### 步骤 A3：WebSocket 端点

**输入**：manager + emit

**操作**：`backend/a_用户与聊天/ws/router.py`
```python
@router.websocket("/ws/{userId}")
async def websocket_endpoint(ws: WebSocket, userId: str):
    await manager.connect(userId, ws)
    try:
        # 客户端发任何消息都视为心跳
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(userId)
```

**输出**：1 个 WS 端点 `/ws/{userId}`

**验证**：
- [ ] 前端 `new WebSocket("ws://localhost:8000/ws/user_001")` 能连
- [ ] 服务端推事件 → 前端 `ws.onmessage` 能收到

---

### 步骤 A4：断线重连事件回放

**输入**：步骤 A3

**操作**：`backend/a_用户与聊天/ws/event_store.py`（用 Redis）
```python
# key: traceId
# value: List[event]
def store_event(traceId, event):
    redis.lpush(f"ws:events:{traceId}", json.dumps(event))
    redis.ltrim(f"ws:events:{traceId}", 0, 99)  # 只保留最近 100 条
    redis.expire(f"ws:events:{traceId}", 3600)  # 1 小时过期

def replay_events(traceId, ws):
    events = redis.lrange(f"ws:events:{traceId}", 0, -1)
    for e in events:
        ws.send_json(json.loads(e))
```

**输出**：1 个事件存储 + 1 个回放函数

**验证**：
- [ ] 客户端断线 → 重连 → 带 `?replay=traceId` → 服务端回放最近事件

---

## B / C / D 侧：接通道（B-05 / C-04 / D-06 任务）

### 步骤 B1：每个 Agent 入口都调 emit

**输入**：A-04 已就绪

**操作**：在 B-05 / C-04 / D-06 的**每个函数入口**都加：
```python
from backend.a_用户与聊天.ws.emit import (
    emit_agent_start, emit_agent_thinking, emit_agent_result
)
```

**输出**：所有 Agent 都能推事件

**验证**：
- [ ] 跑一次 orchestrate → agent_log 表有所有事件
- [ ] 前端能看到完整事件流

---

### 步骤 B2：在关键步骤加 thinking 事件

**输入**：Agent 内部步骤

**操作**：在每个 Agent 的**关键步骤**（数据加载、LLM 调用、解析、metrics 检查）后都加 emit_agent_thinking

**输出**：前端能看到 Agent 的"思考过程"

**验证**：
- [ ] 前端 UI 能展示"Agent 正在思考 XXX..."

---

### 步骤 B3：落 agent_log（D 区函数）

**输入**：D-00 已就绪

**操作**：每个 Agent 在 `emit_agent_result` 之后调：
```python
from backend.d_AI集成.models.agent_log import log_agent_event
log_agent_event(traceId, agentName, "result", result.dict())
```

**输出**：agent_log 表有所有事件

**验证**：
- [ ] `SELECT COUNT(*) FROM agent_log WHERE traceId = 'xxx'` ≥ 3（至少 3 个 Agent）

---

## WebSocket 接入验收清单

### A 区
- [ ] 步骤 A1：WSManager 单例
- [ ] 步骤 A2：5 类事件函数齐全
- [ ] 步骤 A3：WS 端点可连
- [ ] 步骤 A4：断线重连能回放

### B / C / D
- [ ] 步骤 B1：每个 Agent 入口都 emit
- [ ] 步骤 B2：关键步骤都 thinking
- [ ] 步骤 B3：每个 Agent 都落 agent_log

**A + B/C/D 全过 = 实时可视化通道就绪**
