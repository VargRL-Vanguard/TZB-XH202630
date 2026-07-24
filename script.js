/**
 * 聊天消息管理模块
 * 
 * 前端预留的API接口说明：
 * - 当前模块已预留完整的后端API调用接口
 * - 后端开发人员需要实现以下接口：
 *   1. GET /api/chat/history - 获取聊天历史
 *   2. POST /api/chat/send - 发送消息
 *   3. GET /api/user/info - 获取用户信息
 *   4. GET /api/chat/list - 获取聊天列表
 *   5. POST /api/chat/read - 标记消息已读
 * 
 * - 详细接口文档请查看 api/chat.js 文件
 * - API基础配置请修改 api/config.js 文件
 * 
 * 注：当前使用Mock数据作为fallback，后端接口就绪后可启用真实API
 */

// 静态导入API模块
import { getChatHistory, sendMessage as apiSendMessage, getUserInfo } from './api/chat.js';
import { getWebSocketInstance } from './api/websocket.js';

// 模块配置
const CONFIG = {
    // 是否启用真实API（后端接口就绪后改为true）
    useRealAPI: false,
    // 当前用户ID（后端对接时从登录态获取）
    currentUserId: 'user_001',
    // 聊天对象ID
    targetUserId: 'user_002',
    // 聊天对象名称
    targetUserName: '张三'
};

/**
 * Mock数据模拟（用于前端开发和测试）
 * 后端接口就绪后可删除或保留作为fallback
 */
const MOCK_DATA = {
    // 模拟聊天历史
    history: [
        {
            id: 'msg_001',
            content: '你好！',
            senderId: 'user_002',
            receiverId: 'user_001',
            isSent: false,
            timestamp: Date.now() - 3600000,
            avatar: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MCA0MCI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjOUI5QjlCIi8+PHBhdGggZD0iTTIwIDEwYzUuNSAwIDEwIDQuNSAxMCAxMHMtNC41IDEwLTEwIDEwLTEwLTQuNS0xMC0xMCA0LjUtMTAgMTAtMTBtMCAxNmMtMy4zIDAtNi0yLjctNi02IDAtMy4zIDIuNy02IDYtNiA2IDAgMy4zIDIuNyA2IDYgNi0zLjMgNi02IDYtNiIvPjwvc3ZnPg=='
        },
        {
            id: 'msg_002',
            content: '你好，有什么事吗？',
            senderId: 'user_001',
            receiverId: 'user_002',
            isSent: true,
            timestamp: Date.now() - 3500000
        },
        {
            id: 'msg_003',
            content: '周末有空吗？想约你一起吃饭',
            senderId: 'user_002',
            receiverId: 'user_001',
            isSent: false,
            timestamp: Date.now() - 3400000,
            avatar: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MCA0MCI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjOUI5QjlCIi8+PHBhdGggZD0iTTIwIDEwYzUuNSAwIDEwIDQuNSAxMCAxMHMtNC41IDEwLTEwIDEwLTEwLTQuNS0xMC0xMCA0LjUtMTAgMTAtMTBtMCAxNmMtMy4zIDAtNi0yLjctNi02IDAtMy4zIDIuNy02IDYtNiA2IDAgMy4zIDIuNyA2IDYgNi0zLjMgNi02IDYtNiIvPjwvc3ZnPg=='
        }
    ],
    // 模拟对方回复
    replies: [
        '好的，收到！',
        '嗯嗯，我知道了',
        '没问题',
        '等一下，我看看',
        '好的，那我们周末见',
        '谢谢你的消息',
        '明白了，我会处理的',
        '可以啊，什么时候？',
        '好的，我记下了',
        '收到，稍后回复你'
    ],
    // 模拟用户信息
    userInfo: {
        id: 'user_002',
        name: '张三',
        avatar: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MCA0MCI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjOUI5QjlCIi8+PHBhdGggZD0iTTIwIDEwYzUuNSAwIDEwIDQuNSAxMCAxMHMtNC41IDEwLTEwIDEwLTEwLTQuNS0xMC0xMCA0LjUtMTAgMTAtMTBtMCAxNmMtMy4zIDAtNi0yLjctNi02IDAtMy4zIDIuNy02IDYtNiA2IDAgMy4zIDIuNyA2IDYgNi0zLjMgNi02IDYtNiIvPjwvc3ZnPg==',
        status: 'online'
    }
};

/**
 * 获取当前时间格式化字符串
 * @returns {string} HH:mm 格式的时间字符串
 */
