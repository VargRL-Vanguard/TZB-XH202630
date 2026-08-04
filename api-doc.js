/**
 * ============================================================
 * 后端接口文档 - 供后端开发人员参考
 * ============================================================
 * 基础地址: http://your-server:port/api
 * 请求方式: RESTful API
 * 数据格式: JSON
 * 认证方式: Header中携带 token 字段
 * ============================================================
 */

// ==================== 1. 聊天模块 (/api/chat) ====================

/**
 * 1.1 获取聊天历史记录
 * GET /api/chat/history?userId=xxx&targetId=xxx&limit=50&offset=0
 * 返回:
 * {
 *   code: 200,
 *   data: {
 *     list: [
 *       { id: 1, userId: "u001", targetId: "u002", content: "你好", type: "text", timestamp: "2026-07-24 20:00:00", status: "read" }
 *     ],
 *     total: 100,
 *     hasMore: true
 *   }
 * }
 */

/**
 * 1.2 发送消息
 * POST /api/chat/send
 * 请求体:
 * {
 *   userId: "u001",
 *   targetId: "u002",
 *   content: "你好呀",
 *   type: "text"  // text | image | file
 * }
 * 返回:
 * {
 *   code: 200,
 *   data: { id: 101, timestamp: "2026-07-24 20:01:00", status: "sent" }
 * }
 */

/**
 * 1.3 获取用户信息
 * GET /api/user/info?userId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: { userId: "u001", name: "张三", avatar: "url", online: true }
 * }
 */

/**
 * 1.4 获取聊天列表
 * GET /api/chat/list?userId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { targetId: "u002", name: "李四", lastMessage: "好的", lastTime: "2026-07-24 20:00:00", unread: 3 }
 *   ]
 * }
 */

/**
 * 1.5 标记消息已读
 * POST /api/chat/read
 * 请求体: { userId: "u001", targetId: "u002" }
 * 返回: { code: 200, data: { success: true } }
 */


// ==================== 2. 学情画像模块 (/api/student) ====================

/**
 * 2.1 获取学生基本信息
 * GET /api/student/info?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: {
 *     studentId: "s001", name: "张三", grade: "大二", className: "计科1班",
 *     avatar: "url", tags: ["勤奋", "积极"], joinDate: "2025-09-01"
 *   }
 * }
 */

/**
 * 2.2 获取核心指标数据
 * GET /api/student/metrics?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: {
 *     studyHours: 48.5, completionRate: 75, avgScore: 82,
 *     trend: "up", trendValue: 5
 *   }
 * }
 */

/**
 * 2.3 获取能力维度分析
 * GET /api/student/dimensions?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { name: "理解能力", value: 85 },
 *     { name: "应用能力", value: 70 },
 *     { name: "分析能力", value: 75 },
 *     { name: "创新能力", value: 60 },
 *     { name: "协作能力", value: 80 },
 *     { name: "自律能力", value: 90 }
 *   ]
 * }
 */

/**
 * 2.4 获取学习行为数据
 * GET /api/student/behavior?studentId=xxx&period=week
 * 参数: period = week | month | semester
 * 返回:
 * {
 *   code: 200,
 *   data: {
 *     labels: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
 *     values: [2.5, 3.0, 1.5, 4.0, 2.0, 1.0, 0.5]
 *   }
 * }
 */

/**
 * 2.5 获取知识掌握度
 * GET /api/student/knowledge?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { name: "基础语法", progress: 85 },
 *     { name: "函数编程", progress: 45 },
 *     { name: "数据结构", progress: 60 },
 *     { name: "面向对象", progress: 20 },
 *     { name: "文件IO", progress: 10 },
 *     { name: "异常处理", progress: 5 }
 *   ]
 * }
 */

/**
 * 2.6 获取个性化建议
 * GET /api/student/suggestions?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { id: 1, title: "加强函数练习", content: "...", priority: "high", category: "practice" }
 *   ]
 * }
 */


// ==================== 3. 学习路径模块 (/api/learning-path) ====================

/**
 * 3.1 获取学习路径概览
 * GET /api/learning-path/overview?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: { target: "掌握Python基础编程", progress: 35, estimatedDays: 12 }
 * }
 */

/**
 * 3.2 获取学习路径时间线
 * GET /api/learning-path/timeline?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { id: 1, title: "Python基础语法", desc: "变量、数据类型...", status: "completed", progress: 100, duration: "3天", startDate: "2026-07-10", endDate: "2026-07-13" }
 *   ]
 * }
 * status: completed | current | pending
 */

/**
 * 3.3 获取知识模块数据
 * GET /api/learning-path/modules?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { name: "基础语法", progress: 85, desc: "变量、运算符、流程控制" }
 *   ]
 * }
 */

/**
 * 3.4 获取今日任务
 * GET /api/learning-path/tasks?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { id: 1, title: "完成函数参数传递练习", meta: "预计30分钟", priority: "high", completed: false }
 *   ]
 * }
 */

/**
 * 3.5 提交AI生成的学习路径结果
 * POST /api/learning-path/ai-result
 * 请求体: { studentId: "s001", content: "AI生成的路径内容..." }
 * 返回: { code: 200, data: { success: true } }
 */

