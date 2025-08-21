import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { 
  TrendingUp, 
  User, 
  Mail, 
  Eye, 
  EyeOff, 
  Shield,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { userAPI } from '../../services/api';
import toast from 'react-hot-toast';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Form states
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: 'demo123' // Pre-filled for demo purposes
  });
  
  // Validation states
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  // Redirect if already authenticated
  useEffect(() => {
    const userId = localStorage.getItem('userId');
    if (userId) {
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [navigate, location]);

  // Form validation
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }
    
    if (!isLogin) {
      if (!formData.email.trim()) {
        newErrors.email = 'Email is required';
      } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
        newErrors.email = 'Please enter a valid email';
      }
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // Handle input blur for validation
  const handleInputBlur = (field) => {
    setTouched(prev => ({
      ...prev,
      [field]: true
    }));
    validateForm();
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      if (isLogin) {
        // Login flow - simulate login (in real app, authenticate with backend)
        await simulateLogin();
      } else {
        // Registration flow
        await handleRegistration();
      }
    } catch (error) {
      console.error('Authentication error:', error);
      toast.error(error.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  // Simulate login process
  const simulateLogin = async () => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock login validation
    if (formData.username && formData.password) {
      // Generate mock user data
      const userData = {
        id: Date.now().toString(),
        username: formData.username,
        email: formData.email || `${formData.username}@example.com`,
        balance: 10000,
        createdAt: new Date().toISOString()
      };
      
      // Store in localStorage
      localStorage.setItem('userId', userData.id);
      localStorage.setItem('username', userData.username);
      localStorage.setItem('authToken', 'mock-jwt-token');
      
      toast.success(`Welcome back, ${userData.username}!`);
      
      // Redirect to intended page
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    } else {
      throw new Error('Invalid credentials');
    }
  };

  // Handle user registration
  const handleRegistration = async () => {
    try {
      const response = await userAPI.createUser({
        username: formData.username,
        email: formData.email
      });
      
      if (response.data && response.data.user) {
        const userData = response.data.user;
        
        // Store user data
        localStorage.setItem('userId', userData.id.toString());
        localStorage.setItem('username', userData.username);
        localStorage.setItem('authToken', 'mock-jwt-token');
        
        toast.success(`Account created successfully! Welcome, ${userData.username}!`);
        
        // Redirect to dashboard
        navigate('/', { replace: true });
      }
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Registration failed');
    }
  };

  // Demo user login
  const handleDemoLogin = async () => {
    setFormData({
      username: 'demo_trader',
      email: 'demo@stocksim.com',
      password: 'demo123'
    });
    
    setIsLoading(true);
    
    try {
      await simulateLogin();
    } catch (error) {
      toast.error('Demo login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-slate-900 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-slate-900">
            StockSim
          </h1>
          <p className="text-slate-600 mt-2">
            Professional Stock Market Simulation
          </p>
          <div className="flex items-center justify-center space-x-2 mt-3">
            <Shield className="w-4 h-4 text-emerald-600" />
            <span className="text-sm text-emerald-600 font-medium">
              Secure Trading Platform
            </span>
          </div>
        </div>

        {/* Auth Form */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-xl font-semibold text-slate-900">
              {isLogin ? 'Sign In' : 'Create Account'}
            </h2>
            <p className="text-sm text-slate-600 mt-1">
              {isLogin 
                ? 'Access your trading dashboard' 
                : 'Start your trading journey today'
              }
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {/* Username Field */}
            <div className="form-group">
              <label htmlFor="username" className="form-label">
                Username
              </label>
              <div className="relative">
                <User className="w-5 h-5 text-slate-400 absolute left-3 top-3" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  value={formData.username}
                  onChange={handleInputChange}
                  onBlur={() => handleInputBlur('username')}
                  className={`input pl-10 ${errors.username ? 'input-error' : ''}`}
                  placeholder="Enter your username"
                  disabled={isLoading}
                />
              </div>
              {errors.username && (
                <p className="form-error">{errors.username}</p>
              )}
            </div>

            {/* Email Field (Registration only) */}
            {!isLogin && (
              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-5 h-5 text-slate-400 absolute left-3 top-3" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    onBlur={() => handleInputBlur('email')}
                    className={`input pl-10 ${errors.email ? 'input-error' : ''}`}
                    placeholder="Enter your email"
                    disabled={isLoading}
                  />
                </div>
                {errors.email && (
                  <p className="form-error">{errors.email}</p>
                )}
              </div>
            )}

            {/* Password Field */}
            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleInputChange}
                  onBlur={() => handleInputBlur('password')}
                  className={`input pr-10 ${errors.password ? 'input-error' : ''}`}
                  placeholder="Enter your password"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="form-error">{errors.password}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary w-full flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                  <CheckCircle className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Demo Login Button */}
            {isLogin && (
              <button
                type="button"
                onClick={handleDemoLogin}
                disabled={isLoading}
                className="btn btn-secondary w-full"
              >
                Try Demo Account
              </button>
            )}

          </form>

          {/* Toggle Auth Mode */}
          <div className="text-center pt-4 border-t border-slate-200 mt-6">
            <p className="text-sm text-slate-600">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              {' '}
              <button
                onClick={() => {
                  setIsLogin(!isLogin);
                  setErrors({});
                  setTouched({});
                }}
                className="text-slate-900 font-medium hover:underline"
                disabled={isLoading}
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>

        </div>

        {/* Footer Info */}
        <div className="text-center mt-8 text-xs text-slate-500">
          <p>Distributed Systems Stock Market Simulation</p>
          <p className="mt-1">Built with Berkeley Algorithm & Pyro4 RPC</p>
        </div>

      </div>
    </div>
  );
};

export default Login;