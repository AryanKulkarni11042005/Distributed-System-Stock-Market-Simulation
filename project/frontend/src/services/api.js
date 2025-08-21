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

const api = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API endpoints
const API_ENDPOINTS = {
  USER_SERVICE: `${API_BASE_URL}:${USER_SERVICE_PORT}`,
  BANK_SERVICE: `${API_BASE_URL}:${BANK_SERVICE_PORT}`,
  STOCK_SERVICE: `${API_BASE_URL}:${STOCK_SERVICE_PORT}`,
  TRADE_SERVICE: `${API_BASE_URL}:${TRADE_SERVICE_PORT}`
};

// Generic API call function with improved error handling
const apiCall = async (url, options = {}) => {
  if (USE_MOCK_DATA) {
    console.log(`[MOCK] API call to: ${url}`);
    // Simulate a delay for mock calls
    await new Promise(resolve => setTimeout(resolve, 300));
    // Forcing an error to show mock data fallback in logs
    throw new Error('Using mock data - backend not available');
  }

  console.log(`[REAL] API call to: ${url}`);
  
  try {
    // Using fetch API as it's common in modern React
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`[REAL] API response:`, data);
    return { data }; // Standardize response format
    
  } catch (error) {
    console.error(`[REAL] API call failed for ${url}:`, error);
    throw error;
  }
};


// User Service API
export const userAPI = {
  // FIX: Endpoint changed from /create_user to /user/create
  createUser: (userData) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/create`, {
    method: 'POST',
    body: JSON.stringify(userData)
  }),

  // FIX: Endpoint changed to match the blueprint in user_service/app.py
  getUserPortfolio: (userId) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/${userId}/portfolio`),

  // NOTE: buy_stock and sell_stock endpoints are not defined in your Python code.
  // I've mapped them to the portfolio update endpoint.
  buyStock: (userId, tradeData) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/${userId}/portfolio/update`, {
    method: 'POST',
    body: JSON.stringify({ ...tradeData, trade_type: 'buy' })
  }),

  sellStock: (userId, tradeData) => apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/${userId}/portfolio/update`, {
    method: 'POST',
    body: JSON.stringify({ ...tradeData, trade_type: 'sell' })
  })
};

// Bank Service API
export const bankAPI = {
  // FIX: Corrected endpoint to match bank_service/app.py
  getBalance: (userId) => apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/balance/${userId}`),
  creditAccount: (transactionData) => apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/credit`, {
    method: 'POST',
    body: JSON.stringify(transactionData)
  }),
  debitAccount: (transactionData) => apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/debit`, {
    method: 'POST',
    body: JSON.stringify(transactionData)
  })
};

// Stock Service API
export const stockAPI = {
  // Endpoints are correct
  getAllStocks: () => apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks`),
  getStock: (symbol) => apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks/${symbol}`),
  getMarketSummary: () => apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks/market/summary`)
};

// Trade Service API
export const tradeAPI = {
  // Endpoints are correct
  logTrade: (tradeData) => apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/log`, {
    method: 'POST',
    body: JSON.stringify(tradeData)
  }),
  getUserTrades: (userId) => apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/user/${userId}`),
  getAllTrades: () => apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/all`)
};

// Health Check API
export const healthAPI = {
  checkAllServices: async () => {
    const services = [
      { name: 'User Service', url: `${API_ENDPOINTS.USER_SERVICE}/health` },
      { name: 'Bank Service', url: `${API_ENDPOINTS.BANK_SERVICE}/health` },
      { name: 'Stock Exchange', url: `${API_ENDPOINTS.STOCK_SERVICE}/health` },
      { name: 'Trade Logger', url: `${API_ENDPOINTS.TRADE_SERVICE}/health` }
    ];

    const healthChecks = await Promise.allSettled(
      services.map(service => 
        fetch(service.url, { method: 'GET', timeout: 5000 })
          .then(res => ({ name: service.name, status: res.ok ? 'healthy' : 'unhealthy' }))
          .catch(() => ({ name: service.name, status: 'unhealthy' }))
      )
    );

    return healthChecks.map(result => result.value);
  }
};

export default {
  userAPI,
  bankAPI,
  stockAPI,
  tradeAPI,
  healthAPI
};
