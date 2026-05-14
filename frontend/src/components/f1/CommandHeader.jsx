import React, { useState, memo, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, User, Wifi, Clock, LogOut, Radio } from 'lucide-react';
import NotificationBell from '../notifications/NotificationBell';
import SettingsModal from '../settings/SettingsModal';

export const CommandHeader = ({ user, status, onLogout }) => {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const statusConfig = {
    connected: { label: 'LIVE', color: 'text-emerald-400', bg: 'bg-emerald-400', dot: 'animate-f1-pulse-dot' },
    reconnecting: { label: 'RECONNECTING', color: 'text-yellow-400', bg: 'bg-yellow-400', dot: 'animate-pulse' },
    connecting: { label: 'CONNECTING', color: 'text-yellow-400', bg: 'bg-yellow-400', dot: 'animate-pulse' },
    disconnected: { label: 'OFFLINE', color: 'text-red-400', bg: 'bg-red-400', dot: '' },
  };

  const st = statusConfig[status] || statusConfig.disconnected;

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative bg-[#0a0a0a]/90 backdrop-blur-xl border-b border-white/[0.06]"
    >
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#e10600]/40 to-transparent" />

      <div className="px-4 md:px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-11 h-11 rounded-xl overflow-hidden flex items-center justify-center shadow-[0_4px_16px_rgba(225,6,0,0.25)]">
                <img src="/icons/download.png" alt="F1 Strategy Logo" className="w-full h-full object-contain" />
              </div>
              <div className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 ${st.bg} rounded-full border-2 border-[#0a0a0a] ${st.dot}`} />
            </div>
            <div>
              <h1 className="text-lg font-black text-white tracking-tight">
                Strategy<span className="text-[#e10600]">Command</span>
              </h1>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-white/20 uppercase tracking-[0.15em]">v6.3</span>
                <span className="w-1 h-1 bg-white/10 rounded-full" />
                <span className={`text-[10px] font-bold uppercase tracking-wider ${st.color} flex items-center gap-1.5`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${st.bg} ${st.dot}`} />
                  {st.label}
                </span>
              </div>
            </div>
          </div>

          {/* Center Status */}
          <div className="hidden md:flex items-center gap-4">
            <div className={`flex items-center gap-2 px-4 py-2 bg-white/[0.03] rounded-xl border ${
              status === 'connected' ? 'border-emerald-500/20' : 
              status === 'reconnecting' ? 'border-yellow-500/20' : 'border-red-500/20'
            }`}>
              <Wifi className={`w-4 h-4 ${st.color}`} />
              <span className="text-xs text-white/40">
                {status === 'connected' ? 'Connected' : 
                 status === 'reconnecting' ? 'Reconnecting...' : 
                 status === 'connecting' ? 'Connecting...' : 'Disconnected'}
              </span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white/[0.03] rounded-xl border border-white/[0.06]">
              <Radio className="w-4 h-4 text-emerald-400/60" />
              <span className="text-xs text-white/40">Systems Normal</span>
            </div>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-3 py-2 bg-white/[0.03] rounded-xl border border-white/[0.06]">
              <Clock className="w-3.5 h-3.5 text-white/25" />
              <span className="text-sm font-mono text-white/60">
                {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
              </span>
            </div>
            
            <NotificationBell />
            
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSettingsOpen(true)}
              className="p-2.5 hover:bg-white/[0.06] rounded-xl transition-colors border border-transparent hover:border-white/[0.06]"
            >
              <Settings className="w-4 h-4 text-white/30" />
            </motion.button>

            <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
            
            <div className="flex items-center gap-3 pl-3 ml-1 border-l border-white/[0.06]">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-semibold text-white/80">{user?.name || 'Race Engineer'}</p>
                <p className="text-[10px] text-white/25 uppercase tracking-wider">{user?.role || 'Engineer'}</p>
              </div>
              <div className="w-9 h-9 bg-gradient-to-br from-white/[0.08] to-white/[0.03] rounded-xl flex items-center justify-center border border-white/[0.06]">
                <User className="w-4 h-4 text-white/40" />
              </div>
              
              {onLogout && (
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={onLogout}
                  className="p-2.5 hover:bg-red-500/10 hover:text-red-400 rounded-xl transition-colors border border-transparent hover:border-red-500/10"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4 text-white/25" />
                </motion.button>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.header>
  );
};

export default memo(CommandHeader);
