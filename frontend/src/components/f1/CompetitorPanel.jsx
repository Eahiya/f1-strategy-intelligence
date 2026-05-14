import React, { useMemo, memo } from 'react';
import { motion } from 'framer-motion';
import { Trophy, TrendingUp, TrendingDown, Minus, Timer } from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import AnimatedValue from '../common/AnimatedValue';
import { getDriverBadge } from '../../data/drivers';

const CompetitorRow = memo(({ competitor, index, playerPosition, isPlayer }) => {
  const isAhead = competitor.position < playerPosition;
  
  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'gaining': return <TrendingUp className="w-3 h-3 text-emerald-400/50" />;
      case 'losing': return <TrendingDown className="w-3 h-3 text-red-400/50" />;
      default: return <Minus className="w-3 h-3 text-white/15" />;
    }
  };

  const getTireColor = (tire) => {
    switch (tire?.toLowerCase()) {
      case 'soft': return 'bg-red-500/80 text-white';
      case 'medium': return 'bg-yellow-500/80 text-black';
      case 'hard': return 'bg-white/80 text-black';
      case 'inter': return 'bg-green-500/80 text-white';
      case 'wet': return 'bg-blue-500/80 text-white';
      default: return 'bg-white/20 text-white/40';
    }
  };

  const getTeamColorStyle = (teamColor, team) => {
    if (teamColor) {
      return { color: teamColor };
    }
    const colors = {
      'Mercedes': '#00D2BE', 'Red Bull Racing': '#1E41FF', 'Ferrari': '#FF0000',
      'McLaren': '#FF8000', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
      'Williams': '#005AFF', 'Haas': '#B6BABD', 'RB': '#2B4562',
      'Kick Sauber': '#52E252', 'Red Bull': '#1E41FF', 'Alfa Romeo': '#900000',
    };
    return { color: colors[team] || '#888888' };
  };

  const getPositionStyle = (position) => {
    if (position === 1) return 'bg-yellow-500/15 text-yellow-400/70';
    if (position === 2) return 'bg-white/[0.08] text-white/50';
    if (position === 3) return 'bg-amber-700/15 text-amber-500/60';
    return 'bg-white/[0.03] text-white/25';
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04 }}
      className={`flex items-center gap-2.5 p-2.5 rounded-lg transition-all ${
        isPlayer ? 'bg-[#e10600]/[0.06] border border-[#e10600]/15' : 'hover:bg-white/[0.02]'
      }`}
    >
      <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs flex-shrink-0 ${getPositionStyle(competitor.position)}`}>
        {competitor.position}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <div 
            className="w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: competitor.teamColor || '#888888' }}
          />
          <span 
            className="text-xs font-bold truncate"
            style={isPlayer ? { color: 'rgba(255,255,255,0.8)' } : getTeamColorStyle(competitor.teamColor, competitor.team)}
          >
            {competitor.driverCode || competitor.driver?.split(' ').pop() || '???'}
          </span>
          {isPlayer && (
            <span className="px-1 py-0.5 bg-[#e10600]/15 text-[#e10600]/70 text-[8px] rounded font-bold uppercase tracking-wider">You</span>
          )}
        </div>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className="text-[10px] text-white/15">{competitor.team}</span>
          <span className="text-white/[0.06]">|</span>
          <div className="flex items-center gap-1">
            {getTrendIcon(competitor.gapTrend)}
            <span className={`text-[10px] font-mono ${
              isAhead ? 'text-red-400/50' : competitor.position > playerPosition ? 'text-emerald-400/50' : 'text-white/25'
            }`}>
              <AnimatedValue value={competitor.gap} precision={1} suffix="s" />
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-col items-end gap-0.5">
        <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${getTireColor(competitor.tire)}`}>
          {competitor.tire?.[0]}
        </span>
        <span className="text-[9px] text-white/15 font-mono">L{competitor.tireAge}</span>
      </div>

      <div className="text-right min-w-[55px]">
        <div className="flex items-center gap-1 text-white/20">
          <Timer className="w-3 h-3" />
          <span className="text-[10px] font-mono"><AnimatedValue value={competitor.lastLap} precision={2} /></span>
        </div>
      </div>
    </motion.div>
  );
});
CompetitorRow.displayName = 'CompetitorRow';

const CompetitorPanel = () => {
  const { allCompetitors, raceState, player } = useRace();
  const currentLap = raceState.currentLap;
  const playerPosition = player?.position || 3;

  const displayCompetitors = useMemo(() => allCompetitors.slice(0, 8), [allCompetitors]);

  return (
    <div className="f1-card">
      <div className="p-4 pb-3 flex items-center justify-between border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Trophy className="w-4 h-4 text-emerald-400/40" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Competitors</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">Live positions</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-[9px] text-white/15 uppercase tracking-wider">Your Position</p>
          <p className="text-lg font-bold text-[#e10600]/70 font-mono">P{playerPosition}</p>
        </div>
      </div>

      <div className="p-2">
        {displayCompetitors.map((competitor, index) => (
          <CompetitorRow
            key={competitor.id}
            competitor={competitor}
            index={index}
            playerPosition={playerPosition}
            isPlayer={competitor.isPlayer}
          />
        ))}
      </div>

      <div className="px-4 py-2 border-t border-white/[0.06] flex items-center justify-between text-[10px]">
        <div className="flex items-center gap-2.5">
          {[{ c: 'bg-red-500/60', l: 'S' }, { c: 'bg-yellow-500/60', l: 'M' }, { c: 'bg-white/50', l: 'H' }].map((t, idx) => (
            <span key={idx} className="flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-sm ${t.c}`} />
              <span className="text-white/15">{t.l}</span>
            </span>
          ))}
        </div>
        <span className="text-white/15 font-mono">Lap {currentLap}</span>
      </div>
    </div>
  );
};

export default memo(CompetitorPanel);
