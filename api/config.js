/**
 * API配置模块
 * 后端开发人员需要根据实际部署情况修改以下配置
 */

/**
 * API基础URL配置
 * 后端部署后请修改为实际的API地址
 */
const API_CONFIG = {
    // 开发环境 - 本地后端服务
    development: {
        baseURL: 'http://localhost:3000/api',
        timeout: 10000
    },
    // 测试环境
    test: {
        baseURL: 'http://test.example.com/api',
        timeout: 10000
    },
    // 生产环境
    production: {
        baseURL: 'http://api.example.com/api',
        timeout: 10000
    }
};

/**
 * 当前环境（后端可根据实际情况切换）
 * 可选值: 'development' | 'test' | 'production'
 */
const CURRENT_ENV = 'development';

/**
 * 获取当前环境的基础URL
 * @returns {string} 基础API地址
 */
export function getBaseURL() {
    return API_CONFIG[CURRENT_ENV]?.baseURL || API_CONFIG.development.baseURL;
}

/**
 * 获取请求超时时间
 * @returns {number} 超时时间（毫秒）
 */
export function getTimeout() {
    return API_CONFIG[CURRENT_ENV]?.timeout || 10000;
}

/**
 * 请求头配置
 * @returns {object} 默认请求头
 */
export function getDefaultHeaders() {
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };
}

// 导出配置供其他模块使用
export default {
    getBaseURL,
    getTimeout,
    getDefaultHeaders,
    CURRENT_ENV
};