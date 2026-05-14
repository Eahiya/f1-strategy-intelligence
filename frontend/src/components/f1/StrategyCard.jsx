import React, { useState, memo, useMemo, useId } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Clock, TrendingUp, Shield, AlertTriangle, ChevronDown, ChevronUp, Zap, Wind, Target, Brain, BarChart3 } from 'lucide-react';

const RiskBreakdown = memo(({ factors }) => {
  if (!factors?.length) return null;
  return (
    <div className="space-y-1.5 mt-3">
      {factors.map((factor, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: factor.impact > 60 ? '#ef4444' : factor.impact > 40 ? '#fbbf24' : '#10b981' }} />
          <span className="text-[10px] text-white/30 flex-1">{factor.name}</span>
          <div className="w-12 h-1 bg-white/[0.04] rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${factor.impact}%` }}
              transition={{ duration: 0.5, delay: idx * 0.1 }}
              className="h-full rounded-full"
              style={{ backgroundColor: factor.impact > 60 ? '#ef4444' : factor.impact > 40 ? '#fbbf24' : '#10b981' }}
            />
          </div>
          <span className="text-[9px] text-white/15 w-6 text-right">{factor.impact}%</span>
        </div>
      ))}
    </div>
  );
});
RiskBreakdown.displayName = 'RiskBreakdown';

