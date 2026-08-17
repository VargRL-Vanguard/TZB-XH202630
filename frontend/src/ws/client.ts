import { useAuthStore } from '@/stores/auth'
import { useAgentEventsStore } from '@/stores/agentEvents'

/**
 * WebSocket 统一客户端（08 号契约 §5）
 * - 连接 ws://host/ws?token=xxx
 * - 30s 心跳 ping
 * - 断线指数退避重连 1s/2s/4s…最大 30s，重连中页面顶部黄色横幅（NetBanner 监听 status）
 * - 收到未知 type 只 console.debug 不报错
 * - 乱序事件容错：agent.* 事件交由 agentEvents store 按 traceId 分组，不白屏
 * - 服务端 close 4401 / error 鉴权失败 → 清 token 跳登录（与 HTTP 401 同口径）
 */

export type WsStatus = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed'

export type WsPayload = Record<string, unknown>
type Handler = (payload: WsPayload) => void
type StatusHandler = (status: WsStatus) => void

const HEARTBEAT_MS = 30_000
const BASE_BACKOFF_MS = 1_000
const MAX_BACKOFF_MS = 30_000
/** 后端自定义鉴权失败关闭码（ws/server.py） */
const CLOSE_UNAUTHORIZED = 4401

/** 已知服务端事件类型（契约 §5.2/§5.3），其余按未知处理仅 console.debug */
const KNOWN_TYPES = new Set([
  'connected',
  'pong',
  'message',
  'chat',
  'notification',
  'ai_reply',
  'error',
  'agent.start',
  'agent.thinking',
  'agent.result',
  'agent.debate',
  'agent.final'
])

class WsClient {
  private ws: WebSocket | null = null
  private token = ''
  private status: WsStatus = 'idle'
  private retries = 0
  private manualClosed = false
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private handlers = new Map<string, Set<Handler>>()
  private statusHandlers = new Set<StatusHandler>()
  /** 已订阅频道，重连成功后自动补订 */
  private channels = new Set<string>()

  /** 建立连接（已连接时重复调用会先断开旧连接） */
  connect(token: string) {
    if (!token) return
    if (
      this.ws &&
      (this.status === 'open' || this.status === 'connecting') &&
      token === this.token
    ) {
      return
    }
    this.token = token
    this.manualClosed = false
    this.cleanupTimers()
    this.openSocket()
  }

  private openSocket() {
    this.setStatus(this.retries > 0 ? 'reconnecting' : 'connecting')
    const base = (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000').replace(/\/$/, '')
    const url = `${base.replace(/^http/, 'ws')}/ws?token=${encodeURIComponent(this.token)}`
    try {
      this.ws = new WebSocket(url)
    } catch (e) {
      console.debug('WS 创建失败', e)
      this.scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this.retries = 0
      this.setStatus('open')
      this.startHeartbeat()
      // 重连后补订频道（服务端连接维度订阅会随断线丢失）
      this.channels.forEach((ch) => this.rawSend({ type: 'subscribe', channel: ch }))
    }

    this.ws.onmessage = (ev: MessageEvent) => this.handleMessage(ev.data)

    this.ws.onclose = (ev: CloseEvent) => {
      this.stopHeartbeat()
      this.ws = null
      if (this.manualClosed) {
        this.setStatus('closed')
        return
      }
      if (ev.code === CLOSE_UNAUTHORIZED) {
        // token 无效/过期/黑名单：不重连，走统一登出
        this.triggerUnauthorized()
        this.setStatus('closed')
        return
      }
      this.scheduleReconnect()
    }

    this.ws.onerror = () => {
      // onclose 会随后触发，统一在 onclose 里处理重连
    }
  }

  /** 主动关闭（登出时调用），不再重连 */
  close() {
    this.manualClosed = true
    this.cleanupTimers()
    if (this.ws) {
      this.ws.close(1000, 'client logout')
      this.ws = null
    }
    this.setStatus('closed')
  }

  /** 当前是否可用 */
  get isOpen() {
    return !!this.ws && this.ws.readyState === WebSocket.OPEN
  }

  get currentStatus() {
    return this.status
  }

  // ============ 对外发送（契约 §5.1 四类，字段名一字不差） ============

  sendChat(targetId: string, content: string) {
    return this.rawSend({ type: 'chat', targetId, content })
  }

  subscribe(channel: string) {
    this.channels.add(channel)
    return this.rawSend({ type: 'subscribe', channel })
  }

  unsubscribe(channel: string) {
    this.channels.delete(channel)
    return this.rawSend({ type: 'unsubscribe', channel })
  }

  private rawSend(payload: WsPayload): boolean {
    if (!this.isOpen) return false
    this.ws!.send(JSON.stringify(payload))
    return true
  }

  // ============ 心跳 ============

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      // 契约格式：{ "type": "ping", "timestamp": 秒级 }
      this.rawSend({ type: 'ping', timestamp: Math.floor(Date.now() / 1000) })
    }, HEARTBEAT_MS)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  // ============ 重连（指数退避 1s/2s/4s…最大 30s） ============

  private scheduleReconnect() {
    if (this.manualClosed || this.reconnectTimer) return
    const delay = Math.min(BASE_BACKOFF_MS * 2 ** this.retries, MAX_BACKOFF_MS)
    this.retries += 1
    this.setStatus('reconnecting')
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.openSocket()
    }, delay)
  }

  private cleanupTimers() {
    this.stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  // ============ 收消息分发 ============

  private handleMessage(raw: unknown) {
    let msg: WsPayload
    try {
      msg = JSON.parse(String(raw)) as WsPayload
    } catch {
      console.debug('WS 收到非 JSON 消息', raw)
      return
    }
    const type = typeof msg.type === 'string' ? msg.type : ''

    if (!KNOWN_TYPES.has(type)) {
      // 夺奖红线：未知 type 只 console.debug，不许报错/白屏
      console.debug('WS 未知消息类型', msg)
      return
    }

    if (type.startsWith('agent.')) {
      // 5 类 Agent 事件 → store 按 traceId 分组（大屏与回放器共享）
      useAgentEventsStore().pushEvent({ ...msg, type })
      this.emit(type, msg)
      return
    }

    if (type === 'error') {
      const text = String(msg.message ?? '')
      if (/token|401|unauthorized|登录|鉴权/i.test(text)) {
        this.triggerUnauthorized()
        return
      }
      console.warn('WS error 事件', text)
      this.emit(type, msg)
      return
    }

    if (type === 'pong' || type === 'connected') {
      return
    }

    // message / chat / notification / ai_reply
    this.emit(type, msg)
  }

  private emit(type: string, payload: WsPayload) {
    this.handlers.get(type)?.forEach((fn) => {
      try {
        fn(payload)
      } catch (e) {
        console.warn(`WS 处理 ${type} 事件的监听器异常`, e)
      }
    })
  }

  // ============ 监听 ============

  on(type: string, fn: Handler) {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set())
    this.handlers.get(type)!.add(fn)
    return () => this.handlers.get(type)?.delete(fn)
  }

  onStatus(fn: StatusHandler) {
    this.statusHandlers.add(fn)
    fn(this.status)
    return () => this.statusHandlers.delete(fn)
  }

  private setStatus(s: WsStatus) {
    if (this.status === s) return
    this.status = s
    this.statusHandlers.forEach((fn) => fn(s))
  }

  private triggerUnauthorized() {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) return
    auth.logout()
    this.close()
    if (!window.location.hash.includes('/login')) {
      window.location.hash = '#/login'
    }
  }
}

/** 全局单例 */
export const wsClient = new WsClient()
