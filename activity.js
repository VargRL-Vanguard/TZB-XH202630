/**
 * 学习活动记录 - 前端逻辑
 * 预留后端接口，当前使用Mock数据
 */

// ==================== API配置 ====================
const API_CONFIG = {
    baseURL: 'http://localhost:8000/api', // 后端接口地址（对齐后端端口）
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
const mockCourses = [
    {
        id: 1,
        title: 'Python基础语法',
        status: 'completed',
        statusLabel: '已完成',
        progress: 100,
        totalLessons: 8,
        completedLessons: 8,
        lastStudy: '2026-07-13 21:30'
    },
    {
        id: 2,
        title: '函数与模块',
        status: 'in-progress',
        statusLabel: '进行中',
        progress: 45,
        totalLessons: 6,
        completedLessons: 3,
        lastStudy: '2026-07-24 20:15'
    },
    {
        id: 3,
        title: '面向对象编程',
        status: 'not-started',
        statusLabel: '未开始',
        progress: 0,
        totalLessons: 7,
        completedLessons: 0,
        lastStudy: '-'
    },
    {
        id: 4,
        title: '文件操作与异常处理',
        status: 'not-started',
        statusLabel: '未开始',
        progress: 0,
        totalLessons: 5,
        completedLessons: 0,
        lastStudy: '-'
    },
    {
        id: 5,
        title: '数据结构基础',
        status: 'in-progress',
        statusLabel: '进行中',
        progress: 60,
        totalLessons: 6,
        completedLessons: 4,
        lastStudy: '2026-07-23 19:00'
    },
    {
        id: 6,
        title: 'Python标准库',
        status: 'completed',
        statusLabel: '已完成',
        progress: 100,
        totalLessons: 4,
        completedLessons: 4,
        lastStudy: '2026-07-10 22:00'
    }
];

const mockActivities = [
    { id: 1, title: '完成"函数参数传递"课程', desc: '学习了默认参数、关键字参数、*args和**kwargs', time: '20分钟前' },
    { id: 2, title: '完成课后练习5道', desc: '正确率80%，错题：第3题（闭包概念）', time: '1小时前' },
    { id: 3, title: '观看"模块导入机制"视频', desc: '学习时长25分钟，进度100%', time: '3小时前' },
    { id: 4, title: '参与AI辅导对话', desc: '讨论了Python装饰器的使用场景', time: '昨天 21:30' },
    { id: 5, title: '完成"列表推导式"练习', desc: '正确率100%，用时15分钟', time: '昨天 19:00' },
    { id: 6, title: '复习"条件语句"知识点', desc: '复习时长20分钟，完成3道测试题', time: '2天前' }
];

const mockCalendar = [
    { day: '一', date: 19, hours: 1.5 },
    { day: '二', date: 20, hours: 2.0 },
    { day: '三', date: 21, hours: 0.5 },
    { day: '四', date: 22, hours: 3.0 },
    { day: '五', date: 23, hours: 2.5 },
    { day: '六', date: 24, hours: 1.0, today: true },
    { day: '日', date: 25, hours: 0 }
];

// ==================== 后端接口定义 ====================
/**
 * 获取学习统计数据
 * GET /api/activity/stats
 * 返回: { totalHours, completedCourses, totalCourses, streakDays, completionRate }
 */
async function getStats() {
    if (API_CONFIG.useRealAPI) return await request('/activity/stats');
    return { totalHours: 48.5, completedCourses: 12, totalCourses: 20, streakDays: 7, completionRate: 60 };
}

/**
 * 获取课程列表
 * GET /api/activity/courses?filter=all
 * 返回: [{ id, title, status, statusLabel, progress, totalLessons, completedLessons, lastStudy }]
 */
async function getCourses(filter = 'all') {
    if (API_CONFIG.useRealAPI) return await request(`/activity/courses?filter=${filter}`);
    if (filter === 'all') return mockCourses;
    return mockCourses.filter(c => c.status === filter);
}

/**
 * 获取最近学习记录
 * GET /api/activity/recent?limit=10
 * 返回: [{ id, title, desc, time }]
 */
async function getRecentActivities(limit = 10) {
    if (API_CONFIG.useRealAPI) return await request(`/activity/recent?limit=${limit}`);
    return mockActivities.slice(0, limit);
}

/**
 * 获取每周学习日历
 * GET /api/activity/calendar
 * 返回: [{ day, date, hours, today }]
 */
async function getWeeklyCalendar() {
    if (API_CONFIG.useRealAPI) return await request('/activity/calendar');
    return mockCalendar;
}

/**
 * 记录学习活动
 * POST /api/activity/record
 * 参数: { type, courseId, duration, description }
 * 返回: { success: boolean, id: number }
 */
async function recordActivity(data) {
    if (API_CONFIG.useRealAPI) {
        return await request('/activity/record', { method: 'POST', body: JSON.stringify(data) });
    }
    console.log('活动已记录（Mock）:', data);
    return { success: true, id: Date.now() };
}

// ==================== 页面渲染 ====================

function renderCourses(items) {
    const container = document.getElementById('courseList');
    container.innerHTML = items.map(course => `
        <div class="course-item" data-id="${course.id}">
            <div class="course-header">
                <span class="course-title">${course.title}</span>
                <span class="course-status ${course.status}">${course.statusLabel}</span>
            </div>
            <div class="course-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${course.progress}%"></div>
                </div>
            </div>
            <div class="course-meta">
                <span>进度 ${course.progress}%</span>
                <span>课时 ${course.completedLessons}/${course.totalLessons}</span>
                <span>最近学习: ${course.lastStudy}</span>
            </div>
        </div>
    `).join('');
}

function renderActivities(items) {
    const container = document.getElementById('activityTimeline');
    container.innerHTML = items.map(item => `
        <div class="activity-item">
            <div class="activity-header">
                <span class="activity-title">${item.title}</span>
                <span class="activity-time">${item.time}</span>
            </div>
            <div class="activity-desc">${item.desc}</div>
        </div>
    `).join('');
}

function renderCalendar(items) {
    const container = document.getElementById('calendarGrid');
    container.innerHTML = items.map(day => `
        <div class="calendar-day ${day.today ? 'today' : ''}">
            <div class="day-name">${day.day}</div>
            <div class="day-date">${day.date}</div>
            <div class="day-hours">${day.hours > 0 ? day.hours + 'h' : '-'}</div>
        </div>
    `).join('');
}

// 筛选按钮切换
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const data = await getCourses(btn.dataset.filter);
        if (data) renderCourses(data);
    });
});

// ==================== 初始化 ====================
async function init() {
    const stats = await getStats();
    if (stats) {
        document.getElementById('totalHours').textContent = stats.totalHours + 'h';
        document.getElementById('completedCourses').textContent = stats.completedCourses + '/' + stats.totalCourses;
        document.getElementById('streakDays').textContent = stats.streakDays + '天';
        document.getElementById('completionRate').textContent = stats.completionRate + '%';
    }

    const courses = await getCourses('all');
    if (courses) renderCourses(courses);

    const activities = await getRecentActivities(6);
    if (activities) renderActivities(activities);

    const calendar = await getWeeklyCalendar();
    if (calendar) renderCalendar(calendar);
}

document.addEventListener('DOMContentLoaded', init);