const AlternativeCard = memo(({ strategy, index, isSelected, onClick }) => {
  const getTypeColor = (type) => {
    if (type?.includes('aggressive')) return 'text-red-400/60 border-red-500/15 bg-red-500/6';
    if (type?.includes('conservative')) return 'text-blue-400/60 border-blue-500/15 bg-blue-500/6';
    if (type?.includes('balanced') || type?.includes('optimal')) return 'text-emerald-400/60 border-emerald-500/15 bg-emerald-500/6';
    return 'text-white/25 border-white/[0.06] bg-white/[0.02]';
  };

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      className={`w-full text-left p-2.5 rounded-lg border transition-all ${
        isSelected ? 'border-[#e10600]/30 bg-[#e10600]/8' : getTypeColor(strategy.type)
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-bold text-white/60">{strategy.type || `Alt ${index + 1}`}</span>
        <span className={`text-xs font-mono font-bold ${
          strategy.delta > 0 ? 'text-red-400/60' : strategy.delta < 0 ? 'text-emerald-400/60' : 'text-white/25'
        }`}>
          {strategy.delta > 0 ? '+' : ''}{strategy.delta?.toFixed(1)}s
        </span>
      </div>
      {strategy.risk && (
        <div className="flex items-center gap-1">
          <AlertTriangle className="w-2.5 h-2.5" style={{ 
            color: strategy.risk > 60 ? '#ef4444' : strategy.risk > 40 ? '#fbbf24' : '#10b981' 
          }} />
          <span className="text-[8px] uppercase tracking-wider" style={{ 
            color: strategy.risk > 60 ? '#ef4444' : strategy.risk > 40 ? '#fbbf24' : '#10b981' 
          }}>
            {strategy.risk > 60 ? 'High' : strategy.risk > 40 ? 'Med' : 'Low'}
          </span>
        </div>
      )}
    </motion.button>
  );
});
AlternativeCard.displayName = 'AlternativeCard';

function ConfidenceSparkline({ values }) {
  const gradId = useId().replace(/:/g, '');
  if (!values || values.length < 2) return null;
  const w = Math.max(values.length * 10, 80);
  const h = 36;
  const pts = values.map((v, i) => {
    const pct = typeof v === 'number' && v <= 1 ? v * 100 : Math.min(100, Math.max(0, v));
    const x = (i / (values.length - 1)) * (w - 8) + 4;
    const y = h - 4 - (pct / 100) * (h - 8);
    return `${x},${y}`;
  });
  return (
    <div className="mt-2 h-9 w-full opacity-90">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="none">
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#e10600" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#f87171" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        <polyline fill="none" stroke={`url(#${gradId})`} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" points={pts.join(' ')} />
      </svg>
      <p className="text-[8px] text-white/15 uppercase tracking-wider mt-0.5">Confidence evolution (live)</p>
    </div>
  );
}

export const StrategyCard = ({ 
  strategy, confidence = 87, timeGain = 0, isBest = true,
  alternatives = [], riskFactors = [], whyThisStrategy = '', onStrategyChange,
  confidenceTrend = null,
}) => {
  const confBar =
    typeof confidence === 'number' && confidence >= 0 && confidence <= 1
      ? Math.round(confidence * 100)
      : confidence ?? 87;

  const [showDetails, setShowDetails] = useState(false);
  const [selectedAlt, setSelectedAlt] = useState(null);

  const getStrategyIcon = (type) => {
    if (type?.includes('aggressive')) return Zap;
    if (type?.includes('conservative')) return Shield;
    if (type?.includes('AI') || type?.includes('RL')) return Brain;
    return Trophy;
  };

  const StrategyIcon = getStrategyIcon(strategy?.type);
  const displayStrategy = selectedAlt || strategy;

  const handleAltClick = (alt, index) => {
    setSelectedAlt(alt);
    onStrategyChange?.(alt, index);
  };

  const overallRisk = useMemo(() => {
    if (!riskFactors.length) return 35;
    return Math.round(riskFactors.reduce((sum, f) => sum + f.impact, 0) / riskFactors.length);
  }, [riskFactors]);

  const getRiskLabel = (risk) => {
    if (risk <= 30) return { label: 'LOW', color: 'text-emerald-400/60' };
    if (risk <= 60) return { label: 'MED', color: 'text-yellow-400/60' };
    return { label: 'HIGH', color: 'text-red-400/60' };
  };

  const riskConfig = getRiskLabel(overallRisk);

  return (
    <div className={`f1-card relative overflow-hidden ${isBest && !selectedAlt ? 'border-[#e10600]/15' : ''}`}>
      {isBest && !selectedAlt && (
        <div className="absolute -right-8 -top-8 h-20 w-20 bg-[#e10600]/10 blur-3xl rounded-full" />
      )}
      
      <div className="relative z-10 p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${
              isBest && !selectedAlt ? 'bg-[#e10600]/15' : 'bg-white/[0.04]'
            }`}>
              <StrategyIcon className={`w-4 h-4 ${isBest && !selectedAlt ? 'text-[#e10600]' : 'text-white/30'}`} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white/70">{displayStrategy?.type || 'Strategy'}</h3>
              <p className="text-[10px] text-white/20 uppercase tracking-wider">
                {selectedAlt ? 'Alternative' : 'Recommended'}
              </p>
            </div>
          </div>
          {isBest && !selectedAlt && (
            <span className="px-2 py-0.5 text-[9px] font-bold bg-[#e10600]/15 text-[#e10600]/80 rounded uppercase tracking-wider">
              Best
            </span>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="bg-white/[0.03] rounded-xl p-2.5 border border-white/[0.05]">
            <div className="flex items-center gap-1.5 text-[9px] text-white/15 mb-1">
              <Clock className="w-2.5 h-2.5" />Race Time
            </div>
            <p className="text-base font-bold text-white/60 font-mono">
              {displayStrategy?.predicted_time?.toFixed(1) || '--'}s
            </p>
            <p className="text-[8px] text-white/10 mt-0.5">
              ~{displayStrategy?.predicted_time ? (displayStrategy.predicted_time / 60).toFixed(1) : '--'} min
            </p>
          </div>
          <div className="bg-white/[0.03] rounded-xl p-2.5 border border-white/[0.05]">
            <div className="flex items-center gap-1.5 text-[9px] text-white/15 mb-1">
              <TrendingUp className="w-2.5 h-2.5" />vs Baseline
            </div>
            <p className={`text-base font-bold font-mono ${timeGain >= 0 ? 'text-emerald-400/60' : 'text-red-400/60'}`}>
              {timeGain >= 0 ? '+' : ''}{timeGain?.toFixed(1) || '--'}s
            </p>
            <p className="text-[8px] text-white/10 mt-0.5">
              {timeGain > 0 ? 'Faster' : timeGain < 0 ? 'Slower' : 'Equal'}
            </p>
          </div>
        </div>

        {/* Risk */}
        <div className="flex items-center gap-2 bg-white/[0.03] rounded-xl p-2.5 mb-3 border border-white/[0.05]">
          <AlertTriangle className={`w-3.5 h-3.5 ${riskConfig.color}`} />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[9px] text-white/15">Risk</span>
              <span className={`text-[9px] font-bold ${riskConfig.color}`}>{riskConfig.label}</span>
            </div>
            <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${overallRisk}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className={`h-full rounded-full ${overallRisk > 60 ? 'bg-red-500/50' : overallRisk > 30 ? 'bg-yellow-500/40' : 'bg-emerald-500/40'}`}
              />
            </div>
          </div>
        </div>

        {/* Why */}
        {whyThisStrategy && (
          <div className="mb-3 p-2.5 bg-white/[0.03] rounded-xl border border-white/[0.05]">
            <div className="flex items-center gap-1.5 mb-1">
              <Brain className="w-2.5 h-2.5 text-[#e10600]/50" />
              <span className="text-[9px] text-[#e10600]/50 uppercase tracking-wider">Why</span>
            </div>
            <p className="text-[10px] text-white/25 leading-relaxed">{whyThisStrategy}</p>
          </div>
        )}

        {/* Expand */}
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="w-full flex items-center justify-between p-2 hover:bg-white/[0.03] rounded-lg transition-colors"
        >
          <span className="text-[10px] text-white/15 uppercase tracking-wider">Details</span>
          {showDetails ? <ChevronUp className="w-3 h-3 text-white/15" /> : <ChevronDown className="w-3 h-3 text-white/15" />}
        </button>

        <AnimatePresence>
          {showDetails && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-2 space-y-3">
                {riskFactors.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <BarChart3 className="w-2.5 h-2.5 text-white/15" />
                      <span className="text-[9px] text-white/15 uppercase tracking-wider">Risk Breakdown</span>
                    </div>
                    <RiskBreakdown factors={riskFactors} />
                  </div>
                )}

                {displayStrategy?.pit_stops && (
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <Wind className="w-2.5 h-2.5 text-white/15" />
                      <span className="text-[9px] text-white/15 uppercase tracking-wider">Pit Schedule</span>
                    </div>
                    <div className="flex gap-1.5">
                      {displayStrategy.pit_stops.map((stop, idx) => (
                        <span key={idx} className="px-2 py-1 bg-white/[0.04] rounded text-[10px] text-white/30 font-mono border border-white/[0.05]">
                          L{stop}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {alternatives.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <Target className="w-2.5 h-2.5 text-white/15" />
                      <span className="text-[9px] text-white/15 uppercase tracking-wider">Alternatives</span>
                    </div>
                    <div className="space-y-1">
                      {alternatives.map((alt, idx) => (
                        <AlternativeCard key={idx} strategy={alt} index={idx} isSelected={selectedAlt === alt} onClick={() => handleAltClick(alt, idx)} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Confidence */}
        <div className="flex items-center gap-4 pt-3 mt-3 border-t border-white/[0.06]">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[9px] text-white/15 uppercase tracking-wider">Confidence</span>
              <span className="text-[10px] font-bold text-white/40">{confBar}%</span>
            </div>
            <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${confBar}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="h-full bg-gradient-to-r from-[#e10600] to-red-400"
              />
            </div>
            <ConfidenceSparkline values={confidenceTrend} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default memo(StrategyCard);
