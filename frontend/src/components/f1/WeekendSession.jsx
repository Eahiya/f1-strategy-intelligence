import React, { memo, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, Square, Clock, Activity, CloudRain, Sun, Wind, 
  Timer, TrendingUp, ChevronDown, Award, Zap 
} from 'lucide-react';
import { useRace } from '../../context/RaceContext';

const SESSION_TYPES = {
  practice: { name: 'Practice', icon: Activity, color: 'text-blue-400' },
  qualifying: { name: 'Qualifying', icon: Timer, color: 'text-purple-400' },
  race: { name: 'Race', icon: Award, color: 'text-[#e10600]' },
};

const SESSION_PHASES = {
  practice: ['FP1', 'FP2', 'FP3'],
  qualifying: ['Q1', 'Q2', 'Q3'],
  race: ['Formation', 'Start', 'Finish'],
};

const WeatherEvolution = memo(({ weather }) => {
  const getIcon = () => {
    switch (weather.state) {
      case 'wet': return CloudRain;
      case 'mixed': return Wind;
      case 'dry': return Sun;
      default: return Sun;
    }
  };
  
  const Icon = getIcon();
  
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-white/[0.03] rounded-lg border border-white/[0.06]">
      <Icon className="w-4 h-4 text-white/50" />
      <div>
        <p className="text-xs text-white/70 capitalize">{weather.state || 'dry'}</p>
        <p className="text-[10px] text-white/30">{weather.temp || 25}°C Track</p>
      </div>
    </div>
  );
});
WeatherEvolution.displayName = 'WeatherEvolution';

const TrackEvolutionBar = memo(({ progress, sessions }) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-[10px] text-white/30">
        <span>Track Evolution</span>
        <span>{Math.round(progress)}% grip</span>
      </div>
      <div className="h-2 bg-white/[0.04] rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-yellow-600 via-yellow-400 to-emerald-400 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
      <div className="flex items-center justify-between">
        {sessions.map((session, idx) => (
          <div key={session} className="flex flex-col items-center">
            <div 
              className={`w-2 h-2 rounded-full ${
                idx / (sessions.length - 1) * 100 <= progress 
                  ? 'bg-emerald-400' 
                  : 'bg-white/10'
              }`}
            />
            <span className="text-[9px] text-white/20 mt-1">{session}</span>
          </div>
        ))}
      </div>
    </div>
  );
});
TrackEvolutionBar.displayName = 'TrackEvolutionBar';

const SessionTiming = memo(({ session }) => {
  if (!session) return null;

  return (
    <div className="grid grid-cols-3 gap-2">
      <div className="p-2 bg-white/[0.03] rounded-lg border border-white/[0.06]">
        <p className="text-[9px] text-white/30 uppercase">Best</p>
        <p className="text-sm font-mono font-bold text-emerald-400">{session.bestTime || '--:--'}</p>
      </div>
      <div className="p-2 bg-white/[0.03] rounded-lg border border-white/[0.06]">
        <p className="text-[9px] text-white/30 uppercase">Laps</p>
        <p className="text-sm font-mono font-bold text-white/70">{session.laps || 0}</p>
      </div>
      <div className="p-2 bg-white/[0.03] rounded-lg border border-white/[0.06]">
        <p className="text-[9px] text-white/30 uppercase">Position</p>
        <p className="text-sm font-mono font-bold text-white/70">P{session.position || '-'}</p>
      </div>
    </div>
  );
});
SessionTiming.displayName = 'SessionTiming';

