import React, { useMemo, memo } from 'react';
import { motion } from 'framer-motion';
import { Timer, Flag, AlertTriangle, CheckCircle, ChevronRight } from 'lucide-react';
import { useRace } from '../../context/RaceContext';

const TIRE_CONFIG = {
  soft: { color: '#ef4444', laps: 25, label: 'Soft' },
  medium: { color: '#eab308', laps: 40, label: 'Medium' },
  hard: { color: '#ffffff', laps: 55, label: 'Hard' },
  inter: { color: '#22c55e', laps: 30, label: 'Inter' },
  wet: { color: '#3b82f6', laps: 40, label: 'Wet' },
};

const WindowSegment = memo(({ start, end, type, isCurrent, lap }) => {
  const configs = {
    optimal: { accent: '#10b981', label: 'OPTIMAL', icon: CheckCircle },
    closing: { accent: '#eab308', label: 'CLOSING', icon: AlertTriangle },
    missed: { accent: '#ef4444', label: 'MISSED', icon: Flag },
    future: { accent: '#3b82f6', label: 'UPCOMING', icon: Timer },
  };
  
  const config = configs[type] || configs.future;
  const Icon = config.icon;

  return (
    <div 
      className={`relative flex-1 min-h-[55px] rounded-xl border transition-all ${
        isCurrent ? 'ring-1 ring-white/15' : ''
      }`}
      style={{ backgroundColor: config.accent + '0d', borderColor: config.accent + '25' }}
    >
      <div className="absolute -top-2.5 left-2 px-1.5 bg-[#0c0c0c] rounded">
        <span className="text-[8px] font-bold uppercase tracking-wider" style={{ color: config.accent + '80' }}>
          {config.label}
        </span>
      </div>

      <div className="p-2 pt-3">
        <div className="flex items-center justify-between mb-0.5">
          <Icon className="w-3.5 h-3.5" style={{ color: config.accent + '60' }} />
          {isCurrent && (
            <span className="px-1.5 py-0.5 bg-[#e10600] text-white text-[8px] font-bold rounded uppercase tracking-wider">Now</span>
          )}
        </div>
        <div className="text-[10px] text-white/40 font-mono">
          L{start}-{end}
        </div>
      </div>

      {isCurrent && lap >= start && lap <= end && (
        <motion.div
          className="absolute bottom-0 left-0 right-0 h-0.5"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: (lap - start + 1) / (end - start + 1) }}
          style={{ transformOrigin: 'left', backgroundColor: config.accent }}
        />
      )}
    </div>
  );
});
WindowSegment.displayName = 'WindowSegment';

