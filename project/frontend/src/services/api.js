import axios from 'axios';
import toast from 'react-hot-toast';

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost';
const USER_SERVICE_PORT = import.meta.env.VITE_USER_SERVICE_PORT || '5001';
const BANK_SERVICE_PORT = import.meta.env.VITE_BANK_SERVICE_PORT || '5002';
const STOCK_SERVICE_PORT = import.meta.env.VITE_STOCK_SERVICE_PORT || '5003';
const TRADE_SERVICE_PORT = import.meta.env.VITE_TRADE_SERVICE_PORT || '5004';

// Feature flag for development mode - now reads from environment
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

// Mock data generators (same as before)
const mockData = {
  user: {
    id: "1755794388796",
    username: "demo_trader",
    balance: 10000
  },
  
  stocks: [
    { symbol: 'AAPL', name: 'Apple Inc.', current_price: 150.25, price_change: 2.15, change_percent: 1.45, volume: 45000 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', current_price: 2750.80, price_change: -15.30, change_percent: -0.55, volume: 38000 },
    { symbol: 'MSFT', name: 'Microsoft Corp.', current_price: 310.45, price_change: 5.20, change_percent: 1.70, volume: 52000 },
    { symbol: 'TSLA', name: 'Tesla Inc.', current_price: 850.75, price_change: -12.85, change_percent: -1.49, volume: 67000 },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', current_price: 3380.25, price_change: 8.90, change_percent: 0.26, volume: 34000 }
  ],

  portfolio: [
    { stock_symbol: 'AAPL', quantity: 10, average_price: 145.50, purchase_date: '2024-01-15' },
    { stock_symbol: 'GOOGL', quantity: 2, average_price: 2800.00, purchase_date: '2024-01-20' },
    { stock_symbol: 'MSFT', quantity: 5, average_price: 300.25, purchase_date: '2024-02-01' }
  ],

  trades: [
    { trade_id: 1, stock_symbol: 'AAPL', trade_type: 'buy', quantity: 10, price: 145.50, total_amount: 1455.00, timestamp: '2024-01-15T10:30:00Z' },
    { trade_id: 2, stock_symbol: 'GOOGL', trade_type: 'buy', quantity: 2, price: 2800.00, total_amount: 5600.00, timestamp: '2024-01-20T14:15:00Z' },
    { trade_id: 3, stock_symbol: 'MSFT', trade_type: 'buy', quantity: 5, price: 300.25, total_amount: 1501.25, timestamp: '2024-02-01T09:45:00Z' }
  ],

  marketSummary: {
    total_volume: 125000,
    active_stocks: 5,
    gainers: 3,
    losers: 2,
    last_updated: new Date().toISOString()
  }
};

// Mock API delay simulation
const mockDelay = (ms = 500) => new Promise(resolve => setTimeout(resolve, ms));

// Generic API call function with improved error handling
const apiCall = async (url, options = {}) => {
  if (USE_MOCK_DATA) {
    console.log(`[MOCK] API call to: ${url}`);
    await mockDelay(300);
    throw new Error('Using mock data - backend not available');
  }

  console.log(`[REAL] API call to: ${url}`);
  
  try {
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
    return data;
    
  } catch (error) {
    console.error(`[REAL] API call failed for ${url}:`, error);
    throw error;
  }
};

// API request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const message = error.response?.data?.error || 'An error occurred';
    toast.error(message);
    
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// User Service API
export const userAPI = {
  createUser: async (userData) => {
    try {
      if (USE_MOCK_DATA) {
        await mockDelay();
        return {
          data: {
            user: {
              id: Date.now().toString(),
              username: userData.username,
              email: userData.email
            }
          }
        };
      }
      
      const response = await apiCall(`${API_ENDPOINTS.USER_SERVICE}/create_user`, {
        method: 'POST',
        body: JSON.stringify(userData)
      });
      
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for createUser');
      await mockDelay();
      return {
        data: {
          user: {
            id: Date.now().toString(),
            username: userData.username,
            email: userData.email
          }
        }
      };
    }
  },

  getUserPortfolio: async (userId) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      // Try different possible endpoint patterns
      let response;
      try {
        response = await apiCall(`${API_ENDPOINTS.USER_SERVICE}/get_portfolio/${userId}`);
      } catch (error1) {
        try {
          response = await apiCall(`${API_ENDPOINTS.USER_SERVICE}/user/${userId}/portfolio`);
        } catch (error2) {
          try {
            response = await apiCall(`${API_ENDPOINTS.USER_SERVICE}/portfolio/${userId}`);
          } catch (error3) {
            throw error3;
          }
        }
      }
      
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for getUserPortfolio');
      await mockDelay();
      return { data: { portfolio: mockData.portfolio } };
    }
  },

  buyStock: async (userId, tradeData) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.USER_SERVICE}/buy_stock`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, ...tradeData })
      });
      
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for buyStock');
      await mockDelay();
      return { data: { success: true, message: 'Trade executed (mock)' } };
    }
  },

  sellStock: async (userId, tradeData) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.USER_SERVICE}/sell_stock`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, ...tradeData })
      });
      
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for sellStock');
      await mockDelay();
      return { data: { success: true, message: 'Trade executed (mock)' } };
    }
  }
};

