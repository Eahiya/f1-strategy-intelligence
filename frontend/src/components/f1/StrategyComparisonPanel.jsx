// Elite Motorsport Strategy Command Interface (Dynamic Evolution)
// This component replaces the generic intelligence panel with a pit-wall-style command console.
// It prioritises visual hierarchy, urgency, and decision-making flow while actively
// reacting to live race state changes from RaceContext.

  // eslint-disable-next-line no-unused-vars
  // eslint-disable-next-line no-unused-vars
import React, { memo, useMemo, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  // eslint-disable-next-line no-unused-vars
  Play,
  AlertTriangle,
  CheckCircle,
  // eslint-disable-next-line no-unused-vars
  XCircle,
  Clock,
  Droplet,
  // eslint-disable-next-line no-unused-vars
  Wind,
  CloudRain,
  Car,
  ArrowRight,
  // eslint-disable-next-line no-unused-vars
  ChevronRight,
  // eslint-disable-next-line no-unused-vars
  ArrowLeft,
  // eslint-disable-next-line no-unused-vars
  Check,
  Zap,
  BadgeInfo,
  // eslint-disable-next-line no-unused-vars
  BadgeAlert,
  // eslint-disable-next-line no-unused-vars
  BadgeX,
  // eslint-disable-next-line no-unused-vars
  Triangle,
  // eslint-disable-next-line no-unused-vars
  Calendar,
  // eslint-disable-next-line no-unused-vars
  Loader2,
  Crosshair
} from 'lucide-react';
import { useRace } from '../../context/RaceContext';

/* ----------------------------------------------------------
   Dynamic Engine Logic
   ---------------------------------------------------------- */

