// ==================== 消息数据管理 ====================
const STORAGE_KEY_MESSAGES = 'chatMessages';
const STORAGE_KEY_MSG_COUNTER = 'chatMessageIdCounter';

// 从 localStorage 恢复消息与ID计数器
const messages = JSON.parse(localStorage.getItem(STORAGE_KEY_MESSAGES) || '[]');
let messageIdCounter = parseInt(localStorage.getItem(STORAGE_KEY_MSG_COUNTER) || '0', 10) || 0;

// 持久化消息
function saveMessages() {
    try {
        localStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(messages));
        localStorage.setItem(STORAGE_KEY_MSG_COUNTER, String(messageIdCounter));
    } catch (e) {
        console.error('保存消息失败:', e);
    }
}

// 表情库（分类）
const emojiLibrary = {
    smileys: {
        name: '笑脸', icon: '😀',
        list: ['😀','😃','😄','😁','😆','😅','🤣','😂','🙂','🙃','😉','😊','😇','🥰','😍','🤩','😘','😗','😚','😙','😋','😛','😜','🤪','😝','🤑','🤗','🤭','🤫','🤔','🤐','🤨','😐','😑','😶','😏','😒','🙄','😬','🤥','😌','😔','😪','🤤','😴','😷','🤒','🤕','🤢','🤮','🥵','🥶','🥴','😵','🤯','🤠','🥳','😎','🤓','🧐','😕','😟','🙁','😮','😯','😲','😳','🥺','😦','😧','😨','😰','😥','😢','😭','😱','😖','😣','😞','😓','😩','😫','🥱','😤','😡','😠','🤬','😈','👿','💀','💩','🤡','👻','👽','🤖','😺','😸','😹','😻','😼','😽','🙀','😿','😾']
    },
    gestures: {
        name: '手势', icon: '👋',
        list: ['👋','🤚','🖐️','✋','🖖','👌','🤌','🤏','✌️','🤞','🤟','🤘','🤙','👈','👉','👆','👇','☝️','👍','👎','✊','👊','🤛','🤜','👏','🙌','👐','🤲','🙏','✍️','💪','🦾','🦵','🦶','👂','🦻','👃','🧠','🦷','🦴','👀','👁️','👅','👄']
    },
    hearts: {
        name: '心形', icon: '❤️',
        list: ['❤️','🧡','💛','💚','💙','💜','🖤','🤍','🤎','💔','❣️','💕','💞','💓','💗','💖','💘','💝','💟','♥️','💌','💋','💍','💎']
    },
    animals: {
        name: '动物', icon: '🐶',
        list: ['🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐽','🐸','🐵','🙈','🙉','🙊','🐒','🐔','🐧','🐦','🐤','🐣','🐥','🦆','🦅','🦉','🦇','🐺','🐗','🐴','🦄','🐝','🐛','🦋','🐌','🐞','🐜','🦟','🦗','🕷️','🦂','🐢','🐍','🦎','🦖','🦕','🐙','🦑','🦐','🦞','🦀','🐡','🐠','🐟','🐬','🐳','🐋','🦈','🐊','🐅','🐆','🦓','🦍','🦧','🐘','🦛','🦏','🐪','🐫','🦒','🦘','🐃','🐂','🐄','🐎','🐖','🐏','🐑','🦙','🐐','🦌','🐕','🐩','🐈','🐓','🦃','🦚','🦜','🦢','🕊️','🐇','🦝','🦡','🦦','🦥','🐁','🐀','🐿️']
    },
    food: {
        name: '食物', icon: '🍎',
        list: ['🍎','🍐','🍊','🍋','🍌','🍉','🍇','🍓','🫐','🍈','🍒','🍑','🥭','🍍','🥥','🥝','🍅','🍆','🥑','🥦','🥬','🥒','🌶️','🫑','🌽','🥕','🫒','🧄','🧅','🥔','🍠','🥐','🥯','🍞','🥖','🥨','🧀','🥚','🍳','🧈','🥞','🧇','🥓','🥩','🍗','🍖','🦴','🌭','🍔','🍟','🍕','🥪','🥙','🌮','🌯','🥗','🥘','🍝','🍜','🍲','🍛','🍣','🍱','🥟','🍤','🍙','🍚','🍘','🍥','🥠','🍢','🍡','🍧','🍨','🍦','🥧','🧁','🍰','🎂','🍮','🍭','🍬','🍫','🍩','🍪','🌰','🥜','🍯']
    },
    activities: {
        name: '活动', icon: '⚽',
        list: ['⚽','🏀','🏈','⚾','🥎','🎾','🏐','🏉','🥏','🎱','🏓','🏸','🏒','🏑','🥍','🏏','🥅','⛳','🪁','🏹','🎣','🥊','🥋','🎽','🛹','🛷','⛸️','🥌','🎿','⛷️','🏂','🪂','🏋️','🤸','⛹️','🤺','🤾','🏌️','🏇','🧘','🏄','🏊','🤽','🚣','🧗','🚵','🚴','🏆','🥇','🥈','🥉','🏅','🎖️','🏵️','🎗️','🎫','🎟️','🎪','🤹','🎭','🩰','🎨','🎬','🎤','🎧','🎼','🎹','🥁','🎷','🎺','🎸','🎻','🎲','🧩','♟️','🎯','🎳','🎮','🎰','🧸']
    },
    travel: {
        name: '旅行', icon: '🚗',
        list: ['🚗','🚕','🚙','🚌','🚎','🏎️','🚓','🚑','🚒','🚐','🚚','🚛','🚜','🛴','🚲','🛵','🏍️','🚨','🚔','🚍','🚘','🚖','🚡','🚠','🚟','🚃','🚋','🚞','🚝','🚄','🚅','🚈','🚂','🚆','🚇','🚊','🚉','✈️','🛫','🛬','🛩️','💺','🛰️','🚀','🛸','🚁','🛶','⛵','🚤','🛥️','🛳️','⛴️','🚢','⚓','⛽','🚧','🚦','🚥','🗺️','🗿','🗽','🗼','🏰','🏯','🏟️','🎡','🎢','🎠','⛲','⛱️','🏖️','🏝️','🏜️','🌋','⛰️','🏔️','🗻','🏕️','⛺','🏠','🏡','🏘️','🏚️','🏗️','🏭','🏢','🏬','🏣','🏤','🏥','🏦','🏨','🏪','🏫','🏩','💒']
    },
    objects: {
        name: '物品', icon: '💡',
        list: ['⌚','📱','📲','💻','⌨️','🖥️','🖨️','🖱️','🕹️','💽','💾','💿','📀','📼','📷','📸','📹','🎥','📽️','🎞️','📞','☎️','📟','📠','📺','📻','🎙️','🎚️','🎛️','⏱️','⏲️','⏰','🕰️','⌛','⏳','📡','🔋','🔌','💡','🔦','🕯️','🪔','💸','💵','💴','💶','💷','💳','💎','⚖️','🧰','🔧','🔨','🛠️','⛏️','🔩','⚙️','🧱','⛓️','🧲','🔫','💣','🧨','🪓','🔪','🗡️','⚔️','🛡️','🚬','⚰️','⚱️','🏺','🔮','📿','🧿','💈','⚗️','🔭','🔬','🕳️','🩹','🩺','💊','💉','🩸','🧬','🦠','🧫','🧪','🌡️','🧹','🧺','🧻','🚽','🚰','🚿','🛁','🧼','🪒','🧽','🧴','🛎️','🔑','🗝️','🚪','🪑','🛋️','🛏️','🧸','🖼️','🛍️','🛒','🎁','🎈','🎏','🎀','🪄','🎊','🎉']
    },
    symbols: {
        name: '符号', icon: '🔣',
        list: ['⚛️','🕉️','✡️','☸️','☯️','✝️','☦️','☪️','☮️','🕎','🔯','♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓','⛎','🔀','🔁','🔂','▶️','⏩','⏭️','⏯️','◀️','⏪','⏮️','🔼','⏫','🔽','⏬','⏸️','⏹️','⏺️','⏏️','🎦','🔅','🔆','📶','📳','📴','♀️','♂️','⚧️','✖️','➕','➖','➗','♾️','‼️','⁉️','❓','❔','❕','❗','〰️','💱','💲','⚕️','♻️','⚜️','🔱','📛','🔰','⭕','✅','☑️','✔️','❌','❎','➰','➿','〽️','✳️','✴️','❇️','©️','®️','™️','#️⃣','*️⃣','0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟','🔠','🔡','🔢','🔣','🔤','🅰️','🆎','🆑','🅾️','🆘','🆔','🅿️','🆚','🆕','🆓','🔥','⭐','🌟','✨','💥','💫','💦','💨','💤']
    }
};

