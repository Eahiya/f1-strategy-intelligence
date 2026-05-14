import React, { useMemo, memo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceDot } from 'recharts';
import { Activity, Clock, Pause, Play, RotateCcw, TrendingUp, Users } from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import { useSettings } from '../../context/SettingsContext';
import AnimatedValue from '../common/AnimatedValue';
import { getDriverBadge } from '../../data/drivers';

const ChartTooltip = memo(({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) return null;
  
  // Sort by lap time (fastest first)
  const sortedPayload = [...payload].sort((a, b) => (a.value || 0) - (b.value || 0));
  
  return (
    <div className="bg-[#0c0c0c]/95 border border-white/[0.08] rounded-lg p-3 shadow-[0_8px_24px_rgba(0,0,0,0.5)] backdrop-blur-sm min-w-[140px]">
      <p className="text-white/30 text-[10px] mb-2 font-mono uppercase tracking-wider">Lap {label}</p>
      {sortedPayload.map((entry, index) => (
        <p key={index} className="text-xs font-mono flex items-center gap-2 py-0.5" style={{ color: entry.color }}>
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: entry.color }} />
          <span className="flex-1">{entry.name}</span>
          <span className="text-white/60">{typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}s</span>
          <span className="text-white/30 text-[10px]">(P{index + 1})</span>
        </p>
      ))}
    </div>
  );
});
ChartTooltip.displayName = 'ChartTooltip';

const StatCard = memo(({ icon: Icon, label, value, color = 'text-white/60' }) => (
  <div className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.03] rounded-lg border border-white/[0.05]">
    <Icon className={`w-3.5 h-3.5 ${color}`} />
    <span className="text-[10px] text-white/25 uppercase tracking-wider">{label}</span>
    <span className={`text-xs font-mono font-bold ${color}`}>{value}</span>
  </div>
));
StatCard.displayName = 'StatCard';

