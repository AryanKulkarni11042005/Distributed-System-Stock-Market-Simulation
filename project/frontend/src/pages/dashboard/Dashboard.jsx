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
import AddFundsModal from '../../components/common/AddFundsModal';

const Dashboard = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [user, setUser] = useState(null);
  const [marketData, setMarketData] = useState([]);
  const [portfolio, setPortfolio] = useState({ holdings: [] });
  const [recentTrades, setRecentTrades] = useState([]);
  const [systemHealth, setSystemHealth] = useState([]);
  const [marketSummary, setMarketSummary] = useState({});
  const [isAddFundsModalOpen, setIsAddFundsModalOpen] = useState(false);

  // Auto-refresh timer
  useEffect(() => {
    loadDashboardData();
    
    const interval = setInterval(() => {
      refreshMarketData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Load all dashboard data
  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const userId = localStorage.getItem('userId');
      if (userId) {
        await Promise.all([
          loadUserData(userId),
          loadMarketData(),
          loadPortfolioData(userId),
          loadRecentTrades(userId),
          checkSystemHealth()
        ]);
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Load user data
  const loadUserData = async (userId) => {
    try {
      const username = localStorage.getItem('username');
      const balanceResponse = await bankAPI.getBalance(userId);
      setUser({
        id: userId,
        username: username,
        balance: balanceResponse.data.balance || 0
      });
    } catch (error) {
      console.error('Error loading user data:', error);
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
      setMarketSummary(marketSummaryResponse.data.market_summary || {});
    } catch (error) {
      console.error('Error loading market data:', error);
    }
  };

  // Load portfolio data
  const loadPortfolioData = async (userId) => {
    try {
      const response = await userAPI.getUserPortfolio(userId);
      setPortfolio(response.data.portfolio || { holdings: [] });
    } catch (error) {
      console.error('Error loading portfolio:', error);
      setPortfolio({ holdings: [] });
    }
  };

  // Load recent trades
  const loadRecentTrades = async (userId) => {
    try {
      const response = await tradeAPI.getUserTrades(userId);
      setRecentTrades(response.data.trades?.slice(0, 5) || []);
    } catch (error) {
      console.error('Error loading trades:', error);
    }
  };

  // Check system health
  const checkSystemHealth = async () => {
    try {
      const health = await healthAPI.checkAllServices();
      setSystemHealth(health);
    } catch (error) {
      console.error('Error checking system health:', error);
    }
  };

  // Refresh market data only
  const refreshMarketData = async () => {
    setRefreshing(true);
    try {
      const userId = localStorage.getItem('userId');
      await loadMarketData();
      if(userId) {
        await loadPortfolioData(userId);
      }
    } catch (error) {
      console.error('Error refreshing market data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Calculate portfolio value
  const calculatePortfolioValue = () => {
    if (!portfolio || !portfolio.holdings || !marketData) return 0;
    
    return portfolio.holdings.reduce((total, holding) => {
      const stock = marketData.find(s => s.symbol === holding.stock_symbol);
      return total + (holding.quantity * (stock?.current_price || 0));
    }, 0);
  };
  
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };
  
  const formatPercent = (percent) => {
    const p = percent || 0;
    return `${p >= 0 ? '+' : ''}${p.toFixed(2)}%`;
  };

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

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Active Positions</p>
              <p className="text-2xl font-bold text-slate-900">
                {portfolio?.holdings?.length || 0}
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
              {marketData.slice(0, 3).map((stock, index) => (
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
                {marketSummary.total_stocks?.toLocaleString() || '0'}
              </div>
              <div className="text-sm text-slate-600">Total Stocks</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">
                {formatCurrency(marketSummary.total_market_value)}
              </div>
              <div className="text-sm text-slate-600">Market Value</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-emerald-600">
                {formatCurrency(marketSummary.highest_price)}
              </div>
              <div className="text-sm text-slate-600">Highest Price</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {formatCurrency(marketSummary.lowest_price)}
              </div>
              <div className="text-sm text-slate-600">Lowest Price</div>
            </div>
          </div>
        </div>
      )}
      
      <AddFundsModal 
        isOpen={isAddFundsModalOpen}
        onClose={() => setIsAddFundsModalOpen(false)}
        onFundsAdded={handleFundsAdded}
      />

    </div>
  );
};

export default Dashboard;