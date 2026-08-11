# A-04 WebSocket 实时通道 - 技术选型

> **任务**：A-04 WebSocket 实时通道（**挑战杯核心**，影响"可视化"15 分）
> **负责人**：A（成员 1）
> **选型日期**：2026-08-12

## 选型对比

| 维度 | FastAPI WebSocket ✅ | 裸 `websockets` 库 |
|---|---|---|
| **与 REST 共进程** | ✅ 同一个 FastAPI app，鉴权/日志/异常处理复用 | ❌ 单独跑一个端口，需手动桥接 |
| **JWT 鉴权共享** | ✅ 直接 import `decode_access_token` | ❌ 要么重复实现，要么桥接 |
| **依赖项** | ✅ FastAPI 自带 | ❌ 要再加 `websockets` 单独管理 |
| **异步支持** | ✅ 天然 async | ✅ |
| **高并发** | ⚠️ 单 worker 受 GIL 限制（要扩展用 uvicorn workers） | ⚠️ 同样 |
| **学习曲线** | ✅ 已在 S-01 用 FastAPI | ❌ 新概念 |
| **比赛适用度** | ✅ 5min 写完握手，主逻辑在 handlers | ⚠️ 多 30% 模板代码 |

## 选型结论

**选 FastAPI WebSocket**。

理由：
1. 复用 S-01 已搭的 FastAPI 进程
2. 复用 A-01 的 JWT 鉴权（`decode_access_token`）
3. 与 REST 接口统一部署、监控、日志
4. 比赛演示 5min 即可启动，不需要多进程

## 关键设计

### 1. 事件协议（5 类，前端必看）

```
agent.start    → "学情诊断Agent 启动"
agent.thinking → "正在匹配知识盲区..." （可多次）
agent.result   → "{...结构化结果...}"
agent.debate   → ["领域专家Agent", "审核裁判Agent"] 围绕 "该知识点是否准确"
agent.final    → ok=true, "协同完成"
```

前端通过 `subscribe channel="agent:学情诊断Agent"` 订阅。

### 2. 断线重连重放

服务端用 `deque(maxlen=50)` 维护最近 50 条事件，新连接建立时自动重放。

**效果**：前端刷新页面 / 网络抖动重连，可补回可视化进度。

### 3. 心跳超时清理

- 客户端每 30s 发 `{"type": "ping"}`
- 服务端更新 `last_ping` 时间戳
- 后台任务每 60s 检查一次，>5min 无 ping → close + 清理

### 4. 多 Agent 频道

频道名格式：`agent:<agent_name>`，例如 `agent:学情诊断Agent`。

**B/C/D 推事件用法**：

```python
from backend.a_用户与聊天.ws.manager import connection_manager

# 给"学情诊断Agent"频道所有订阅者推事件
await connection_manager.record_event(event_dict)  # 计入缓冲（重放用）
await connection_manager.broadcast_to_channel(
    channel="agent:学情诊断Agent",
    event=event_dict,
)
```

## 已知限制 / 后续优化

- ❌ 单进程（uvicorn 1 worker），高并发需多 worker
- ❌ 事件缓冲在内存，重启丢；生产可换 Redis Stream
- ❌ 没用 WSS（生产必须配 Nginx + TLS）

## 接口契约

| 端点 | 方法 | 鉴权 | 用途 |
|---|---|---|---|
| `/ws?token=xxx` | WebSocket | 必填 query token | 实时通道 |
