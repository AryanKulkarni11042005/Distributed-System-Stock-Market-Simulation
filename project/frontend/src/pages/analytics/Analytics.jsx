import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  PieChart,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  DollarSign,
  Calendar,
  Download,
  RefreshCw,
  Filter,
  Eye,
  Target,
  Zap,
  Database,
  Clock,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area,
  ResponsiveContainer
} from 'recharts';
import { tradeAPI, stockAPI } from '../../services/api';
import toast from 'react-hot-toast';

const Analytics = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [analyticsData, setAnalyticsData] = useState({
    portfolioAnalysis: [],
    volumeAnalysis: [],
    profitAnalysis: [],
    stockPerformance: [],
    tradingPatterns: []
  });
  const [selectedMetric, setSelectedMetric] = useState('volume');
  const [selectedTimeRange, setSelectedTimeRange] = useState('30d');
  const [sparkJobStatus, setSparkJobStatus] = useState('idle');

  // Color schemes for charts
  const COLORS = ['#0f172a', '#475569', '#64748b', '#94a3b8', '#cbd5e1'];
  const PROFIT_COLORS = ['#10b981', '#ef4444'];

  // Load initial data
  useEffect(() => {
    const abortController = new AbortController();
    const { signal } = abortController;
    
    loadAnalyticsData(signal);
    
    const interval = setInterval(() => {
      refreshAnalytics(signal);
    }, 60000);

    return () => {
      clearInterval(interval);
      abortController.abort();
    };
  }, []);

  // Load analytics data
  const loadAnalyticsData = async (signal) => {
    setLoading(true);
    setSparkJobStatus('running');
    
    try {
      await runSparkAnalytics(signal);
      
      await Promise.all([
        loadPortfolioAnalysis(signal),
        loadVolumeAnalysis(signal),
        loadProfitAnalysis(signal),
        loadStockPerformance(signal),
        loadTradingPatterns(signal)
      ]);
      
      if (!signal.aborted) setSparkJobStatus('completed');
    } catch (error) {
       if (error.name !== 'AbortError') {
        console.error('Error loading analytics:', error);
        toast.error('Failed to load analytics data');
        setSparkJobStatus('failed');
        loadMockAnalyticsData(); // Fallback to mock data on error
      }
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  };

  // Simulate Spark analytics job
  const runSparkAnalytics = async (signal) => {
    return new Promise(resolve => setTimeout(() => {
        if(!signal.aborted) resolve();
    }, 2000));
  };

  // The following functions are placeholders and should be adapted for real API calls
  const loadPortfolioAnalysis = async (signal) => {
    // In a real app, this would be an API call, e.g., api.getPortfolioAnalysis({ signal })
    if (!signal.aborted) setAnalyticsData(prev => ({ ...prev, portfolioAnalysis: getMockPortfolioAnalysis() }));
  };
  const loadVolumeAnalysis = async (signal) => {
    if (!signal.aborted) setAnalyticsData(prev => ({ ...prev, volumeAnalysis: getMockVolumeAnalysis() }));
  };
  const loadProfitAnalysis = async (signal) => {
    if (!signal.aborted) setAnalyticsData(prev => ({ ...prev, profitAnalysis: getMockProfitAnalysis() }));
  };
  const loadStockPerformance = async (signal) => {
    if (!signal.aborted) setAnalyticsData(prev => ({ ...prev, stockPerformance: getMockStockPerformance() }));
  };
  const loadTradingPatterns = async (signal) => {
    if (!signal.aborted) setAnalyticsData(prev => ({ ...prev, tradingPatterns: getMockTradingPatterns() }));
  };

  const loadMockAnalyticsData = () => {
    setAnalyticsData({
      portfolioAnalysis: getMockPortfolioAnalysis(),
      volumeAnalysis: getMockVolumeAnalysis(),
      profitAnalysis: getMockProfitAnalysis(),
      stockPerformance: getMockStockPerformance(),
      tradingPatterns: getMockTradingPatterns()
    });
  };

  const refreshAnalytics = async (signal) => {
    setRefreshing(true);
    try {
      await loadAnalyticsData(signal);
    } catch (error) {
      if(error.name !== 'AbortError') console.error('Error refreshing analytics:', error);
    } finally {
      if(!signal.aborted) setRefreshing(false);
    }
  };

  // Mock data generators
  const getMockPortfolioAnalysis = () => [{ stock: 'AAPL', value: 1502.50, percentage: 28.5, shares: 10, gainLoss: 47.50 },{ stock: 'GOOGL', value: 5501.60, percentage: 45.2, shares: 2, gainLoss: -98.40 },{ stock: 'MSFT', value: 1552.25, percentage: 18.8, shares: 5, gainLoss: 51.00 },{ stock: 'TSLA', value: 2552.25, percentage: 7.5, shares: 3, gainLoss: -347.75 }];
  const getMockVolumeAnalysis = () => [{ date: '2024-08-15', AAPL: 45000, GOOGL: 38000, MSFT: 52000, TSLA: 67000, AMZN: 34000 },{ date: '2024-08-16', AAPL: 47000, GOOGL: 35000, MSFT: 54000, TSLA: 69000, AMZN: 36000 },{ date: '2024-08-17', AAPL: 43000, GOOGL: 40000, MSFT: 51000, TSLA: 64000, AMZN: 38000 },{ date: '2024-08-18', AAPL: 49000, GOOGL: 42000, MSFT: 56000, TSLA: 71000, AMZN: 35000 },{ date: '2024-08-19', AAPL: 46000, GOOGL: 39000, MSFT: 53000, TSLA: 68000, AMZN: 37000 },{ date: '2024-08-20', AAPL: 48000, GOOGL: 41000, MSFT: 55000, TSLA: 70000, AMZN: 39000 },{ date: '2024-08-21', AAPL: 50000, GOOGL: 44000, MSFT: 57000, TSLA: 72000, AMZN: 40000 }];
  const getMockProfitAnalysis = () => [{ category: 'Profitable Trades', value: 68, amount: 1250.75 },{ category: 'Loss Trades', value: 32, amount: -485.30 }];
  const getMockStockPerformance = () => [{ stock: 'AAPL', performance: 3.26, volume: 450000, volatility: 1.8 },{ stock: 'GOOGL', performance: -3.51, volume: 380000, volatility: 2.4 },{ stock: 'MSFT', performance: 1.70, volume: 520000, volatility: 1.5 },{ stock: 'TSLA', performance: -4.49, volume: 670000, volatility: 4.2 },{ stock: 'AMZN', performance: 0.26, volume: 340000, volatility: 2.1 }];
  const getMockTradingPatterns = () => [{ hour: '09:00', buyOrders: 45, sellOrders: 23, volume: 125000 },{ hour: '10:00', buyOrders: 52, sellOrders: 31, volume: 145000 },{ hour: '11:00', buyOrders: 38, sellOrders: 42, volume: 132000 },{ hour: '12:00', buyOrders: 28, sellOrders: 35, volume: 98000 },{ hour: '13:00', buyOrders: 41, sellOrders: 29, volume: 118000 },{ hour: '14:00', buyOrders: 56, sellOrders: 38, volume: 167000 },{ hour: '15:00', buyOrders: 63, sellOrders: 45, volume: 189000 },{ hour: '16:00', buyOrders: 49, sellOrders: 52, volume: 156000 }];

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  const formatPercent = (percent) => `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="flex justify-center mb-4"><div className="relative"><Database className="w-12 h-12 text-slate-300" /><Zap className="w-6 h-6 text-blue-600 absolute -top-1 -right-1 animate-pulse" /></div></div>
          <h3 className="text-lg font-medium text-slate-900">Running Spark Analytics</h3>
          <p className="text-slate-600">Processing distributed analytics across your trading data...</p>
          <div className="spinner mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div><h1 className="text-3xl font-bold text-slate-900">Analytics Dashboard</h1><p className="text-slate-600 mt-1">Apache Spark distributed analytics and insights</p></div>
        <div className="flex items-center space-x-3"><div className="flex items-center space-x-2 text-sm"><Zap className="w-4 h-4 text-blue-600" /><span className="text-slate-600">Spark Job:</span><span className={`font-medium ${sparkJobStatus === 'completed' ? 'text-emerald-600' : sparkJobStatus === 'running' ? 'text-blue-600' : 'text-red-600'}`}>{sparkJobStatus.charAt(0).toUpperCase() + sparkJobStatus.slice(1)}</span></div><button onClick={() => refreshAnalytics()} disabled={refreshing} className="btn btn-outline btn-sm flex items-center space-x-2"><RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} /><span>Refresh</span></button></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card"><div className="flex items-center justify-between"><div><p className="text-sm text-slate-600">Analyzed Volume</p><p className="text-2xl font-bold text-slate-900">2.4M</p><p className="text-sm text-slate-500">trades processed</p></div><div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center"><Database className="w-6 h-6 text-blue-600" /></div></div></div>
        <div className="card"><div className="flex items-center justify-between"><div><p className="text-sm text-slate-600">Processing Speed</p><p className="text-2xl font-bold text-slate-900">1.2k/s</p><p className="text-sm text-slate-500">records per second</p></div><div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center"><Zap className="w-6 h-6 text-emerald-600" /></div></div></div>
        <div className="card"><div className="flex items-center justify-between"><div><p className="text-sm text-slate-600">Data Sources</p><p className="text-2xl font-bold text-slate-900">4</p><p className="text-sm text-slate-500">distributed services</p></div><div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center"><Activity className="w-6 h-6 text-amber-600" /></div></div></div>
        <div className="card"><div className="flex items-center justify-between"><div><p className="text-sm text-slate-600">Last Updated</p><p className="text-2xl font-bold text-slate-900">2m ago</p><p className="text-sm text-slate-500">real-time sync</p></div><div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center"><Clock className="w-6 h-6 text-slate-600" /></div></div></div>
      </div>
      <div className="card"><div className="flex flex-col sm:flex-row gap-4"><div className="flex items-center space-x-2"><Filter className="w-5 h-5 text-slate-400" /><select value={selectedMetric} onChange={(e) => setSelectedMetric(e.target.value)} className="input min-w-[150px]"><option value="volume">Volume Analysis</option><option value="performance">Performance Metrics</option><option value="patterns">Trading Patterns</option><option value="portfolio">Portfolio Analysis</option></select></div><div className="flex items-center space-x-2"><Calendar className="w-5 h-5 text-slate-400" /><select value={selectedTimeRange} onChange={(e) => setSelectedTimeRange(e.target.value)} className="input min-w-[120px]"><option value="7d">Last 7 Days</option><option value="30d">Last 30 Days</option><option value="90d">Last 90 Days</option><option value="1y">Last Year</option></select></div><div className="flex-1"></div><button className="btn btn-outline btn-sm flex items-center space-x-2"><Download className="w-4 h-4" /><span>Export Data</span></button></div></div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card"><div className="card-header"><h3 className="text-lg font-semibold text-slate-900">Portfolio Distribution</h3><p className="text-sm text-slate-600">Asset allocation by value</p></div><div className="h-80"><ResponsiveContainer width="100%" height="100%"><RechartsPieChart><Pie data={analyticsData.portfolioAnalysis} cx="50%" cy="50%" outerRadius={80} fill="#8884d8" dataKey="value" label={({ stock, percentage }) => `${stock} ${percentage.toFixed(1)}%`}>{analyticsData.portfolioAnalysis.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}</Pie><Tooltip formatter={(value) => formatCurrency(value)} /><Legend /></RechartsPieChart></ResponsiveContainer></div></div>
        <div className="card"><div className="card-header"><h3 className="text-lg font-semibold text-slate-900">Trading Volume Trends</h3><p className="text-sm text-slate-600">Daily volume by stock</p></div><div className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={analyticsData.volumeAnalysis}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis /><Tooltip /><Legend /><Bar dataKey="AAPL" stackId="a" fill="#0f172a" /><Bar dataKey="GOOGL" stackId="a" fill="#475569" /><Bar dataKey="MSFT" stackId="a" fill="#64748b" /><Bar dataKey="TSLA" stackId="a" fill="#94a3b8" /><Bar dataKey="AMZN" stackId="a" fill="#cbd5e1" /></BarChart></ResponsiveContainer></div></div>
        <div className="card"><div className="card-header"><h3 className="text-lg font-semibold text-slate-900">Intraday Trading Patterns</h3><p className="text-sm text-slate-600">Buy vs Sell orders by hour</p></div><div className="h-80"><ResponsiveContainer width="100%" height="100%"><LineChart data={analyticsData.tradingPatterns}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="hour" /><YAxis /><Tooltip /><Legend /><Line type="monotone" dataKey="buyOrders" stroke="#10b981" strokeWidth={2} name="Buy Orders" /><Line type="monotone" dataKey="sellOrders" stroke="#ef4444" strokeWidth={2} name="Sell Orders" /></LineChart></ResponsiveContainer></div></div>
        <div className="card"><div className="card-header"><h3 className="text-lg font-semibold text-slate-900">Stock Performance Analysis</h3><p className="text-sm text-slate-600">Performance vs volatility matrix</p></div><div className="space-y-4">{analyticsData.stockPerformance.map((stock, index) => (<div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"><div className="flex items-center space-x-3"><div className="font-medium text-slate-900">{stock.stock}</div><div className="text-sm text-slate-600">Vol: {stock.volume.toLocaleString()}</div></div><div className="flex items-center space-x-4"><div className="text-right"><div className={`font-medium ${stock.performance >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatPercent(stock.performance)}</div><div className="text-xs text-slate-500">Volatility: {stock.volatility}%</div></div><div className={`w-8 h-8 rounded-full flex items-center justify-center ${stock.performance >= 0 ? 'bg-emerald-100' : 'bg-red-100'}`}>{stock.performance >= 0 ? <ArrowUpRight className="w-4 h-4 text-emerald-600" /> : <ArrowDownRight className="w-4 h-4 text-red-600" />}</div></div></div>))}</div></div>
      </div>
      <div className="card"><div className="card-header"><h3 className="text-lg font-semibold text-slate-900">Distributed Analytics Status</h3><p className="text-sm text-slate-600">Apache Spark job execution details</p></div><div className="grid grid-cols-1 md:grid-cols-3 gap-6"><div className="space-y-3"><h4 className="font-medium text-slate-700">Job Execution</h4><div className="space-y-2 text-sm"><div className="flex justify-between"><span className="text-slate-600">Status:</span><span className={`font-medium ${sparkJobStatus === 'completed' ? 'text-emerald-600' : 'text-blue-600'}`}>{sparkJobStatus.charAt(0).toUpperCase() + sparkJobStatus.slice(1)}</span></div><div className="flex justify-between"><span className="text-slate-600">Duration:</span><span className="font-medium">2.4s</span></div><div className="flex justify-between"><span className="text-slate-600">Tasks:</span><span className="font-medium">156 completed</span></div></div></div><div className="space-y-3"><h4 className="font-medium text-slate-700">Data Processing</h4><div className="space-y-2 text-sm"><div className="flex justify-between"><span className="text-slate-600">Records Processed:</span><span className="font-medium">2,401,856</span></div><div className="flex justify-between"><span className="text-slate-600">Data Volume:</span><span className="font-medium">450 MB</span></div><div className="flex justify-between"><span className="text-slate-600">Partitions:</span><span className="font-medium">8</span></div></div></div><div className="space-y-3"><h4 className="font-medium text-slate-700">Resource Usage</h4><div className="space-y-2 text-sm"><div className="flex justify-between"><span className="text-slate-600">Executors:</span><span className="font-medium">4 active</span></div><div className="flex justify-between"><span className="text-slate-600">Memory Used:</span><span className="font-medium">1.2 GB</span></div><div className="flex justify-between"><span className="text-slate-600">CPU Cores:</span><span className="font-medium">8 cores</span></div></div></div></div></div>
    </div>
  );
};

export default Analytics;