function getCurrentTime(timestamp = Date.now()) {
    const date = new Date(timestamp);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * 创建消息元素
 * @param {object} message - 消息数据对象
 * @param {string} message.content - 消息内容
 * @param {boolean} message.isSent - 是否为我方发送
 * @param {string} message.avatar - 头像URL（可选）
 * @param {number} message.timestamp - 时间戳（可选）
 * @returns {HTMLElement} 消息元素
 */
function createMessageElement(message) {
    const { content, isSent, avatar, timestamp } = message;
    
    // 创建消息容器div
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isSent ? 'message-sent' : 'message-received'}`;

    if (!isSent && avatar) {
        // 对方消息，添加头像
        const avatarImg = document.createElement('img');
        avatarImg.className = 'avatar';
        avatarImg.src = avatar;
        avatarImg.alt = '头像';
        messageDiv.appendChild(avatarImg);
    }

    // 创建消息气泡div
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';

    // 创建消息内容p标签
    const contentP = document.createElement('p');
    contentP.className = 'message-content';
    contentP.textContent = content;
    bubbleDiv.appendChild(contentP);

    // 创建消息时间span标签
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = getCurrentTime(timestamp);
    bubbleDiv.appendChild(timeSpan);

    // 将气泡添加到消息容器
    messageDiv.appendChild(bubbleDiv);

    return messageDiv;
}

/**
 * 渲染消息列表
 * @param {Array} messages - 消息数组
 */
function renderMessages(messages) {
    const chatMessages = document.getElementById('chatMessages');
    
    // 清空现有消息
    chatMessages.innerHTML = '';
    
    // 依次渲染每条消息
    messages.forEach(message => {
        const messageElement = createMessageElement(message);
        chatMessages.appendChild(messageElement);
    });
    
    // 滚动到底部
    scrollToBottom();
}

/**
 * 追加单条消息
 * @param {object} message - 消息对象
 */
function appendMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    const messageElement = createMessageElement(message);
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

/**
 * 自动滚动到底部（最新消息位置）
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Mock发送消息（前端模拟）
 * @param {string} content - 消息内容
 * @returns {Promise<object>} 发送结果
 */
function mockSendMessage(content) {
    return new Promise((resolve) => {
        // 创建发送消息
        const sentMessage = {
            id: `msg_${Date.now()}`,
            content: content,
            senderId: CONFIG.currentUserId,
            receiverId: CONFIG.targetUserId,
            isSent: true,
            timestamp: Date.now()
        };

        // 延迟模拟网络请求
        setTimeout(() => {
            resolve({
                success: true,
                data: sentMessage,
                message: 'success'
            });
        }, 300);
    });
}

/**
 * Mock获取回复（模拟对方回复）
 * @returns {Promise<object>} 回复消息
 */
function mockGetReply() {
    return new Promise((resolve) => {
        // 随机选择回复内容
        const randomReply = MOCK_DATA.replies[Math.floor(Math.random() * MOCK_DATA.replies.length)];
        
        // 模拟延迟（1-2秒）
        const delay = 1000 + Math.random() * 1000;
        
        setTimeout(() => {
            const replyMessage = {
                id: `msg_${Date.now()}`,
                content: randomReply,
                senderId: CONFIG.targetUserId,
                receiverId: CONFIG.currentUserId,
                isSent: false,
                timestamp: Date.now(),
                avatar: MOCK_DATA.userInfo.avatar
            };
            
            resolve({
                success: true,
                data: replyMessage,
                message: 'success'
            });
        }, delay);
    });
}

/**
 * Mock获取聊天历史
 * @returns {Promise<object>} 历史消息
 */
function mockGetHistory() {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                success: true,
                data: {
                    messages: MOCK_DATA.history,
                    total: MOCK_DATA.history.length,
                    page: 1,
                    pageSize: 20
                },
                message: 'success'
            });
        }, 300);
    });
}

/**
 * Mock获取用户信息
 * @returns {Promise<object>} 用户信息
 */
function mockGetUserInfo() {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                success: true,
                data: MOCK_DATA.userInfo,
                message: 'success'
            });
        }, 200);
    });
}

/**
 * 发送消息函数（主入口）
 */
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const content = messageInput.value.trim();

    // 如果内容为空，不发送
    if (!content) {
        return;
    }

    try {
        // 发送消息
        let result;
        
        if (CONFIG.useRealAPI) {
            // 使用真实API（后端接口就绪后启用）
            result = await apiSendMessage({
                userId: CONFIG.currentUserId,
                targetId: CONFIG.targetUserId,
                content: content
            });
        } else {
            // 使用Mock数据
            result = await mockSendMessage(content);
        }

        if (result.success && result.data) {
            // 添加我方消息到界面
            appendMessage(result.data);
            
            // 清空输入框
            messageInput.value = '';

            // 如果使用Mock，模拟对方回复
            if (!CONFIG.useRealAPI) {
                const replyResult = await mockGetReply();
                if (replyResult.success && replyResult.data) {
                    appendMessage(replyResult.data);
                }
            }
        }
    } catch (error) {
        console.error('发送消息失败:', error);
        // 失败时使用Mock作为fallback
        if (!CONFIG.useRealAPI) {
            const fallbackMessage = {
                id: `msg_${Date.now()}`,
                content: content,
                senderId: CONFIG.currentUserId,
                receiverId: CONFIG.targetUserId,
                isSent: true,
                timestamp: Date.now()
            };
            appendMessage(fallbackMessage);
            messageInput.value = '';
            
            // 模拟对方回复
            const replyResult = await mockGetReply();
            if (replyResult.success && replyResult.data) {
                appendMessage(replyResult.data);
            }
        }
    }
}

/**
 * 加载聊天历史
 */
async function loadChatHistory() {
    try {
        let result;
        
        if (CONFIG.useRealAPI) {
            // 使用真实API
            result = await getChatHistory({
                userId: CONFIG.currentUserId,
                targetId: CONFIG.targetUserId,
                page: 1,
                pageSize: 20
            });
        } else {
            // 使用Mock数据
            result = await mockGetHistory();
        }

        if (result.success && result.data && result.data.messages) {
            renderMessages(result.data.messages);
        }
    } catch (error) {
        console.error('加载聊天历史失败:', error);
        // 失败时使用Mock数据作为fallback
        if (!CONFIG.useRealAPI) {
            renderMessages(MOCK_DATA.history);
        }
    }
}

/**
 * 更新用户信息显示
 */
async function updateUserInfo() {
    try {
        let result;
        
        if (CONFIG.useRealAPI) {
            // 使用真实API
            result = await getUserInfo({
                userId: CONFIG.targetUserId
            });
        } else {
            // 使用Mock数据
            result = await mockGetUserInfo();
        }

        if (result.success && result.data) {
            const userInfo = result.data;
            
            // 更新聊天标题
            const chatTitle = document.querySelector('.chat-title');
            if (chatTitle) {
                chatTitle.textContent = userInfo.name;
            }
            
            // 更新在线状态
            const chatStatus = document.querySelector('.chat-status');
            if (chatStatus) {
                chatStatus.textContent = userInfo.status === 'online' ? '在线' : '离线';
            }
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
    }
}

/**
 * 处理回车键发送消息
 * @param {KeyboardEvent} e - 键盘事件
 */
function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

/**
 * 初始化事件监听
 */
function initEventListeners() {
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    
    // 发送按钮点击事件
    sendBtn.addEventListener('click', sendMessage);
    
    // 输入框键盘事件
    messageInput.addEventListener('keypress', handleKeyPress);
}

/**
 * 初始化WebSocket连接
 */
function initWebSocket() {
    // 如果启用真实API，初始化WebSocket
    if (CONFIG.useRealAPI) {
        const ws = getWebSocketInstance();
        
        // 设置消息回调
        ws.on('onMessage', (message) => {
            // 收到新消息，追加到界面
            appendMessage(message);
        });
        
        // 设置连接回调
        ws.on('onConnect', () => {
            console.log('WebSocket已连接');
        });
        
        // 设置断开回调
        ws.on('onDisconnect', () => {
            console.log('WebSocket已断开');
        });
        
        // 设置错误回调
        ws.on('onError', (error) => {
            console.error('WebSocket错误:', error);
        });
        
        // 设置系统消息回调
        ws.on('onSystem', (systemMessage) => {
            console.log('系统消息:', systemMessage);
            // 处理在线状态变更等系统消息
            if (systemMessage.code === 'ONLINE_STATUS') {
                const chatStatus = document.querySelector('.chat-status');
                if (chatStatus && systemMessage.data.userId === CONFIG.targetUserId) {
                    chatStatus.textContent = systemMessage.data.status === 'online' ? '在线' : '离线';
                }
            }
        });
        
        // 连接WebSocket
        ws.connect().catch(error => {
            console.error('WebSocket连接失败:', error);
        });
    }
}

/**
 * 页面初始化函数
 */
async function init() {
    // 初始化事件监听
    initEventListeners();
    
    // 加载聊天历史
    await loadChatHistory();
    
    // 更新用户信息
    await updateUserInfo();
    
    // 初始化WebSocket（仅在启用真实API时）
    initWebSocket();
    
    // 页面加载完成后滚动到底部
    setTimeout(scrollToBottom, 100);
}

// 页面加载完成后执行初始化
document.addEventListener('DOMContentLoaded', init);

/**
 * 暴露给全局的API方法（供后端或调试使用）
 */
window.ChatAPI = {
    sendMessage,
    loadChatHistory,
    updateUserInfo,
    getConfig: () => CONFIG,
    setConfig: (newConfig) => Object.assign(CONFIG, newConfig)
};