import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  TrendingUp, 
  User, 
  PieChart, 
  BarChart3, 
  Wallet, 
  LogOut,
  Menu,
  X,
  Clock,
  Wifi,
  WifiOff
} from 'lucide-react';

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [servicesStatus, setServicesStatus] = useState('checking');
  const [user, setUser] = useState(null);

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Check if user is logged in
  useEffect(() => {
    const userId = localStorage.getItem('userId');
    const username = localStorage.getItem('username');
    if (userId && username) {
      setUser({ id: userId, username });
    }
  }, []);

  // Mock services status check
  useEffect(() => {
    // Simulate checking backend services
    const checkServices = async () => {
      try {
        // This would be a real health check to your backend
        setServicesStatus('online');
      } catch (error) {
        setServicesStatus('offline');
      }
    };
    
    checkServices();
    const interval = setInterval(checkServices, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: PieChart },
    { name: 'Trading', href: '/trading', icon: TrendingUp },
    { name: 'Portfolio', href: '/portfolio', icon: Wallet },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ];

  const handleLogout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    localStorage.removeItem('authToken');
    navigate('/login');
  };

  const isCurrentPath = (path) => {
    return location.pathname === path;
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (location.pathname === '/login') {
    return null; // Don't show navbar on login page
  }

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="container">
        <div className="flex justify-between items-center h-16">
          
          {/* Logo and Brand */}
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-slate-900">
                StockSim
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                      isCurrentPath(item.href)
                        ? 'bg-slate-900 text-white'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Right Side - Time, Status, User */}
          <div className="flex items-center space-x-6">
            
            {/* System Time & Status */}
            <div className="hidden lg:flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2 text-slate-600">
                <Clock className="w-4 h-4" />
                <span className="font-mono">{formatTime(currentTime)}</span>
              </div>
              
              <div className="flex items-center space-x-2">
                {servicesStatus === 'online' ? (
                  <>
                    <Wifi className="w-4 h-4 text-emerald-600" />
                    <span className="text-emerald-600 text-xs font-medium">Online</span>
                  </>
                ) : servicesStatus === 'offline' ? (
                  <>
                    <WifiOff className="w-4 h-4 text-red-600" />
                    <span className="text-red-600 text-xs font-medium">Offline</span>
                  </>
                ) : (
                  <div className="spinner"></div>
                )}
              </div>
            </div>

            {/* User Menu */}
            {user ? (
              <div className="flex items-center space-x-3">
                <div className="hidden sm:block text-right">
                  <div className="text-sm font-medium text-slate-900">
                    Welcome back
                  </div>
                  <div className="text-xs text-slate-500">
                    {user.username}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-slate-600" />
                  </div>
                  
                  <button
                    onClick={handleLogout}
                    className="p-2 text-slate-400 hover:text-slate-600 transition-colors duration-200"
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <Link
                to="/login"
                className="btn btn-primary btn-sm"
              >
                Login
              </Link>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 text-slate-400 hover:text-slate-600"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 py-4">
            <div className="space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center space-x-3 px-4 py-3 text-sm font-medium rounded-lg mx-2 transition-colors duration-200 ${
                      isCurrentPath(item.href)
                        ? 'bg-slate-900 text-white'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
            
            {/* Mobile Status Info */}
            <div className="border-t border-slate-200 mt-4 pt-4 px-4">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2 text-slate-600">
                  <Clock className="w-4 h-4" />
                  <span className="font-mono">{formatTime(currentTime)}</span>
                </div>
                
                <div className="flex items-center space-x-2">
                  {servicesStatus === 'online' ? (
                    <>
                      <Wifi className="w-4 h-4 text-emerald-600" />
                      <span className="text-emerald-600 text-xs font-medium">Online</span>
                    </>
                  ) : (
                    <>
                      <WifiOff className="w-4 h-4 text-red-600" />
                      <span className="text-red-600 text-xs font-medium">Offline</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;