const WeekendSessionPanel = () => {
  const { raceState } = useRace();
  const [activeSession, setActiveSession] = useState('practice');
  const [activePhase, setActivePhase] = useState(0);
  const [sessionData, setSessionData] = useState({
    practice: { phases: [{ bestTime: '1:23.456', laps: 24, position: 3 }] },
    qualifying: { phases: [{ bestTime: '1:21.234', laps: 6, position: 2 }] },
    race: { phases: [{ bestTime: '--:--', laps: 0, position: '-' }] },
  });

  const currentSession = SESSION_TYPES[activeSession];
  const phases = SESSION_PHASES[activeSession];
  const currentPhase = sessionData[activeSession]?.phases[activePhase] || {};

  // Calculate track evolution based on session progress
  const trackEvolution = useMemo(() => {
    const baseProgress = {
      practice: 30,
      qualifying: 70,
      race: 90,
    };
    return baseProgress[activeSession] + (activePhase * 10);
  }, [activeSession, activePhase]);

  return (
    <div className="f1-card">
      <div className="p-4 pb-3 flex items-center justify-between border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]`}>
            <currentSession.icon className={`w-4 h-4 ${currentSession.color}`} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Weekend Session</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">{currentSession.name}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-1">
          {Object.entries(SESSION_TYPES).map(([key, config]) => (
            <button
              key={key}
              onClick={() => {
                setActiveSession(key);
                setActivePhase(0);
              }}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-medium uppercase tracking-wider transition-all ${
                activeSession === key
                  ? 'bg-white/[0.08] text-white/80 border border-white/[0.12]'
                  : 'text-white/30 hover:text-white/50 hover:bg-white/[0.04]'
              }`}
            >
              {key.substring(0, 2)}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Session Phase Selector */}
        <div className="flex items-center gap-2">
          {phases.map((phase, idx) => (
            <button
              key={phase}
              onClick={() => setActivePhase(idx)}
              className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                activePhase === idx
                  ? 'bg-white/[0.06] text-white/80 border border-white/[0.10]'
                  : 'text-white/30 hover:text-white/50 hover:bg-white/[0.03] border border-transparent'
              }`}
            >
              {phase}
            </button>
          ))}
        </div>

        {/* Session Timing */}
        <SessionTiming session={currentPhase} />

        {/* Track Evolution */}
        <TrackEvolutionBar 
          progress={trackEvolution} 
          sessions={['Start', ...phases]} 
        />

        {/* Weather Evolution */}
        <div className="pt-2 border-t border-white/[0.06]">
          <p className="text-[10px] text-white/30 uppercase tracking-wider mb-2">Conditions</p>
          <div className="flex items-center gap-2">
            <WeatherEvolution 
              weather={raceState.weather || { state: 'dry', temp: 28 }} 
            />
            <div className="flex-1 p-2 bg-white/[0.03] rounded-lg border border-white/[0.06]">
              <p className="text-[9px] text-white/30 uppercase">Track Temp</p>
              <p className="text-xs text-white/70">{35 + (trackEvolution * 0.05).toFixed(1)}°C</p>
            </div>
          </div>
        </div>

        {/* Driver Form / Confidence */}
        <div className="pt-2 border-t border-white/[0.06]">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] text-white/30 uppercase tracking-wider">Driver Confidence</p>
            <span className="text-xs text-emerald-400">High</span>
          </div>
          <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: '85%' }}
              transition={{ duration: 1 }}
            />
          </div>
          <p className="text-[10px] text-white/20 mt-2">
            Consistent lap times, positive trend in {activeSession}
          </p>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 pt-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex-1 py-2.5 bg-[#e10600]/10 hover:bg-[#e10600]/20 border border-[#e10600]/30 rounded-lg text-xs text-[#e10600] font-medium transition-colors flex items-center justify-center gap-2"
          >
            <Play className="w-3.5 h-3.5" />
            Start {activeSession === 'practice' ? 'Session' : activeSession === 'qualifying' ? 'Run' : 'Race'}
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="p-2.5 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] rounded-lg text-white/40 hover:text-white/60 transition-colors"
          >
            <TrendingUp className="w-4 h-4" />
          </motion.button>
        </div>
      </div>
    </div>
  );
};

export const WeekendSession = memo(WeekendSessionPanel);
WeekendSession.displayName = 'WeekendSession';

export default WeekendSession;
