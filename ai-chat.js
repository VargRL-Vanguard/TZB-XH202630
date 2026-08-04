/**
 * AI辅导对话 - 前端逻辑
 * 预留后端接口，当前使用Mock数据模拟AI回复
 */

// ==================== API配置 ====================
const API_CONFIG = {
    baseURL: 'http://localhost:3000/api',
    useRealAPI: false,
    timeout: 30000 // AI对话超时时间较长
};

// ==================== HTTP请求工具 ====================
async function request(url, options = {}) {
    if (API_CONFIG.useRealAPI) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);
        try {
            const res = await fetch(API_CONFIG.baseURL + url, {
                ...options,
                signal: controller.signal,
                headers: { 'Content-Type': 'application/json', ...options.headers }
            });
            clearTimeout(timeoutId);
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return await res.json();
        } catch (err) {
            clearTimeout(timeoutId);
            console.error('请求失败:', err);
            return null;
        }
    }
    return null;
}

// ==================== Mock AI回复 ====================
const mockReplies = {
    '函数参数传递': 'Python函数参数传递有以下几种方式：\n\n1. 位置参数：按顺序传递，如 func(1, 2)\n2. 关键字参数：指定参数名，如 func(a=1, b=2)\n3. 默认参数：func(a, b=10)，b有默认值\n4. 可变参数：*args接收元组，**kwargs接收字典\n\n建议重点练习*args和**kwargs的使用场景，这是考试常考点。',
    '学习效率': '根据你的学习数据分析，我有以下建议：\n\n1. 调整学习时间：你在晚上8-10点效率最高，建议将难点内容安排在此时段\n2. 番茄工作法：每学习25分钟休息5分钟，保持专注\n3. 主动回忆：学完后尝试不看书复述知识点\n4. 间隔复习：按照1天、3天、7天的间隔复习已学内容\n\n需要我帮你制定具体的学习计划吗？',
    '学习计划': '根据你当前的学习进度，我为你制定了本周计划：\n\n周一~周二：完成函数与模块章节\n- 函数定义与调用（2h）\n- 参数传递详解（1.5h）\n- 模块导入机制（1h）\n\n周三~周四：数据结构进阶\n- 列表推导式（1h）\n- 字典与集合（1.5h）\n\n周五~周六：面向对象入门\n- 类与对象（2h）\n- 继承与多态（2h）\n\n周日：综合复习与测验\n\n需要我调整计划吗？',
    '面向对象': '面向对象编程(OOP)是Python的核心概念，让我帮你梳理：\n\n三大特性：\n1. 封装：将数据和方法包装在类中\n2. 继承：子类继承父类的属性和方法\n3. 多态：同一方法在不同对象中有不同表现\n\n常见难点：\n- self参数的理解\n- __init__构造方法\n- 方法重写与super()\n\n建议从简单的"学生类"开始练习，逐步理解概念。需要我出几道练习题吗？'
};

// 默认回复
const defaultReply = '感谢你的提问！我正在分析你的问题，结合你的学习数据，我会给出针对性的建议。请稍等，AI正在生成回复...';

// ==================== 后端接口定义 ====================
/**
 * 发送AI对话消息
 * POST /api/ai-chat/send
 * 参数: { message: string, context?: object }
 * 返回: { reply: string, conversationId: string }
 */
async function sendAIMessage(message, context) {
    context = context || {};
    if (API_CONFIG.useRealAPI) {
        return await request('/ai-chat/send', {
            method: 'POST',
            body: JSON.stringify({ message: message, context: context })
        });
    }
    // Mock回复 - 模拟网络延迟
    await new Promise(function(resolve) { setTimeout(resolve, 1000 + Math.random() * 1000); });
    for (var key in mockReplies) {
        if (message.indexOf(key) !== -1) {
            return { reply: mockReplies[key], conversationId: 'mock-' + Date.now() };
        }
    }
    return { reply: defaultReply, conversationId: 'mock-' + Date.now() };
}

/**
 * 获取对话历史
 * GET /api/ai-chat/history?limit=20
 * 返回: [{ id, role, content, timestamp }]
 */
