import React, { useState, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Clock, AlertTriangle, ChevronDown, Radio, Navigation } from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import { useOpenF1Context } from '../../context/OpenF1Context';

// Import child components
import TrackMapVisualization from './TrackMapVisualization';
import RaceDirectorFeed from './RaceDirectorFeed';
import IncidentTracker from './IncidentTracker';
import WeatherForecastPanel from './WeatherForecastPanel';

/**
 * Timing Tower specific to Race Control
 * Uses existing CompetitorPanel under the hood but optimized for side-panel display
 */
import CompetitorPanel from './CompetitorPanel';

/**
 * Mode Selector Pill
 */
const ModeSelector = memo(({ currentMode, setMode, openF1Session }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const modes = [
    { id: 'sim', label: 'SIMULATION', color: 'text-blue-400', desc: 'Local physics engine' },
    { id: 'live', label: 'OPENF1 LIVE', color: 'text-emerald-400', desc: 'Real-time telemetry', disabled: !openF1Session?.is_live },
    { id: 'hybrid', label: 'HYBRID', color: 'text-purple-400', desc: 'Sim + Live Data', disabled: !openF1Session?.available }
  ];

  const activeMode = modes.find(m => m.id === currentMode);

  return (
    <div className="relative z-50">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.04] border border-white/[0.1] hover:bg-white/[0.08] rounded-lg transition-colors"
      >
        <div className={`w-2 h-2 rounded-full ${activeMode.color.replace('text-', 'bg-')} animate-pulse`} />
        <span className={`text-[10px] font-bold ${activeMode.color}`}>{activeMode.label}</span>
        <ChevronDown className="w-3 h-3 text-white/40" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            className="absolute top-full left-0 mt-2 w-48 bg-[#111111] border border-white/10 rounded-xl shadow-2xl overflow-hidden"
          >
            {modes.map((m) => (
              <button
                key={m.id}
                onClick={() => {
                  if (!m.disabled) {
                    setMode(m.id);
                    setIsOpen(false);
                  }
                }}
                disabled={m.disabled}
                className={`w-full flex flex-col items-start px-4 py-3 text-left transition-colors ${
                  m.disabled ? 'opacity-30 cursor-not-allowed' : 'hover:bg-white/[0.04]'
                } ${currentMode === m.id ? 'bg-white/[0.02]' : ''}`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${m.color.replace('text-', 'bg-')}`} />
                  <span className={`text-[10px] font-bold ${m.color}`}>{m.label}</span>
                </div>
                <span className="text-[9px] text-white/40 mt-1">{m.desc}</span>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});
ModeSelector.displayName = 'ModeSelector';

export const RaceControlCenter = () => {
  const { raceState, currentRecommendation } = useRace();
  const openF1 = useOpenF1Context();

  return (
    <div className="flex flex-col gap-4">
      {/* Race Control Header */}
      <div className="flex flex-wrap items-center justify-between p-4 bg-white/[0.02] border border-white/[0.06] rounded-xl">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-[#e10600]/10 rounded-xl flex items-center justify-center border border-[#e10600]/20">
            <Radio className="w-5 h-5 text-[#e10600]" />
          </div>
          <div>
            <h2 className="text-lg font-black text-white/90 uppercase tracking-widest">Race Operations Center</h2>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-[10px] text-white/40 font-mono">SYS.VER_6.5</span>
              <span className="text-[10px] text-white/20">•</span>
              {openF1?.session?.session_name ? (
                <span className="text-[10px] text-emerald-400 font-bold">{openF1.session.session_name}</span>
              ) : (
                <span className="text-[10px] text-white/40">SIMULATION ENGINE ACTIVE</span>
              )}
            </div>
          </div>
        </div>

        {/* Dynamic Mode Selector */}
        <ModeSelector 
          currentMode={openF1?.mode || 'sim'} 
          setMode={openF1?.setMode || (() => {})} 
          openF1Session={openF1?.session}
        />
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* LEFT COLUMN: Track Map (Dominant) + Alerts */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {/* Main Track Map */}
          <div className="flex-1 min-h-[400px]">
            <TrackMapVisualization />
          </div>

          {/* Bottom Row: Weather + Strategic Alerts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Weather & Track Status */}
            <div className="f1-card p-4">
              <WeatherForecastPanel />
            </div>

            {/* Strategic Alerts (Derived from Intelligence) */}
            <div className="f1-card p-4">
              <div className="flex items-center gap-2 px-1 mb-4">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-white/80 uppercase tracking-[0.15em]">Strategic Alerts</h3>
              </div>
              <div className="space-y-3">
                {currentRecommendation ? (
                  <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-bold text-amber-400 uppercase">Primary Directive</span>
                      <span className="text-[9px] text-amber-400/60 font-mono">Lap {raceState.currentLap}</span>
                    </div>
                    <p className="text-xs text-white/80 leading-relaxed">{currentRecommendation.explanation}</p>
                  </div>
                ) : (
                   <div className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-lg text-center">
                     <Navigation className="w-5 h-5 text-white/20 mx-auto mb-2" />
                     <p className="text-[10px] text-white/40 uppercase tracking-widest">No Active Alerts</p>
                   </div>
                )}
                
                {raceState.safetyCarActive && (
                  <div className="p-2.5 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-center gap-3">
                    <Clock className="w-4 h-4 text-yellow-400" />
                    <div>
                      <p className="text-[10px] font-bold text-yellow-400 uppercase">Pit Window Open</p>
                      <p className="text-[9px] text-white/40">Reduced time loss under SC</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Timing Tower, Race Director, Incidents */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          
          {/* Live Timing Tower */}
          <div className="f1-card flex-1 max-h-[500px] overflow-hidden flex flex-col">
            <div className="p-4 pb-0">
              <div className="flex items-center justify-between px-1 mb-2">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-400" />
                  <h3 className="text-sm font-bold text-white/80 uppercase tracking-[0.15em]">Live Timing</h3>
                </div>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono uppercase border border-blue-500/20">
                  {openF1?.mode === 'live' ? 'OPENF1' : 'SIMULATION'}
                </span>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
              <CompetitorPanel compact={true} overrideData={openF1?.mode === 'live' ? openF1.positions : null} />
            </div>
          </div>

          {/* Race Director Feed */}
          <div className="h-[250px] overflow-hidden">
            <RaceDirectorFeed externalMessages={openF1?.raceControl} />
          </div>

          {/* Incident Center */}
          <div className="h-[250px] overflow-hidden">
            <IncidentTracker externalIncidents={openF1?.mode === 'live' ? [] : undefined} />
          </div>

        </div>
      </div>
    </div>
  );
};

export default memo(RaceControlCenter);
