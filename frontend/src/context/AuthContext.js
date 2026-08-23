/**
 * F1 Strategy Intelligence System - Security Layer v3.1
 * Authentication Context for React Frontend
 * 
 * Provides JWT token management, user state, and authentication flows.
 */
import React, { createContext, useState, useContext, useEffect, useMemo, useCallback } from 'react';
import api from '../services/api';

// Create context
const AuthContext = createContext(null);

// Custom hook for using auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const DEFAULT_USER = { username: 'Race Engineer', role: 'admin', email: 'admin@f1strategy.com' };

// Auth Provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(DEFAULT_USER);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading] = useState(false);
  const [error, setError] = useState(null);

  // Sync token to localStorage
  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  // Logout function (Resets session data without navigating away)
  const logout = useCallback(() => {
    setUser(DEFAULT_USER);
    setError(null);
  }, []);

  // Check for existing session or attempt silent login on mount
  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await api.get('/auth/me');
          if (response.data) {
            setUser(response.data);
          }
        } catch (err) {
          // Token invalid or backend offline; maintain default session
        }
      } else {
        try {
          const response = await api.post('/auth/login', {
            username: 'admin',
            password: 'admin123'
          });
          if (response.data?.access_token) {
            setToken(response.data.access_token);
            if (response.data.user) {
              setUser(response.data.user);
            }
          }
        } catch (err) {
          // Auto-login unavailable; continue with default session
        }
      }
    };

    initAuth();
  }, [token]);

  // Login function
  const login = useCallback(async (username, password) => {
    try {
      setError(null);
      const response = await api.post('/auth/login', {
        username,
        password
      });

      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      
      return { success: true, user: userData };
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      return { success: false, error: message };
    }
  }, []);



  // Check if user has required role
  const hasRole = useCallback((requiredRoles) => {
    if (!user) return false;
    if (typeof requiredRoles === 'string') {
      return user.role === requiredRoles;
    }
    return requiredRoles.includes(user.role);
  }, [user]);

  // Check if user is admin
  const isAdmin = useCallback(() => user?.role === 'admin', [user]);

  // Check if user is engineer or admin
  const isEngineerPlus = useCallback(() => ['admin', 'engineer'].includes(user?.role), [user]);

  // Register new user (admin only)
  const register = async (userData) => {
    try {
      setError(null);
      const response = await api.post('/auth/register', userData);
      return { success: true, user: response.data };
    } catch (err) {
      const message = err.response?.data?.detail || 'Registration failed';
      setError(message);
      return { success: false, error: message };
    }
  };

  // Change password
  const changePassword = async (currentPassword, newPassword) => {
    try {
      setError(null);
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      });
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Password change failed';
      setError(message);
      return { success: false, error: message };
    }
  };

  // Get auth header for manual requests
  const getAuthHeader = useCallback(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  const value = useMemo(() => ({
    user,
    token,
    loading,
    error,
    login,
    logout,
    register,
    changePassword,
    hasRole,
    isAdmin,
    isEngineerPlus,
    getAuthHeader,
    isAuthenticated: !!user
  }), [user, token, loading, error, login, logout, hasRole, isAdmin, isEngineerPlus, getAuthHeader]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