// 快捷短语数据
const quickPhrases = [
    '你好呀！',
    '今天天气真好',
    '有什么可以帮你的？',
    '这个想法很棒！',
    '我明白了',
    '好的，谢谢！',
    '能再详细说说吗？',
    '帮我举个例子',
    '我没太理解',
    '学到了，感谢！',
    '继续加油',
    '稍等一下'
];

// ==================== DOM元素 ====================
const chatMessages = document.getElementById('chat-messages');
const messagesList = document.getElementById('messages-list');
const messageInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const emojiBtn = document.getElementById('emojiBtn');
const emojiPicker = document.getElementById('emojiPicker');
const toast = document.getElementById('toast');
const scrollTopBtn = document.getElementById('scrollTopBtn');
const scrollBottomBtn = document.getElementById('scrollBottomBtn');
const newMessageBadge = document.getElementById('newMessageBadge');
const searchInput = document.getElementById('searchInput');
const themeToggle = document.getElementById('themeToggle');
const typingIndicator = document.getElementById('typingIndicator');
const charCounter = document.getElementById('charCounter');
const emptyState = document.getElementById('emptyState');
const reactionPicker = document.getElementById('reactionPicker');
const doubleClickActionMenu = document.getElementById('doubleClickActionMenu');
const shortcutsBtn = document.getElementById('shortcutsBtn');
const shortcutsOverlay = document.getElementById('shortcutsOverlay');
const shortcutsClose = document.getElementById('shortcutsClose');
const settingsBtn = document.getElementById('settingsBtn');
const settingsOverlay = document.getElementById('settingsOverlay');
const settingsClose = document.getElementById('settingsClose');
const settingsThemeToggle = document.getElementById('settingsThemeToggle');
const settingsClearChat = document.getElementById('settingsClearChat');
const settingsExport = document.getElementById('settingsExport');
const settingsShortcuts = document.getElementById('settingsShortcuts');
const settingsAbout = document.getElementById('settingsAbout');
const comboNotification = document.getElementById('comboNotification');
const comboText = document.getElementById('comboText');
const comboCount = document.getElementById('comboCount');
const onlineStatusText = document.getElementById('onlineStatusText');

// 收藏的消息
const favoriteMessages = JSON.parse(localStorage.getItem('favoriteMessages') || '[]');

// 消息反应数据 { messageId: { '👍': 1, '❤️': 2 } }
const messageReactions = JSON.parse(localStorage.getItem('messageReactions') || '{}');
// 当前用户已添加的反应 { messageId: '👍' }
const myReactions = JSON.parse(localStorage.getItem('myReactions') || '{}');

// 清理孤儿数据：移除不存在消息的反应/收藏，避免id复用导致误显示点赞
(function cleanupOrphanData() {
    const validIds = new Set(messages.map(m => m.id));
    if (validIds.size === 0) {
        // 没有任何消息，清空所有残留反应和收藏
        if (Object.keys(messageReactions).length > 0) {
            for (const k of Object.keys(messageReactions)) delete messageReactions[k];
            localStorage.setItem('messageReactions', '{}');
        }
        if (Object.keys(myReactions).length > 0) {
            for (const k of Object.keys(myReactions)) delete myReactions[k];
            localStorage.setItem('myReactions', '{}');
        }
        if (favoriteMessages.length > 0) {
            favoriteMessages.length = 0;
            localStorage.setItem('favoriteMessages', '[]');
        }
        return;
    }
    let changed = false;
    for (const key of Object.keys(messageReactions)) {
        if (!validIds.has(parseInt(key, 10))) {
            delete messageReactions[key];
            changed = true;
        }
    }
    for (const key of Object.keys(myReactions)) {
        if (!validIds.has(parseInt(key, 10))) {
            delete myReactions[key];
            changed = true;
        }
    }
    for (let i = favoriteMessages.length - 1; i >= 0; i--) {
        if (!validIds.has(favoriteMessages[i])) {
            favoriteMessages.splice(i, 1);
            changed = true;
        }
    }
    if (changed) {
        localStorage.setItem('messageReactions', JSON.stringify(messageReactions));
        localStorage.setItem('myReactions', JSON.stringify(myReactions));
        localStorage.setItem('favoriteMessages', JSON.stringify(favoriteMessages));
    }
})();

