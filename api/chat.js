/**
 * 聊天相关API接口模块
 * 
 * 后端对接文档：
 * 
 * 【接口列表】
 * 
 * 1. 获取聊天历史记录
 *    - URL: GET /api/chat/history
 *    - 参数: 
 *      - userId: string (可选) 当前用户ID
 *      - targetId: string (必需) 聊天对象ID
 *      - page: number (可选) 页码，默认1
 *      - pageSize: number (可选) 每页数量，默认20
 *    - 响应:
 *      {
 *        success: true,
 *        data: {
 *          messages: [
 *            {
 *              id: string,        // 消息ID
 *              content: string,   // 消息内容
 *              senderId: string,  // 发送者ID
 *              receiverId: string,// 接收者ID
 *              isSent: boolean,   // 是否为我方发送
 *              timestamp: number, // 发送时间戳(毫秒)
 *              avatar: string     // 头像URL（对方消息才有）
 *            }
 *          ],
 *          total: number,        // 总消息数
 *          page: number,
 *          pageSize: number
 *        },
 *        message: 'success'
 *      }
 * 
 * 2. 发送消息
 *    - URL: POST /api/chat/send
 *    - 请求体:
 *      {
 *        userId: string,        // 当前用户ID
 *        targetId: string,      // 聊天对象ID
 *        content: string        // 消息内容
 *      }
 *    - 响应:
 *      {
 *        success: true,
 *        data: {
 *          id: string,          // 消息ID
 *          content: string,     // 消息内容
 *          senderId: string,    // 发送者ID
 *          receiverId: string,  // 接收者ID
 *          timestamp: number,   // 发送时间戳
 *          avatar: string       // 头像URL（对方回复时才有）
 *        },
 *        message: 'success'
 *      }
 * 
 * 3. 获取用户信息
 *    - URL: GET /api/user/info
 *    - 参数:
 *      - userId: string (必需) 用户ID
 *    - 响应:
 *      {
 *        success: true,
 *        data: {
 *          id: string,          // 用户ID
 *          name: string,        // 用户名
 *          avatar: string,      // 头像URL
 *          status: string       // 在线状态: 'online' | 'offline' | 'away'
 *        },
 *        message: 'success'
 *      }
 * 
 * 4. 获取聊天列表
 *    - URL: GET /api/chat/list
 *    - 参数:
 *      - userId: string (必需) 当前用户ID
 *    - 响应:
 *      {
 *        success: true,
 *        data: [
 *          {
 *            id: string,        // 聊天会话ID
 *            targetId: string,  // 聊天对象ID
 *            targetName: string,// 聊天对象名称
 *            targetAvatar: string,// 聊天对象头像
 *            lastMessage: string,// 最后一条消息内容
 *            lastTime: number,  // 最后消息时间戳
 *            unreadCount: number // 未读消息数
 *          }
 *        ],
 *        message: 'success'
 *      }
 * 
 * 5. 标记消息已读
 *    - URL: POST /api/chat/read
 *    - 请求体:
 *      {
 *        userId: string,        // 当前用户ID
 *        targetId: string,      // 聊天对象ID
 *        messageId: string      // 消息ID（可选，不传则标记所有）
 *      }
 *    - 响应:
 *      {
 *        success: true,
 *        message: 'success'
 *      }
 */

import { get, post } from './request.js';

/**
 * 获取聊天历史记录
 * @param {object} params - 请求参数
 * @param {string} params.userId - 当前用户ID
 * @param {string} params.targetId - 聊天对象ID
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页数量
 * @returns {Promise<object>} 聊天历史数据
 */
export async function getChatHistory(params) {
    return get('/chat/history', params);
}

/**
 * 发送消息
 * @param {object} data - 请求数据
 * @param {string} data.userId - 当前用户ID
 * @param {string} data.targetId - 聊天对象ID
 * @param {string} data.content - 消息内容
 * @returns {Promise<object>} 发送结果
 */
export async function sendMessage(data) {
    return post('/chat/send', data);
}

/**
 * 获取用户信息
 * @param {object} params - 请求参数
 * @param {string} params.userId - 用户ID
 * @returns {Promise<object>} 用户信息
 */
export async function getUserInfo(params) {
    return get('/user/info', params);
}

/**
 * 获取聊天列表
 * @param {object} params - 请求参数
 * @param {string} params.userId - 当前用户ID
 * @returns {Promise<object>} 聊天列表数据
 */
export async function getChatList(params) {
    return get('/chat/list', params);
}

/**
 * 标记消息已读
 * @param {object} data - 请求数据
 * @param {string} data.userId - 当前用户ID
 * @param {string} data.targetId - 聊天对象ID
 * @param {string} data.messageId - 消息ID（可选）
 * @returns {Promise<object>} 标记结果
 */
export async function markMessageRead(data) {
    return post('/chat/read', data);
}

// 导出所有聊天API
export default {
    getChatHistory,
    sendMessage,
    getUserInfo,
    getChatList,
    markMessageRead
};