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

// Auth Provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sync token to localStorage
  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  // Logout function
  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setError(null);
    localStorage.removeItem('token');
  }, []);

  // Check for existing session on mount
  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await api.get('/auth/me');
          setUser(response.data);
        } catch (err) {
          // Token invalid or expired
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [token, logout]);

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
