/**
 * 学情画像页面逻辑
 * 
 * API接口预留说明：
 * 后端需要实现以下接口，当前使用Mock数据作为fallback
 * 
 * 接口列表：
 * 1. GET /api/student/info - 获取学生基本信息
 * 2. GET /api/student/metrics - 获取核心指标数据
 * 3. GET /api/student/dimensions - 获取能力维度分析数据
 * 4. GET /api/student/behavior - 获取学习行为分析数据
 * 5. GET /api/student/knowledge - 获取知识掌握度数据
 * 6. GET /api/student/suggestions - 获取个性化学习建议
 */

// API配置
const API_CONFIG = {
    baseURL: 'http://localhost:3000/api', // 后端接口地址，部署时修改
    useRealAPI: false, // 是否启用真实API，后端就绪后改为true
    timeout: 10000
};

// Mock数据
const MOCK_DATA = {
    // 学生基本信息
    studentInfo: {
        name: '张三',
        studentId: '2024001',
        grade: '高三',
        class: '理科1班',
        enrollDate: '2021-09',
        avatar: '👨‍🎓',
        tags: ['学霸', '理科强', '活跃']
    },
    
    // 核心指标
    metrics: {
        totalStudyHours: 156,
        completionRate: 87,
        avgScore: 92,
        learningTrend: '上升'
    },
    
    // 能力维度
    dimensions: [
        { name: '逻辑思维', value: 85, color: '#6366f1' },
        { name: '空间想象', value: 78, color: '#8b5cf6' },
        { name: '运算能力', value: 92, color: '#ec4899' },
        { name: '数据分析', value: 80, color: '#f59e0b' },
        { name: '抽象理解', value: 75, color: '#10b981' },
        { name: '应用能力', value: 88, color: '#3b82f6' }
    ],
    
    // 学习行为数据（按周）
    behavior: {
        week: {
            labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            data: [2.5, 3.2, 2.8, 3.5, 4.0, 5.2, 4.8],
            stats: {
                totalHours: 26,
                avgDaily: 3.7,
                peakTime: '周六'
            }
        },
        month: {
            labels: ['第1周', '第2周', '第3周', '第4周'],
            data: [18, 22, 25, 28],
            stats: {
                totalHours: 93,
                avgDaily: 3.3,
                peakTime: '第4周'
            }
        },
        semester: {
            labels: ['9月', '10月', '11月', '12月', '1月'],
            data: [65, 78, 85, 92, 88],
            stats: {
                totalHours: 408,
                avgDaily: 3.5,
                peakTime: '12月'
            }
        }
    },
    
    // 知识掌握度
    knowledge: [
        { name: '函数与导数', score: 92 },
        { name: '三角函数', score: 85 },
        { name: '数列', score: 78 },
        { name: '立体几何', score: 88 },
        { name: '解析几何', score: 72 },
        { name: '概率统计', score: 90 }
    ],
    
    // 学习建议
    suggestions: [
        {
            icon: '💡',
            title: '加强解析几何练习',
            desc: '你在解析几何方面的掌握度为72%，建议每天增加30分钟专项练习，重点关注圆锥曲线和直线方程。'
        },
        {
            icon: '📚',
            title: '保持函数优势',
            desc: '函数与导数掌握度高达92%，继续保持！可以尝试挑战更高难度的题目，巩固优势。'
        },
        {
            icon: '⏰',
            title: '优化学习时间',
            desc: '周六是你的学习高峰期，建议将重要知识点安排在这个时段学习，效率会更高。'
        },
        {
            icon: '🎯',
            title: '制定阶段性目标',
            desc: '根据当前学习趋势，建议设定下次月考目标分数为95分，并制定详细的学习计划。'
        }
    ]
};

// 当前时间筛选
let currentTimeFilter = 'week';

// 显示Toast提示
function showToast(text) {
    const toast = document.getElementById('toast');
    toast.textContent = text;
    toast.classList.add('active');
    setTimeout(() => {
        toast.classList.remove('active');
    }, 2000);
}

