import React, { useState, useEffect } from 'react';
import {
  Search,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  ShoppingCart,
  DollarSign,
  Activity,
  Filter,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Loader2,
  Eye,
  Plus,
  Minus
} from 'lucide-react';
import { stockAPI, bankAPI, userAPI, tradeAPI } from '../../services/api';
import toast from 'react-hot-toast';

const Trading = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stocks, setStocks] = useState([]);
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [userBalance, setUserBalance] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedStock, setSelectedStock] = useState(null);
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [tradeType, setTradeType] = useState('buy');
  const [tradeQuantity, setTradeQuantity] = useState(1);
  const [isProcessingTrade, setIsProcessingTrade] = useState(false);

  // Load initial data and set up auto-refresh
  useEffect(() => {
    const abortController = new AbortController();
    const { signal } = abortController;
    
    loadTradingData(signal);
    
    const interval = setInterval(() => {
      refreshStockPrices(signal);
    }, 15000);

    return () => {
      clearInterval(interval);
      abortController.abort();
    };
  }, []);

  // Filter and search stocks
  useEffect(() => {
    let filtered = stocks;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(stock =>
        stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stock.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply category filter
    if (selectedFilter !== 'all') {
      switch (selectedFilter) {
        case 'gainers':
          filtered = filtered.filter(stock => (stock.price_change || 0) > 0);
          break;
        case 'losers':
          filtered = filtered.filter(stock => (stock.price_change || 0) < 0);
          break;
        case 'most_active':
          filtered = [...filtered].sort((a, b) => (b.volume || 0) - (a.volume || 0));
          break;
        default:
          break;
      }
    }

    setFilteredStocks(filtered);
  }, [stocks, searchTerm, selectedFilter]);

  // Load all trading data
  const loadTradingData = async (signal) => {
    setLoading(true);
    try {
      await Promise.all([
        loadStocks(signal),
        loadUserBalance(signal)
      ]);
    } catch (error) {
       if (error.name !== 'AbortError') {
        console.error('Error loading trading data:', error);
        toast.error('Failed to load trading data');
      }
    } finally {
      if(!signal.aborted) {
        setLoading(false);
      }
    }
  };

  // Load stocks data
  const loadStocks = async (signal) => {
    try {
      const response = await stockAPI.getAllStocks({ signal });
      if(response) setStocks(response.data.stocks || getMockStocks());
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error loading stocks:', error);
        setStocks(getMockStocks()); // Fallback to mock data
      }
    }
  };

  // Load user balance
  const loadUserBalance = async (signal) => {
    try {
      const userId = localStorage.getItem('userId');
      if (userId) {
        const response = await bankAPI.getBalance(userId, { signal });
        if(response) setUserBalance(response.data.balance || 10000);
      }
    } catch (error) {
       if (error.name !== 'AbortError') {
        console.error('Error loading balance:', error);
        setUserBalance(10000); // Fallback
      }
    }
  };

  // Refresh stock prices only
  const refreshStockPrices = async (signal) => {
    setRefreshing(true);
    try {
      await loadStocks(signal);
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error refreshing prices:', error);
      }
    } finally {
       if (!signal.aborted) {
        setRefreshing(false);
      }
    }
  };
  
  // Mock stocks data
  const getMockStocks = () => [
    { symbol: 'AAPL', name: 'Apple Inc.', current_price: 150.25, price_change: 2.15, change_percent: 1.45, volume: 45000 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', current_price: 2750.80, price_change: -15.30, change_percent: -0.55, volume: 38000 },
    { symbol: 'MSFT', name: 'Microsoft Corp.', current_price: 310.45, price_change: 5.20, change_percent: 1.70, volume: 52000 },
    { symbol: 'TSLA', name: 'Tesla Inc.', current_price: 850.75, price_change: -12.85, change_percent: -1.49, volume: 67000 },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', current_price: 3380.25, price_change: 8.90, change_percent: 0.26, volume: 34000 },
    { symbol: 'META', name: 'Meta Platforms Inc.', current_price: 285.60, price_change: -3.40, change_percent: -1.18, volume: 41000 },
    { symbol: 'NVDA', name: 'NVIDIA Corp.', current_price: 420.15, price_change: 12.75, change_percent: 3.13, volume: 59000 },
    { symbol: 'NFLX', name: 'Netflix Inc.', current_price: 385.90, price_change: -8.20, change_percent: -2.08, volume: 28000 }
  ];

  // Handle trade execution
  const handleTrade = async () => {
    if (!selectedStock || tradeQuantity <= 0) {
      toast.error('Please select a valid quantity');
      return;
    }

    const totalAmount = selectedStock.current_price * tradeQuantity;
    
    if (tradeType === 'buy' && totalAmount > userBalance) {
      toast.error('Insufficient funds for this purchase');
      return;
    }

    setIsProcessingTrade(true);

    try {
      const userId = localStorage.getItem('userId');
      const tradeData = {
        stock_symbol: selectedStock.symbol,
        quantity: tradeQuantity,
        price: selectedStock.current_price,
        trade_type: tradeType,
        total_amount: totalAmount
      };

      if (tradeType === 'buy') {
        await userAPI.buyStock(userId, tradeData);
        await bankAPI.debitAccount({ user_id: userId, amount: totalAmount });
      } else {
        await userAPI.sellStock(userId, tradeData);
        await bankAPI.creditAccount({ user_id: userId, amount: totalAmount });
      }

      await tradeAPI.logTrade({ user_id: userId, ...tradeData });

      toast.success(
        `Successfully ${tradeType === 'buy' ? 'bought' : 'sold'} ${tradeQuantity} shares of ${selectedStock.symbol}`
      );

      await loadUserBalance();
      
      setShowTradeModal(false);
      setSelectedStock(null);
      setTradeQuantity(1);

    } catch (error) {
      console.error('Trade execution failed:', error);
      toast.error(error.response?.data?.error || 'Trade execution failed');
    } finally {
      setIsProcessingTrade(false);
    }
  };

  const formatCurrency = (amount) => {
    if (amount === undefined || amount === null || isNaN(amount)) return '$0.00';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(amount));
  };

  const formatPercent = (percent) => {
    if (percent === undefined || percent === null || isNaN(percent)) return '0.00%';
    const p = Number(percent);
    return `${p >= 0 ? '+' : ''}${p.toFixed(2)}%`;
  };

  const openTradeModal = (stock, type) => {
    setSelectedStock(stock);
    setTradeType(type);
    setTradeQuantity(1);
    setShowTradeModal(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="spinner mx-auto"></div>
          <p className="text-slate-600">Loading market data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Stock Trading
          </h1>
          <p className="text-slate-600 mt-1">
            Real-time market data from your distributed system
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <div className="text-sm text-slate-600">Available Balance</div>
            <div className="text-lg font-bold text-slate-900">
              {formatCurrency(userBalance)}
            </div>
          </div>
          
          <button
            onClick={() => refreshStockPrices()}
            disabled={refreshing}
            className="btn btn-outline btn-sm flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Search and Filter Controls */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          
          <div className="flex-1 relative">
            <Search className="w-5 h-5 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search stocks by symbol or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10 w-full"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-slate-400" />
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="input min-w-[150px]"
            >
              <option value="all">All Stocks</option>
              <option value="gainers">Gainers</option>
              <option value="losers">Losers</option>
              <option value="most_active">Most Active</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stock List */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-slate-900">
            Market Data ({filteredStocks.length} stocks)
          </h3>
          <p className="text-sm text-slate-600">
            Live prices updated every 15 seconds
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Stock</th>
                <th>Price</th>
                <th>Change</th>
                <th>Volume</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredStocks.map((stock) => (
                <tr key={stock.symbol} className="table-hover">
                  <td>
                    <div>
                      <div className="font-medium text-slate-900">{stock.symbol}</div>
                      <div className="text-sm text-slate-600">{stock.name}</div>
                    </div>
                  </td>
                  <td>
                    <div className="font-medium text-slate-900">{formatCurrency(stock.current_price)}</div>
                  </td>
                  <td>
                    <div className={`flex items-center space-x-1 ${(stock.price_change || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {(stock.price_change || 0) >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                      <span className="font-medium">{formatPercent(stock.change_percent)}</span>
                    </div>
                    <div className="text-sm text-slate-500">
                      {stock.price_change !== undefined ? `${stock.price_change >= 0 ? '+' : ''}${Number(stock.price_change).toFixed(2)}` : '0.00'}
                    </div>
                  </td>
                  <td>
                    <div className="text-slate-700">{(stock.volume || 0).toLocaleString()}</div>
                  </td>
                  <td>
                    <div className="flex items-center space-x-2">
                      <button onClick={() => openTradeModal(stock, 'buy')} className="btn btn-success btn-sm flex items-center space-x-1"><Plus className="w-3 h-3" /><span>Buy</span></button>
                      <button onClick={() => openTradeModal(stock, 'sell')} className="btn btn-danger btn-sm flex items-center space-x-1"><Minus className="w-3 h-3" /><span>Sell</span></button>
                      <button className="btn btn-outline btn-sm p-2" title="View Details"><Eye className="w-3 h-3" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {filteredStocks.length === 0 && (
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No stocks found</h3>
              <p className="text-slate-600">Try adjusting your search or filter criteria</p>
            </div>
          )}
        </div>
      </div>

      {/* Trade Modal */}
      {showTradeModal && selectedStock && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
            <div className="p-6 border-b"><h3 className="text-xl font-semibold text-slate-900">{tradeType === 'buy' ? 'Buy' : 'Sell'} {selectedStock.symbol}</h3><p className="text-sm text-slate-600 mt-1">Current Price: {formatCurrency(selectedStock.current_price)}</p></div>
            <div className="p-6 space-y-4">
              <div className="bg-slate-50 rounded-lg p-4"><div className="flex items-center justify-between"><div><div className="font-medium text-slate-900">{selectedStock.name}</div><div className="text-sm text-slate-600">{selectedStock.symbol}</div></div><div className="text-right"><div className="font-medium text-slate-900">{formatCurrency(selectedStock.current_price)}</div><div className={`text-sm ${selectedStock.price_change >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatPercent(selectedStock.change_percent)}</div></div></div></div>
              <div className="form-group"><label className="form-label">Quantity</label><div className="flex items-center space-x-2"><button onClick={() => setTradeQuantity(Math.max(1, tradeQuantity - 1))} className="btn btn-outline btn-sm p-2"><Minus className="w-4 h-4" /></button><input type="number" min="1" value={tradeQuantity} onChange={(e) => setTradeQuantity(Math.max(1, parseInt(e.target.value) || 1))} className="input text-center flex-1" /><button onClick={() => setTradeQuantity(tradeQuantity + 1)} className="btn btn-outline btn-sm p-2"><Plus className="w-4 h-4" /></button></div></div>
              <div className="bg-slate-50 rounded-lg p-4"><div className="space-y-2 text-sm"><div className="flex justify-between"><span className="text-slate-600">Shares:</span><span className="font-medium">{tradeQuantity}</span></div><div className="flex justify-between"><span className="text-slate-600">Price per share:</span><span className="font-medium">{formatCurrency(selectedStock.current_price)}</span></div><div className="border-t pt-2 flex justify-between"><span className="font-medium text-slate-900">Total:</span><span className="font-bold text-slate-900">{formatCurrency(selectedStock.current_price * tradeQuantity)}</span></div></div></div>
              {tradeType === 'buy' && (<div className="text-sm"><div className="flex justify-between"><span className="text-slate-600">Available Balance:</span><span className="font-medium">{formatCurrency(userBalance)}</span></div><div className="flex justify-between"><span className="text-slate-600">After Trade:</span><span className={`font-medium ${userBalance - (selectedStock.current_price * tradeQuantity) < 0 ? 'text-red-600' : 'text-emerald-600'}`}>{formatCurrency(userBalance - (selectedStock.current_price * tradeQuantity))}</span></div></div>)}
            </div>
            <div className="p-6 border-t flex space-x-3"><button onClick={() => setShowTradeModal(false)} className="btn btn-outline flex-1" disabled={isProcessingTrade}>Cancel</button><button onClick={handleTrade} disabled={isProcessingTrade || (tradeType === 'buy' && selectedStock.current_price * tradeQuantity > userBalance)} className={`btn flex-1 flex items-center justify-center space-x-2 ${tradeType === 'buy' ? 'btn-success' : 'btn-danger'}`}>{isProcessingTrade ? (<><Loader2 className="w-4 h-4 animate-spin" /><span>Processing...</span></>) : (<><ShoppingCart className="w-4 h-4" /><span>{tradeType === 'buy' ? 'Buy' : 'Sell'} Shares</span></>)}</button></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Trading;