// 当前主题
let currentTheme = localStorage.getItem('chatTheme') || 'light';

// 连击计数器
let comboCounter = 0;
let comboTimer = null;

// 未读消息计数
let unreadCount = 0;
let isAtBottom = true;

// 当前打开的反应选择器对应的消息ID
let activeReactionMessageId = null;
// 当前双击操作菜单对应的消息ID
let activeDoubleClickMessageId = null;

// ==================== Toast提示 ====================
function showToast(text) {
    toast.textContent = text;
    toast.classList.add('active');
    setTimeout(() => {
        toast.classList.remove('active');
    }, 2000);
}

// ==================== 滚动控制 ====================
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
    isAtBottom = true;
    unreadCount = 0;
    updateNewMessageBadge();
    hideScrollBottomBtn();
}

function scrollToTop() {
    chatMessages.scrollTop = 0;
}

function isScrolledToBottom() {
    const threshold = 80;
    return chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight < threshold;
}

function showScrollBottomBtn() {
    scrollBottomBtn.classList.add('active');
}

function hideScrollBottomBtn() {
    scrollBottomBtn.classList.remove('active');
}

function updateNewMessageBadge() {
    if (unreadCount > 0) {
        newMessageBadge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        newMessageBadge.classList.add('active');
    } else {
        newMessageBadge.classList.remove('active');
    }
}

// ==================== 空状态管理 ====================
function updateEmptyState() {
    if (messages.length === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }
}

// ==================== 字符计数器 ====================
function updateCharCounter() {
    const len = messageInput.value.length;
    const max = 500;
    charCounter.textContent = `${len}/${max}`;
    charCounter.classList.remove('warning', 'danger');
    if (len >= max) {
        charCounter.classList.add('danger');
    } else if (len >= max * 0.8) {
        charCounter.classList.add('warning');
    }
    // 智能发送按钮
    sendBtn.disabled = len === 0;
}

// ==================== 涟漪效果 ====================
function createRipple(event) {
    const target = event.currentTarget;
    // 只对鼠标点击生效
    if (event.clientX === 0 && event.clientY === 0 && !(target instanceof HTMLAnchorElement)) {
        // 键盘触发时在中心生成
    }
    const rect = target.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;

    // 确保父元素有定位
    const position = getComputedStyle(target).position;
    if (position === 'static') {
        target.style.position = 'relative';
    }
    target.style.overflow = 'hidden';

    target.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
}

// ==================== 表情选择器（含快捷短语） ====================
function renderEmojiPicker() {
    let html = '';
    // 顶部主标签：表情 / 快捷短语
    html += '<div class="emoji-picker-tabs">';
    html += '<button class="emoji-picker-tab active" data-tab="emoji">表情</button>';
    html += '<button class="emoji-picker-tab" data-tab="phrase">快捷短语</button>';
    html += '</div>';

    // 表情面板
    html += '<div class="emoji-picker-panel active" data-panel="emoji">';
    // 分类导航
    html += '<div class="emoji-category-nav">';
    Object.keys(emojiLibrary).forEach((key, idx) => {
        const cat = emojiLibrary[key];
        const activeCls = idx === 0 ? ' active' : '';
        html += `<button class="emoji-category-btn${activeCls}" data-category="${key}" title="${cat.name}">${cat.icon}</button>`;
    });
    html += '</div>';
    // 分类内容
    Object.keys(emojiLibrary).forEach((key, idx) => {
        const cat = emojiLibrary[key];
        const display = idx === 0 ? 'flex' : 'none';
        html += `<div class="emoji-category-content" data-category="${key}" style="display:${display}">`;
        cat.list.forEach(emoji => {
            html += `<span class="emoji-item" data-emoji="${emoji}">${emoji}</span>`;
        });
        html += '</div>';
    });
    html += '</div>';

    // 快捷短语面板
    html += '<div class="emoji-picker-panel" data-panel="phrase">';
    html += '<div class="phrase-list">';
    quickPhrases.forEach(text => {
        html += `<div class="phrase-item" data-text="${text}">${text}</div>`;
    });
    html += '</div>';
    html += '</div>';

    emojiPicker.innerHTML = html;

    // 事件委托：主标签 / 分类 / 表情 / 短语
    emojiPicker.addEventListener('click', (e) => {
        // 主标签切换
        const tab = e.target.closest('.emoji-picker-tab');
        if (tab) {
            const target = tab.dataset.tab;
            emojiPicker.querySelectorAll('.emoji-picker-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            emojiPicker.querySelectorAll('.emoji-picker-panel').forEach(p => {
                p.classList.toggle('active', p.dataset.panel === target);
            });
            return;
        }
        // 表情分类切换
        const catBtn = e.target.closest('.emoji-category-btn');
        if (catBtn) {
            const cat = catBtn.dataset.category;
            emojiPicker.querySelectorAll('.emoji-category-btn').forEach(b => b.classList.remove('active'));
            catBtn.classList.add('active');
            emojiPicker.querySelectorAll('.emoji-category-content').forEach(c => {
                c.style.display = c.dataset.category === cat ? 'flex' : 'none';
            });
            return;
        }
        // 点击表情插入输入框
        const emojiItem = e.target.closest('.emoji-item');
        if (emojiItem) {
            insertEmoji(emojiItem.dataset.emoji);
            return;
        }
        // 点击快捷短语直接发送
        const phraseItem = e.target.closest('.phrase-item');
        if (phraseItem) {
            messageInput.value = phraseItem.dataset.text;
            updateCharCounter();
            sendMessage();
            emojiPicker.classList.remove('active');
            return;
        }
    });
}

function insertEmoji(emoji) {
    messageInput.value += emoji;
    messageInput.focus();
    updateCharCounter();
}

// ==================== 日期分隔符 ====================
function getDateLabel(timestamp) {
    const date = new Date(timestamp);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const msgDate = new Date(date);
    msgDate.setHours(0, 0, 0, 0);

    if (msgDate.getTime() === today.getTime()) {
        return '今天';
    } else if (msgDate.getTime() === yesterday.getTime()) {
        return '昨天';
    } else {
        return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
    }
}

function createDateSeparator(label) {
    const div = document.createElement('div');
    div.className = 'date-separator';
    div.innerHTML = `<span>${label}</span>`;
    return div;
}