async function getChatHistory(limit) {
    limit = limit || 20;
    if (API_CONFIG.useRealAPI) return await request('/ai-chat/history?limit=' + limit);
    return [];
}

/**
 * 清除对话历史
 * DELETE /api/ai-chat/history
 * 返回: { success: boolean }
 */
async function clearChatHistory() {
    if (API_CONFIG.useRealAPI) {
        return await request('/ai-chat/history', { method: 'DELETE' });
    }
    console.log('对话历史已清除（Mock）');
    return { success: true };
}

// ==================== 页面逻辑 ====================
var chatMessages = document.getElementById('chatMessages');
var messageInput = document.getElementById('messageInput');
var sendBtn = document.getElementById('sendBtn');

// 获取当前时间
function getCurrentTime() {
    var now = new Date();
    var h = now.getHours().toString();
    var m = now.getMinutes().toString();
    if (h.length < 2) h = '0' + h;
    if (m.length < 2) m = '0' + m;
    return h + ':' + m;
}

// 添加消息到聊天区域
function addMessage(content, role) {
    var messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + role + '-message';

    var avatarSvg;
    if (role === 'ai') {
        avatarSvg = '<svg viewBox="0 0 40 40" width="40" height="40"><rect width="40" height="40" rx="10" fill="#6366f1"/><text x="20" y="26" text-anchor="middle" fill="white" font-size="20">AI</text></svg>';
    } else {
        avatarSvg = '<svg viewBox="0 0 40 40" width="40" height="40"><rect width="40" height="40" rx="10" fill="#10b981"/><text x="20" y="26" text-anchor="middle" fill="white" font-size="16">我</text></svg>';
    }

    // 将换行符转为<br>
    var htmlContent = content.replace(/\n/g, '<br>');

    messageDiv.innerHTML = '<div class="message-avatar">' + avatarSvg + '</div>' +
        '<div class="message-bubble">' +
        '<div class="bubble-content">' + htmlContent + '</div>' +
        '<div class="bubble-time">' + getCurrentTime() + '</div>' +
        '</div>';

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示加载动画
function showTyping() {
    var typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = '<div class="message-avatar">' +
        '<svg viewBox="0 0 40 40" width="40" height="40">' +
        '<rect width="40" height="40" rx="10" fill="#6366f1"/>' +
        '<text x="20" y="26" text-anchor="middle" fill="white" font-size="20">AI</text>' +
        '</svg></div>' +
        '<div class="message-bubble"><div class="bubble-content">' +
        '<div class="typing-indicator"><span></span><span></span><span></span></div>' +
        '</div></div>';
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

// 移除加载动画
function removeTyping() {
    var typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
}

// 滚动到底部
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 发送消息
async function sendMessage() {
    var content = messageInput.value.trim();
    if (!content) return;

    // 添加用户消息
    addMessage(content, 'user');
    messageInput.value = '';

    // 显示加载动画
    showTyping();

    // 调用AI接口
    var result = await sendAIMessage(content);

    // 移除加载动画，添加AI回复
    removeTyping();
    if (result && result.reply) {
        addMessage(result.reply, 'ai');
    } else {
        addMessage('抱歉，我暂时无法回答这个问题，请稍后再试。', 'ai');
    }
}

// 发送按钮点击事件
sendBtn.addEventListener('click', sendMessage);

// 回车发送
messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendMessage();
});

// 快捷问题点击事件
var quickBtns = document.querySelectorAll('.quick-btn');
for (var i = 0; i < quickBtns.length; i++) {
    quickBtns[i].addEventListener('click', function() {
        messageInput.value = this.getAttribute('data-question');
        sendMessage();
    });
}

// ==================== 初始化 ====================
async function init() {
    // 加载历史对话
    var history = await getChatHistory(20);
    if (history && history.length > 0) {
        chatMessages.innerHTML = '';
        for (var i = 0; i < history.length; i++) {
            var msg = history[i];
            addMessage(msg.content, msg.role === 'user' ? 'user' : 'ai');
        }
    }
}

document.addEventListener('DOMContentLoaded', init);