const LiveSimulationChart = () => {
  const { raceState, allCompetitors, pauseRace, resumeRace, chartData, stopRace, player } = useRace();
  const { chartAnimations } = useSettings();
  
  const data = chartData;

  const playerData = useMemo(() => {
    if (!player) return null;
    return {
      position: player.position,
      raceTime: player.raceTime,
      avgLapTime: player.raceTime && raceState.currentLap > 0 
        ? (player.raceTime / raceState.currentLap).toFixed(2)
        : '0.00',
      gapToLeader: typeof player.gapToLeader === 'number' ? player.gapToLeader.toFixed(2) : '0.00',
    };
  }, [player, raceState.currentLap]);

  // Get all visible competitors (not just top 3) for the chart
  const visibleCompetitors = useMemo(() => {
    return allCompetitors
      .filter(c => !c.isPlayer)
      .slice(0, 5) // Show up to 5 competitors for better visibility
      .map((c, idx) => {
        // Use driver_code from backend data - should be uppercase like "VER", "PER", "NOR"
        const driverCode = c.driverCode || c.driver_code || c.driver?.substring(0, 3).toUpperCase() || `DRV${idx}`;
        const key = driverCode.toLowerCase(); // Chart data keys are lowercase
        const driverBadge = getDriverBadge(driverCode);
        const color = c.teamColor || c.team_color || driverBadge.color || '#888888';
        
        return {
          key,                    // lowercase for dataKey matching (e.g., "ver")
          driverCode,            // uppercase for display (e.g., "VER")
          name: driverCode,      // Display name in legend/tooltip
          color,
          position: c.position,
          gradientId: `gradient-${key}`,
        };
      });
  }, [allCompetitors]);
  

  const handlePauseResume = useCallback(() => {
    if (raceState.isPaused) resumeRace();
    else pauseRace();
  }, [raceState.isPaused, pauseRace, resumeRace]);

  const yDomain = useMemo(() => {
    if (data.length === 0) return [85, 95];
    
    // Collect all lap times from player and visible competitors
    const allLapTimes = [];
    data.forEach(d => {
      // Player
      if (typeof d.player === 'number') allLapTimes.push(d.player);
      // Competitors
      visibleCompetitors.forEach(comp => {
        const val = d[comp.key];
        if (typeof val === 'number') allLapTimes.push(val);
      });
    });
    
    if (allLapTimes.length === 0) return [85, 95];
    
    const min = Math.min(...allLapTimes);
    const max = Math.max(...allLapTimes);
    const padding = 2;
    return [Math.max(70, min - padding), max + padding];
  }, [data, visibleCompetitors]);

  return (
    <div className="relative">
      {/* Header - Fixed Layout with no overlap */}
      <div className="p-5 pb-4">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Title */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="w-10 h-10 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
              <Activity className="w-4 h-4 text-[#e10600]/60" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white/70">Live Race Simulation</h3>
              <p className="text-[10px] text-white/20 uppercase tracking-wider">Real-time lap tracking</p>
            </div>
          </div>
          
          {/* Right: Stats + Controls + Live Badge */}
          <div className="flex items-center gap-3 flex-wrap justify-end">
            {/* Stats */}
            <div className="flex items-center gap-2">
              <StatCard 
                icon={Clock} 
                label={`Lap ${raceState.currentLap}/${raceState.totalLaps}`}
                value=""
                color="text-white/30"
              />
              {playerData && (
                <>
                  <StatCard 
                    icon={TrendingUp} 
                    label="Avg"
                    value={<AnimatedValue value={playerData.avgLapTime} precision={2} suffix="s" />}
                    color="text-emerald-400/60"
                  />
                  <StatCard 
                    icon={Users} 
                    label="P"
                    value={playerData.position}
                    color="text-[#e10600]/60"
                  />
                </>
              )}
            </div>
            
            {/* Live Badge - Now in flow, not absolute */}
            <AnimatePresence>
              {raceState.isRunning && !raceState.isPaused && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="flex items-center gap-2 px-2.5 py-1.5 bg-[#e10600]/10 rounded-md border border-[#e10600]/20"
                >
                  <motion.div
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                    className="w-1.5 h-1.5 bg-[#e10600] rounded-full"
                  />
                  <span className="text-[9px] font-bold text-[#e10600]/80 uppercase tracking-wider">Live</span>
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Controls */}
            <div className="flex items-center gap-1.5">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handlePauseResume}
                disabled={!raceState.isRunning}
                className="p-2 bg-white/[0.03] hover:bg-white/[0.06] disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all border border-white/[0.05]"
                title={raceState.isPaused ? 'Resume' : 'Pause'}
              >
                {raceState.isPaused ? 
                  <Play className="w-3.5 h-3.5 text-emerald-400/60" /> : 
                  <Pause className="w-3.5 h-3.5 text-yellow-400/60" />
                }
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={stopRace}
                className="p-2 bg-white/[0.03] hover:bg-red-500/10 rounded-lg transition-all border border-white/[0.05]"
                title="Stop"
              >
                <RotateCcw className="w-3.5 h-3.5 text-white/20" />
              </motion.button>
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="px-5 pb-2">
        <div className="h-72 min-w-[600px]">
          {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                {/* Player gradient */}
                <linearGradient id="gradient-player" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={player?.teamColor || '#e10600'} stopOpacity={0.25}/>
                  <stop offset="95%" stopColor={player?.teamColor || '#e10600'} stopOpacity={0}/>
                </linearGradient>
                {/* Dynamic gradients for each competitor */}
                {visibleCompetitors.map(comp => (
                  <linearGradient key={comp.gradientId} id={comp.gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={comp.color} stopOpacity={0.2}/>
                    <stop offset="95%" stopColor={comp.color} stopOpacity={0}/>
                  </linearGradient>
                ))}
              </defs>
              
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              
              <XAxis 
                dataKey="lap" 
                stroke="rgba(255,255,255,0.1)" 
                fontSize={10}
                tickLine={false}
                axisLine={false}
              />
              
              <YAxis 
                stroke="rgba(255,255,255,0.1)" 
                fontSize={10}
                tickLine={false}
                axisLine={false}
                domain={yDomain}
                tickFormatter={(val) => `${typeof val === 'number' ? val.toFixed(0) : val}`}
              />
              
              <Tooltip content={<ChartTooltip />} />
              
              {/* Player Area - Render first so competitors appear on top if overlapping */}
              <Area
                type="monotone"
                dataKey="player"
                stroke={player?.teamColor || '#e10600'}
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#gradient-player)"
                name={player?.driverCode || 'YOU'}
                isAnimationActive={chartAnimations}
                animationDuration={300}
              />
              
              {/* Competitor Areas - Dynamic based on visible competitors */}
              {visibleCompetitors.map((comp, idx) => (
                <Area
                  key={comp.key}
                  type="monotone"
                  dataKey={comp.key}
                  stroke={comp.color}
                  strokeWidth={2}
                  fill={`url(#${comp.gradientId})`}
                  fillOpacity={1}
                  name={comp.name}
                  isAnimationActive={chartAnimations}
                  animationDuration={300}
                  strokeDasharray={idx % 2 === 0 ? '0' : '4 2'}
                />
              ))}
              
              {raceState.currentLap > 0 && (
                <ReferenceLine 
                  x={raceState.currentLap} 
                  stroke="#e10600" 
                  strokeDasharray="4 4"
                  strokeWidth={1.5}
                  label={{ 
                    value: `L${raceState.currentLap}`, 
                    fill: '#e10600', 
                    fontSize: 9,
                    position: 'insideTopRight'
                  }}
                />
              )}
              
              {/* Reference dots for all visible drivers */}
              {data.length > 0 && player && (
                <ReferenceDot
                  x={raceState.currentLap || 1}
                  y={data[data.length - 1]?.player}
                  r={5}
                  fill={player?.teamColor || '#e10600'}
                  stroke="#fff"
                  strokeWidth={1.5}
                  isFront
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-white/15">
            <Activity className="w-10 h-10 mb-3 opacity-20" />
            <p className="text-xs uppercase tracking-wider">Start simulation to view live data</p>
          </div>
        )}
        </div>
      </div>

      {/* Legend - Show all visible drivers */}
      {data.length > 0 && (
        <div className="px-5 pb-4 flex items-center gap-3 flex-wrap">
          {/* Player */}
          <div className="flex items-center gap-1.5 px-2 py-1 bg-white/[0.03] rounded-md">
            <div 
              className="w-2.5 h-2.5 rounded-full" 
              style={{ backgroundColor: player?.teamColor || '#e10600' }} 
            />
            <span className="text-[10px] text-white/40 uppercase tracking-wider">
              {player?.driverCode || 'YOU'} (You)
            </span>
          </div>
          {/* Competitors */}
          {visibleCompetitors.map(comp => (
            <div 
              key={comp.key} 
              className="flex items-center gap-1.5 px-2 py-1 bg-white/[0.03] rounded-md"
            >
              <div 
                className="w-2.5 h-2.5 rounded-full" 
                style={{ backgroundColor: comp.color }} 
              />
              <span className="text-[10px] text-white/40 uppercase tracking-wider">
                {comp.driverCode} <span className="text-white/20">(P{comp.position})</span>
              </span>
            </div>
          ))}
        </div>
      )}

    </div>
  );
};

export default memo(LiveSimulationChart);