// ==================== 消息反应 ====================
function renderReactions(messageId) {
    const reactions = messageReactions[messageId] || {};
    const myReaction = myReactions[messageId];
    const emojis = Object.keys(reactions);
    if (emojis.length === 0) return '';

    return '<div class="message-reactions">' + emojis.map(emoji => {
        const count = reactions[emoji];
        const isActive = myReaction === emoji;
        return `<span class="reaction-badge ${isActive ? 'active' : ''}" data-message-id="${messageId}" data-emoji="${emoji}">
            <span class="reaction-emoji">${emoji}</span>
            <span class="reaction-count">${count}</span>
        </span>`;
    }).join('') + '</div>';
}

function toggleReaction(messageId, emoji) {
    if (!messageReactions[messageId]) {
        messageReactions[messageId] = {};
    }
    const reactions = messageReactions[messageId];
    const myCurrent = myReactions[messageId];

    // 如果已经选了这个反应，取消
    if (myCurrent === emoji) {
        reactions[emoji]--;
        if (reactions[emoji] <= 0) delete reactions[emoji];
        delete myReactions[messageId];
    } else {
        // 如果已有其他反应，先减掉
        if (myCurrent && reactions[myCurrent]) {
            reactions[myCurrent]--;
            if (reactions[myCurrent] <= 0) delete reactions[myCurrent];
        }
        // 添加新反应
        reactions[emoji] = (reactions[emoji] || 0) + 1;
        myReactions[messageId] = emoji;
    }

    localStorage.setItem('messageReactions', JSON.stringify(messageReactions));
    localStorage.setItem('myReactions', JSON.stringify(myReactions));
    renderMessages();
}

function showReactionPicker(messageId, anchorEl) {
    hideReactionPicker();
    activeReactionMessageId = messageId;
    const rect = anchorEl.getBoundingClientRect();
    reactionPicker.style.left = `${rect.left}px`;
    reactionPicker.style.top = `${rect.top - 44}px`;
    reactionPicker.classList.add('active');
}

function hideReactionPicker() {
    reactionPicker.classList.remove('active');
    activeReactionMessageId = null;
}

// ==================== 双击操作菜单 ====================
function showDoubleClickActionMenu(messageId, anchorEl, event) {
    hideDoubleClickActionMenu();
    activeDoubleClickMessageId = messageId;

    // 更新收藏按钮的状态
    const favItem = doubleClickActionMenu.querySelector('[data-action="favorite"]');
    const isFav = favoriteMessages.includes(messageId);
    favItem.querySelector('.action-menu-icon').textContent = isFav ? '❤️' : '🤍';
    favItem.querySelector('.action-menu-text').textContent = isFav ? '取消收藏' : '收藏';

    // 定位菜单：优先使用双击的鼠标位置
    const clickX = event?.clientX;
    const clickY = event?.clientY;

    let left, top;
    if (clickX && clickY) {
        // 鼠标双击位置显示
        left = clickX + 10;
        top = clickY - 10;
    } else {
        const rect = anchorEl.getBoundingClientRect();
        left = rect.left + rect.width / 2 - 90;
        top = rect.top - 16;
    }

    // 边界检查，避免超出视窗
    const menuWidth = 180;
    const menuHeight = 280; // 大致高度
    if (left + menuWidth > window.innerWidth - 8) {
        left = window.innerWidth - menuWidth - 8;
    }
    if (left < 8) left = 8;
    if (top + menuHeight > window.innerHeight - 8) {
        top = (clickY ?? anchorEl.getBoundingClientRect().bottom) - menuHeight - 10;
    }
    if (top < 8) top = 8;

    doubleClickActionMenu.style.left = `${left}px`;
    doubleClickActionMenu.style.top = `${top}px`;
    doubleClickActionMenu.classList.add('active');
}

function hideDoubleClickActionMenu() {
    doubleClickActionMenu.classList.remove('active');
    activeDoubleClickMessageId = null;
}

// 双击操作菜单点击委托
function initDoubleClickActionMenu() {
    doubleClickActionMenu.addEventListener('click', (e) => {
        const item = e.target.closest('.action-menu-item');
        if (!item || activeDoubleClickMessageId === null) return;
        const action = item.dataset.action;
        const messageId = activeDoubleClickMessageId;
        const message = messages.find(m => m.id === messageId);
        if (!message) return;

        hideDoubleClickActionMenu();

        switch (action) {
            case 'copy': {
                navigator.clipboard.writeText(message.content).then(() => {
                    showToast('已复制到剪贴板');
                });
                break;
            }
            case 'reply': {
                replyMessage(messageId);
                break;
            }
            case 'forward': {
                forwardMessage(messageId);
                break;
            }
            case 'react': {
                // 显示反应选择器，定位在消息上方
                const msgEl = messagesList.querySelector(`[data-message-id="${messageId}"]`);
                if (msgEl) {
                    showReactionPicker(messageId, msgEl);
                }
                break;
            }
            case 'favorite': {
                const index = favoriteMessages.indexOf(messageId);
                if (index > -1) {
                    favoriteMessages.splice(index, 1);
                    showToast('已取消收藏');
                } else {
                    favoriteMessages.push(messageId);
                    showToast('已收藏');
                }
                localStorage.setItem('favoriteMessages', JSON.stringify(favoriteMessages));
                renderMessages();
                break;
            }
            case 'delete': {
                deleteMessage(messageId);
                break;
            }
        }
    });
}

