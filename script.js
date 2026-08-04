// 消息数据管理
const messages = [];
let messageIdCounter = 0;

// 表情数据
const emojis = {
    smileys: ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗'],
    hearts: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💕', '💞', '💓', '💗', '💖', '💘', '💝'],
    animals: ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵', '🐔'],
    food: ['🍎', '🍊', '🍋', '🍇', '🍓', '🍑', '🍒', '🥝', '🍅', '🍆', '🥑', '🥦', '🍕', '🍔', '🍟', '🍩']
};

// 快捷回复数据
const quickReplies = [
    '你好呀！',
    '今天天气真好',
    '有什么可以帮你的？',
    '这个想法很棒！',
    '我明白了',
    '好的，谢谢！'
];

// DOM元素
const chatMessages = document.getElementById('chat-messages');
const messagesList = document.getElementById('messages-list');
const messageInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const emojiBtn = document.getElementById('emojiBtn');
const emojiPicker = document.getElementById('emojiPicker');
const toast = document.getElementById('toast');
const scrollTopBtn = document.getElementById('scrollTopBtn');
const quickRepliesContainer = document.getElementById('quickReplies');
const searchInput = document.getElementById('searchInput');
const themeToggle = document.getElementById('themeToggle');
const typingIndicator = document.getElementById('typingIndicator');

// 收藏的消息
const favoriteMessages = JSON.parse(localStorage.getItem('favoriteMessages') || '[]');

// 当前主题
let currentTheme = localStorage.getItem('chatTheme') || 'light';

// 连击计数器
let comboCounter = 0;
let comboTimer = null;

// 显示Toast提示
function showToast(text) {
    toast.textContent = text;
    toast.classList.add('active');
    setTimeout(() => {
        toast.classList.remove('active');
    }, 2000);
}

// 滚动到底部
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 渲染表情选择器
function renderEmojiPicker() {
    let html = '';
    Object.keys(emojis).forEach(category => {
        html += '<div class="emoji-category">';
        emojis[category].forEach(emoji => {
            html += `<span class="emoji-item" onclick="insertEmoji('${emoji}')">${emoji}</span>`;
        });
        html += '</div>';
    });
    emojiPicker.innerHTML = html;
}

// 插入表情
function insertEmoji(emoji) {
    messageInput.value += emoji;
    emojiPicker.classList.remove('active');
    messageInput.focus();
}

// 渲染快捷回复
function renderQuickReplies() {
    let html = '';
    quickReplies.forEach(text => {
        html += `<span class="quick-reply" onclick="sendQuickReply('${text}')">${text}</span>`;
    });
    quickRepliesContainer.innerHTML = html;
}

// 发送快捷回复
function sendQuickReply(text) {
    sendMessage(text);
}