const useDynamicStrategyEngine = (strategies, raceState, player, allCompetitors) => {
  return useMemo(() => {
    if (!strategies || strategies.length === 0) return [];

    const { currentLap = 0, totalLaps = 53, safetyCarActive = false, weather = {} } = raceState;
    const isWet = weather.state === 'wet' || weather.state === 'rain';
    
    // Find rival immediately ahead and behind
    const myPos = player?.position || 0;
    const carAhead = allCompetitors?.find(c => c.position === myPos - 1);
    const carBehind = allCompetitors?.find(c => c.position === myPos + 1);

    return strategies.map((s) => {
      const pits = s.pit_stops || [];
      const tires = s.tires_used?.length ? s.tires_used : ['soft'];
      const nextPitLap = pits.find(p => p > currentLap) || null;
      const lapsToPit = nextPitLap ? nextPitLap - currentLap : 0;
      
      const tireDeg = player?.tireDegradation || 0;
      const tireAge = player?.tireAge || 0;
      
      // Determine urgency level
      let urgency = 'normal';
      let actionText = s.type === 'aggressive' ? 'MAINTAIN PACE' : 'STAY OUT';
      
      if (safetyCarActive) {
        urgency = 'critical';
        actionText = 'BOX UNDER SC';
      } else if (lapsToPit > 0 && lapsToPit <= 2) {
        urgency = 'critical';
        actionText = 'PIT THIS LAP';
      } else if (tireDeg > 75 || isWet) {
        urgency = 'warning';
        actionText = isWet ? 'PREPARE INTERS' : 'TYRE CLIFF';
      } else if (carAhead && (player?.gapToLeader || 0) < 1.5 && lapsToPit <= 5) {
        urgency = 'warning';
        actionText = 'PREPARE UNDERCUT';
      }
      
      if (s.type !== strategies[0]?.type) {
        urgency = 'normal'; // secondary strategies are always normal
      }

      // Build timeline phases
      const phases = [];
      let start = 1;
      pits.forEach((lap, idx) => {
        const end = lap - 1;
        phases.push({ from: start, to: end, type: tires[idx] || 'soft', label: idx === 0 ? 'PUSH' : 'MANAGE' });
        start = lap;
      });
      phases.push({ from: start, to: totalLaps, type: tires[pits.length] || 'soft', label: 'ATTACK' });

      // Generate dynamic intelligence bullets
      const bullets = [];
      
      // Threat / Risk bullets
      if (tireDeg > 70) bullets.push({ type: 'risk', text: `Tire cliff approaching (${Math.round(tireDeg)}% deg).` });
      if (carBehind && carBehind.lap_time < (player?.lapTime || 999)) {
        bullets.push({ type: 'risk', text: `P${carBehind.position} is closing gap rapidly.` });
      }
      
      // Opportunity bullets
      if (carAhead && (player?.gapToLeader || 0) < 2.0) {
        bullets.push({ type: 'opportunity', text: `Traffic ahead: Undercut vulnerability high.` });
      }
      if (safetyCarActive) {
        bullets.push({ type: 'opportunity', text: `Free pit stop window open under SC.` });
      }
      
      // Environment bullets
      if (isWet) bullets.push({ type: 'environment', text: `Track conditions deteriorating.` });
      if (weather.state === 'dry' && tireAge > 10) bullets.push({ type: 'environment', text: `Track evolution stabilizing tyre temps.` });
      
      // Fallbacks if no dynamic events
      if (bullets.length === 0) {
        bullets.push({ type: 'opportunity', text: 'Clean air opportunity available.' });
        bullets.push({ type: 'environment', text: 'Stable race conditions.' });
      }

      // Dynamic decision tree rules
      const rules = [];
      if (safetyCarActive) rules.push({ condition: 'Safety Car ACTIVE', action: 'Execute free pit stop now.' });
      else rules.push({ condition: `Safety Car before lap ${pits[0] || 20}`, action: 'Switch to alternate strategy.' });
      
      if (isWet) rules.push({ condition: 'Rain intensity increases', action: 'Extend wet stint.' });
      else rules.push({ condition: 'Rain probability > 40%', action: 'Delay planned pit stop.' });

      // Dynamic confidence evolution
      let baseConf = s.confidence || (s.type === 'conservative' ? 88 : 82);
      if (isWet) baseConf -= 10;
      if (safetyCarActive) baseConf -= 15;
      baseConf += (currentLap / totalLaps) * 10; // confidence grows over time
      baseConf = Math.min(Math.max(baseConf, 0), 100);

      const breakdown = {
        model_confidence: Math.round(baseConf),
        traffic_certainty: Math.round(100 - (allCompetitors?.length || 20) * 1.5),
        weather_stability: isWet ? 45 : 90,
        tyre_prediction: Math.round(100 - (tireDeg * 0.3)),
      };

      const primary = {
        action: actionText,
        gain: s.advantage ?? 0,
        expiresInLaps: lapsToPit,
        confidence: baseConf,
        urgency,
      };

      return { ...s, phases, bullets, rules, breakdown, primary };
    });
  }, [strategies, raceState, player, allCompetitors]);
};


/* ----------------------------------------------------------
   Helper UI components
   ---------------------------------------------------------- */

const RaceStateHeader = memo(() => {
  const { raceState, player } = useRace();
  const { currentLap, totalLaps, safetyCarActive, weather } = raceState;
  const gap = player?.gapToLeader ? `${player.gapToLeader.toFixed(1)}s` : '--';
  const position = player?.position ?? '--';

  return (
    <div className="flex items-center justify-between text-xs text-white/70 bg-black/40 backdrop-blur-sm p-2 rounded-t-xl border-b border-white/10 relative overflow-hidden">
      {safetyCarActive && (
        <motion.div 
          animate={{ opacity: [0.1, 0.3, 0.1] }} 
          transition={{ repeat: Infinity, duration: 2 }}
          className="absolute inset-0 bg-yellow-500/20 pointer-events-none" 
        />
      )}
      
      <div className="flex items-center gap-2 relative z-10">
        <span className="font-mono font-bold text-white/90">P{position}</span>
        <span className="text-white/50">·</span>
        <span className="font-mono text-white/60">Δ {gap}</span>
      </div>
      
      <div className="flex items-center gap-1 relative z-10">
        <Clock className="w-3 h-3 text-white/50" />
        <span className="font-mono text-white/80">{currentLap}/{totalLaps}</span>
      </div>
      
      <div className="flex items-center gap-2 relative z-10">
        <Car className="w-3 h-3 text-white/50" />
        <span className="font-mono text-white/60">{player?.tire?.toUpperCase() || '—'}</span>
        {weather?.state && (
          <span className="flex items-center gap-0.5">
            {weather.state === 'wet' || weather.state === 'rain' ? (
              <CloudRain className="w-3 h-3 text-blue-400" />
            ) : (
              <Droplet className="w-3 h-3 text-blue-300" />
            )}
            <span className="text-white/60 capitalize text-xs">{weather.state}</span>
          </span>
        )}
        {safetyCarActive && (
          <AlertTriangle className="w-3 h-3 text-yellow-400" title="Safety Car" />
        )}
      </div>
    </div>
  );
});