// ==================== 创建消息元素 ====================
function createMessageElement(message) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.isUser ? 'user-message' : 'bot-message'}`;
    messageElement.dataset.messageId = message.id;

    const isFavorite = favoriteMessages.includes(message.id);
    messageElement.innerHTML = `
        <div class="message-menu">
            <button class="menu-react-btn" data-action="react" data-id="${message.id}" title="添加反应">😊</button>
            <button data-action="reply" data-id="${message.id}" title="回复">↩️</button>
            <button data-action="forward" data-id="${message.id}" title="转发">➡️</button>
            <button data-action="copy" data-id="${message.id}" title="复制">📋</button>
            <button data-action="favorite" data-id="${message.id}" title="${isFavorite ? '取消收藏' : '收藏'}">${isFavorite ? '❤️' : '🤍'}</button>
            <button data-action="delete" data-id="${message.id}" title="删除">🗑️</button>
        </div>
        <div class="message-wrapper">
            <div class="message-content">${escapeHtml(message.content)}</div>
            ${renderReactions(message.id)}
            <div class="message-time">${message.time}</div>
            <div class="message-status">
                ${message.isUser ? (message.isRead ? '✓✓' : '✓') : ''}
            </div>
        </div>
    `;

    // 菜单事件委托
    messageElement.querySelector('.message-menu').addEventListener('click', (e) => {
        const btn = e.target.closest('button[data-action]');
        if (!btn) return;
        const action = btn.dataset.action;
        const id = parseInt(btn.dataset.id);
        e.stopPropagation();
        switch (action) {
            case 'reply': replyMessage(id); break;
            case 'forward': forwardMessage(id); break;
            case 'copy': copyMessage(id, btn); break;
            case 'favorite': toggleFavorite(id, btn); break;
            case 'delete': deleteMessage(id); break;
            case 'react': showReactionPickerForButton(id, btn); break;
        }
    });

    // 反应徽章点击
    messageElement.querySelectorAll('.reaction-badge').forEach(badge => {
        badge.addEventListener('click', (e) => {
            e.stopPropagation();
            const mid = parseInt(badge.dataset.messageId);
            const emoji = badge.dataset.emoji;
            toggleReaction(mid, emoji);
        });
    });

    // 双击弹出操作菜单
    messageElement.querySelector('.message-content').addEventListener('dblclick', (e) => {
        e.stopPropagation();
        const contentEl = e.currentTarget;
        contentEl.classList.add('reacting');
        setTimeout(() => contentEl.classList.remove('reacting'), 400);
        showDoubleClickActionMenu(message.id, messageElement, e);
    });

    return messageElement;
}

function showReactionPickerForButton(messageId, btn) {
    showReactionPicker(messageId, btn);
}

// 简单的HTML转义，防止XSS
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ==================== 删除消息 ====================
function deleteMessage(messageId) {
    const index = messages.findIndex(m => m.id === messageId);
    if (index > -1) {
        messages.splice(index, 1);
        saveMessages();
        delete messageReactions[messageId];
        delete myReactions[messageId];
        localStorage.setItem('messageReactions', JSON.stringify(messageReactions));
        localStorage.setItem('myReactions', JSON.stringify(myReactions));
        renderMessages();
        showToast('消息已删除');
    }
}

// ==================== 渲染消息列表 ====================
function renderMessages() {
    messagesList.innerHTML = '';
    let lastDateLabel = null;
    messages.forEach(message => {
        // 日期分隔符
        const dateLabel = getDateLabel(message.timestamp || Date.now());
        if (dateLabel !== lastDateLabel) {
            messagesList.appendChild(createDateSeparator(dateLabel));
            lastDateLabel = dateLabel;
        }
        messagesList.appendChild(createMessageElement(message));
    });
    updateEmptyState();
    if (isAtBottom) {
        scrollToBottom();
    }
}

// ==================== 添加单条消息 ====================
function appendMessage(message) {
    messages.push(message);
    saveMessages();
    // 检查是否需要日期分隔符
    const prevMessage = messages[messages.length - 2];
    const dateLabel = getDateLabel(message.timestamp);
    const prevDateLabel = prevMessage ? getDateLabel(prevMessage.timestamp) : null;

    if (dateLabel !== prevDateLabel) {
        messagesList.appendChild(createDateSeparator(dateLabel));
    }
    messagesList.appendChild(createMessageElement(message));

    updateEmptyState();

    // 如果用户不在底部，增加未读计数
    if (isScrolledToBottom()) {
        scrollToBottom();
    } else {
        if (message.isUser) {
            scrollToBottom();
        } else {
            unreadCount++;
            updateNewMessageBadge();
            showScrollBottomBtn();
        }
    }
}

// ==================== 时间格式化 ====================
function getFormattedTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// ==================== Mock回复数据 ====================
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

function getRandomReply() {
    return mockReplies[Math.floor(Math.random() * mockReplies.length)];
}

// ==================== 发送消息 ====================
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
        timestamp: Date.now(),
        isUser: true
    };

    appendMessage(userMessage);
    messageInput.value = '';
    updateCharCounter();

    // 发送特效
    createSendEffect();

    // 显示打字状态
    showTypingIndicator();
    updateOnlineStatus('typing');

    // Mock回复
    setTimeout(() => {
        hideTypingIndicator();
        updateOnlineStatus('online');
        const botMessage = {
            id: messageIdCounter++,
            content: getRandomReply(),
            time: getFormattedTime(),
            timestamp: Date.now(),
            isUser: false
        };
        appendMessage(botMessage);
        // 更新已发送消息的状态为已读
        userMessage.isRead = true;
        saveMessages();
        renderMessages();
    }, 1000 + Math.random() * 1000);
}

// ==================== 发送特效 ====================
function createSendEffect() {
    const effect = document.createElement('div');
    effect.className = 'send-effect';
    sendBtn.appendChild(effect);
    setTimeout(() => {
        effect.remove();
    }, 600);
}

// ==================== 连击提示 ====================
function showCombo(count) {
    comboText.textContent = '连击！';
    comboCount.textContent = `x${count}`;
    comboNotification.classList.add('active');
    setTimeout(() => {
        comboNotification.classList.remove('active');
    }, 800);
}

// ==================== 打字状态 ====================
function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// ==================== 在线状态 ====================
function updateOnlineStatus(status) {
    if (status === 'typing') {
        onlineStatusText.textContent = '正在输入...';
    } else if (status === 'online') {
        onlineStatusText.textContent = '在线';
    }
}

// ==================== 搜索消息 ====================
function searchMessages(query) {
    if (!query.trim()) {
        renderMessages();
        return;
    }

    const filtered = messages.filter(m =>
        m.content.toLowerCase().includes(query.toLowerCase())
    );

    messagesList.innerHTML = '';
    if (filtered.length === 0) {
        messagesList.innerHTML = '<div style="text-align:center;padding:32px;color:var(--text-muted);font-size:14px;">没有找到相关消息</div>';
        return;
    }
    filtered.forEach(message => {
        const element = createMessageElement(message);
        // 高亮搜索关键词
        const contentEl = element.querySelector('.message-content');
        const escaped = escapeHtml(message.content);
        contentEl.innerHTML = escaped.replace(
            new RegExp(escapeRegExp(query), 'gi'),
            '<span class="highlight">$&</span>'
        );
        messagesList.appendChild(element);
    });
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ==================== 主题切换 ====================
function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    localStorage.setItem('chatTheme', currentTheme);
    document.body.classList.toggle('dark-theme', currentTheme === 'dark');
    themeToggle.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
    showToast(currentTheme === 'dark' ? '已切换到深色模式' : '已切换到浅色模式');
}

// ==================== 收藏消息 ====================
function toggleFavorite(messageId, btn) {
    const index = favoriteMessages.indexOf(messageId);
    if (index > -1) {
        favoriteMessages.splice(index, 1);
        btn.textContent = '🤍';
        btn.title = '收藏';
        showToast('已取消收藏');
    } else {
        favoriteMessages.push(messageId);
        btn.textContent = '❤️';
        btn.title = '取消收藏';
        showToast('已收藏');
    }
    localStorage.setItem('favoriteMessages', JSON.stringify(favoriteMessages));
}

// ==================== 回复消息 ====================
function replyMessage(messageId) {
    const message = messages.find(m => m.id === messageId);
    if (message) {
        messageInput.value = `回复: ${message.content.substring(0, 20)}${message.content.length > 20 ? '...' : ''} `;
        messageInput.focus();
        updateCharCounter();
        emojiPicker.classList.remove('active');
    }
}

// ==================== 转发消息 ====================
function forwardMessage(messageId) {
    const message = messages.find(m => m.id === messageId);
    if (message) {
        navigator.clipboard.writeText(message.content).then(() => {
            showToast('内容已复制，可以转发啦！');
        });
    }
}

// ==================== 复制消息 ====================
function copyMessage(messageId, btn) {
    const message = messages.find(m => m.id === messageId);
    if (message) {
        navigator.clipboard.writeText(message.content).then(() => {
            showToast('已复制到剪贴板');
            // 复制成功动画
            const contentEl = btn.closest('.message').querySelector('.message-content');
            contentEl.classList.add('copy-success');
            setTimeout(() => contentEl.classList.remove('copy-success'), 500);
        });
    }
}

// ==================== 滚动事件处理 ====================
function handleScroll() {
    // 顶部按钮
    if (chatMessages.scrollTop > 300) {
        scrollTopBtn.classList.add('active');
    } else {
        scrollTopBtn.classList.remove('active');
    }
    // 底部按钮
    if (isScrolledToBottom()) {
        isAtBottom = true;
        unreadCount = 0;
        updateNewMessageBadge();
        hideScrollBottomBtn();
    } else {
        isAtBottom = false;
        showScrollBottomBtn();
    }
}

// ==================== 快捷键面板 ====================
function showShortcuts() {
    shortcutsOverlay.classList.add('active');
}

function hideShortcuts() {
    shortcutsOverlay.classList.remove('active');
}

// ==================== 设置面板 ====================
function showSettings() {
    // 同步深色模式开关状态
    settingsThemeToggle.checked = currentTheme === 'dark';
    settingsOverlay.classList.add('active');
}

function hideSettings() {
    settingsOverlay.classList.remove('active');
}

// 清除所有聊天记录（当前对话 + 历史会话）
function clearAllChatData() {
    if (messages.length === 0 && !localStorage.getItem('chatSessions')) {
        showToast('没有可清除的记录');
        return;
    }
    if (!confirm('确定要清除所有聊天记录吗？此操作不可恢复。')) return;

    // 清空当前消息
    messages.length = 0;
    messageIdCounter = 0;
    // 清空反应/收藏
    for (const k of Object.keys(messageReactions)) delete messageReactions[k];
    for (const k of Object.keys(myReactions)) delete myReactions[k];
    favoriteMessages.length = 0;
    // 清空历史会话
    localStorage.removeItem('chatSessions');
    // 持久化
    saveMessages();
    localStorage.setItem('messageReactions', '{}');
    localStorage.setItem('myReactions', '{}');
    localStorage.setItem('favoriteMessages', '[]');

    // 重新渲染
    renderMessages();
    updateEmptyState();
    if (historySidebar.classList.contains('active')) {
        renderHistoryList();
    }
    showToast('已清除所有聊天记录');
    hideSettings();
}

// 导出聊天记录为文本文件
function exportChatRecords() {
    if (messages.length === 0) {
        showToast('暂无消息可导出');
        return;
    }
    const lines = messages.map(m => {
        const role = m.isUser ? '我' : '助手';
        return `[${m.time}] ${role}：${m.content}`;
    });
    const text = '智能助手 - 聊天记录\n' + '='.repeat(40) + '\n\n' + lines.join('\n\n');
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `聊天记录_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('聊天记录已导出');
}

