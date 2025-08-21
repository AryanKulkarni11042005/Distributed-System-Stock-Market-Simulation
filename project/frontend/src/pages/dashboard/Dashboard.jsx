import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  Activity,
  Users,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Wallet,
  BarChart3,
  PlusCircle
} from 'lucide-react';
import { stockAPI, bankAPI, userAPI, tradeAPI, healthAPI } from '../../services/api';
import toast from 'react-hot-toast';
import AddFundsModal from '../../components/common/AddFundsModal'; // Import the new modal

const Dashboard = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [user, setUser] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [recentTrades, setRecentTrades] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [marketSummary, setMarketSummary] = useState(null);
  const [isAddFundsModalOpen, setIsAddFundsModalOpen] = useState(false); // State for the modal

  // Auto-refresh timer
  useEffect(() => {
    loadDashboardData();
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      refreshMarketData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Load all dashboard data
  const loadDashboardData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadUserData(),
        loadMarketData(),
        loadPortfolioData(),
        loadRecentTrades(),
        checkSystemHealth()
      ]);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Load user data
  const loadUserData = async () => {
    try {
      const userId = localStorage.getItem('userId');
      const username = localStorage.getItem('username');
      
      if (userId) {
        // Get user balance
        const balanceResponse = await bankAPI.getBalance(userId);
        setUser({
          id: userId,
          username: username,
          balance: balanceResponse.data.balance || 10000
        });
      }
    } catch (error) {
      console.error('Error loading user data:', error);
      // Use fallback data
      setUser({
        id: localStorage.getItem('userId'),
        username: localStorage.getItem('username'),
        balance: 10000
      });
    }
  };

  // Load market data
  const loadMarketData = async () => {
    try {
      const [stocksResponse, marketSummaryResponse] = await Promise.all([
        stockAPI.getAllStocks(),
        stockAPI.getMarketSummary()
      ]);
      
      setMarketData(stocksResponse.data.stocks || []);
      setMarketSummary(marketSummaryResponse.data || {});
    } catch (error) {
      console.error('Error loading market data:', error);
      // Use mock data as fallback
      setMarketData(getMockStocks());
      setMarketSummary(getMockMarketSummary());
    }
  };

  // Load portfolio data
  const loadPortfolioData = async () => {
    try {
      const userId = localStorage.getItem('userId');
      if (userId) {
        const response = await userAPI.getUserPortfolio(userId);
        setPortfolio(response.data.portfolio || []);
      }
    } catch (error) {
      console.error('Error loading portfolio:', error);
      setPortfolio([]);
    }
  };

  // Load recent trades
  const loadRecentTrades = async () => {
    try {
      const userId = localStorage.getItem('userId');
      if (userId) {
        const response = await tradeAPI.getUserTrades(userId);
        setRecentTrades(response.data.trades?.slice(0, 5) || []);
      }
    } catch (error) {
      console.error('Error loading trades:', error);
      setRecentTrades([]);
    }
  };

  // Check system health
  const checkSystemHealth = async () => {
    try {
      const health = await healthAPI.checkAllServices();
      setSystemHealth(health);
    } catch (error) {
      console.error('Error checking system health:', error);
      setSystemHealth([
        { name: 'User Service', status: 'unhealthy' },
        { name: 'Bank Service', status: 'unhealthy' },
        { name: 'Stock Exchange', status: 'unhealthy' },
        { name: 'Trade Logger', status: 'unhealthy' }
      ]);
    }
  };

  // Refresh market data only
  const refreshMarketData = async () => {
    setRefreshing(true);
    try {
      await loadMarketData();
    } catch (error) {
      console.error('Error refreshing market data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Mock data fallbacks
  const getMockStocks = () => [
    { symbol: 'AAPL', name: 'Apple Inc.', current_price: 150.25, price_change: 2.15, change_percent: 1.45 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', current_price: 2750.80, price_change: -15.30, change_percent: -0.55 },
    { symbol: 'MSFT', name: 'Microsoft Corp.', current_price: 310.45, price_change: 5.20, change_percent: 1.70 },
    { symbol: 'TSLA', name: 'Tesla Inc.', current_price: 850.75, price_change: -12.85, change_percent: -1.49 },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', current_price: 3380.25, price_change: 8.90, change_percent: 0.26 }
  ];

  const getMockMarketSummary = () => ({
    total_volume: 125000,
    active_stocks: 5,
    gainers: 3,
    losers: 2,
    last_updated: new Date().toISOString()
  });

  // Calculate portfolio value
  const calculatePortfolioValue = () => {
    if (!portfolio || !marketData) return 0;
    
    return portfolio.reduce((total, holding) => {
      const stock = marketData.find(s => s.symbol === holding.stock_symbol);
      return total + (holding.quantity * (stock?.current_price || 0));
    }, 0);
  };

  // Update the formatPercent function
  const formatPercent = (percent) => {
    if (percent === undefined || percent === null || isNaN(percent)) {
      return '0.00%';
    }
    return `${Number(percent) >= 0 ? '+' : ''}${Number(percent).toFixed(2)}%`;
  };

  // Update the formatCurrency function
  const formatCurrency = (amount) => {
    if (amount === undefined || amount === null || isNaN(amount)) {
      return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(Number(amount));
  };
  
  // Callback function for when funds are added
  const handleFundsAdded = (newBalance) => {
    setUser(prevUser => ({ ...prevUser, balance: newBalance }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="spinner mx-auto"></div>
          <p className="text-slate-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  const portfolioValue = calculatePortfolioValue();
  const totalValue = (user?.balance || 0) + portfolioValue;

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Trading Dashboard
          </h1>
          <p className="text-slate-600 mt-1">
            Welcome back, {user?.username}. Here's your market overview.
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsAddFundsModalOpen(true)}
            className="btn btn-success btn-sm flex items-center space-x-2"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Funds</span>
          </button>
          <Link to="/trading" className="btn btn-primary btn-sm">
            Start Trading
          </Link>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Total Portfolio Value */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Total Value</p>
              <p className="text-2xl font-bold text-slate-900">
                {formatCurrency(totalValue)}
              </p>
            </div>
            <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <PieChart className="w-6 h-6 text-slate-600" />
            </div>
          </div>
        </div>

        {/* Available Cash */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Available Cash</p>
              <p className="text-2xl font-bold text-slate-900">
                {formatCurrency(user?.balance || 0)}
              </p>
            </div>
            <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
              <Wallet className="w-6 h-6 text-emerald-600" />
            </div>
          </div>
        </div>

        {/* Portfolio Value */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Stocks Value</p>
              <p className="text-2xl font-bold text-slate-900">
                {formatCurrency(portfolioValue)}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Active Positions */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Active Positions</p>
              <p className="text-2xl font-bold text-slate-900">
                {portfolio?.length || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-amber-600" />
            </div>
          </div>
        </div>

      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Market Overview */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Top Stocks */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-slate-900">
                Market Overview
              </h3>
              <p className="text-sm text-slate-600">
                Real-time stock prices from your distributed system
              </p>
            </div>
            
            <div className="space-y-3">
              {marketData && Array.isArray(marketData) && marketData.slice(0, 3).map((stock, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      (stock.price_change || 0) >= 0 ? 'bg-emerald-100' : 'bg-red-100'
                    }`}>
                      {(stock.price_change || 0) >= 0 ? (
                        <ArrowUpRight className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4 text-red-600" />
                      )}
                    </div>
                    <div>
                      <div className="font-medium text-slate-900">
                        {stock.symbol || 'N/A'}
                      </div>
                      <div className="text-sm text-slate-600">
                        {formatCurrency(stock.current_price)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={`text-sm font-medium ${
                      (stock.price_change || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'
                    }`}>
                      {formatPercent(stock.change_percent)}
                    </div>
                    <div className="text-xs text-slate-500">
                      {stock.price_change !== undefined && stock.price_change !== null
                        ? `${stock.price_change >= 0 ? '+' : ''}${Number(stock.price_change).toFixed(2)}`
                        : '0.00'
                      }
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="card-footer">
              <Link 
                to="/trading" 
                className="btn btn-primary w-full"
              >
                View All Stocks
              </Link>
            </div>
          </div>

        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          
          {/* System Health */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-slate-900">
                System Status
              </h3>
              <p className="text-sm text-slate-600">
                Distributed services health
              </p>
            </div>
            
            <div className="space-y-3">
              {systemHealth?.map((service) => (
                <div key={service.name} className="flex items-center justify-between">
                  <span className="text-sm text-slate-700">
                    {service.name}
                  </span>
                  <div className="flex items-center space-x-2">
                    {service.status === 'healthy' ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-emerald-600" />
                        <span className="text-xs text-emerald-600 font-medium">
                          Online
                        </span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-4 h-4 text-red-600" />
                        <span className="text-xs text-red-600 font-medium">
                          Offline
                        </span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-slate-900">
                Recent Trades
              </h3>
              <p className="text-sm text-slate-600">
                Your latest transactions
              </p>
            </div>
            
            {recentTrades.length > 0 ? (
              <div className="space-y-3">
                {recentTrades.map((trade, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <div>
                      <div className="font-medium text-slate-900">
                        {trade.trade_type?.toUpperCase()} {trade.stock_symbol}
                      </div>
                      <div className="text-slate-600">
                        {trade.quantity} shares
                      </div>
                    </div>
                    <div className={`font-medium ${
                      trade.trade_type === 'buy' ? 'text-red-600' : 'text-emerald-600'
                    }`}>
                      {trade.trade_type === 'buy' ? '-' : '+'}
                      {formatCurrency(trade.total_amount)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <Activity className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-500">
                  No trades yet. Start trading to see activity here.
                </p>
              </div>
            )}

            <div className="card-footer">
              <Link 
                to="/portfolio" 
                className="btn btn-outline w-full btn-sm"
              >
                View All Trades
              </Link>
            </div>
          </div>

        </div>
      </div>

      {/* Market Summary Footer */}
      {marketSummary && (
        <div className="card">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-slate-900">
                {marketSummary.total_volume?.toLocaleString() || '0'}
              </div>
              <div className="text-sm text-slate-600">Total Volume</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">
                {marketSummary.active_stocks || 0}
              </div>
              <div className="text-sm text-slate-600">Active Stocks</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-emerald-600">
                {marketSummary.gainers || 0}
              </div>
              <div className="text-sm text-slate-600">Gainers</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {marketSummary.losers || 0}
              </div>
              <div className="text-sm text-slate-600">Losers</div>
            </div>
          </div>
        </div>
      )}
      
      {/* Add Funds Modal */}
      <AddFundsModal 
        isOpen={isAddFundsModalOpen}
        onClose={() => setIsAddFundsModalOpen(false)}
        onFundsAdded={handleFundsAdded}
      />

    </div>
  );
};

export default Dashboard;
