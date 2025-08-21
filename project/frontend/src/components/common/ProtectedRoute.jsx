import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Shield, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null); // null = checking, true/false = result
  const [userInfo, setUserInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      setIsLoading(true);
      
      // Check localStorage for user credentials
      const userId = localStorage.getItem('userId');
      const username = localStorage.getItem('username');
      const authToken = localStorage.getItem('authToken');

      if (!userId || !username) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // Optional: Verify with backend (simulate API call)
      // In a real app, you'd validate the token with your backend
      try {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Mock validation - in real app, call your user service
        const mockUserValidation = {
          id: userId,
          username: username,
          isValid: true,
          balance: 10000, // Mock balance
          lastLogin: new Date().toISOString()
        };

        if (mockUserValidation.isValid) {
          setUserInfo(mockUserValidation);
          setIsAuthenticated(true);
        } else {
          // Invalid token, clear storage
          localStorage.removeItem('userId');
          localStorage.removeItem('username');
          localStorage.removeItem('authToken');
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Authentication validation failed:', error);
        setIsAuthenticated(false);
      }

    } catch (error) {
      console.error('Authentication check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Loading state
  if (isLoading || isAuthenticated === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="relative">
              <Shield className="w-12 h-12 text-slate-300" />
              <Loader2 className="w-6 h-6 text-slate-600 absolute top-3 left-3 animate-spin" />
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium text-slate-900">
              Verifying Access
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              Checking your authentication status...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return (
      <Navigate 
        to="/login" 
        state={{ from: location }} 
        replace 
      />
    );
  }

  // Authenticated - show success message briefly then render children
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Optional: Brief authentication success indicator */}
      {userInfo && (
        <AuthenticationSuccess userInfo={userInfo} />
      )}
      
      {/* Render the protected content */}
      {children}
    </div>
  );
};

// Optional success notification component
const AuthenticationSuccess = ({ userInfo }) => {
  const [showSuccess, setShowSuccess] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSuccess(false);
    }, 2000); // Hide after 2 seconds

    return () => clearTimeout(timer);
  }, []);

  if (!showSuccess) return null;

  return (
    <div className="fixed top-20 right-4 z-50 animate-slide-in">
      <div className="bg-white border border-emerald-200 rounded-lg shadow-lg p-4 max-w-sm">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-medium text-slate-900">
              Access Granted
            </h4>
            <p className="text-xs text-slate-500 mt-1">
              Welcome back, {userInfo.username}
            </p>
            <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
              <span>Secure Session</span>
              <span className="status-dot status-online"></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Error boundary for authentication errors
export const AuthenticationError = ({ error, onRetry }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center space-y-6 max-w-md mx-auto p-6">
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
        </div>
        
        <div>
          <h2 className="text-xl font-semibold text-slate-900">
            Authentication Error
          </h2>
          <p className="text-slate-600 mt-2">
            We couldn't verify your access to the trading platform.
          </p>
          {error && (
            <p className="text-sm text-red-600 mt-2 bg-red-50 p-2 rounded">
              {error.message}
            </p>
          )}
        </div>

        <div className="space-y-3">
          <button
            onClick={onRetry}
            className="btn btn-primary w-full"
          >
            Try Again
          </button>
          
          <button
            onClick={() => {
              localStorage.clear();
              window.location.href = '/login';
            }}
            className="btn btn-outline w-full"
          >
            Return to Login
          </button>
        </div>

        <div className="text-xs text-slate-500">
          <p>If the problem persists, please contact support.</p>
        </div>
      </div>
    </div>
  );
};

export default ProtectedRoute;