/**
 * 3.6 获取AI生成的学习路径
 * GET /api/learning-path/ai-result?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: { content: "AI生成的路径内容...", generatedAt: "2026-07-24 20:00:00" }
 * }
 */


// ==================== 4. 学习建议模块 (/api/suggestions) ====================

/**
 * 4.1 获取学习建议列表
 * GET /api/suggestions/list?studentId=xxx&category=all
 * 参数: category = all | method | resource | review | practice
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { id: 1, title: "加强函数参数传递练习", content: "...", category: "practice", categoryLabel: "练习推荐", priority: "high", priorityLabel: "重要", source: "基于最近3次测验结果" }
 *   ]
 * }
 */

/**
 * 4.2 获取AI生成的建议结果
 * GET /api/suggestions/ai-result?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: { content: "AI建议内容...", generatedAt: "2026-07-24 20:00:00" }
 * }
 */

/**
 * 4.3 标记建议为已读
 * POST /api/suggestions/read
 * 请求体: { studentId: "s001", suggestionId: 1 }
 * 返回: { code: 200, data: { success: true } }
 */


// ==================== 5. 学习活动记录模块 (/api/activity) ====================

/**
 * 5.1 获取学习统计数据
 * GET /api/activity/stats?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: { totalHours: 48.5, completedCourses: 12, totalCourses: 20, streakDays: 7, completionRate: 60 }
 * }
 */

/**
 * 5.2 获取课程列表
 * GET /api/activity/courses?studentId=xxx&filter=all
 * 参数: filter = all | in-progress | completed | not-started
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { id: 1, title: "Python基础语法", status: "completed", statusLabel: "已完成", progress: 100, totalLessons: 8, completedLessons: 8, lastStudy: "2026-07-13 21:30" }
 *   ]
 * }
 */

/**
 * 5.3 获取最近学习记录
 * GET /api/activity/recent?studentId=xxx&limit=10
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { id: 1, title: "完成函数参数传递课程", desc: "学习了默认参数...", time: "20分钟前" }
 *   ]
 * }
 */

/**
 * 5.4 获取每周学习日历
 * GET /api/activity/calendar?studentId=xxx
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { day: "一", date: 19, hours: 1.5 },
 *     { day: "二", date: 20, hours: 2.0, today: true }
 *   ]
 * }
 */

/**
 * 5.5 记录学习活动
 * POST /api/activity/record
 * 请求体: { studentId: "s001", type: "course", courseId: 1, duration: 30, description: "完成函数章节" }
 * 返回: { code: 200, data: { success: true, id: 101 } }
 */


// ==================== 6. AI辅导对话模块 (/api/ai-chat) ====================

/**
 * 6.1 发送AI对话消息
 * POST /api/ai-chat/send
 * 请求体:
 * {
 *   studentId: "s001",
 *   message: "帮我解释一下Python函数的参数传递",
 *   context: { currentModule: "函数与模块", studyProgress: 45 }
 * }
 * 返回:
 * {
 *   code: 200,
 *   data: {
 *     reply: "Python函数参数传递有以下几种方式...",
 *     conversationId: "conv_001"
 *   }
 * }
 */

/**
 * 6.2 获取对话历史
 * GET /api/ai-chat/history?studentId=xxx&limit=20
 * 返回:
 * {
 *   code: 200,
 *   data: [
 *     { id: 1, role: "user", content: "你好", timestamp: "2026-07-24 20:00:00" },
 *     { id: 2, role: "ai", content: "你好！有什么可以帮你的？", timestamp: "2026-07-24 20:00:01" }
 *   ]
 * }
 */

/**
 * 6.3 清除对话历史
 * DELETE /api/ai-chat/history?studentId=xxx
 * 返回: { code: 200, data: { success: true } }
 */


// ==================== 7. WebSocket实时推送 (/ws) ====================

/**
 * 7.1 WebSocket连接
 * 地址: ws://your-server:port/ws?token=xxx&studentId=xxx
 *
 * 客户端发送消息格式:
 * { type: "ping" }                          // 心跳（每30秒一次）
 * { type: "chat", targetId: "u002", content: "你好" }  // 发送聊天消息
 * { type: "subscribe", channel: "notification" }       // 订阅通知
 *
 * 服务端推送消息格式:
 * { type: "message", from: "u002", content: "你好", timestamp: "..." }  // 新消息
 * { type: "notification", title: "学习提醒", content: "..." }           // 系统通知
 * { type: "ai_reply", content: "AI回复内容..." }                        // AI回复
 * { type: "pong" }                          // 心跳响应
 * { type: "error", message: "错误信息" }     // 错误信息
 */


// ==================== 通用规范 ====================

/**
 * 统一响应格式:
 * {
 *   code: 200,        // 200=成功, 400=参数错误, 401=未认证, 403=无权限, 500=服务器错误
 *   message: "success", // 响应消息
 *   data: { ... }     // 响应数据
 * }
 *
 * 分页参数:
 * - limit: 每页数量（默认20）
 * - offset: 偏移量（默认0）
 *
 * 认证方式:
 * - Header: Authorization: Bearer <token>
 * - 或 Query参数: ?token=xxx
 *
 * 错误码:
 * - 200: 成功
 * - 400: 请求参数错误
 * - 401: 未登录或token过期
 * - 403: 无权限访问
 * - 404: 资源不存在
 * - 500: 服务器内部错误
 */
