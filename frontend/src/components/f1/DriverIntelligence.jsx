import React, { memo, useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  Brain, Target, Zap, Shield, TrendingUp, Users, 
  AlertTriangle, Activity, Award, BarChart3 
} from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import { getDriverByCode } from '../../data/drivers';

const PERSONALITY_TRAITS = {
  aggressive: { 
    icon: Zap, 
    color: 'text-red-400', 
    bg: 'bg-red-500/10', 
    label: 'Aggressive',
    description: 'High risk, high reward approach'
  },
  defensive: { 
    icon: Shield, 
    color: 'text-blue-400', 
    bg: 'bg-blue-500/10', 
    label: 'Defensive',
    description: 'Conservative, protects position'
  },
  opportunistic: { 
    icon: Target, 
    color: 'text-yellow-400', 
    bg: 'bg-yellow-500/10', 
    label: 'Opportunistic',
    description: 'Strikes at perfect moments'
  },
  consistent: { 
    icon: Activity, 
    color: 'text-emerald-400', 
    bg: 'bg-emerald-500/10', 
    label: 'Consistent',
    description: 'Steady, error-free driving'
  },
};

const TEAM_STYLES = {
  red_bull: { name: 'Red Bull', style: 'Aggressive Strategy', color: '#1e41ff' },
  mercedes: { name: 'Mercedes', style: 'Calculated Approach', color: '#00d2be' },
  ferrari: { name: 'Ferrari', style: 'Race Pace Focus', color: '#e10600' },
  mclaren: { name: 'McLaren', style: 'Balanced Racing', color: '#ff8000' },
  aston_martin: { name: 'Aston Martin', style: 'Tire Management', color: '#006f62' },
  alpine: { name: 'Alpine', style: 'Adaptive', color: '#0090ff' },
  williams: { name: 'Williams', style: 'Underdog Aggression', color: '#005aff' },
  rb: { name: 'RB', style: 'Development Focus', color: '#2b4562' },
  sauber: { name: 'Kick Sauber', style: 'Steady Progress', color: '#52e252' },
  haas: { name: 'Haas', style: 'Direct Approach', color: '#b6babd' },
};

