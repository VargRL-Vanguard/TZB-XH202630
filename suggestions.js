/**
 * 个性化学习建议 - 前端逻辑
 * 预留后端接口，当前使用Mock数据
 */

// ==================== API配置 ====================
const API_CONFIG = {
    baseURL: 'http://localhost:3000/api',
    useRealAPI: false,
    timeout: 10000
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
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            clearTimeout(timeoutId);
            console.error('请求失败:', err);
            return null;
        }
    }
    return null;
}

// ==================== Mock数据 ====================
const mockSuggestions = [
    {
        id: 1,
        title: '加强函数参数传递练习',
        content: '根据近期学习数据分析，你在函数参数传递（尤其是默认参数和关键字参数）方面存在薄弱环节。建议每天完成3道相关练习题，重点理解*args和**kwargs的使用场景。',
        category: 'practice',
        categoryLabel: '练习推荐',
        priority: 'high',
        priorityLabel: '重要',
        source: '基于最近3次测验结果'
    },
    {
        id: 2,
        title: '推荐观看Python函数教学视频',
        content: '发现你更倾向于通过视频学习，推荐观看"Python函数高级用法"系列课程（共5集，约2小时）。该课程由资深讲师讲解，配合实例演示，适合你的学习风格。',
        category: 'resource',
        categoryLabel: '学习资源',
        priority: 'medium',
        priorityLabel: '推荐',
        source: '基于学习风格分析'
    },
    {
        id: 3,
        title: '调整学习时间段',
        content: '数据显示你在晚上8-10点的学习效率最高（正确率85%），建议将难度较大的内容安排在此时间段学习。上午时段适合复习和轻度练习。',
        category: 'method',
        categoryLabel: '学习方法',
        priority: 'medium',
        priorityLabel: '推荐',
        source: '基于学习行为分析'
    },
    {
        id: 4,
        title: '复习基础语法中的循环结构',
        content: '你在for循环和while循环的嵌套使用上容易出错。建议回顾第2章内容，重点练习循环控制语句（break、continue）的使用，并完成配套的10道练习题。',
        category: 'review',
        categoryLabel: '复习建议',
        priority: 'high',
        priorityLabel: '重要',
        source: '基于错题分析'
    },
    {
        id: 5,
        title: '尝试项目驱动学习法',
        content: '你的理论学习进度良好，但实践应用较少。建议通过完成小型项目（如计算器、待办事项应用）来巩固所学知识，提升实际编程能力。',
        category: 'method',
        categoryLabel: '学习方法',
        priority: 'low',
        priorityLabel: '建议',
        source: '基于学习进度分析'
    },
    {
        id: 6,
        title: '推荐Python官方文档阅读',
        content: '针对你当前学习的模块导入部分，推荐阅读Python官方文档中关于"Modules and Packages"的章节。文档内容权威且详细，有助于深入理解模块机制。',
        category: 'resource',
        categoryLabel: '学习资源',
        priority: 'low',
        priorityLabel: '建议',
        source: '基于当前学习模块'
    }
];

// ==================== 后端接口定义 ====================
/**
 * 获取学习建议列表
 * GET /api/suggestions/list?category=all
 * 返回: [{ id, title, content, category, categoryLabel, priority, priorityLabel, source }]
 */
async function getSuggestions(category = 'all') {
    if (API_CONFIG.useRealAPI) {
        return await request(`/suggestions/list?category=${category}`);
    }
    if (category === 'all') return mockSuggestions;
    return mockSuggestions.filter(s => s.category === category);
}

/**
 * 获取AI生成的建议结果
 * GET /api/suggestions/ai-result
 * 返回: { content: string, generatedAt: string }
 */
async function getAIResult() {
    if (API_CONFIG.useRealAPI) {
        return await request('/suggestions/ai-result');
    }
    return null;
}

/**
 * 标记建议为已读
 * POST /api/suggestions/read
 * 参数: { id: number }
 * 返回: { success: boolean }
 */
async function markAsRead(id) {
    if (API_CONFIG.useRealAPI) {
        return await request('/suggestions/read', {
            method: 'POST',
            body: JSON.stringify({ id })
        });
    }
    console.log('建议已标记为已读（Mock）:', id);
    return { success: true };
}

// ==================== 页面渲染 ====================
let currentCategory = 'all';

function renderSuggestions(items) {
    const container = document.getElementById('suggestionList');
    if (items.length === 0) {
        container.innerHTML = '<div class="placeholder-text">暂无相关建议</div>';
        return;
    }
    container.innerHTML = items.map(item => `
        <div class="suggestion-item" data-id="${item.id}">
            <div class="suggestion-header">
                <span class="suggestion-title">${item.title}</span>
                <span class="suggestion-category">${item.categoryLabel}</span>
            </div>
            <div class="suggestion-content">${item.content}</div>
            <div class="suggestion-meta">
                <span class="suggestion-priority priority-${item.priority}">${item.priorityLabel}</span>
                <span>${item.source}</span>
            </div>
        </div>
    `).join('');
}

function renderAIResult(content) {
    const container = document.getElementById('aiOutput');
    if (content) {
        container.innerHTML = `<div style="font-size:14px;color:#374151;line-height:1.8;">${content}</div>`;
    }
}

// 标签切换
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentCategory = btn.dataset.category;
        const data = await getSuggestions(currentCategory);
        if (data) renderSuggestions(data);
    });
});

// ==================== 初始化 ====================
async function init() {
    const data = await getSuggestions('all');
    if (data) {
        renderSuggestions(data);
        document.getElementById('suggestionCount').textContent = data.length;
    }
    const aiResult = await getAIResult();
    if (aiResult && aiResult.content) renderAIResult(aiResult.content);
}

document.addEventListener('DOMContentLoaded', init);
