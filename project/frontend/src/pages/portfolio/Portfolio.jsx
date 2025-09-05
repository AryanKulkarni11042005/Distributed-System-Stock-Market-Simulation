import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  PieChart,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  Activity,
  Download,
  RefreshCw,
  Wallet,
  Target,
  Plus,
  Minus
} from 'lucide-react';
import { userAPI, bankAPI, stockAPI, tradeAPI } from '../../services/api';
import toast from 'react-hot-toast';

const Portfolio = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [portfolio, setPortfolio] = useState({ holdings: [] });
  const [userBalance, setUserBalance] = useState(0);
  const [currentStockPrices, setCurrentStockPrices] = useState({});
  const [tradeHistory, setTradeHistory] = useState([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState('all');
  const [portfolioStats, setPortfolioStats] = useState({
    totalValue: 0,
    totalGainLoss: 0,
    totalGainLossPercent: 0,
    dayChange: 0,
    dayChangePercent: 0
  });

  // Load initial data and set up auto-refresh
  useEffect(() => {
    const abortController = new AbortController();
    const { signal } = abortController;
    
    loadPortfolioData(signal);
    
    const interval = setInterval(() => {
      refreshPortfolioData(signal);
    }, 30000);

    return () => {
      clearInterval(interval);
      abortController.abort();
    };
  }, []);

  // Calculate portfolio stats when data changes
  useEffect(() => {
    calculatePortfolioStats();
  }, [portfolio, currentStockPrices, userBalance]);

  // Load all portfolio data
  const loadPortfolioData = async (signal) => {
    setLoading(true);
    try {
      const userId = localStorage.getItem('userId');
      if (userId) {
        await Promise.all([
          loadUserPortfolio(userId, signal),
          loadUserBalance(userId, signal),
          loadCurrentStockPrices(signal),
          loadTradeHistory(userId, signal)
        ]);
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error loading portfolio data:', error);
        toast.error('Failed to load portfolio data');
      }
    } finally {
      if (!signal.aborted) {
        setLoading(false);
      }
    }
  };

  const loadUserPortfolio = async (userId, signal) => {
    try {
      const response = await userAPI.getUserPortfolio(userId, { signal });
      if (response) setPortfolio(response.data.portfolio || { holdings: [] });
    } catch (error) {
      if (error.name !== 'AbortError') console.error('Error loading portfolio:', error);
    }
  };

  const loadUserBalance = async (userId, signal) => {
    try {
      const response = await bankAPI.getBalance(userId, { signal });
      if (response) setUserBalance(response.data.balance || 0);
    } catch (error) {
      if (error.name !== 'AbortError') console.error('Error loading balance:', error);
    }
  };

  const loadCurrentStockPrices = async (signal) => {
    try {
      const response = await stockAPI.getAllStocks({ signal });
      const pricesMap = {};
      if (response && response.data.stocks) {
        response.data.stocks.forEach(stock => {
          pricesMap[stock.symbol] = {
            current_price: stock.current_price,
            price_change: stock.price_change || 0,
            change_percent: stock.change_percent || 0
          };
        });
      }
      setCurrentStockPrices(pricesMap);
    } catch (error) {
      if (error.name !== 'AbortError') console.error('Error loading stock prices:', error);
    }
  };

  const loadTradeHistory = async (userId, signal) => {
    try {
      const response = await tradeAPI.getUserTrades(userId, { signal });
      if (response) setTradeHistory(response.data.trades || []);
    } catch (error) {
      if (error.name !== 'AbortError') console.error('Error loading trade history:', error);
    }
  };

  const refreshPortfolioData = async (signal) => {
    setRefreshing(true);
    try {
      const userId = localStorage.getItem('userId');
      if(userId) {
        await Promise.all([
          loadUserPortfolio(userId, signal),
          loadCurrentStockPrices(signal)
        ]);
      }
    } catch (error) {
      if (error.name !== 'AbortError') console.error('Error refreshing portfolio:', error);
    } finally {
      if (!signal.aborted) setRefreshing(false);
    }
  };

  const calculatePortfolioStats = () => {
    if (!portfolio || !portfolio.holdings || Object.keys(currentStockPrices).length === 0) return;

    let totalHoldingsValue = 0, totalCost = 0, dayChange = 0;

    portfolio.holdings.forEach(holding => {
      const stockPrice = currentStockPrices[holding.stock_symbol];
      if (stockPrice) {
        totalHoldingsValue += holding.quantity * stockPrice.current_price;
        totalCost += holding.quantity * holding.avg_price;
        dayChange += holding.quantity * stockPrice.price_change;
      }
    });

    const totalGainLoss = totalHoldingsValue - totalCost;
    const totalGainLossPercent = totalCost > 0 ? (totalGainLoss / totalCost) * 100 : 0;
    const dayChangePercent = (totalHoldingsValue - dayChange) > 0 ? (dayChange / (totalHoldingsValue - dayChange)) * 100 : 0;

    setPortfolioStats({
      totalValue: totalHoldingsValue + userBalance,
      totalGainLoss, totalGainLossPercent,
      dayChange, dayChangePercent
    });
  };

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  
  const formatPercent = (percent) => {
    const p = percent || 0;
    return `${p >= 0 ? '+' : ''}${p.toFixed(2)}%`;
  };

  const formatDate = (dateString) => {
    if(!dateString) return 'N/A';
    const dateValue = dateString.$date || dateString;
    return new Date(dateValue).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const getHoldingValue = (h) => (currentStockPrices[h.stock_symbol]?.current_price || 0) * h.quantity;
  const getHoldingGainLoss = (h) => getHoldingValue(h) - (h.quantity * h.avg_price);
  const getHoldingGainLossPercent = (h) => {
    const cost = h.quantity * h.avg_price;
    return cost > 0 ? (getHoldingGainLoss(h) / cost) * 100 : 0;
  };

  const getFilteredTradeHistory = () => {
    if (selectedTimeframe === 'all') return tradeHistory;
    const now = new Date();
    const cutoffDate = new Date();
    const days = { '7d': 7, '30d': 30, '90d': 90 }[selectedTimeframe];
    if (!days) return tradeHistory;
    cutoffDate.setDate(now.getDate() - days);
    return tradeHistory.filter(t => new Date(t.timestamp.$date || t.timestamp) >= cutoffDate);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="spinner mx-auto"></div>
          <p className="text-slate-600">Loading your portfolio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div><h1 className="text-3xl font-bold text-slate-900">Portfolio</h1><p className="text-slate-600 mt-1">Track your investments and performance</p></div>
        <div className="flex items-center space-x-3"><button onClick={() => refreshPortfolioData()} disabled={refreshing} className="btn btn-outline btn-sm flex items-center space-x-2"><RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} /><span>Refresh</span></button><Link to="/trading" className="btn btn-primary btn-sm">Trade Stocks</Link></div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
            <div className="flex items-center justify-between"><div><p className="text-sm text-slate-600">Total Portfolio</p><p className="text-2xl font-bold text-slate-900">{formatCurrency(portfolioStats.totalValue)}</p></div><div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center"><PieChart className="w-6 h-6 text-blue-600" /></div></div>
        </div>
        <div className="card">
            <div className="flex items-center justify-between"><div><p className="text-sm text-slate-600">Total Return</p><p className={`text-2xl font-bold ${portfolioStats.totalGainLoss >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatCurrency(portfolioStats.totalGainLoss)}</p><p className={`text-sm ${portfolioStats.totalGainLoss >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatPercent(portfolioStats.totalGainLossPercent)}</p></div><div className={`w-12 h-12 rounded-lg flex items-center justify-center ${portfolioStats.totalGainLoss >= 0 ? 'bg-emerald-100' : 'bg-red-100'}`}>{portfolioStats.totalGainLoss >= 0 ? <TrendingUp className="w-6 h-6 text-emerald-600" /> : <TrendingDown className="w-6 h-6 text-red-600" />}</div></div>
        </div>
        <div className="card">
            <div className="flex items-center justify-between"><div><p className="text-sm text-slate-600">Today's Change</p><p className={`text-2xl font-bold ${portfolioStats.dayChange >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatCurrency(portfolioStats.dayChange)}</p><p className={`text-sm ${portfolioStats.dayChange >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatPercent(portfolioStats.dayChangePercent)}</p></div><div className={`w-12 h-12 rounded-lg flex items-center justify-center ${portfolioStats.dayChange >= 0 ? 'bg-emerald-100' : 'bg-red-100'}`}>{portfolioStats.dayChange >= 0 ? <ArrowUpRight className="w-6 h-6 text-emerald-600" /> : <ArrowDownRight className="w-6 h-6 text-red-600" />}</div></div>
        </div>
        <div className="card">
            <div className="flex items-center justify-between"><div><p className="text-sm text-slate-600">Available Cash</p><p className="text-2xl font-bold text-slate-900">{formatCurrency(userBalance)}</p></div><div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center"><Wallet className="w-6 h-6 text-slate-600" /></div></div>
        </div>
      </div>

      {/* Holdings and History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card"><div className="card-header"><h3 className="text-lg font-semibold text-slate-900">Current Holdings</h3><p className="text-sm text-slate-600">Your active stock positions</p></div>
          {portfolio?.holdings?.length > 0 ? (
            <div className="space-y-4">{portfolio.holdings.map((h, i) => (<div key={i} className="border rounded-lg p-4 hover:bg-slate-50 transition-colors"><div className="flex items-center justify-between mb-3"><div><div className="font-medium text-slate-900">{h.stock_symbol}</div><div className="text-sm text-slate-600">{h.quantity} shares @ {formatCurrency(h.avg_price)}</div></div><div className="text-right"><div className="font-medium text-slate-900">{formatCurrency(getHoldingValue(h))}</div><div className={`text-sm ${currentStockPrices[h.stock_symbol]?.price_change >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatCurrency(currentStockPrices[h.stock_symbol]?.current_price)}</div></div></div><div className="flex items-center justify-between text-sm"><div className={`flex items-center space-x-1 ${getHoldingGainLoss(h) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{getHoldingGainLoss(h) >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}<span>{formatCurrency(getHoldingGainLoss(h))} ({formatPercent(getHoldingGainLossPercent(h))})</span></div><div className="text-slate-500">Since {formatDate(h.purchase_date)}</div></div></div>))}</div>
          ) : (
            <div className="text-center py-8"><Target className="w-12 h-12 text-slate-300 mx-auto mb-4" /><h3 className="text-lg font-medium text-slate-900 mb-2">No holdings yet</h3><p className="text-slate-600 mb-4">Start trading to build your portfolio</p><Link to="/trading" className="btn btn-primary">Start Trading</Link></div>
          )}
        </div>
        <div className="card"><div className="card-header"><div className="flex justify-between items-center"><div><h3 className="text-lg font-semibold text-slate-900">Trade History</h3><p className="text-sm text-slate-600">Your recent transactions</p></div><div className="flex items-center space-x-2"><select value={selectedTimeframe} onChange={(e) => setSelectedTimeframe(e.target.value)} className="input btn-sm min-w-[100px]"><option value="all">All Time</option><option value="7d">Last 7 Days</option><option value="30d">Last 30 Days</option><option value="90d">Last 90 Days</option></select><button className="btn btn-outline btn-sm p-2" title="Export CSV"><Download className="w-4 h-4" /></button></div></div></div>
          {getFilteredTradeHistory().length > 0 ? (
            <div className="space-y-3">{getFilteredTradeHistory().slice(0, 10).map((t, i) => (<div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"><div className="flex items-center space-x-3"><div className={`w-8 h-8 rounded-full flex items-center justify-center ${t.trade_type === 'buy' ? 'bg-emerald-100' : 'bg-red-100'}`}>{t.trade_type === 'buy' ? <Plus className="w-4 h-4 text-emerald-600" /> : <Minus className="w-4 h-4 text-red-600" />}</div><div><div className="font-medium text-slate-900">{t.trade_type.toUpperCase()} {t.stock_symbol}</div><div className="text-sm text-slate-600">{t.quantity} shares @ {formatCurrency(t.price)}</div><div className="text-xs text-slate-500">{formatDate(t.timestamp)}</div></div></div><div className="text-right"><div className={`font-medium ${t.trade_type === 'buy' ? 'text-red-600' : 'text-emerald-600'}`}>{t.trade_type === 'buy' ? '-' : '+'}{formatCurrency(t.total_amount)}</div></div></div>))} {getFilteredTradeHistory().length > 10 && <div className="text-center pt-4"><button className="btn btn-outline btn-sm">View All Trades ({getFilteredTradeHistory().length})</button></div>}</div>
          ) : (
            <div className="text-center py-8"><Activity className="w-12 h-12 text-slate-300 mx-auto mb-4" /><h3 className="text-lg font-medium text-slate-900 mb-2">No trades found</h3><p className="text-slate-600">{selectedTimeframe === 'all' ? 'Start trading to see your transaction history' : 'No trades in the selected timeframe'}</p></div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Portfolio;