// Bank Service API
export const bankAPI = {
  getBalance: async (userId) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/balance/${userId}`);
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for getBalance');
      await mockDelay();
      return { data: { balance: mockData.user.balance } };
    }
  },

  creditAccount: async (transactionData) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/credit`, {
        method: 'POST',
        body: JSON.stringify(transactionData)
      });
      
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for creditAccount');
      await mockDelay();
      return { data: { success: true, new_balance: mockData.user.balance + transactionData.amount } };
    }
  },

  debitAccount: async (transactionData) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.BANK_SERVICE}/bank/debit`, {
        method: 'POST',
        body: JSON.stringify(transactionData)
      });
      
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for debitAccount');
      await mockDelay();
      return { data: { success: true, new_balance: mockData.user.balance - transactionData.amount } };
    }
  }
};

// Stock Service API
export const stockAPI = {
  getAllStocks: async () => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks`);
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for getAllStocks');
      await mockDelay();
      return { data: { stocks: mockData.stocks } };
    }
  },

  getStock: async (symbol) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks/${symbol}`);
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for getStock');
      await mockDelay();
      const stock = mockData.stocks.find(s => s.symbol === symbol);
      return { data: { stock: stock || mockData.stocks[0] } };
    }
  },

  getMarketSummary: async () => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.STOCK_SERVICE}/stocks/market/summary`);
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for getMarketSummary');
      await mockDelay();
      return { data: mockData.marketSummary };
    }
  }
};

// Trade Service API
export const tradeAPI = {
  logTrade: async (tradeData) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/log`, {
        method: 'POST',
        body: JSON.stringify(tradeData)
      });
      
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for logTrade');
      await mockDelay();
      return { data: { success: true, trade_id: Date.now() } };
    }
  },

  getUserTrades: async (userId) => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/user/${userId}`);
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for getUserTrades');
      await mockDelay();
      return { data: { trades: mockData.trades } };
    }
  },

  getAllTrades: async () => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const response = await apiCall(`${API_ENDPOINTS.TRADE_SERVICE}/trade/all`);
      return { data: response };
      
    } catch (error) {
      console.log('Falling back to mock data for getAllTrades');
      await mockDelay();
      return { data: { trades: mockData.trades } };
    }
  }
};

// Health Check API
export const healthAPI = {
  checkAllServices: async () => {
    try {
      if (USE_MOCK_DATA) throw new Error('Mock mode');
      
      const services = [
        { name: 'User Service', url: `${API_ENDPOINTS.USER_SERVICE}/health` },
        { name: 'Bank Service', url: `${API_ENDPOINTS.BANK_SERVICE}/health` },
        { name: 'Stock Exchange', url: `${API_ENDPOINTS.STOCK_SERVICE}/health` },
        { name: 'Trade Logger', url: `${API_ENDPOINTS.TRADE_SERVICE}/health` }
      ];

      const healthChecks = await Promise.allSettled(
        services.map(async (service) => {
          try {
            const response = await fetch(service.url, { 
              method: 'GET',
              timeout: 5000 
            });
            return {
              name: service.name,
              status: response.ok ? 'healthy' : 'unhealthy'
            };
          } catch (error) {
            return {
              name: service.name,
              status: 'unhealthy'
            };
          }
        })
      );

      return healthChecks.map(result => 
        result.status === 'fulfilled' ? result.value : { 
          name: 'Unknown Service', 
          status: 'unhealthy' 
        }
      );
      
    } catch (error) {
      console.log('Falling back to mock data for health check');
      await mockDelay();
      return [
        { name: 'User Service', status: 'healthy' },
        { name: 'Bank Service', status: 'healthy' },
        { name: 'Stock Exchange', status: 'healthy' },
        { name: 'Trade Logger', status: 'healthy' }
      ];
    }
  }
};

export default {
  userAPI,
  bankAPI,
  stockAPI,
  tradeAPI,
  healthAPI
};