const TireLifeBar = memo(({ compound, currentAge, totalLaps }) => {
  const config = TIRE_CONFIG[compound] || TIRE_CONFIG.medium;
  const remaining = Math.max(0, config.laps - currentAge);
  const percentage = (currentAge / config.laps) * 100;
  const isCliff = percentage > 80;
  const isOptimal = percentage < 60;

  return (
    <div className="p-3 bg-white/[0.02] rounded-xl border border-white/[0.05]">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: config.color }} />
          <span className="text-xs font-bold text-white/50">{config.label}</span>
        </div>
        <span className={`text-[10px] font-mono ${
          isCliff ? 'text-red-400/60' : isOptimal ? 'text-emerald-400/60' : 'text-yellow-400/60'
        }`}>
          {remaining}L left
        </span>
      </div>
      
      <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, percentage)}%` }}
          className="h-full rounded-full transition-colors"
          style={{ backgroundColor: isCliff ? '#ef4444' : isOptimal ? '#10b981' : '#eab308' }}
        />
      </div>
      
      <div className="mt-1.5 flex justify-between text-[8px] text-white/10">
        <span>L{currentAge}</span>
        <span>Cliff @ L{Math.round(config.laps * 0.8)}</span>
        <span>Limit @ L{config.laps}</span>
      </div>
    </div>
  );
});
TireLifeBar.displayName = 'TireLifeBar';

export const PitWindowVisualization = ({ externalPitWindows }) => {
  const { raceState, player, strategy } = useRace();
  
  const currentLap = raceState.currentLap || 0;
  const totalLaps = raceState.totalLaps || 53;
  
  const pitWindows = useMemo(() => {
    if (externalPitWindows && externalPitWindows.length > 0) return externalPitWindows;
    
    const tireConfig = TIRE_CONFIG[player?.tire] || TIRE_CONFIG.medium;
    const currentTireAge = player?.tireAge || 0;
    const remainingTireLife = tireConfig.laps - currentTireAge;
    
    const windows = [];
    const nextPitLap = strategy?.nextPitLap || currentLap + remainingTireLife;
    const earlyWindow = Math.max(currentLap + 2, nextPitLap - 2);
    const lateWindow = Math.min(nextPitLap + 2, currentLap + remainingTireLife);
    
    if (currentLap > lateWindow) {
      windows.push({ start: earlyWindow, end: lateWindow, type: 'missed' });
    } else if (currentLap >= earlyWindow && currentLap <= lateWindow) {
      const mid = Math.floor((earlyWindow + lateWindow) / 2);
      if (currentLap <= mid) {
        windows.push({ start: earlyWindow, end: mid, type: 'optimal' });
        windows.push({ start: mid + 1, end: lateWindow, type: 'closing' });
      } else {
        windows.push({ start: earlyWindow, end: currentLap - 1, type: 'optimal' });
        windows.push({ start: currentLap, end: lateWindow, type: 'closing' });
      }
    } else {
      windows.push({ start: earlyWindow, end: lateWindow, type: 'future' });
    }
    
    if (strategy?.pitStops?.length > 1 && strategy.pitStops[1] > currentLap) {
      windows.push({ start: strategy.pitStops[1] - 2, end: strategy.pitStops[1] + 2, type: 'future' });
    }
    
    return windows.sort((a, b) => a.start - b.start);
  }, [externalPitWindows, player, strategy, currentLap]);

  const isInWindow = useMemo(() => {
    return pitWindows.some(w => w.type !== 'missed' && currentLap >= w.start && currentLap <= w.end);
  }, [pitWindows, currentLap]);

  return (
    <div className="f1-card">
      <div className="p-4 pb-3 flex items-center justify-between border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Timer className="w-4 h-4 text-yellow-400/40" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Pit Window</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">Optimal timing</p>
          </div>
        </div>
        
        {isInWindow && (
          <div className="px-2 py-0.5 bg-emerald-500/10 rounded border border-emerald-500/15">
            <span className="text-[9px] font-bold text-emerald-400/70 uppercase tracking-wider">Open</span>
          </div>
        )}
      </div>

      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <ChevronRight className="w-3 h-3 text-white/15" />
          <span className="text-[9px] text-white/15 uppercase tracking-wider">Pit Windows</span>
        </div>
        
        <div className="flex gap-1.5">
          {pitWindows.map((window, idx) => (
            <WindowSegment
              key={idx}
              start={window.start}
              end={window.end}
              type={window.type}
              isCurrent={currentLap >= window.start && currentLap <= window.end}
              lap={currentLap}
            />
          ))}
        </div>

        <div className="mt-3 flex justify-between text-[9px] text-white/10 font-mono">
          <span>L{currentLap}</span>
          <span>L{Math.round(totalLaps * 0.33)}</span>
          <span>L{Math.round(totalLaps * 0.67)}</span>
          <span>L{totalLaps}</span>
        </div>
      </div>

      {player && (
        <div className="px-4 pb-4">
          <div className="flex items-center gap-2 mb-2">
            <Flag className="w-3 h-3 text-white/15" />
            <span className="text-[9px] text-white/15 uppercase tracking-wider">Current Tire</span>
          </div>
          <TireLifeBar compound={player.tire} currentAge={player.tireAge} totalLaps={totalLaps} />
        </div>
      )}

      {strategy && (
        <div className="px-4 py-2 border-t border-white/[0.06]">
          <div className="flex items-center justify-between text-[10px]">
            <div className="flex items-center gap-3">
              <span className="text-white/15">Plan: <span className="text-white/40 font-bold">{strategy.type}</span></span>
              <span className="text-white/15">Stops: <span className="text-white/40 font-bold">{strategy.pitStops?.length || 0}</span></span>
            </div>
            <span className="text-white/15">Next: <span className="text-yellow-400/50 font-bold">L{strategy.nextPitLap || 'TBD'}</span></span>
          </div>
        </div>
      )}
    </div>
  );
};

export default memo(PitWindowVisualization);