// HTTP请求工具
async function request(url, options = {}) {
    const { method = 'GET', params = {}, body = null } = options;
    
    // 构建完整URL
    let fullURL = `${API_CONFIG.baseURL}${url}`;
    if (Object.keys(params).length > 0) {
        const queryString = new URLSearchParams(params).toString();
        fullURL += `?${queryString}`;
    }
    
    // 请求配置
    const fetchOptions = {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    };
    
    if (body) {
        fetchOptions.body = JSON.stringify(body);
    }
    
    try {
        const response = await fetch(fullURL, fetchOptions);
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

// 获取学生信息
async function getStudentInfo() {
    if (API_CONFIG.useRealAPI) {
        try {
            const result = await request('/student/info');
            return result.data;
        } catch (error) {
            console.error('获取学生信息失败，使用Mock数据');
            return MOCK_DATA.studentInfo;
        }
    }
    return MOCK_DATA.studentInfo;
}

// 获取核心指标
async function getMetrics() {
    if (API_CONFIG.useRealAPI) {
        try {
            const result = await request('/student/metrics');
            return result.data;
        } catch (error) {
            console.error('获取核心指标失败，使用Mock数据');
            return MOCK_DATA.metrics;
        }
    }
    return MOCK_DATA.metrics;
}

// 获取能力维度
async function getDimensions() {
    if (API_CONFIG.useRealAPI) {
        try {
            const result = await request('/student/dimensions');
            return result.data;
        } catch (error) {
            console.error('获取能力维度失败，使用Mock数据');
            return MOCK_DATA.dimensions;
        }
    }
    return MOCK_DATA.dimensions;
}

// 获取学习行为数据
async function getBehavior(period = 'week') {
    if (API_CONFIG.useRealAPI) {
        try {
            const result = await request('/student/behavior', { params: { period } });
            return result.data;
        } catch (error) {
            console.error('获取学习行为失败，使用Mock数据');
            return MOCK_DATA.behavior[period];
        }
    }
    return MOCK_DATA.behavior[period];
}

// 获取知识掌握度
async function getKnowledge() {
    if (API_CONFIG.useRealAPI) {
        try {
            const result = await request('/student/knowledge');
            return result.data;
        } catch (error) {
            console.error('获取知识掌握度失败，使用Mock数据');
            return MOCK_DATA.knowledge;
        }
    }
    return MOCK_DATA.knowledge;
}

// 获取学习建议
async function getSuggestions() {
    if (API_CONFIG.useRealAPI) {
        try {
            const result = await request('/student/suggestions');
            return result.data;
        } catch (error) {
            console.error('获取学习建议失败，使用Mock数据');
            return MOCK_DATA.suggestions;
        }
    }
    return MOCK_DATA.suggestions;
}

// 渲染学生信息
async function renderStudentInfo() {
    const data = await getStudentInfo();
    
    document.getElementById('studentAvatar').textContent = data.avatar;
    document.getElementById('studentName').textContent = data.name;
    document.getElementById('studentId').textContent = `学号: ${data.studentId}`;
    document.getElementById('studentGrade').textContent = data.grade;
    document.getElementById('studentClass').textContent = data.class;
    document.getElementById('studentEnrollDate').textContent = data.enrollDate;
    
    // 渲染标签
    const tagsContainer = document.getElementById('studentTags');
    tagsContainer.innerHTML = data.tags.map(tag => 
        `<span class="student-tag">${tag}</span>`
    ).join('');
}

// 渲染核心指标
async function renderMetrics() {
    const data = await getMetrics();
    
    document.getElementById('totalStudyHours').textContent = data.totalStudyHours;
    document.getElementById('completionRate').textContent = `${data.completionRate}%`;
    document.getElementById('avgScore').textContent = data.avgScore;
    document.getElementById('learningTrend').textContent = data.learningTrend;
}

// 绘制雷达图
function drawRadarChart(dimensions) {
    const canvas = document.getElementById('radarCanvas');
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 40;
    
    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const count = dimensions.length;
    const angleStep = (Math.PI * 2) / count;
    
    // 绘制背景网格
    for (let level = 1; level <= 5; level++) {
        ctx.beginPath();
        const levelRadius = (radius / 5) * level;
        
        for (let i = 0; i <= count; i++) {
            const angle = angleStep * i;
            const x = centerX + Math.cos(angle) * levelRadius;
            const y = centerY + Math.sin(angle) * levelRadius;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.strokeStyle = '#e5e7eb';
        ctx.lineWidth = 1;
        ctx.stroke();
    }
    
    // 绘制轴线
    for (let i = 0; i < count; i++) {
        const angle = angleStep * i;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.strokeStyle = '#e5e7eb';
        ctx.lineWidth = 1;
        ctx.stroke();
    }
    
    // 绘制数据区域
    ctx.beginPath();
    for (let i = 0; i <= count; i++) {
        const index = i % count;
        const angle = angleStep * i;
        const value = dimensions[index].value / 100;
        const x = centerX + Math.cos(angle) * radius * value;
        const y = centerY + Math.sin(angle) * radius * value;
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    
    ctx.fillStyle = 'rgba(99, 102, 241, 0.2)';
    ctx.fill();
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // 绘制数据点
    for (let i = 0; i < count; i++) {
        const angle = angleStep * i;
        const value = dimensions[i].value / 100;
        const x = centerX + Math.cos(angle) * radius * value;
        const y = centerY + Math.sin(angle) * radius * value;
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = dimensions[i].color;
        ctx.fill();
    }
    
    // 绘制标签
    ctx.font = '14px sans-serif';
    ctx.fillStyle = '#6b7280';
    ctx.textAlign = 'center';
    
    for (let i = 0; i < count; i++) {
        const angle = angleStep * i;
        const labelRadius = radius + 25;
        const x = centerX + Math.cos(angle) * labelRadius;
        const y = centerY + Math.sin(angle) * labelRadius;
        
        ctx.fillText(dimensions[i].name, x, y);
    }
}

// 渲染能力维度
async function renderDimensions() {
    const data = await getDimensions();
    
    // 隐藏占位符
    document.getElementById('radarPlaceholder').style.display = 'none';
    
    // 绘制雷达图
    drawRadarChart(data);
    
    // 渲染维度列表
    const listContainer = document.getElementById('dimensionList');
    listContainer.innerHTML = data.map(dim => `
        <div class="dimension-item">
            <div class="dimension-color" style="background: ${dim.color}"></div>
            <span class="dimension-name">${dim.name}</span>
            <span class="dimension-value">${dim.value}</span>
        </div>
    `).join('');
}

// 绘制行为图表
function drawBehaviorChart(labels, data) {
    const canvas = document.getElementById('behaviorCanvas');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const padding = 60;
    
    // 清空画布
    ctx.clearRect(0, 0, width, height);
    
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const maxValue = Math.max(...data) * 1.2;
    const barWidth = chartWidth / labels.length * 0.6;
    const barGap = chartWidth / labels.length * 0.4;
    
    // 绘制Y轴刻度
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#9ca3af';
    ctx.textAlign = 'right';
    
    for (let i = 0; i <= 5; i++) {
        const y = padding + (chartHeight / 5) * i;
        const value = Math.round(maxValue - (maxValue / 5) * i);
        
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
        
        ctx.fillText(value.toString(), padding - 10, y + 4);
    }
    
    // 绘制柱状图
    labels.forEach((label, i) => {
        const x = padding + (chartWidth / labels.length) * i + barGap / 2;
        const barHeight = (data[i] / maxValue) * chartHeight;
        const y = padding + chartHeight - barHeight;
        
        // 绘制柱子
        const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
        gradient.addColorStop(0, '#6366f1');
        gradient.addColorStop(1, '#8b5cf6');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth, barHeight);
        
        // 绘制数值
        ctx.fillStyle = '#1f2937';
        ctx.font = '13px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(data[i].toString(), x + barWidth / 2, y - 8);
        
        // 绘制X轴标签
        ctx.fillStyle = '#6b7280';
        ctx.font = '13px sans-serif';
        ctx.fillText(label, x + barWidth / 2, padding + chartHeight + 20);
    });
}

// 渲染学习行为
async function renderBehavior(period = 'week') {
    const data = await getBehavior(period);
    
    // 隐藏占位符
    document.getElementById('behaviorPlaceholder').style.display = 'none';
    
    // 绘制图表
    drawBehaviorChart(data.labels, data.data);
    
    // 渲染统计数据
    const statsContainer = document.getElementById('behaviorStats');
    statsContainer.innerHTML = `
        <div class="behavior-stat-item">
            <div class="behavior-stat-value">${data.stats.totalHours}</div>
            <div class="behavior-stat-label">总学习时长(小时)</div>
        </div>
        <div class="behavior-stat-item">
            <div class="behavior-stat-value">${data.stats.avgDaily}</div>
            <div class="behavior-stat-label">日均学习(小时)</div>
        </div>
        <div class="behavior-stat-item">
            <div class="behavior-stat-value">${data.stats.peakTime}</div>
            <div class="behavior-stat-label">学习高峰期</div>
        </div>
    `;
}

// 渲染知识掌握度
async function renderKnowledge() {
    const data = await getKnowledge();
    
    const container = document.getElementById('knowledgeList');
    container.innerHTML = data.map(item => `
        <div class="knowledge-item">
            <div class="knowledge-header">
                <span class="knowledge-name">${item.name}</span>
                <span class="knowledge-score">${item.score}分</span>
            </div>
            <div class="knowledge-bar">
                <div class="knowledge-progress" style="width: ${item.score}%"></div>
            </div>
        </div>
    `).join('');
}

// 渲染学习建议
async function renderSuggestions() {
    const data = await getSuggestions();
    
    const container = document.getElementById('suggestionsList');
    container.innerHTML = data.map(item => `
        <div class="suggestion-item">
            <span class="suggestion-icon">${item.icon}</span>
            <div class="suggestion-content">
                <div class="suggestion-title">${item.title}</div>
                <div class="suggestion-desc">${item.desc}</div>
            </div>
        </div>
    `).join('');
}

// 初始化时间筛选器
function initTimeFilter() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            // 更新激活状态
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 获取时间周期
            const period = btn.dataset.period;
            currentTimeFilter = period;
            
            // 重新渲染行为数据
            document.getElementById('behaviorPlaceholder').style.display = 'flex';
            await renderBehavior(period);
        });
    });
}

