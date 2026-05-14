import React, { createContext, useContext, useState, useCallback, useRef, useMemo } from 'react';
import { useSettings } from './SettingsContext';

const NotificationContext = createContext(null);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

const NOTIFICATION_TYPES = {
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical',
  PIT_STOP: 'pit_stop',
  OVERTAKE: 'overtake',
  WEATHER: 'weather',
  STRATEGY: 'strategy',
};

export const NotificationProvider = ({ children }) => {
  const { notificationsEnabled, soundEnabled } = useSettings();
  const [notifications, setNotifications] = useState([]);
  const [activeToasts, setActiveToasts] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const idCounter = useRef(0);
  const audioRef = useRef(null);

  // Initialize audio on first user interaction
  const initAudio = useCallback(() => {
    if (!audioRef.current && soundEnabled) {
      audioRef.current = new Audio('/notification.mp3');
    }
  }, [soundEnabled]);

  const playSound = useCallback(() => {
    if (soundEnabled && audioRef.current) {
      audioRef.current.play().catch(() => {});
    }
  }, [soundEnabled]);

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
    setActiveToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const dismissToast = useCallback((id) => {
    setActiveToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addNotification = useCallback(({
    type = NOTIFICATION_TYPES.INFO,
    title,
    message,
    duration = 5000,
    persistent = false,
    data = null,
    icon = null,
  }) => {
    if (!notificationsEnabled && !persistent) return;

    const id = ++idCounter.current;
    const timestamp = new Date().toISOString();

    const notification = {
      id,
      type,
      title,
      message,
      timestamp,
      read: false,
      persistent,
      data,
      icon,
    };

    setNotifications(prev => [notification, ...prev].slice(0, 50)); // Keep last 50
    setUnreadCount(prev => prev + 1);
    
    // Add to active toasts
    setActiveToasts(prev => [notification, ...prev]);

    if (soundEnabled && (type === NOTIFICATION_TYPES.CRITICAL || type === NOTIFICATION_TYPES.STRATEGY)) {
      playSound();
    }

    // Auto-remove toast after duration (keeps it in notification history)
    if (duration > 0) {
      setTimeout(() => {
        dismissToast(id);
      }, duration);
    }

    return id;
  }, [notificationsEnabled, soundEnabled, playSound, dismissToast]);

  const markAsRead = useCallback((id) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  // Convenience methods for common notification types - stable via useMemo
  const notify = useMemo(() => ({
    info: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.INFO, title, message, ...options }),
    success: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.SUCCESS, title, message, ...options }),
    warning: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.WARNING, title, message, ...options }),
    error: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.ERROR, title, message, ...options }),
    critical: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.CRITICAL, title, message, persistent: true, ...options }),
    pitStop: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.PIT_STOP, title, message, ...options }),
    overtake: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.OVERTAKE, title, message, ...options }),
    weather: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.WEATHER, title, message, ...options }),
    strategy: (title, message, options = {}) => 
      addNotification({ type: NOTIFICATION_TYPES.STRATEGY, title, message, persistent: true, ...options }),
  }), [addNotification]);

  const value = useMemo(() => ({
    notifications,
    activeToasts,
    unreadCount,
    addNotification,
    removeNotification,
    dismissToast,
    markAsRead,
    markAllAsRead,
    clearAll,
    notify,
    NOTIFICATION_TYPES,
    initAudio,
  }), [notifications, activeToasts, unreadCount, addNotification, removeNotification, dismissToast, markAsRead, markAllAsRead, clearAll, notify, initAudio]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export default NotificationContext;