// ==================== 初始化事件监听 ====================
function initEventListeners() {
    // 发送按钮点击
    sendBtn.addEventListener('click', (e) => {
        createRipple(e);
        sendMessage();
    });

    // 输入框监听
    messageInput.addEventListener('input', updateCharCounter);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 表情按钮点击
    emojiBtn.addEventListener('click', (e) => {
        createRipple(e);
        e.stopPropagation();
        emojiPicker.classList.toggle('active');
    });

    // 点击其他区域关闭表情选择器
    document.addEventListener('click', (e) => {
        if (!emojiBtn.contains(e.target) && !emojiPicker.contains(e.target)) {
            emojiPicker.classList.remove('active');
        }
        // 关闭反应选择器
        if (!reactionPicker.contains(e.target)) {
            const reactBtn = e.target.closest('[data-action="react"]');
            if (!reactBtn) hideReactionPicker();
        }
        // 关闭双击操作菜单
        if (!doubleClickActionMenu.contains(e.target)) {
            hideDoubleClickActionMenu();
        }
    });

    // 反应选择器点击
    reactionPicker.addEventListener('click', (e) => {
        const item = e.target.closest('.reaction-item');
        if (item && activeReactionMessageId !== null) {
            toggleReaction(activeReactionMessageId, item.dataset.reaction);
            hideReactionPicker();
        }
    });

    // 滚动事件
    chatMessages.addEventListener('scroll', handleScroll);

    // 滚动按钮
    scrollTopBtn.addEventListener('click', (e) => {
        createRipple(e);
        scrollToTop();
    });
    scrollBottomBtn.addEventListener('click', (e) => {
        createRipple(e);
        scrollToBottom();
    });

    // 搜索功能
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchMessages(e.target.value);
        });
    }

    // 主题切换
    if (themeToggle) {
        themeToggle.addEventListener('click', (e) => {
            createRipple(e);
            toggleTheme();
        });
    }

    // 快捷键面板
    shortcutsBtn.addEventListener('click', (e) => {
        createRipple(e);
        showShortcuts();
    });
    shortcutsClose.addEventListener('click', hideShortcuts);
    shortcutsOverlay.addEventListener('click', (e) => {
        if (e.target === shortcutsOverlay) hideShortcuts();
    });

    // 设置面板
    settingsBtn.addEventListener('click', (e) => {
        createRipple(e);
        showSettings();
    });
    settingsClose.addEventListener('click', hideSettings);
    settingsOverlay.addEventListener('click', (e) => {
        if (e.target === settingsOverlay) hideSettings();
    });
    // 深色模式开关
    settingsThemeToggle.addEventListener('change', () => {
        toggleTheme();
        settingsThemeToggle.checked = currentTheme === 'dark';
    });
    // 清除聊天记录
    settingsClearChat.addEventListener('click', clearAllChatData);
    // 导出聊天记录
    settingsExport.addEventListener('click', exportChatRecords);
    // 快捷键入口
    settingsShortcuts.addEventListener('click', () => {
        hideSettings();
        showShortcuts();
    });
    // 关于
    settingsAbout.addEventListener('click', () => {
        showToast('智能助手 v1.0 · 让学习更高效');
    });

    // 建议卡片点击
    document.querySelectorAll('.suggestion-card').forEach(card => {
        card.addEventListener('click', (e) => {
            createRipple(e);
            sendMessage(card.dataset.suggestion);
        });
    });

    // 涟漪效果 - 所有按钮和卡片
    document.querySelectorAll('.header-btn, .input-btn, .suggestion-card').forEach(el => {
        el.addEventListener('click', createRipple);
    });

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + / 聚焦搜索框
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            searchInput?.focus();
            return;
        }
        // Ctrl/Cmd + Enter 发送消息
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
            return;
        }
        // Ctrl/Cmd + D 切换主题
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            toggleTheme();
            return;
        }
        // Ctrl/Cmd + E 打开表情
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            emojiPicker.classList.toggle('active');
            messageInput.focus();
            return;
        }
        // ? 查看快捷键（不在输入框中时）
        if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
            e.preventDefault();
            showShortcuts();
            return;
        }
        // ESC 关闭弹窗
        if (e.key === 'Escape') {
            emojiPicker.classList.remove('active');
            hideReactionPicker();
            hideShortcuts();
            hideSettings();
            hideDoubleClickActionMenu();
        }
    });

    // 窗口失焦时关闭弹层
    window.addEventListener('blur', () => {
        hideReactionPicker();
        hideDoubleClickActionMenu();
    });
}

