import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, Check, Trash2, AlertCircle, CheckCircle2, Info, AlertTriangle, Zap, CloudRain, Timer, TrendingUp } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';

const NotificationBell = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const { 
    notifications, 
    unreadCount, 
    markAsRead, 
    markAllAsRead, 
    removeNotification, 
    clearAll,
    NOTIFICATION_TYPES 
  } = useNotifications();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getIcon = (type) => {
    switch (type) {
      case NOTIFICATION_TYPES.CRITICAL:
      case NOTIFICATION_TYPES.ERROR:
        return AlertCircle;
      case NOTIFICATION_TYPES.SUCCESS:
        return CheckCircle2;
      case NOTIFICATION_TYPES.WARNING:
        return AlertTriangle;
      case NOTIFICATION_TYPES.PIT_STOP:
        return Timer;
      case NOTIFICATION_TYPES.OVERTAKE:
        return Zap;
      case NOTIFICATION_TYPES.WEATHER:
        return CloudRain;
      case NOTIFICATION_TYPES.STRATEGY:
        return TrendingUp;
      default:
        return Info;
    }
  };

  const getColors = (type) => {
    switch (type) {
      case NOTIFICATION_TYPES.CRITICAL:
      case NOTIFICATION_TYPES.ERROR:
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case NOTIFICATION_TYPES.SUCCESS:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case NOTIFICATION_TYPES.WARNING:
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case NOTIFICATION_TYPES.PIT_STOP:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case NOTIFICATION_TYPES.OVERTAKE:
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case NOTIFICATION_TYPES.WEATHER:
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case NOTIFICATION_TYPES.STRATEGY:
        return 'bg-[#e10600]/20 text-[#e10600] border-[#e10600]/30';
      default:
        return 'bg-gray-700/50 text-gray-400 border-gray-600';
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-white/5 rounded-lg transition-colors"
      >
        <Bell className="w-5 h-5 text-gray-400" />
        {unreadCount > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute top-1 right-1 w-4 h-4 bg-[#e10600] rounded-full flex items-center justify-center text-[10px] font-bold text-white"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </motion.span>
        )}
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 top-full mt-2 w-96 bg-gradient-to-b from-gray-900 to-black border border-gray-800 rounded-xl shadow-2xl z-[100] overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-800">
              <div>
                <h3 className="font-semibold text-white">Notifications</h3>
                <p className="text-xs text-gray-500">
                  {unreadCount > 0 ? `${unreadCount} unread` : 'No new notifications'}
                </p>
              </div>
              <div className="flex items-center gap-1">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                    title="Mark all as read"
                  >
                    <Check className="w-4 h-4 text-gray-400" />
                  </button>
                )}
                {notifications.length > 0 && (
                  <button
                    onClick={() => {
                      // eslint-disable-next-line no-restricted-globals
                      if (confirm('Clear all notifications?')) {
                        clearAll();
                      }
                    }}
                    className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                    title="Clear all"
                  >
                    <Trash2 className="w-4 h-4 text-gray-400" />
                  </button>
                )}
              </div>
            </div>

            {/* Notification List */}
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="w-12 h-12 text-gray-700 mx-auto mb-3" />
                  <p className="text-gray-500 text-sm">No notifications yet</p>
                  <p className="text-gray-600 text-xs mt-1">
                    Race events will appear here
                  </p>
                </div>
              ) : (
                notifications.map((notification, index) => {
                  const Icon = getIcon(notification.type);
                  const colors = getColors(notification.type);

                  return (
                    <motion.div
                      key={notification.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      onClick={() => markAsRead(notification.id)}
                      className={`group relative p-4 border-b border-gray-800 hover:bg-gray-800/50 transition-colors cursor-pointer ${
                        !notification.read ? 'bg-gray-800/30' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {/* Icon */}
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 border ${colors}`}>
                          <Icon className="w-5 h-5" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <h4 className={`font-medium text-sm ${!notification.read ? 'text-white' : 'text-gray-400'}`}>
                              {notification.title}
                            </h4>
                            <span className="text-xs text-gray-600 flex-shrink-0">
                              {formatTime(notification.timestamp)}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                            {notification.message}
                          </p>
                          
                          {/* Data badge if present */}
                          {notification.data && (
                            <div className="flex items-center gap-2 mt-2">
                              {notification.data.lap && (
                                <span className="px-2 py-0.5 bg-gray-800 rounded text-[10px] text-gray-400">
                                  Lap {notification.data.lap}
                                </span>
                              )}
                              {notification.data.gain && (
                                <span className="px-2 py-0.5 bg-emerald-500/20 rounded text-[10px] text-emerald-400">
                                  {notification.data.gain}
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Unread indicator */}
                        {!notification.read && (
                          <span className="w-2 h-2 bg-[#e10600] rounded-full flex-shrink-0 mt-1" />
                        )}
                      </div>

                      {/* Delete button on hover */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeNotification(notification.id);
                        }}
                        className="absolute top-2 right-2 p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-700 rounded transition-all"
                      >
                        <X className="w-3 h-3 text-gray-500" />
                      </button>
                    </motion.div>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-gray-800 bg-gray-900/50">
              <button
                onClick={() => setIsOpen(false)}
                className="w-full py-2 text-xs text-gray-500 hover:text-white transition-colors"
              >
                Close
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationBell;
