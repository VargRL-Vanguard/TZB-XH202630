/**
 * HTTP请求工具模块
 * 封装通用的fetch请求，提供统一的错误处理和响应格式
 * 
 * 认证机制说明：
 * - 默认使用Authorization Header携带JWT Token
 * - Token存储在localStorage的'chat_token'键中
 * - 后端可根据实际情况修改认证方式
 */

import { getBaseURL, getTimeout, getDefaultHeaders } from './config.js';

/**
 * 获取认证Token
 * @returns {string|null} Token字符串
 */
export function getAuthToken() {
    // 从localStorage获取Token（后端可根据实际情况修改）
    return localStorage.getItem('chat_token');
}

/**
 * 设置认证Token
 * @param {string} token - Token字符串
 */
export function setAuthToken(token) {
    localStorage.setItem('chat_token', token);
}

/**
 * 清除认证Token
 */
export function clearAuthToken() {
    localStorage.removeItem('chat_token');
}

/**
 * 获取完整的请求头（包含认证信息）
 * @returns {object} 请求头对象
 */
export function getRequestHeaders() {
    const headers = { ...getDefaultHeaders() };
    const token = getAuthToken();
    
    // 如果有Token，添加Authorization头
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
}

/**
 * 请求拦截器（可扩展）
 * @param {object} config - 请求配置
 * @returns {object} 处理后的配置
 */
export function requestInterceptor(config) {
    // 可在此添加请求前的统一处理逻辑
    // 例如：添加时间戳、签名等
    return config;
}

/**
 * 响应拦截器（可扩展）
 * @param {object} response - 响应数据
 * @returns {object} 处理后的响应
 */
export function responseInterceptor(response) {
    // 可在此添加响应后的统一处理逻辑
    // 例如：处理Token过期、统一错误格式等
    
    // 示例：如果返回401，清除Token
    if (response && response.code === 401) {
        clearAuthToken();
    }
    
    return response;
}

/**
 * 通用HTTP请求函数
 * @param {string} url - 请求路径（相对路径）
 * @param {object} options - 请求配置
 * @param {string} options.method - HTTP方法 (GET/POST/PUT/DELETE)
 * @param {object} options.headers - 请求头
 * @param {object} options.body - 请求体
 * @param {number} options.timeout - 超时时间
 * @param {boolean} options.needAuth - 是否需要认证（默认true）
 * @returns {Promise<object>} 响应数据
 */
export async function request(url, options = {}) {
    const {
        method = 'GET',
        headers = {},
        body = null,
        timeout = getTimeout(),
        needAuth = true // 是否需要认证
    } = options;

    // 构建完整URL
    const fullURL = `${getBaseURL()}${url}`;

    // 获取基础请求头（包含认证信息）
    const baseHeaders = needAuth ? getRequestHeaders() : getDefaultHeaders();
    
    // 合并默认请求头和自定义请求头
    const mergedHeaders = {
        ...baseHeaders,
        ...headers
    };

    // 创建请求配置
    const fetchOptions = {
        method,
        headers: mergedHeaders,
        credentials: 'include' // 携带Cookie
    };

    // 如果有请求体，添加到配置中
    if (body) {
        fetchOptions.body = JSON.stringify(body);
    }

    // 请求拦截处理
    const finalOptions = requestInterceptor(fetchOptions);

    // 创建超时Promise
    const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
            reject(new Error('请求超时'));
        }, timeout);
    });

    // 创建请求Promise
    const requestPromise = fetch(fullURL, finalOptions)
        .then(response => {
            // 检查HTTP状态码
            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }
            // 尝试解析JSON响应
            return response.json();
        })
        .then(data => {
            // 响应拦截处理
            return responseInterceptor(data);
        })
        .catch(error => {
            // 统一错误处理
            console.error('请求失败:', error.message);
            throw error;
        });

    // 竞态处理：超时或请求完成
    try {
        const result = await Promise.race([requestPromise, timeoutPromise]);
        return result;
    } catch (error) {
        // 抛出统一格式的错误
        throw {
            success: false,
            message: error.message || '请求失败',
            code: error.code || -1
        };
    }
}

/**
 * GET请求封装
 * @param {string} url - 请求路径
 * @param {object} params - URL参数
 * @param {object} options - 额外配置
 * @returns {Promise<object>} 响应数据
 */
export async function get(url, params = {}, options = {}) {
    // 将params转换为URL查询字符串
    const queryString = new URLSearchParams(params).toString();
    const fullURL = queryString ? `${url}?${queryString}` : url;

    return request(fullURL, {
        method: 'GET',
        ...options
    });
}

/**
 * POST请求封装
 * @param {string} url - 请求路径
 * @param {object} data - 请求体数据
 * @param {object} options - 额外配置
 * @returns {Promise<object>} 响应数据
 */
export async function post(url, data = {}, options = {}) {
    return request(url, {
        method: 'POST',
        body: data,
        ...options
    });
}

/**
 * PUT请求封装
 * @param {string} url - 请求路径
 * @param {object} data - 请求体数据
 * @param {object} options - 额外配置
 * @returns {Promise<object>} 响应数据
 */
export async function put(url, data = {}, options = {}) {
    return request(url, {
        method: 'PUT',
        body: data,
        ...options
    });
}

/**
 * DELETE请求封装
 * @param {string} url - 请求路径
 * @param {object} params - URL参数
 * @param {object} options - 额外配置
 * @returns {Promise<object>} 响应数据
 */
export async function del(url, params = {}, options = {}) {
    const queryString = new URLSearchParams(params).toString();
    const fullURL = queryString ? `${url}?${queryString}` : url;

    return request(fullURL, {
        method: 'DELETE',
        ...options
    });
}

// 导出请求方法
export default {
    request,
    get,
    post,
    put,
    del
};