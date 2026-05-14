import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Flag,
  Users,
  CloudRain,
  Car,
  Shield,
  Clock,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Race Control', icon: LayoutDashboard },
  { id: 'live', label: 'Live Weekend', icon: Flag },
  { id: 'headtohead', label: 'Head-to-Head', icon: Users },
  { id: 'weather', label: 'Weather', icon: CloudRain },
  { id: 'multicar', label: 'Multi-Car', icon: Car },
  { id: 'opponent', label: 'Opponent', icon: Shield },
  { id: 'history', label: 'History', icon: Clock },
];

export const NavigationSidebar = ({ activeTab, onTabChange }) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 56 : 200 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="fixed left-0 top-0 bottom-0 z-40 bg-[#0a0a0a] border-r border-white/[0.06] flex flex-col"
    >
      <div className="flex items-center justify-between p-3 border-b border-white/[0.06]">
        {!collapsed && (
          <span className="text-xs font-black text-white/60 uppercase tracking-[0.2em]">Strategy</span>
        )}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg hover:bg-white/[0.06] transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-3.5 h-3.5 text-white/40" />
          ) : (
            <ChevronLeft className="w-3.5 h-3.5 text-white/40" />
          )}
        </motion.button>
      </div>

      <nav className="flex-1 py-2 space-y-0.5 px-2">
        {NAV_ITEMS.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = item.icon;
          return (
            <motion.button
              key={item.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-2.5 py-2 rounded-xl transition-all ${
                isActive
                  ? 'bg-[#e10600]/10 text-[#e10600] border border-[#e10600]/20'
                  : 'text-white/40 hover:text-white/60 hover:bg-white/[0.04] border border-transparent'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && (
                <span className="text-[11px] font-semibold truncate">{item.label}</span>
              )}
            </motion.button>
          );
        })}
      </nav>
    </motion.aside>
  );
};

export default NavigationSidebar;
