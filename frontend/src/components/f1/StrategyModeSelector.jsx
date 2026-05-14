import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { Zap, Target, Cpu, Sliders } from 'lucide-react';

const MODES = [
  {
    id: 'auto',
    name: 'Auto',
    description: 'AI optimizes',
    icon: Cpu,
    accent: 'text-blue-400',
    border: 'border-blue-500/20',
    bg: 'bg-blue-500/8',
    selectedBg: 'bg-blue-500/15',
  },
  {
    id: 'conservative',
    name: 'Conservative',
    description: 'Reliability first',
    icon: Target,
    accent: 'text-emerald-400',
    border: 'border-emerald-500/20',
    bg: 'bg-emerald-500/8',
    selectedBg: 'bg-emerald-500/15',
  },
  {
    id: 'aggressive',
    name: 'Aggressive',
    description: 'Max performance',
    icon: Zap,
    accent: 'text-[#e10600]',
    border: 'border-[#e10600]/20',
    bg: 'bg-[#e10600]/8',
    selectedBg: 'bg-[#e10600]/15',
  },
  {
    id: 'custom',
    name: 'Custom',
    description: 'Manual config',
    icon: Sliders,
    accent: 'text-purple-400',
    border: 'border-purple-500/20',
    bg: 'bg-purple-500/8',
    selectedBg: 'bg-purple-500/15',
  },
];

export const StrategyModeSelector = ({ selected, onSelect }) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 mb-3 px-1">
        <span className="f1-label">Strategy Mode</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {MODES.map((mode) => {
          const Icon = mode.icon;
          const isSelected = selected === mode.id;
          
          return (
            <motion.button
              key={mode.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(mode.id)}
              className={`relative p-3 rounded-xl border transition-all duration-300 ${
                isSelected 
                  ? `${mode.selectedBg} ${mode.border} shadow-[0_0_15px_rgba(0,0,0,0.3)]` 
                  : 'bg-white/[0.02] border-white/[0.05] hover:bg-white/[0.04] hover:border-white/[0.08]'
              }`}
            >
              <div className="flex flex-col items-center gap-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                  isSelected ? mode.bg : 'bg-white/[0.03]'
                }`}>
                  <Icon className={`w-4 h-4 transition-colors ${
                    isSelected ? mode.accent : 'text-white/20'
                  }`} />
                </div>
                <div className="text-center">
                  <p className={`text-xs font-bold transition-colors ${
                    isSelected ? 'text-white/80' : 'text-white/40'
                  }`}>
                    {mode.name}
                  </p>
                  <p className={`text-[10px] transition-colors ${
                    isSelected ? 'text-white/30' : 'text-white/15'
                  }`}>
                    {mode.description}
                  </p>
                </div>
              </div>
              
              {isSelected && (
                <motion.div
                  layoutId="selectedMode"
                  className="absolute inset-0 rounded-xl ring-1 ring-white/10"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
};

export default memo(StrategyModeSelector);