const PrimaryDecisionCard = memo(({ decision }) => {
  const isCritical = decision.urgency === 'critical';
  const isWarning = decision.urgency === 'warning';
  
  const bgGradient = isCritical 
    ? 'from-[#3a0d0d] to-[#1a0000]' 
    : isWarning 
      ? 'from-[#3a200d] to-[#1a0d00]'
      : 'from-[#0d1a3a] to-[#000d1a]';
      
  const borderColor = isCritical ? 'border-[#e10600]/40' : isWarning ? 'border-orange-500/40' : 'border-blue-500/20';
  const iconColor = isCritical ? 'text-[#e10600]' : isWarning ? 'text-orange-500' : 'text-blue-500';

  const pulseVariant = {
    animate: {
      opacity: isCritical ? [1, 0.7, 1] : 1,
      scale: isCritical ? [1, 1.02, 1] : 1,
      boxShadow: isCritical 
        ? ['0 0 0px rgba(225,6,0,0)', '0 0 20px rgba(225,6,0,0.3)', '0 0 0px rgba(225,6,0,0)'] 
        : isWarning 
          ? ['0 0 0px rgba(249,115,22,0)', '0 0 15px rgba(249,115,22,0.2)', '0 0 0px rgba(249,115,22,0)'] 
          : 'none',
      transition: { repeat: Infinity, duration: isCritical ? 1.0 : 2.0 },
    },
  };

  return (
    <motion.div
      variants={pulseVariant}
      animate="animate"
      className={`relative overflow-hidden rounded-xl border ${borderColor} bg-gradient-to-br ${bgGradient} p-6 shadow-xl transition-colors duration-500`}
    >
      <div className="flex items-center gap-4">
        {isCritical ? (
          <Zap className={`w-10 h-10 ${iconColor} animate-pulse`} />
        ) : isWarning ? (
          <AlertTriangle className={`w-10 h-10 ${iconColor}`} />
        ) : (
          <Crosshair className={`w-10 h-10 ${iconColor}`} />
        )}
        
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-white uppercase mb-1 tracking-wider">
            {decision.action.toUpperCase()}
          </h2>
          <p className="text-sm text-white/80 mb-2">
            Gain: <span className={`font-mono font-bold ${isCritical ? 'text-[#e10600]' : isWarning ? 'text-orange-400' : 'text-emerald-400'}`}>
              {decision.gain > 0 ? `+${decision.gain.toFixed(1)}` : `${decision.gain.toFixed(1)}`}
            </span>s
          </p>
          <div className="flex items-center gap-3">
            <div className="flex items-center text-white/70 text-xs">
              <Clock className="w-3 h-3 mr-1" />
              {decision.expiresInLaps <= 0 ? (
                <span className="text-white/50">Optimal window passed</span>
              ) : (
                <span>Window closes in {decision.expiresInLaps} lap{decision.expiresInLaps !== 1 ? 's' : ''}</span>
              )}
            </div>
            <div className="flex items-center text-white/70 text-xs">
              <BadgeInfo className="w-3 h-3 mr-1" />
              <span>Conf: {Math.round(decision.confidence)}%</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
});

const DecisionReasoning = memo(({ bullets }) => (
  <div className="space-y-1.5 text-sm text-white/70">
    <AnimatePresence>
      {bullets.map((b, i) => (
        <motion.div 
          key={i} 
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-start gap-2 bg-white/[0.02] p-1.5 rounded"
        >
          <div className="mt-0.5">
            {b.type === 'opportunity' && <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
            {b.type === 'risk' && <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />}
            {b.type === 'environment' && <CloudRain className="w-3.5 h-3.5 text-blue-400" />}
          </div>
          <span className="leading-tight text-xs">{b.text}</span>
        </motion.div>
      ))}
    </AnimatePresence>
  </div>
));

const StrategyTimeline = memo(({ phases, totalLaps, currentLap }) => {
  return (
    <div className="relative overflow-x-auto py-6">
      {/* Current Lap Progress Line */}
      <div className="absolute top-0 bottom-0 z-10 flex flex-col items-center" style={{ left: `${(currentLap / totalLaps) * 100}%` }}>
        <div className="w-0.5 h-full bg-[#e10600] shadow-[0_0_8px_rgba(225,6,0,0.8)]" />
        <div className="absolute top-0 bg-[#e10600] text-white text-[9px] font-bold px-1 rounded transform -translate-x-1/2 -translate-y-full">
          L{currentLap}
        </div>
      </div>

      <div className="flex items-center relative w-full h-8 bg-black/40 rounded-md overflow-hidden border border-white/10">
        {phases.map((p, i) => {
          const widthPct = ((p.to - p.from + 1) / totalLaps) * 100;
          const bg = p.type === 'soft' ? 'bg-red-500' : p.type === 'medium' ? 'bg-yellow-500' : 'bg-white';
          const isPast = currentLap > p.to;
          
          return (
            <motion.div
              key={i}
              className={`flex items-center justify-center h-full border-r border-black/50 ${bg} relative group`}
              style={{ width: `${widthPct}%` }}
              whileHover={{ opacity: 0.9 }}
            >
              <div className={`absolute inset-0 ${isPast ? 'bg-black/60' : 'bg-black/20'}`} />
              <span className={`relative z-10 text-[10px] font-bold ${p.type === 'white' ? 'text-black/70' : 'text-white/90'} tracking-wider`}>
                {widthPct > 10 ? p.label : ''}
              </span>
              
              {/* Tooltip */}
              <div className="absolute bottom-full mb-1 opacity-0 group-hover:opacity-100 transition-opacity bg-black/90 text-white text-[9px] px-2 py-1 rounded whitespace-nowrap z-20 border border-white/20">
                L{p.from} - L{p.to} ({p.type})
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
});

const DecisionTree = memo(({ rules }) => (
  <div className="space-y-1.5 text-xs text-white/70">
    {rules.map((r, i) => (
      <div key={i} className="flex flex-col bg-white/[0.02] p-2 rounded-md border border-white/5">
        <span className="text-white/50 font-mono text-[10px] uppercase mb-0.5">IF {r.condition}</span>
        <div className="flex items-center gap-1.5 text-white/80">
          <ArrowRight className="w-3 h-3 text-[#e10600]/80" />
          <span>{r.action}</span>
        </div>
      </div>
    ))}
  </div>
));

const ConfidenceBreakdown = memo(({ breakdown }) => {
  const total = 100;
  return (
    <div className="space-y-2.5">
      {Object.entries(breakdown).map(([key, value]) => {
        const colorClass = value > 80 ? 'bg-emerald-500' : value > 50 ? 'bg-yellow-500' : 'bg-red-500';
        return (
          <div key={key} className="flex items-center gap-3 text-[10px] text-white/70">
            <span className="w-28 capitalize tracking-wide">{key.replace('_', ' ')}</span>
            <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(value / total) * 100}%` }}
                transition={{ duration: 1, ease: 'easeOut' }}
                className={`h-full ${colorClass}`}
              />
            </div>
            <span className="w-8 text-right font-mono font-bold text-white/80">{value}%</span>
          </div>
        );
      })}
    </div>
  );
});

/* ----------------------------------------------------------
   Main elite command interface component
   ---------------------------------------------------------- */
export const EliteStrategyCommand = ({ strategies = [] }) => {
  const { raceState, player, allCompetitors, confidence, metrics } = useRace();
  
  // Connect to dynamic engine
  const enriched = useDynamicStrategyEngine(strategies, raceState, player, allCompetitors);

  const primaryData = useMemo(() => {
    const row = enriched[0] || {};
    if (!raceState.isRunning || confidence?.overall == null) return row;
    const liveConfPct = confidence.overall > 1 ? confidence.overall : confidence.overall * 100;
    const b = confidence.breakdown || {};
    const bd = { ...(row.breakdown || {}) };
    if (b.model_confidence != null) bd.model_confidence = Math.round(b.model_confidence * 100);
    if (b.tire_certainty != null) bd.tyre_prediction = Math.round(b.tire_certainty * 100);
    if (b.weather_stability != null) bd.weather_stability = Math.round(b.weather_stability * 100);
    if (b.model_agreement != null) bd.traffic_certainty = Math.round(b.model_agreement * 100);
    const pr = { ...(row.primary || {}), confidence: Math.round(liveConfPct) };
    if (metrics?.risk_score != null) {
      const r01 = metrics.risk_score > 1 ? metrics.risk_score / 100 : metrics.risk_score;
      if (r01 > 0.55 && pr.urgency === 'normal') pr.urgency = 'warning';
    }
    return { ...row, breakdown: bd, primary: pr };
  }, [enriched, raceState.isRunning, confidence, metrics]);

  return (
    <div className="flex flex-col h-full bg-[#080808] text-white">
      <RaceStateHeader />

      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Left column – primary decision & reasoning */}
          <div className="space-y-6">
            <PrimaryDecisionCard decision={primaryData.primary || { action: 'WAIT', gain: 0, expiresInLaps: 0, confidence: 0, urgency: 'normal' }} />

            <div className="bg-black/30 backdrop-blur-sm p-4 rounded-xl border border-white/10 shadow-lg">
              <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em] mb-3">Live Tactical Intel</h3>
              <DecisionReasoning bullets={primaryData.bullets || []} />
            </div>

            <div className="bg-black/30 backdrop-blur-sm p-4 rounded-xl border border-white/10 shadow-lg">
              <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em] mb-3">Decision Logic</h3>
              <DecisionTree rules={primaryData.rules || []} />
            </div>
            
            <div className="bg-black/30 backdrop-blur-sm p-4 rounded-xl border border-white/10 shadow-lg">
              <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em] mb-3">Confidence Breakdown</h3>
              <ConfidenceBreakdown breakdown={primaryData.breakdown || {}} />
            </div>
          </div>

          {/* Right column – timeline and alternative strategies */}
          <div className="space-y-6">
            <div className="bg-black/30 backdrop-blur-sm p-4 rounded-xl border border-white/10 shadow-lg">
              <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em] mb-1">Strategy Timeline</h3>
              <StrategyTimeline phases={primaryData.phases || []} totalLaps={raceState.totalLaps} currentLap={raceState.currentLap} />
            </div>

            <div className="space-y-3">
              <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em] mb-2 px-1">Alternative Strategies</h3>
              {enriched.slice(1).map((alt, idx) => (
                <div key={idx} className="bg-gradient-to-r from-black/40 to-transparent border-l-2 border-white/20 rounded-r-lg p-3 flex items-center justify-between group hover:bg-white/[0.04] transition-colors">
                  <div>
                    <h4 className="text-xs font-bold text-white/80 capitalize mb-0.5">{alt.type} strategy</h4>
                    <p className="text-[10px] text-white/40">Risk: {alt.risk || '—'}%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-mono font-bold text-white/60">
                      {alt.advantage > 0 ? `+${alt.advantage}` : alt.advantage}s
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

EliteStrategyCommand.displayName = 'EliteStrategyCommand';
export default memo(EliteStrategyCommand);
