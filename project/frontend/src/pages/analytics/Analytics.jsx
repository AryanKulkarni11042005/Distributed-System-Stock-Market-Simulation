import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  PieChart,
  TrendingUp,
  Award,
  Database,
  RefreshCw,
  Zap,
  AlertCircle
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';
import { analyticsAPI } from '../../services/api';
import toast from 'react-hot-toast';

// Colors for charts
const COLORS = ['#0f172a', '#475569', '#64748b', '#94a3b8', '#cbd5e1'];

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [runningJob, setRunningJob] = useState(false);
  const [analyticsData, setAnalyticsData] = useState({
    portfolio: [],
    volume: [],
    profit: [],
    topPerformers: []
  });

  useEffect(() => {
    const controller = new AbortController();
    loadAnalyticsData(controller.signal);
    return () => controller.abort();
  }, []);

  const loadAnalyticsData = async (signal) => {
    setLoading(true);
    try {
      const [portfolioRes, volumeRes, profitRes, topPerformersRes] = await Promise.all([
        analyticsAPI.getPortfolioAnalysis({ signal }),
        analyticsAPI.getVolumeAnalysis({ signal }),
        analyticsAPI.getProfitAnalysis({ signal }),
        analyticsAPI.getTopPerformers({ signal })
      ]);
      setAnalyticsData({
        portfolio: portfolioRes?.data?.portfolio_growth || [],
        volume: volumeRes?.data?.daily_volume || [],
        profit: profitRes?.data?.user_profits || [],
        topPerformers: topPerformersRes?.data?.top_performers || []
      });
    } catch (error) {
      if (error.name !== 'AbortError') {
        toast.error('Could not load analytics. Run jobs first.');
        console.error("Error loading analytics data:", error);
      }
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  };

  const handleRunJobs = async () => {
    const toastId = toast.loading('Starting Spark jobs...');
    setRunningJob(true);
    try {
      await analyticsAPI.runJobs();
      toast.success('Spark jobs completed successfully!', { id: toastId });
      // Reload data after jobs complete
      const controller = new AbortController();
      await loadAnalyticsData(controller.signal);
    } catch (error) {
      toast.error('One or more Spark jobs failed.', { id: toastId });
      console.error("Error running Spark jobs:", error);
    } finally {
      setRunningJob(false);
    }
  };
  
  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="spinner mx-auto"></div>
          <p className="text-slate-600">Loading analytics data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Analytics Dashboard</h1>
          <p className="text-slate-600 mt-1">Insights from your distributed trading data</p>
        </div>
        <button onClick={handleRunJobs} disabled={runningJob} className="btn btn-primary flex items-center space-x-2">
          {runningJob ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          <span>{runningJob ? 'Running Spark Jobs...' : 'Run Spark Jobs'}</span>
        </button>
      </div>
      
      {!analyticsData.portfolio.length && !analyticsData.volume.length ? (
        <div className="card text-center py-12">
            <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-800">No Analytics Data Found</h3>
            <p className="text-slate-600 mt-2">
                It looks like the analytics jobs haven't been run yet.
            </p>
            <p className="text-slate-600 mt-1">
                Click the "Run Spark Jobs" button to process your trading data.
            </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="card-header text-lg font-semibold text-slate-900">User Profit & Loss</h3>
            <div className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={analyticsData.profit} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="user_id" tickFormatter={(id) => `User ${String(id).slice(-4)}`} /><YAxis tickFormatter={formatCurrency} /><Tooltip formatter={(value) => formatCurrency(value)} /><Legend /><Bar dataKey="net_profit" fill="#0f172a" name="Net Profit" /></BarChart></ResponsiveContainer></div>
          </div>

          <div className="card">
            <h3 className="card-header text-lg font-semibold text-slate-900">Daily Trading Volume</h3>
            <div className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={analyticsData.volume} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis /><Tooltip formatter={(value) => value.toLocaleString()} /><Legend /><Bar dataKey="total_daily_volume" fill="#475569" name="Total Volume" /></BarChart></ResponsiveContainer></div>
          </div>
          
          <div className="card lg:col-span-2">
            <h3 className="card-header text-lg font-semibold text-slate-900">Top Performing Traders</h3>
            <div className="space-y-4">
              {analyticsData.topPerformers.map((user, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Award className="w-6 h-6 text-amber-500" />
                    <div>
                      <div className="font-medium text-slate-900">User {String(user.user_id).slice(-4)}</div>
                      <div className="text-sm text-slate-600">{user.total_trades} trades</div>
                    </div>
                  </div>
                  <div className={`text-right font-medium ${user.estimated_profit >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    <div>{formatCurrency(user.estimated_profit)}</div>
                    <div className="text-xs">{user.profit_percentage.toFixed(2)}% ROI</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;

