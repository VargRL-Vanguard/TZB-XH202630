/**
 * 个性化学习路径 - 前端逻辑
 * 预留后端接口，当前使用Mock数据
 */

// ==================== API配置 ====================
const API_CONFIG = {
    baseURL: 'http://localhost:3000/api', // 后端基础地址，修改为实际地址
    useRealAPI: false, // false=使用Mock数据，true=调用真实API
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
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
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
const mockData = {
    // 学习路径时间线
    timeline: [
        {
            id: 1,
            title: 'Python基础语法',
            desc: '变量、数据类型、运算符、条件语句',
            status: 'completed',
            progress: 100,
            duration: '3天',
            startDate: '2026-07-10',
            endDate: '2026-07-13'
        },
        {
            id: 2,
            title: '函数与模块',
            desc: '函数定义、参数传递、模块导入',
            status: 'current',
            progress: 45,
            duration: '2天',
            startDate: '2026-07-14',
            endDate: '2026-07-16'
        },
        {
            id: 3,
            title: '面向对象编程',
            desc: '类与对象、继承、多态',
            status: 'pending',
            progress: 0,
            duration: '3天',
            startDate: '2026-07-17',
            endDate: '2026-07-20'
        },
        {
            id: 4,
            title: '文件操作与异常处理',
            desc: '文件读写、异常捕获、上下文管理',
            status: 'pending',
            progress: 0,
            duration: '2天',
            startDate: '2026-07-21',
            endDate: '2026-07-23'
        },
        {
            id: 5,
            title: '综合项目实战',
            desc: '完成一个完整的小型项目',
            status: 'pending',
            progress: 0,
            duration: '2天',
            startDate: '2026-07-24',
            endDate: '2026-07-26'
        }
    ],
    // 知识模块
    modules: [
        { name: '基础语法', progress: 85, desc: '变量、运算符、流程控制' },
        { name: '函数编程', progress: 45, desc: '函数定义、lambda、闭包' },
        { name: '数据结构', progress: 60, desc: '列表、字典、集合、元组' },
        { name: '面向对象', progress: 20, desc: '类、继承、封装、多态' },
        { name: '文件IO', progress: 10, desc: '文件读写、CSV、JSON' },
        { name: '异常处理', progress: 5, desc: 'try-except、自定义异常' }
    ],
    // 今日任务
    tasks: [
        { id: 1, title: '完成函数参数传递练习', meta: '预计30分钟 · 函数与模块', priority: 'high', completed: true },
        { id: 2, title: '学习模块导入与包管理', meta: '预计45分钟 · 函数与模块', priority: 'high', completed: false },
        { id: 3, title: '完成课后练习题5道', meta: '预计20分钟 · 函数与模块', priority: 'medium', completed: false },
        { id: 4, title: '复习基础语法知识点', meta: '预计15分钟 · 基础语法', priority: 'low', completed: false }
    ]
};

// ==================== 后端接口定义 ====================
/**
 * 获取学习路径数据
 * GET /api/learning-path/overview
 * 返回: { target, progress, estimatedDays }
 */
async function getLearningPathOverview() {
    if (API_CONFIG.useRealAPI) {
        return await request('/learning-path/overview');
    }
    return { target: '掌握Python基础编程', progress: 35, estimatedDays: 12 };
}

/**
 * 获取学习路径时间线
 * GET /api/learning-path/timeline
 * 返回: [{ id, title, desc, status, progress, duration, startDate, endDate }]
 */
async function getLearningPathTimeline() {
    if (API_CONFIG.useRealAPI) {
        return await request('/learning-path/timeline');
    }
    return mockData.timeline;
}

/**
 * 获取知识模块数据
 * GET /api/learning-path/modules
 * 返回: [{ name, progress, desc }]
 */
async function getKnowledgeModules() {
    if (API_CONFIG.useRealAPI) {
        return await request('/learning-path/modules');
    }
    return mockData.modules;
}

/**
 * 获取今日任务
 * GET /api/learning-path/tasks
 * 返回: [{ id, title, meta, priority, completed }]
 */
async function getDailyTasks() {
    if (API_CONFIG.useRealAPI) {
        return await request('/learning-path/tasks');
    }
    return mockData.tasks;
}

/**
 * 提交AI生成的学习路径结果
 * POST /api/learning-path/ai-result
 * 参数: { content: string }
 * 返回: { success: boolean }
 */
async function submitAIResult(content) {
    if (API_CONFIG.useRealAPI) {
        return await request('/learning-path/ai-result', {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }
    console.log('AI结果已提交（Mock）:', content);
    return { success: true };
}

/**
 * 获取AI生成的学习路径
 * GET /api/learning-path/ai-result
 * 返回: { content: string, generatedAt: string }
 */
async function getAIResult() {
    if (API_CONFIG.useRealAPI) {
        return await request('/learning-path/ai-result');
    }
    return null;
}

// ==================== 页面渲染 ====================

// 渲染时间线
function renderTimeline(items) {
    const container = document.getElementById('timeline');
    container.innerHTML = items.map(item => {
        const statusMap = {
            completed: '已完成',
            current: '进行中',
            pending: '待开始'
        };
        return `
            <div class="timeline-item ${item.status}">
                <div class="timeline-header">
                    <span class="timeline-title">${item.title}</span>
                    <span class="timeline-status ${item.status}">${statusMap[item.status]}</span>
                </div>
                <div class="timeline-desc">${item.desc}</div>
                <div class="timeline-meta">
                    <span> ${item.startDate} ~ ${item.endDate}</span>
                    <span>⏱️ ${item.duration}</span>
                    <span> 进度 ${item.progress}%</span>
                </div>
            </div>
        `;
    }).join('');
}

// 渲染知识模块
function renderModules(items) {
    const container = document.getElementById('moduleGrid');
    container.innerHTML = items.map(item => `
        <div class="module-card">
            <div class="module-header">
                <span class="module-name">${item.name}</span>
                <span class="module-progress">${item.progress}%</span>
            </div>
            <div class="module-bar">
                <div class="module-bar-fill" style="width: ${item.progress}%"></div>
            </div>
            <div class="module-desc">${item.desc}</div>
        </div>
    `).join('');
}

// 渲染每日任务
function renderTasks(items) {
    const container = document.getElementById('taskList');
    container.innerHTML = items.map(item => `
        <div class="task-item ${item.completed ? 'completed' : ''}">
            <div class="task-checkbox ${item.completed ? 'checked' : ''}" onclick="toggleTask(${item.id})"></div>
            <div class="task-content">
                <div class="task-title">${item.title}</div>
                <div class="task-meta">${item.meta}</div>
            </div>
            <span class="task-priority ${item.priority}">
                ${item.priority === 'high' ? '高' : item.priority === 'medium' ? '中' : '低'}
            </span>
        </div>
    `).join('');
}

// 渲染AI输出结果
function renderAIResult(content) {
    const container = document.getElementById('aiOutput');
    if (content) {
        container.innerHTML = `<div style="font-size:14px; color:#374151; line-height:1.8;">${content}</div>`;
    }
}

// 切换任务完成状态
function toggleTask(id) {
    const task = mockData.tasks.find(t => t.id === id);
    if (task) {
        task.completed = !task.completed;
        renderTasks(mockData.tasks);
    }
}

// ==================== 初始化 ====================
async function init() {
    // 加载概览数据
    const overview = await getLearningPathOverview();
    if (overview) {
        document.querySelector('.target-text').textContent = overview.target;
        document.querySelector('.progress-text').textContent = overview.progress + '%';
        document.querySelector('.time-text').textContent = overview.estimatedDays + '天';
    }

    // 加载时间线
    const timeline = await getLearningPathTimeline();
    if (timeline) renderTimeline(timeline);

    // 加载知识模块
    const modules = await getKnowledgeModules();
    if (modules) renderModules(modules);

    // 加载今日任务
    const tasks = await getDailyTasks();
    if (tasks) renderTasks(tasks);

    // 加载AI生成结果
    const aiResult = await getAIResult();
    if (aiResult && aiResult.content) {
        renderAIResult(aiResult.content);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
