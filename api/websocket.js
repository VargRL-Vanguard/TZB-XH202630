/**
 * WebSocket模块
 * 用于实时消息推送，实现聊天消息的即时接收
 * 
 * 后端WebSocket接口说明：
 * - 连接地址: ws://localhost:3000/ws (开发环境)
 * - 连接时需携带认证信息（通过URL参数或header）
 * - 心跳机制: 客户端每30秒发送ping，服务端回复pong
 * 
 * 消息格式：
 * 
 * 客户端发送消息：
 * {
 *   type: 'message',      // 消息类型
 *   userId: 'user_001',   // 当前用户ID
 *   targetId: 'user_002', // 聊天对象ID
 *   content: '消息内容',  // 消息内容
 *   timestamp: 1234567890 // 时间戳
 * }
 * 
 * 服务端推送消息：
 * {
 *   type: 'message',      // 消息类型
 *   data: {
 *     id: 'msg_001',      // 消息ID
 *     content: '消息内容', // 消息内容
 *     senderId: 'user_002',// 发送者ID
 *     receiverId: 'user_001',// 接收者ID
 *     isSent: false,      // 是否为我方发送
 *     timestamp: 1234567890, // 时间戳
 *     avatar: '头像URL'   // 头像URL（对方消息才有）
 *   }
 * }
 * 
 * 系统消息：
 * {
 *   type: 'system',
 *   code: 'ONLINE_STATUS', // 系统消息类型
 *   data: {
 *     userId: 'user_002',
 *     status: 'online'     // online/offline/away
 *   }
 * }
 */

import { getBaseURL } from './config.js';
import { getAuthToken } from './request.js';

/**
 * WebSocket客户端类
 */
export class WebSocketClient {
    constructor() {
        this.socket = null;
        this.url = this.getWebSocketURL();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000; // 重连延迟（毫秒）
        this.heartbeatInterval = 30000; // 心跳间隔（毫秒）
        this.heartbeatTimer = null;
        
        // 事件回调
        this.callbacks = {
            onMessage: null,      // 收到消息
            onConnect: null,      // 连接成功
            onDisconnect: null,   // 断开连接
            onError: null,        // 发生错误
            onSystem: null        // 系统消息
        };
    }

    /**
     * 获取WebSocket连接URL
     * @returns {string} WebSocket URL
     */
    getWebSocketURL() {
        const baseURL = getBaseURL();
        // 将HTTP协议转换为WebSocket协议
        const wsProtocol = baseURL.startsWith('https') ? 'wss' : 'ws';
        const wsHost = baseURL.replace(/^https?:\/\//, '');
        const token = getAuthToken();
        
        // 构建WebSocket URL，携带Token
        return `${wsProtocol}://${wsHost}/ws${token ? `?token=${token}` : ''}`;
    }

    /**
     * 连接WebSocket
     */
    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.socket = new WebSocket(this.url);
                
                // 连接成功
                this.socket.onopen = (event) => {
                    console.log('WebSocket连接成功');
                    this.reconnectAttempts = 0;
                    this.startHeartbeat();
                    
                    if (this.callbacks.onConnect) {
                        this.callbacks.onConnect(event);
                    }
                    
                    resolve(event);
                };
                
                // 收到消息
                this.socket.onmessage = (event) => {
                    this.handleMessage(event);
                };
                
                // 连接关闭
                this.socket.onclose = (event) => {
                    console.log('WebSocket连接关闭:', event);
                    this.stopHeartbeat();
                    
                    if (this.callbacks.onDisconnect) {
                        this.callbacks.onDisconnect(event);
                    }
                    
                    // 自动重连
                    this.autoReconnect();
                };
                
                // 连接错误
                this.socket.onerror = (error) => {
                    console.error('WebSocket错误:', error);
                    this.stopHeartbeat();
                    
                    if (this.callbacks.onError) {
                        this.callbacks.onError(error);
                    }
                    
                    reject(error);
                };
                
            } catch (error) {
                console.error('WebSocket连接失败:', error);
                reject(error);
            }
        });
    }

    /**
     * 断开连接
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.stopHeartbeat();
        }
    }

    /**
     * 发送消息
     * @param {object} message - 消息对象
     * @param {string} message.type - 消息类型
     * @param {string} message.userId - 用户ID
     * @param {string} message.targetId - 目标ID
     * @param {string} message.content - 消息内容
     */
    send(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('发送消息失败:', error);
                return false;
            }
        }
        return false;
    }

    /**
     * 发送聊天消息
     * @param {string} userId - 当前用户ID
     * @param {string} targetId - 聊天对象ID
     * @param {string} content - 消息内容
     */
    sendChatMessage(userId, targetId, content) {
        return this.send({
            type: 'message',
            userId,
            targetId,
            content,
            timestamp: Date.now()
        });
    }

    /**
     * 处理收到的消息
     * @param {MessageEvent} event - 消息事件
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'message':
                    // 聊天消息
                    if (this.callbacks.onMessage) {
                        this.callbacks.onMessage(data.data);
                    }
                    break;
                    
                case 'system':
                    // 系统消息
                    if (this.callbacks.onSystem) {
                        this.callbacks.onSystem(data);
                    }
                    break;
                    
                case 'pong':
                    // 心跳响应
                    break;
                    
                default:
                    console.warn('未知消息类型:', data.type);
            }
        } catch (error) {
            console.error('解析消息失败:', error);
        }
    }

    /**
     * 启动心跳
     */
    startHeartbeat() {
        this.stopHeartbeat();
        
        this.heartbeatTimer = setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.send({
                    type: 'ping',
                    timestamp: Date.now()
                });
            }
        }, this.heartbeatInterval);
    }

    /**
     * 停止心跳
     */
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * 自动重连
     */
    autoReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
            
            console.log(`WebSocket重连尝试 ${this.reconnectAttempts}/${this.maxReconnectAttempts}，延迟 ${delay}ms`);
            
            setTimeout(() => {
                this.connect().catch(() => {
                    // 重连失败，继续尝试
                });
            }, delay);
        } else {
            console.error('WebSocket重连次数已达上限');
        }
    }

    /**
     * 设置事件回调
     * @param {string} eventName - 事件名称
     * @param {function} callback - 回调函数
     */
    on(eventName, callback) {
        if (this.callbacks[eventName]) {
            this.callbacks[eventName] = callback;
        }
    }

    /**
     * 获取连接状态
     * @returns {number} WebSocket状态码
     */
    getReadyState() {
        return this.socket ? this.socket.readyState : WebSocket.CLOSED;
    }

    /**
     * 检查是否已连接
     * @returns {boolean} 是否已连接
     */
    isConnected() {
        return this.socket && this.socket.readyState === WebSocket.OPEN;
    }
}

// 创建全局WebSocket实例
let instance = null;

/**
 * 获取WebSocket实例（单例模式）
 * @returns {WebSocketClient} WebSocket客户端实例
 */
export function getWebSocketInstance() {
    if (!instance) {
        instance = new WebSocketClient();
    }
    return instance;
}

// 导出WebSocket客户端
export default {
    WebSocketClient,
    getWebSocketInstance
};