// ==================== 初始化页面 ====================
function init() {
    // 应用主题
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeToggle.textContent = '☀️';
    }

    renderEmojiPicker();
    initDoubleClickActionMenu();
    initEventListeners();
    initHistoryFeatures();
    updateCharCounter();
    updateOnlineStatus('online');

    if (messages.length > 0) {
        // 恢复历史消息
        renderMessages();
        // 等待DOM渲染完成后再滚动到底部
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                scrollToBottom();
            });
        });
    } else {
        // 首次访问，显示空状态后添加欢迎消息
        updateEmptyState();
        setTimeout(() => {
            const welcomeMessage = {
                id: messageIdCounter++,
                content: '你好呀！很高兴认识你！😊 有什么我可以帮你的吗？',
                time: getFormattedTime(),
                timestamp: Date.now(),
                isUser: false
            };
            appendMessage(welcomeMessage);
        }, 500);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// ==================== 新对话 & 历史聊天记录 ====================
const STORAGE_KEY_SESSIONS = 'chatSessions';

// 所有历史会话 [{ id, title, createdAt, messages }]
const chatSessions = JSON.parse(localStorage.getItem(STORAGE_KEY_SESSIONS) || '[]');

// 历史面板 DOM
const historyToggleBtn = document.getElementById('historyToggleBtn');
const historySidebar = document.getElementById('historySidebar');
const historySidebarClose = document.getElementById('historySidebarClose');
const historyList = document.getElementById('historyList');
const historyEmpty = document.getElementById('historyEmpty');
const historySearchInput = document.getElementById('historySearchInput');
const historyDetailOverlay = document.getElementById('historyDetailOverlay');
const historyDetailTitle = document.getElementById('historyDetailTitle');
const historyDetailBody = document.getElementById('historyDetailBody');
const historyDetailClose = document.getElementById('historyDetailClose');
const historyDetailRestore = document.getElementById('historyDetailRestore');
const historyDetailDelete = document.getElementById('historyDetailDelete');
const newChatBtn = document.getElementById('newChatBtn');

// 当前正在查看的历史会话ID
let viewingSessionId = null;

// 保存历史会话列表
function saveSessions() {
    try {
        localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(chatSessions));
    } catch (e) {
        console.error('保存历史会话失败:', e);
    }
}

// 根据消息生成会话标题（取第一条用户消息，否则取第一条消息）
function generateSessionTitle(msgs) {
    if (!msgs || msgs.length === 0) return '空对话';
    const firstUser = msgs.find(m => m.isUser);
    const target = firstUser || msgs[0];
    let title = target.content.replace(/\s+/g, ' ').trim();
    if (title.length > 24) title = title.substring(0, 24) + '...';
    return title || '空对话';
}

// 格式化会话时间
function formatSessionTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const msgDate = new Date(date);
    msgDate.setHours(0, 0, 0, 0);
    if (msgDate.getTime() === today.getTime()) return '今天';
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (msgDate.getTime() === yesterday.getTime()) return '昨天';
    return `${date.getMonth() + 1}月${date.getDate()}日`;
}

// 将当前对话保存为历史会话
function saveCurrentAsSession() {
    // 只有欢迎消息或无消息时不保存
    if (messages.length === 0) return null;
    if (messages.length === 1 && !messages[0].isUser) return null;

    const session = {
        id: 'session_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
        title: generateSessionTitle(messages),
        createdAt: Date.now(),
        messages: JSON.parse(JSON.stringify(messages))
    };
    chatSessions.unshift(session);
    saveSessions();
    return session;
}

// 创建新对话（保存当前并清空）
function startNewChat() {
    // 如果当前有实质对话，先保存
    const hasRealConversation = messages.length > 1 ||
        (messages.length === 1 && messages[0].isUser);
    if (hasRealConversation) {
        saveCurrentAsSession();
        showToast('当前对话已保存到历史记录');
    }

    // 清空当前消息
    messages.length = 0;
    // 清空与消息关联的反应/收藏（避免孤儿数据）
    for (const k of Object.keys(messageReactions)) delete messageReactions[k];
    for (const k of Object.keys(myReactions)) delete myReactions[k];
    favoriteMessages.length = 0;
    localStorage.setItem('messageReactions', '{}');
    localStorage.setItem('myReactions', '{}');
    localStorage.setItem('favoriteMessages', '[]');
    saveMessages();

    // 重新渲染
    renderMessages();
    updateEmptyState();

    // 添加新的欢迎消息
    setTimeout(() => {
        const welcomeMessage = {
            id: messageIdCounter++,
            content: '你好呀！很高兴认识你！😊 有什么我可以帮你的吗？',
            time: getFormattedTime(),
            timestamp: Date.now(),
            isUser: false
        };
        appendMessage(welcomeMessage);
    }, 200);

    // 刷新历史列表（如果侧边栏打开着）
    if (historySidebar.classList.contains('active')) {
        renderHistoryList();
    }
}