// 刷新数据
async function refreshData() {
    showToast('正在刷新数据...');
    
    try {
        await Promise.all([
            renderStudentInfo(),
            renderMetrics(),
            renderDimensions(),
            renderBehavior(currentTimeFilter),
            renderKnowledge(),
            renderSuggestions()
        ]);
        
        showToast('数据刷新成功');
    } catch (error) {
        showToast('刷新失败，请重试');
    }
}

// 导出报告
function exportReport() {
    showToast('报告导出功能开发中...');
    // TODO: 实现报告导出功能
}

// 初始化页面
async function init() {
    try {
        // 加载所有数据
        await Promise.all([
            renderStudentInfo(),
            renderMetrics(),
            renderDimensions(),
            renderBehavior(currentTimeFilter),
            renderKnowledge(),
            renderSuggestions()
        ]);
        
        // 初始化事件监听
        initTimeFilter();
        
        // 绑定按钮事件
        document.getElementById('refreshBtn').addEventListener('click', refreshData);
        document.getElementById('exportBtn').addEventListener('click', exportReport);
        document.getElementById('refreshRadar').addEventListener('click', async () => {
            document.getElementById('radarPlaceholder').style.display = 'flex';
            await renderDimensions();
            showToast('能力维度已刷新');
        });
        
    } catch (error) {
        console.error('初始化失败:', error);
        showToast('页面加载失败，请刷新重试');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// 暴露全局方法供调试使用
window.ProfileAPI = {
    getStudentInfo,
    getMetrics,
    getDimensions,
    getBehavior,
    getKnowledge,
    getSuggestions,
    refreshData,
    getConfig: () => API_CONFIG,
    setConfig: (newConfig) => Object.assign(API_CONFIG, newConfig)
};
