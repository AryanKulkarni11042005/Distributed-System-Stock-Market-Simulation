import axios from 'axios';
import toast from 'react-hot-toast';

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost';
const USER_SERVICE_PORT = import.meta.env.VITE_USER_SERVICE_PORT || '5001';
const BANK_SERVICE_PORT = import.meta.env.VITE_BANK_SERVICE_PORT || '5002';
const STOCK_SERVICE_PORT = import.meta.env.VITE_STOCK_SERVICE_PORT || '5003';
const TRADE_SERVICE_PORT = import.meta.env.VITE_TRADE_SERVICE_PORT || '5004';

// Feature flag for development mode
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';

console.log('API Configuration:', {
  USE_MOCK_DATA,
  USER_SERVICE: `${API_BASE_URL}:${USER_SERVICE_PORT}`,
  BANK_SERVICE: `${API_BASE_URL}:${BANK_SERVICE_PORT}`,
  STOCK_SERVICE: `${API_BASE_URL}:${STOCK_SERVICE_PORT}`,
  TRADE_SERVICE: `${API_BASE_URL}:${TRADE_SERVICE_PORT}`
});

// API endpoints
const API_ENDPOINTS = {
  USER_SERVICE: `${API_BASE_URL}:${USER_SERVICE_PORT}`,
  BANK_SERVICE: `${API_BASE_URL}:${BANK_SERVICE_PORT}`,
  STOCK_SERVICE: `${API_BASE_URL}:${STOCK_SERVICE_PORT}`,
  TRADE_SERVICE: `${API_BASE_URL}:${TRADE_SERVICE_PORT}`
};

// Generic API call function with AbortController support
const apiCall = async (url, options = {}) => {
  if (USE_MOCK_DATA) {
    console.log(`[MOCK] API call to: ${url}`);
    await new Promise(resolve => setTimeout(resolve, 300));
    throw new Error('Using mock data - backend not available');
  }

  console.log(`[REAL] API call to: ${url}`);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      signal: options.signal, // Pass the signal to the fetch request
    });

    if (options.signal?.aborted) {
        throw new DOMException('Request aborted', 'AbortError');
    }

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }
    
    console.log(`[REAL] API response for ${url}:`, data);
    return { data };
    
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error(`[REAL] API call failed for ${url}:`, error);
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
  creditAccount: (transactionData, options) => apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/credit`, { method: 'POST', body: JSON.stringify(transactionData), ...options }),
  debitAccount: (transactionData, options) => apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/debit`, { method: 'POST', body: JSON.stringify(transactionData), ...options })
};

// Stock Service API
export const stockAPI = {
  getAllStocks: (options) => apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks`, options),
  getStock: (symbol, options) => apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks/${symbol}`, options),
  getMarketSummary: (options) => apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks/market/summary`, options)
};

// Trade Service API
export const tradeAPI = {
  logTrade: (tradeData, options) => apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/log`, { method: 'POST', body: JSON.stringify(tradeData), ...options }),
  getUserTrades: (userId, options) => apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/user/${userId}`, options),
  getAllTrades: (options) => apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/all`, options)
};

// Health Check API
export const healthAPI = {
  checkAllServices: async (options) => {
    const services = [
      { name: 'User Service', url: `${API_ENDPOINTS.USER_SERVICE}/health` },
      { name: 'Bank Service', url: `${API_ENDPOINTS.BANK_SERVICE}/health` },
      { name: 'Stock Exchange', url: `${API_ENDPOINTS.STOCK_SERVICE}/health` },
      { name: 'Trade Logger', url: `${API_ENDPOINTS.TRADE_SERVICE}/health` }
    ];

    const healthChecks = await Promise.allSettled(
      services.map(service => 
        fetch(service.url, { method: 'GET', timeout: 5000, signal: options?.signal })
          .then(res => ({ name: service.name, status: res.ok ? 'healthy' : 'unhealthy' }))
          .catch(() => ({ name: service.name, status: 'unhealthy' }))
      )
    );

    return healthChecks.map(result => result.status === 'fulfilled' ? result.value : { name: result.reason.name, status: 'unhealthy' });
  }
};

export default {
  userAPI,
  bankAPI,
  stockAPI,
  tradeAPI,
  healthAPI
};