// 渲染历史会话列表
function renderHistoryList(filter = '') {
    historyList.innerHTML = '';
    const filtered = filter
        ? chatSessions.filter(s =>
            s.title.toLowerCase().includes(filter.toLowerCase()) ||
            s.messages.some(m => m.content.toLowerCase().includes(filter.toLowerCase()))
        )
        : chatSessions;

    if (filtered.length === 0) {
        historyEmpty.classList.remove('hidden');
        historyList.style.display = 'none';
        if (filter) {
            historyEmpty.querySelector('p').textContent = '没有匹配的历史会话';
        } else {
            historyEmpty.querySelector('p').textContent = '暂无历史聊天记录';
        }
        return;
    }

    historyEmpty.classList.add('hidden');
    historyList.style.display = 'block';

    filtered.forEach(session => {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.dataset.sessionId = session.id;
        const previewMsg = session.messages[session.messages.length - 1] || {};
        const preview = previewMsg.content ? previewMsg.content.replace(/\s+/g, ' ').trim() : '';
        item.innerHTML = `
            <div class="history-item-title">${escapeHtml(session.title)}</div>
            <div class="history-item-preview">${escapeHtml(preview)}</div>
            <div class="history-item-meta">
                <span class="history-item-time">${formatSessionTime(session.createdAt)}</span>
                <span class="history-item-count">${session.messages.length} 条</span>
            </div>
        `;
        item.addEventListener('click', () => openHistoryDetail(session.id));
        historyList.appendChild(item);
    });
}

// 打开历史会话详情
function openHistoryDetail(sessionId) {
    const session = chatSessions.find(s => s.id === sessionId);
    if (!session) return;
    viewingSessionId = sessionId;

    historyDetailTitle.textContent = session.title;
    historyDetailBody.innerHTML = '';

    // 渲染历史消息（只读模式，不带交互菜单）
    let lastDateLabel = null;
    session.messages.forEach(message => {
        const dateLabel = getDateLabel(message.timestamp || session.createdAt);
        if (dateLabel !== lastDateLabel) {
            const sep = document.createElement('div');
            sep.className = 'date-separator';
            sep.innerHTML = `<span>${dateLabel}</span>`;
            historyDetailBody.appendChild(sep);
            lastDateLabel = dateLabel;
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.isUser ? 'user-message' : 'bot-message'}`;
        messageElement.innerHTML = `
            <div class="message-wrapper">
                <div class="message-content">${escapeHtml(message.content)}</div>
                <div class="message-time">${message.time || ''}</div>
            </div>
        `;
        historyDetailBody.appendChild(messageElement);
    });

    historyDetailOverlay.classList.add('active');
}

// 关闭历史详情
function closeHistoryDetail() {
    historyDetailOverlay.classList.remove('active');
    viewingSessionId = null;
}

// 恢复历史会话到当前对话
function restoreHistorySession() {
    if (!viewingSessionId) return;
    const session = chatSessions.find(s => s.id === viewingSessionId);
    if (!session) return;

    // 先保存当前对话（如果有实质内容）
    const hasRealConversation = messages.length > 1 ||
        (messages.length === 1 && messages[0].isUser);
    if (hasRealConversation) {
        saveCurrentAsSession();
    }

    // 用历史会话替换当前消息
    messages.length = 0;
    // 深拷贝历史消息，并重新分配ID避免冲突
    const idMap = {};
    session.messages.forEach(oldMsg => {
        const newId = messageIdCounter++;
        idMap[oldMsg.id] = newId;
        messages.push({
            ...oldMsg,
            id: newId
        });
    });

    // 迁移该会话的反应数据（如果有）
    // 由于历史会话通常不带反应，这里简单清空当前反应
    for (const k of Object.keys(messageReactions)) delete messageReactions[k];
    for (const k of Object.keys(myReactions)) delete myReactions[k];
    favoriteMessages.length = 0;
    localStorage.setItem('messageReactions', '{}');
    localStorage.setItem('myReactions', '{}');
    localStorage.setItem('favoriteMessages', '[]');

    saveMessages();
    renderMessages();
    closeHistoryDetail();
    closeHistorySidebar();
    showToast('已恢复历史会话到当前对话');
}

// 删除历史会话
function deleteHistorySession() {
    if (!viewingSessionId) return;
    const index = chatSessions.findIndex(s => s.id === viewingSessionId);
    if (index === -1) return;
    chatSessions.splice(index, 1);
    saveSessions();
    closeHistoryDetail();
    renderHistoryList(historySearchInput.value);
    showToast('历史会话已删除');
}

// 打开/关闭历史侧边栏
function openHistorySidebar() {
    renderHistoryList(historySearchInput.value);
    historySidebar.classList.add('active');
}

function closeHistorySidebar() {
    historySidebar.classList.remove('active');
}

function toggleHistorySidebar() {
    if (historySidebar.classList.contains('active')) {
        closeHistorySidebar();
    } else {
        openHistorySidebar();
    }
}

// 初始化历史 & 新对话事件
function initHistoryFeatures() {
    historyToggleBtn.addEventListener('click', (e) => {
        createRipple(e);
        toggleHistorySidebar();
    });
    historySidebarClose.addEventListener('click', closeHistorySidebar);
    newChatBtn.addEventListener('click', (e) => {
        createRipple(e);
        startNewChat();
    });

    historySearchInput.addEventListener('input', (e) => {
        renderHistoryList(e.target.value);
    });

    historyDetailClose.addEventListener('click', closeHistoryDetail);
    historyDetailOverlay.addEventListener('click', (e) => {
        if (e.target === historyDetailOverlay) closeHistoryDetail();
    });
    historyDetailRestore.addEventListener('click', restoreHistorySession);
    historyDetailDelete.addEventListener('click', deleteHistorySession);

    // 快捷键 Ctrl+N 新对话
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            startNewChat();
        }
        if (e.key === 'Escape') {
            if (historyDetailOverlay.classList.contains('active')) {
                closeHistoryDetail();
            } else if (historySidebar.classList.contains('active')) {
                closeHistorySidebar();
            }
        }
    });
}