// 创建消息元素
function createMessageElement(message) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.isUser ? 'user-message' : 'bot-message'}`;
    messageElement.dataset.messageId = message.id;
    
    const isFavorite = favoriteMessages.includes(message.id);
        messageElement.innerHTML = `
        <div class="message-menu">
            <button onclick="replyMessage(${message.id})" title="回复">↩️</button>
            <button onclick="forwardMessage(${message.id})" title="转发">➡️</button>
            <button onclick="copyMessage(${message.id})" title="复制">📋</button>
            <button onclick="toggleFavorite(${message.id})" title="${isFavorite ? '取消收藏' : '收藏'}">${isFavorite ? '❤️' : '🤍'}</button>
            <button onclick="deleteMessage(${message.id})" title="删除">🗑️</button>
        </div>
        <div class="message-wrapper">
            <div class="message-content">${message.content}</div>
            <div class="message-time">${message.time}</div>
            <div class="message-status">
                ${message.isUser ? (message.isRead ? '✓✓' : '✓') : ''}
            </div>
        </div>
    `;
    
    // 添加双击放大效果
    messageElement.addEventListener('dblclick', () => {
        messageElement.style.transform = 'scale(1.05)';
        setTimeout(() => {
            messageElement.style.transform = 'scale(1)';
        }, 300);
    });
    
    // 鼠标悬停显示菜单
    messageElement.addEventListener('mouseenter', () => {
        const menu = messageElement.querySelector('.message-menu');
        if (menu) {
            menu.style.opacity = '1';
            menu.style.visibility = 'visible';
            menu.style.transform = 'translateY(0)';
        }
    });
    
    messageElement.addEventListener('mouseleave', () => {
        const menu = messageElement.querySelector('.message-menu');
        if (menu) {
            menu.style.opacity = '0';
            menu.style.visibility = 'hidden';
            menu.style.transform = 'translateY(-10px)';
        }
    });
    
    // 移动端长按操作
    let longPressTimer = null;
    messageElement.addEventListener('touchstart', () => {
        longPressTimer = setTimeout(() => {
            const menu = messageElement.querySelector('.message-menu');
            if (menu) {
                menu.style.opacity = '1';
                menu.style.visibility = 'visible';
                menu.style.transform = 'translateY(0)';
            }
        }, 500);
    });
    
    messageElement.addEventListener('touchend', () => {
        if (longPressTimer) {
            clearTimeout(longPressTimer);
        }
    });
    
    return messageElement;
}

// 删除消息
function deleteMessage(messageId) {
    const index = messages.findIndex(m => m.id === messageId);
    if (index > -1) {
        messages.splice(index, 1);
        renderMessages();
        showToast('消息已删除');
    }
}

// 渲染消息列表
function renderMessages() {
    messagesList.innerHTML = '';
    messages.forEach(message => {
        messagesList.appendChild(createMessageElement(message));
    });
    scrollToBottom();
}

// 添加单条消息
function appendMessage(message) {
    messages.push(message);
    messagesList.appendChild(createMessageElement(message));
    scrollToBottom();
}

// 获取格式化时间
function getFormattedTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// Mock回复数据
const mockReplies = [
    '好的，我明白了！',
    '这个想法很棒！',
    '让我想想...',
    '没问题，我来帮你！',
    '谢谢你的分享！',
    '哈哈，有意思！',
    '是的，我也这么觉得',
    '太棒了！继续加油！',
    '我会记住的！',
    '有什么我可以帮你的吗？'
];

// 获取随机回复
function getRandomReply() {
    return mockReplies[Math.floor(Math.random() * mockReplies.length)];
}

// 发送消息
function sendMessage(content = null) {
    const text = content || messageInput.value.trim();
    if (!text) return;
    
    // 连击检测
    comboCounter++;
    clearTimeout(comboTimer);
    comboTimer = setTimeout(() => {
        comboCounter = 0;
    }, 3000);
    
    // 显示连击提示
    if (comboCounter >= 3) {
        showCombo(comboCounter);
    }
    
    // 创建用户消息
    const userMessage = {
        id: messageIdCounter++,
        content: text,
        time: getFormattedTime(),
        isUser: true
    };
    
    appendMessage(userMessage);
    messageInput.value = '';
    
    // 发送特效
    createSendEffect();
    
    // 显示打字状态
    showTypingIndicator();
    
    // Mock回复
    setTimeout(() => {
        hideTypingIndicator();
        const botMessage = {
            id: messageIdCounter++,
            content: getRandomReply(),
            time: getFormattedTime(),
            isUser: false
        };
        appendMessage(botMessage);
        // 更新已发送消息的状态为已读
        userMessage.isRead = true;
        renderMessages();
    }, 1000 + Math.random() * 1000);
}

// 创建发送特效
function createSendEffect() {
    const effect = document.createElement('div');
    effect.className = 'send-effect';
    sendBtn.appendChild(effect);
    setTimeout(() => {
        effect.remove();
    }, 600);
}

// 显示连击提示
function showCombo(count) {
    comboText.textContent = '连击！';
    comboCount.textContent = `x${count}`;
    comboNotification.classList.add('active');
    setTimeout(() => {
        comboNotification.classList.remove('active');
    }, 800);
}

// 显示打字状态
function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
}

// 隐藏打字状态
function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// 搜索消息
function searchMessages(query) {
    if (!query.trim()) {
        renderMessages();
        return;
    }
    
    const filtered = messages.filter(m => 
        m.content.toLowerCase().includes(query.toLowerCase())
    );
    
    messagesList.innerHTML = '';
    filtered.forEach(message => {
        const element = createMessageElement(message);
        // 高亮搜索关键词
        const contentEl = element.querySelector('.message-content');
        contentEl.innerHTML = message.content.replace(
            new RegExp(query, 'gi'),
            '<span class="highlight">$&</span>'
        );
        messagesList.appendChild(element);
    });
}

// 切换主题
function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    localStorage.setItem('chatTheme', currentTheme);
    document.body.classList.toggle('dark-theme', currentTheme === 'dark');
    themeToggle.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
    showToast(currentTheme === 'dark' ? '已切换到深色模式' : '已切换到浅色模式');
}

// 收藏消息
function toggleFavorite(messageId) {
    const index = favoriteMessages.indexOf(messageId);
    if (index > -1) {
        favoriteMessages.splice(index, 1);
        showToast('已取消收藏');
    } else {
        favoriteMessages.push(messageId);
        showToast('已收藏');
    }
    localStorage.setItem('favoriteMessages', JSON.stringify(favoriteMessages));
}

// 回复消息
function replyMessage(messageId) {
    const message = messages.find(m => m.id === messageId);
    if (message) {
        messageInput.value = `回复: ${message.content.substring(0, 20)}${message.content.length > 20 ? '...' : ''} `;
        messageInput.focus();
        emojiPicker.classList.remove('active');
    }
}

// 转发消息
function forwardMessage(messageId) {
    const message = messages.find(m => m.id === messageId);
    if (message) {
        navigator.clipboard.writeText(message.content).then(() => {
            showToast('内容已复制，可以转发啦！');
        });
    }
}

// 复制消息
function copyMessage(messageId) {
    const message = messages.find(m => m.id === messageId);
    if (message) {
        navigator.clipboard.writeText(message.content).then(() => {
            showToast('已复制到剪贴板');
        });
    }
}

// 滚动到顶部
function scrollToTop() {
    chatMessages.scrollTop = 0;
}

// 监听滚动事件
function handleScroll() {
    if (chatMessages.scrollTop > 300) {
        scrollTopBtn.classList.add('active');
    } else {
        scrollTopBtn.classList.remove('active');
    }
}

// 初始化事件监听
function initEventListeners() {
    // 发送按钮点击
    sendBtn.addEventListener('click', () => sendMessage());
    
    // 回车键发送
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 表情按钮点击
    emojiBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        emojiPicker.classList.toggle('active');
    });
    
    // 点击其他区域关闭表情选择器
    document.addEventListener('click', (e) => {
        if (!emojiBtn.contains(e.target) && !emojiPicker.contains(e.target)) {
            emojiPicker.classList.remove('active');
        }
    });
    
    // 滚动事件
    chatMessages.addEventListener('scroll', handleScroll);
    
    // 滚动到顶部按钮
    scrollTopBtn.addEventListener('click', scrollToTop);
    
    // 搜索功能
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchMessages(e.target.value);
        });
    }
    
    // 主题切换
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + / 聚焦搜索框
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            searchInput?.focus();
        }
        // Ctrl/Cmd + Enter 发送消息
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            sendMessage();
        }
        // ESC 关闭表情选择器
        if (e.key === 'Escape') {
            emojiPicker.classList.remove('active');
        }
    });
}

// 初始化页面
function init() {
    renderEmojiPicker();
    renderQuickReplies();
    initEventListeners();
    
    // 添加欢迎消息
    setTimeout(() => {
        const welcomeMessage = {
            id: messageIdCounter++,
            content: '你好呀！很高兴认识你！😊',
            time: getFormattedTime(),
            isUser: false
        };
        appendMessage(welcomeMessage);
    }, 500);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// 暴露全局方法
window.insertEmoji = insertEmoji;
window.sendQuickReply = sendQuickReply;
window.replyMessage = replyMessage;
window.forwardMessage = forwardMessage;
window.copyMessage = copyMessage;

// ==================== 语音输入功能 ====================
// 获取语音输入按钮
const voiceInputBtn = document.getElementById('voiceInputBtn');

// 语音识别状态
let isRecording = false;
let recognition = null;

// 检查浏览器是否支持语音识别
function isSpeechRecognitionSupported() {
    return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
}

// 初始化语音识别
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        showToast('您的浏览器不支持语音输入');
        return null;
    }

    const rec = new SpeechRecognition();
    rec.lang = 'zh-CN';          // 设置为中文
    rec.continuous = false;      // 不连续识别，说完一句自动停止
    rec.interimResults = true;   // 显示中间结果

    // 识别开始
    rec.onstart = function() {
        isRecording = true;
        voiceInputBtn.textContent = '⏹️';
        voiceInputBtn.title = '点击停止录音';
        showToast('正在聆听，请说话...');
    };

    // 识别结果
    rec.onresult = function(event) {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        // 将识别结果填入输入框
        messageInput.value = transcript;
        messageInput.focus();
    };

    // 识别结束
    rec.onend = function() {
        isRecording = false;
        voiceInputBtn.textContent = '🎙️';
        voiceInputBtn.title = '语音输入';
    };

    // 识别错误
    rec.onerror = function(event) {
        isRecording = false;
        voiceInputBtn.textContent = '🎙️';
        voiceInputBtn.title = '语音输入';
        if (event.error === 'no-speech') {
            showToast('没有检测到语音，请重试');
        } else if (event.error === 'not-allowed') {
            showToast('请允许麦克风权限');
        } else {
            showToast('语音识别出错: ' + event.error);
        }
    };

    return rec;
}

// 语音输入按钮点击事件
if (voiceInputBtn) {
    voiceInputBtn.addEventListener('click', function() {
        if (!isSpeechRecognitionSupported()) {
            showToast('您的浏览器不支持语音输入，请使用Chrome浏览器');
            return;
        }

        // 如果正在录音，停止录音
        if (isRecording && recognition) {
            recognition.stop();
            return;
        }

        // 开始录音
        recognition = initSpeechRecognition();
        if (recognition) {
            try {
                recognition.start();
            } catch (e) {
                showToast('语音识别启动失败，请重试');
            }
        }
    });
}