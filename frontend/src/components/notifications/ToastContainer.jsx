import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle2, AlertTriangle, Timer, Zap, CloudRain, TrendingUp, Info, X } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';

const ToastContainer = () => {
  const { activeToasts, dismissToast, NOTIFICATION_TYPES } = useNotifications();

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
        return 'bg-red-500/20 text-red-400 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.2)]';
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
        return 'bg-[#e10600]/20 text-[#e10600] border-[#e10600]/30 shadow-[0_0_15px_rgba(225,6,0,0.3)]';
      default:
        return 'bg-gray-800/80 text-gray-300 border-gray-700';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none sm:max-w-md w-[calc(100vw-2rem)] sm:w-full">
      <AnimatePresence>
        {activeToasts.map((toast) => {
          const Icon = getIcon(toast.type);
          const colors = getColors(toast.type);

          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 50, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
              className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md shadow-2xl ${
                toast.type === NOTIFICATION_TYPES.CRITICAL || toast.type === NOTIFICATION_TYPES.STRATEGY
                  ? 'bg-gray-900/95'
                  : 'bg-gray-900/90'
              }`}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 border ${colors}`}>
                <Icon className="w-5 h-5" />
              </div>

              <div className="flex-1 min-w-0 pt-0.5">
                <h4 className="font-bold text-white text-sm">{toast.title}</h4>
                <p className="text-sm text-gray-300 mt-1 leading-snug break-words">
                  {toast.message}
                </p>

                {toast.data && (
                  <div className="flex items-center gap-2 mt-2">
                    {toast.data.lap && (
                      <span className="px-2 py-0.5 bg-gray-800 rounded text-[10px] text-gray-400 font-mono">
                        Lap {toast.data.lap}
                      </span>
                    )}
                    {toast.data.gain && (
                      <span className="px-2 py-0.5 bg-emerald-500/20 rounded text-[10px] text-emerald-400 font-bold">
                        {toast.data.gain}
                      </span>
                    )}
                  </div>
                )}
              </div>

              <button
                onClick={() => dismissToast(toast.id)}
                className="p-1 hover:bg-white/10 rounded-lg transition-colors flex-shrink-0 text-gray-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

export default ToastContainer;