const DriverCard = memo(({ driver, index }) => {
  const personality = driver.personality || 'consistent';
  const trait = PERSONALITY_TRAITS[personality];
  const TraitIcon = trait.icon;
  
  const driverInfo = getDriverByCode(driver.driverCode || driver.driver_code);
  const teamStyle = TEAM_STYLES[driverInfo?.team?.toLowerCase().replace(' ', '_')] || 
                    { name: driver.team, style: 'Standard', color: driver.teamColor || '#888' };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="p-3 bg-white/[0.03] hover:bg-white/[0.05] rounded-xl border border-white/[0.06] hover:border-white/[0.10] transition-all"
    >
      <div className="flex items-start gap-3">
        {/* Position & Driver */}
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold font-mono text-white/40 w-6">
            {driver.position}
          </span>
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-black"
            style={{ backgroundColor: teamStyle.color }}
          >
            {driver.driverCode?.[0] || '?'}
          </div>
        </div>

        {/* Driver Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-white/80 truncate">
              {driverInfo?.name || driver.driver || 'Unknown'}
            </span>
            <span 
              className="text-[9px] px-1.5 py-0.5 rounded"
              style={{ 
                backgroundColor: `${teamStyle.color}20`,
                color: teamStyle.color 
              }}
            >
              {teamStyle.name}
            </span>
          </div>
          
          <p className="text-[10px] text-white/30 mt-0.5">{teamStyle.style}</p>

          {/* Personality Trait */}
          <div className={`flex items-center gap-1.5 mt-2 ${trait.bg} ${trait.color} px-2 py-1 rounded w-fit`}>
            <TraitIcon className="w-3 h-3" />
            <span className="text-[9px] font-medium uppercase">{trait.label}</span>
          </div>
        </div>

        {/* Threat Level */}
        <div className="text-right">
          <div className="flex items-center gap-1 mb-1">
            <AlertTriangle className="w-3 h-3 text-yellow-400/60" />
            <span className="text-[10px] text-white/40">
              {driver.position <= 3 ? 'High' : driver.position <= 6 ? 'Med' : 'Low'}
            </span>
          </div>
          <div className="h-1 w-12 bg-white/[0.1] rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full"
              style={{ 
                width: `${Math.max(20, 100 - (driver.position * 8))}%`,
                backgroundColor: driver.position <= 3 ? '#ef4444' : driver.position <= 6 ? '#fbbf24' : '#10b981'
              }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
});
DriverCard.displayName = 'DriverCard';

const ThreatAnalysis = memo(({ competitors, player }) => {
  // Calculate threat levels based on gap and pace
  const threats = useMemo(() => {
    const ahead = competitors.filter(c => c.position < player?.position);
    const behind = competitors.filter(c => c.position > player?.position);
    
    return {
      immediate: ahead.slice(-1)[0], // Car just ahead
      undercutThreat: behind.find(c => c.tire === 'soft' && c.tireAge < 3), // Fresh soft tires behind
      drsThreat: behind.find(c => c.gapToLeader - player?.gapToLeader < 1), // Within DRS
    };
  }, [competitors, player]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-white/30 uppercase tracking-wider">Threat Analysis</span>
        <BarChart3 className="w-3.5 h-3.5 text-white/20" />
      </div>
      
      {threats.immediate && (
        <div className="flex items-center gap-2 p-2 bg-red-500/5 rounded-lg border border-red-500/10">
          <TrendingUp className="w-3.5 h-3.5 text-red-400/60" />
          <span className="text-xs text-white/60">
            <strong className="text-red-400">{threats.immediate.driverCode}</strong> defending P{threats.immediate.position}
          </span>
        </div>
      )}
      
      {threats.undercutThreat && (
        <div className="flex items-center gap-2 p-2 bg-yellow-500/5 rounded-lg border border-yellow-500/10">
          <Zap className="w-3.5 h-3.5 text-yellow-400/60" />
          <span className="text-xs text-white/60">
            <strong className="text-yellow-400">{threats.undercutThreat.driverCode}</strong> undercut threat
          </span>
        </div>
      )}
      
      {threats.drsThreat && (
        <div className="flex items-center gap-2 p-2 bg-blue-500/5 rounded-lg border border-blue-500/10">
          <Target className="w-3.5 h-3.5 text-blue-400/60" />
          <span className="text-xs text-white/60">
            <strong className="text-blue-400">{threats.drsThreat.driverCode}</strong> in DRS range
          </span>
        </div>
      )}

      {!threats.immediate && !threats.undercutThreat && !threats.drsThreat && (
        <div className="flex items-center gap-2 p-2 bg-emerald-500/5 rounded-lg border border-emerald-500/10">
          <Shield className="w-3.5 h-3.5 text-emerald-400/60" />
          <span className="text-xs text-emerald-400/60">No immediate threats</span>
        </div>
      )}
    </div>
  );
});
ThreatAnalysis.displayName = 'ThreatAnalysis';

export const DriverIntelligence = () => {
  const { allCompetitors, player, raceState } = useRace();

  // Enrich competitors with personality data
  const enrichedCompetitors = useMemo(() => {
    const personalities = ['aggressive', 'defensive', 'opportunistic', 'consistent'];
    return allCompetitors.map((comp, idx) => ({
      ...comp,
      personality: personalities[idx % personalities.length],
      threatLevel: Math.max(0, 10 - comp.position),
    }));
  }, [allCompetitors]);

  return (
    <div className="f1-card">
      <div className="p-4 pb-3 flex items-center justify-between border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Brain className="w-4 h-4 text-purple-400/60" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Driver Intelligence</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">Personalities & Threats</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2 py-1 bg-white/[0.03] rounded border border-white/[0.06]">
            <Users className="w-3 h-3 text-white/30" />
            <span className="text-[10px] text-white/40">{enrichedCompetitors.length}</span>
          </div>
        </div>
      </div>

      <div className="p-3 space-y-2 max-h-64 overflow-y-auto">
        {/* Threat Analysis */}
        <ThreatAnalysis competitors={enrichedCompetitors} player={player} />
        
        <div className="pt-2 border-t border-white/[0.06]">
          <p className="text-[10px] text-white/30 uppercase tracking-wider mb-2">
            Field Analysis
          </p>
          
          {enrichedCompetitors.length === 0 ? (
            <div className="text-center py-6">
              <Award className="w-8 h-8 text-white/[0.08] mx-auto mb-2" />
              <p className="text-white/15 text-xs">No race data available</p>
            </div>
          ) : (
            enrichedCompetitors.slice(0, 5).map((driver, index) => (
              <DriverCard key={driver.id || index} driver={driver} index={index} />
            ))
          )}
          
          {enrichedCompetitors.length > 5 && (
            <p className="text-center text-[10px] text-white/20 pt-2">
              +{enrichedCompetitors.length - 5} more drivers
            </p>
          )}
        </div>
      </div>

      <div className="px-3 py-2 border-t border-white/[0.06] flex items-center justify-between text-[10px]">
        <span className="text-white/20">
          {raceState.isRunning ? 'Live analysis' : 'Waiting for race'}
        </span>
        <span className="text-white/15">
          AI-powered
        </span>
      </div>
    </div>
  );
};

export default memo(DriverIntelligence);
