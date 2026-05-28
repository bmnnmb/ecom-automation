/**
 * API服务层 - 统一数据接口
 * 
 * 双模式：
 * 1. 后端API可用 → 从真实抖音API获取数据
 * 2. 后端不可用 → 降级使用本地Mock数据
 */

import { 
  generateOrders, generateProducts, generateConversations, 
  generateCompetitors, generateDashboardStats,
  PLATFORMS, ORDER_STATUS 
} from './mock';

// 后端API地址（可通过环境变量配置）
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

// 当前后端是否可用
let apiAvailable = false;
let authToken = null;

// 检测后端可用性
async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { 
      signal: AbortSignal.timeout(3000) 
    });
    apiAvailable = res.ok;
  } catch {
    apiAvailable = false;
  }
  return apiAvailable;
}

// 通用API请求
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
    ...options.headers,
  };

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  const json = await res.json();
  return json.data || json;
}

// ==================== 抖音授权 ====================

export async function getDouyinAuthUrl(redirectUri) {
  try {
    const data = await apiRequest(`/auth/url?redirect_uri=${encodeURIComponent(redirectUri)}`);
    return data.auth_url;
  } catch {
    return null;
  }
}

export async function handleDouyinCallback(code) {
  try {
    const data = await apiRequest(`/auth/callback?code=${code}`, { method: 'POST' });
    authToken = data.access_token;
    // 持久化token
    localStorage.setItem('douyin_token', JSON.stringify(data));
    return data;
  } catch (e) {
    console.error('授权回调失败:', e);
    return null;
  }
}

// ==================== 订单 ====================

export async function fetchOrders(params = {}) {
  if (!apiAvailable) {
    return { items: generateOrders(80), total: 80, source: 'mock' };
  }
  try {
    const query = new URLSearchParams(params).toString();
    const data = await apiRequest(`/api/order/list?${query}`);
    return { ...data, source: 'api' };
  } catch {
    return { items: generateOrders(80), total: 80, source: 'mock' };
  }
}

// ==================== 商品 ====================

export async function fetchProducts(params = {}) {
  if (!apiAvailable) {
    return { items: generateProducts(30), total: 30, source: 'mock' };
  }
  try {
    const query = new URLSearchParams(params).toString();
    const data = await apiRequest(`/api/product/list?${query}`);
    return { ...data, source: 'api' };
  } catch {
    return { items: generateProducts(30), total: 30, source: 'mock' };
  }
}

// ==================== 客服消息 ====================

export async function fetchConversations() {
  if (!apiAvailable) {
    return { items: generateConversations(12), source: 'mock' };
  }
  try {
    // TODO: 对接抖音客服消息API
    const data = await apiRequest('/api/customer/conversations');
    return { ...data, source: 'api' };
  } catch {
    return { items: generateConversations(12), source: 'mock' };
  }
}

export async function sendMessage(conversationId, content) {
  if (!apiAvailable) {
    return { success: true, source: 'mock' };
  }
  try {
    return await apiRequest('/api/customer/send', {
      method: 'POST',
      body: JSON.stringify({ conversation_id: conversationId, content }),
    });
  } catch {
    return { success: true, source: 'mock' };
  }
}

// ==================== Dashboard ====================

export async function fetchDashboardStats() {
  try {
    const data = await apiRequest('/api/dashboard/stats');
    return { ...data, source: 'api' };
  } catch {
    return { ...generateDashboardStats(), source: 'mock' };
  }
}

export async function fetchDashboardTrend(days = 7) {
  try {
    const data = await apiRequest(`/api/dashboard/trend?days=${days}`);
    return { ...data, source: 'api' };
  } catch {
    return null;
  }
}

// ==================== 竞品 ====================

// ==================== 客户 ====================

const CUSTOMER_API_BASE = import.meta.env.VITE_CUSTOMER_API_BASE || 'http://localhost:8006';

async function customerApiRequest(endpoint, options = {}) {
  const url = `${CUSTOMER_API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) throw new Error(`Customer API Error: ${res.status}`);
  return await res.json();
}

export async function fetchCustomerStats() {
  try {
    const json = await customerApiRequest('/api/customers/stats');
    return { ...json.data, source: 'api' };
  } catch {
    return { total: 0, newCustomers: 0, activeCustomers: 0, vipCustomers: 0, source: 'mock' };
  }
}

export async function fetchCustomers(params = {}) {
  try {
    const query = new URLSearchParams(params).toString();
    const json = await customerApiRequest(`/api/customers?${query}`);
    return { items: json.data, total: json.meta?.total || json.data.length, meta: json.meta, source: 'api' };
  } catch {
    return { items: [], total: 0, source: 'mock' };
  }
}

export async function fetchCustomerDetail(dbId) {
  try {
    const json = await customerApiRequest(`/api/customers/${dbId}`);
    return { ...json.data, source: 'api' };
  } catch {
    return null;
  }
}

export async function createCustomer(data) {
  try {
    const json = await customerApiRequest('/api/customers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return json;
  } catch (e) {
    return { success: false, message: e.message };
  }
}

export async function updateCustomer(dbId, data) {
  try {
    const json = await customerApiRequest(`/api/customers/${dbId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    return json;
  } catch (e) {
    return { success: false, message: e.message };
  }
}

export async function deleteCustomer(dbId) {
  try {
    const json = await customerApiRequest(`/api/customers/${dbId}`, {
      method: 'DELETE',
    });
    return json;
  } catch (e) {
    return { success: false, message: e.message };
  }
}

export async function fetchCompetitors() {
  if (!apiAvailable) {
    return { items: generateCompetitors(20), source: 'mock' };
  }
  try {
    const data = await apiRequest('/api/competitors/list');
    return { ...data, source: 'api' };
  } catch {
    return { items: generateCompetitors(20), source: 'mock' };
  }
}

// ==================== 系统设置 ====================

export async function fetchSettings() {
  try {
    const data = await apiRequest('/api/settings');
    return { ...data, source: 'api' };
  } catch {
    // 后端不可用时从 localStorage 读取
    const saved = localStorage.getItem('ecom_settings');
    if (saved) {
      try { return { ...JSON.parse(saved), source: 'local' }; } catch {}
    }
    return null; // 返回 null 表示使用默认值
  }
}

export async function saveSettings(settings) {
  try {
    const data = await apiRequest('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
    // 同步保存到 localStorage 作为备份
    localStorage.setItem('ecom_settings', JSON.stringify(data));
    return { ...data, source: 'api' };
  } catch {
    // 后端不可用时保存到 localStorage
    localStorage.setItem('ecom_settings', JSON.stringify(settings));
    return { ...settings, source: 'local' };
  }
}

// ==================== 初始化 ====================

export async function initApi() {
  // 尝试恢复token
  const saved = localStorage.getItem('douyin_token');
  if (saved) {
    try {
      const tokenData = JSON.parse(saved);
      authToken = tokenData.access_token;
    } catch {}
  }
  
  // 检测后端
  await checkApiHealth();
  
  return {
    apiAvailable,
    hasToken: !!authToken,
    source: apiAvailable ? 'api' : 'mock',
  };
}

export { apiAvailable, PLATFORMS, ORDER_STATUS };
