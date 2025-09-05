import axios from 'axios';
import toast from 'react-hot-toast';

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost';
const USER_SERVICE_PORT = import.meta.env.VITE_USER_SERVICE_PORT || '5001';
const BANK_SERVICE_PORT = import.meta.env.VITE_BANK_SERVICE_PORT || '5002';
const STOCK_SERVICE_PORT = import.meta.env.VITE_STOCK_SERVICE_PORT || '5003';
const TRADE_SERVICE_PORT = import.meta.env.VITE_TRADE_SERVICE_PORT || '5004';
const ANALYTICS_SERVICE_PORT = import.meta.env.VITE_ANALYTICS_SERVICE_PORT || '5005';

// API endpoints
const API_ENDPOINTS = {
  USER_SERVICE: `${API_BASE_URL}:${USER_SERVICE_PORT}`,
  BANK_SERVICE: `${API_BASE_URL}:${BANK_SERVICE_PORT}`,
  STOCK_SERVICE: `${API_BASE_URL}:${STOCK_SERVICE_PORT}`,
  TRADE_SERVICE: `${API_BASE_URL}:${TRADE_SERVICE_PORT}`,
  ANALYTICS_SERVICE: `${API_BASE_URL}:${ANALYTICS_SERVICE_PORT}`
};

// Generic API call function
const apiCall = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
      signal: options.signal,
    });
    if (options.signal?.aborted) throw new DOMException('Request aborted', 'AbortError');
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP error! status: ${response.status}`);
    return { data };
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error(`API call failed for ${url}:`, error);
      throw error;
    }
  }
};

// User Service API
export const userAPI = {
  login: (credentials, options) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/login`, { method: 'POST', body: JSON.stringify(credentials), ...options }),
  createUser: (userData, options) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/create`, { method: 'POST', body: JSON.stringify(userData), ...options }),
  getUserPortfolio: (userId, options) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/${userId}/portfolio`, options),
  buyStock: (userId, tradeData, options) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/${userId}/portfolio/update`, { method: 'POST', body: JSON.stringify({ ...tradeData, trade_type: 'buy' }), ...options }),
  sellStock: (userId, tradeData, options) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/${userId}/portfolio/update`, { method: 'POST', body: JSON.stringify({ ...tradeData, trade_type: 'sell' }), ...options })
};

// Bank Service API
export const bankAPI = {
  getBalance: (userId, options) => apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/balance/${userId}`, options),
  creditAccount: (data, options) => apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/credit`, { method: 'POST', body: JSON.stringify(data), ...options }),
  debitAccount: (data, options) => apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/debit`, { method: 'POST', body: JSON.stringify(data), ...options })
};

// Stock Service API
export const stockAPI = {
  getAllStocks: (options) => apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks`, options),
  getMarketSummary: (options) => apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks/market/summary`, options)
};

// Trade Service API
export const tradeAPI = {
  getUserTrades: (userId, options) => apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/user/${userId}`, options),
};

// Analytics Service API
export const analyticsAPI = {
    runJobs: (options) => apiCall(`${API_ENDPOINTS.ANALYTICS_SERVICE}/analytics/run`, { method: 'POST', ...options }),
    getPortfolioAnalysis: (options) => apiCall(`${API_ENDPOINTS.ANALYTICS_SERVICE}/analytics/portfolio`, options),
    getVolumeAnalysis: (options) => apiCall(`${API_ENDPOINTS.ANALYTICS_SERVICE}/analytics/volume`, options),
    getProfitAnalysis: (options) => apiCall(`${API_ENDPOINTS.ANALYTICS_SERVICE}/analytics/profit`, options),
    getTopPerformers: (options) => apiCall(`${API_ENDPOINTS.ANALYTICS_SERVICE}/analytics/top-performers`, options),
};


// Health Check API
export const healthAPI = {
  checkAllServices: async (options) => {
    const services = [
      { name: 'User Service', url: `${API_ENDPOINTS.USER_SERVICE}/health` },
      { name: 'Bank Service', url: `${API_ENDPOINTS.BANK_SERVICE}/health` },
      { name: 'Stock Exchange', url: `${API_ENDPOINTS.STOCK_SERVICE}/health` },
      { name: 'Trade Logger', url: `${API_ENDPOINTS.TRADE_SERVICE}/health` },
      { name: 'Analytics Service', url: `${API_ENDPOINTS.ANALYTICS_SERVICE}/health` }
    ];
    const checks = await Promise.allSettled(
      services.map(s => fetch(s.url, { method: 'GET', signal: options?.signal }).then(res => ({ name: s.name, status: res.ok ? 'healthy' : 'unhealthy' })).catch(() => ({ name: s.name, status: 'unhealthy' })))
    );
    return checks.map(res => res.status === 'fulfilled' ? res.value : { name: 'Unknown', status: 'unhealthy' });
  }
};

