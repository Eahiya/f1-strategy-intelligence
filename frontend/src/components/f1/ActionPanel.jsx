import React, { useState, useEffect, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertCircle, CheckCircle2, Clock, Zap, TrendingUp, Shield, ArrowRight,
  // eslint-disable-next-line no-unused-vars
  Timer, Flag, RefreshCw, Loader2, Car, Fuel, Wind, ChevronDown, ChevronUp,
  Target, TrendingDown, Activity, BarChart3
} from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import AnimatedValue from '../common/AnimatedValue';

const TIRE_COMPOUNDS = [
  { id: 'soft', name: 'Soft', color: '#ef4444', laps: 25, pace: -0.8 },
  { id: 'medium', name: 'Medium', color: '#eab308', laps: 40, pace: 0 },
  { id: 'hard', name: 'Hard', color: '#ffffff', laps: 55, pace: 1.2 },
];

const ActionPanel = () => {
  const [showDetails, setShowDetails] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [selectedCompound, setSelectedCompound] = useState('medium');
  const [showCompoundSelector, setShowCompoundSelector] = useState(false);
  const [executionStage, setExecutionStage] = useState('idle');
  
  const { currentRecommendation, uiRecommendation, raceState, executeAction, actionState, player, isConnected } = useRace();
  
  const isSimulating = raceState.isRunning;
  const rec = uiRecommendation || currentRecommendation;
  const isExecuting = actionState.isExecuting;
  
  useEffect(() => {
    if (rec?.urgency === 'critical') setCountdown(rec.expiresIn || 5);
  }, [rec?.id, rec?.urgency, rec?.expiresIn]);
  
  useEffect(() => {
    if (rec?.urgency === 'critical' && countdown > 0 && isSimulating) {
      const timer = setInterval(() => setCountdown(c => c <= 1 ? 0 : c - 1), 1000);
      return () => clearInterval(timer);
    }
  }, [rec?.urgency, countdown, isSimulating]);

  useEffect(() => {
    if (rec?.recommendedCompound) setSelectedCompound(rec.recommendedCompound);
  }, [rec?.recommendedCompound]);
  
  const handleExecuteAction = useCallback(async () => {
    if (!rec || !isSimulating || isExecuting || !isConnected) return;
    setExecutionStage('executing');
    try {
      const actionData = rec.type === 'pit' ? { compound: selectedCompound } : {};
      const result = await executeAction(rec.type, actionData);
      if (result.success) {
        setExecutionStage('success');
        setTimeout(() => { setExecutionStage('idle'); setShowCompoundSelector(false); }, 2000);
      } else {
        setExecutionStage('error');
        setTimeout(() => setExecutionStage('idle'), 3000);
      }
    } catch {
      setExecutionStage('error');
      setTimeout(() => setExecutionStage('idle'), 3000);
    }
  }, [rec, isSimulating, isExecuting, isConnected, executeAction, selectedCompound]);

  if (!rec) {
    return (
      <div className="f1-card">
        <div className="p-5 text-center">
          <div className="w-14 h-14 bg-white/[0.03] rounded-2xl flex items-center justify-center mx-auto mb-4 border border-white/[0.05]">
            <Shield className="w-6 h-6 text-white/15" />
          </div>
          <h3 className="text-sm font-bold text-white/60 mb-1">No Active Actions</h3>
          <p className="text-xs text-white/20">
            {isSimulating ? `Lap ${raceState.currentLap}/${raceState.totalLaps}` : 'Start simulation to see recommendations'}
          </p>
          {isSimulating && player && (
            <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
              <div className="bg-white/[0.03] rounded-lg p-2 border border-white/[0.05]">
                <div className="text-[9px] text-white/15 uppercase tracking-wider">Position</div>
                <div className="text-white/60 font-bold font-mono">P{player.position}</div>
              </div>
              <div className="bg-white/[0.03] rounded-lg p-2 border border-white/[0.05]">
                <div className="text-[9px] text-white/15 uppercase tracking-wider">Tire</div>
                <div className="font-bold font-mono" style={{ color: TIRE_COMPOUNDS.find(t => t.id === player.tire)?.color || '#fff' }}>
                  {player.tire?.toUpperCase()} {player.tireAge}L
                </div>
              </div>
              <div className="bg-white/[0.03] rounded-lg p-2 border border-white/[0.05]">
                <div className="text-[9px] text-white/15 uppercase tracking-wider">Gap</div>
                <div className="text-white/60 font-bold font-mono">
                  <AnimatedValue value={player.gapToLeader} precision={1} suffix="s" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  const getUrgencyConfig = () => {
    switch (rec.urgency) {
      case 'critical': return { accent: '#ef4444', label: 'CRITICAL', pulse: true };
      case 'high': return { accent: '#f97316', label: 'HIGH', pulse: true };
      case 'normal': return { accent: '#3b82f6', label: 'NORMAL', pulse: false };
      default: return { accent: '#6b7280', label: 'STANDBY', pulse: false };
    }
  };

  const urgencyConfig = getUrgencyConfig();

  const getTypeIcon = (type) => {
    switch (type) {
      case 'pit': return Timer;
      case 'undercut': return Zap;
      case 'defend': return Shield;
      case 'push': return TrendingUp;
      case 'conserve': return Fuel;
      case 'finish': return Flag;
      default: return ArrowRight;
    }
  };

  const TypeIcon = getTypeIcon(rec.type);

  const getExecutionButtonContent = () => {
    switch (executionStage) {
      case 'executing': return (<><Loader2 className="w-4 h-4 animate-spin" /><span>Executing...</span></>);
      case 'success': return (<><CheckCircle2 className="w-4 h-4 text-emerald-400" /><span className="text-emerald-400">Confirmed</span></>);
      case 'error': return (<><AlertCircle className="w-4 h-4 text-red-400" /><span className="text-red-400">Retry</span></>);
      default: return (<><CheckCircle2 className="w-4 h-4" /><span>Confirm Action</span><ArrowRight className="w-4 h-4" /></>);
    }
  };

  return (
    <div className={`f1-card relative overflow-hidden ${urgencyConfig.pulse ? 'border-l-2' : ''}`}
      style={{ borderLeftColor: urgencyConfig.pulse ? urgencyConfig.accent + '50' : undefined }}>
      <AnimatePresence>
        {urgencyConfig.pulse && (
          <motion.div
            className="absolute inset-0 pointer-events-none"
            animate={{ opacity: [0, 0.03, 0] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            style={{ backgroundColor: urgencyConfig.accent }}
          />
        )}
      </AnimatePresence>

      <div className="relative z-10 p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ backgroundColor: urgencyConfig.accent + '15' }}>
              <TypeIcon className="w-5 h-5" style={{ color: urgencyConfig.accent }} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white/80">{rec.title}</h3>
                {rec.urgency === 'critical' && (
                  <span className="px-1.5 py-0.5 text-[9px] font-bold bg-red-500/20 text-red-400 rounded animate-pulse uppercase tracking-wider">
                    Now!
                  </span>
                )}
              </div>
              <p className="text-[10px] text-white/25">{rec.subtitle}</p>
            </div>
          </div>
          
          <div className="text-right">
            {rec.urgency === 'critical' ? (
              <div>
                <p className="text-[9px] text-white/15 uppercase tracking-wider">Decide in</p>
                <p className="text-lg font-mono font-bold text-white/60">
                  <AnimatedValue value={countdown} precision={0} suffix="s" duration={0.2} />
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-end">
                <p className="text-[9px] text-white/15 uppercase tracking-wider">Probability</p>
                <p className="text-lg font-mono font-bold text-white/60">
                  {rec.probability !== undefined ? `${(rec.probability * 100).toFixed(1)}%` : rec.confidence !== undefined ? `${(rec.confidence * 100).toFixed(1)}%` : `75.0%`}
                </p>
              </div>
            )}
          </div>
        </div>

        <p className="text-xs text-white/25 leading-relaxed mb-4">{rec.description}</p>

        {rec.timeAdvantage !== undefined && rec.timeAdvantage !== 0 && (
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/[0.03] rounded-lg border border-white/[0.05] mb-3">
            <TrendingUp className="w-3 h-3 text-emerald-400/50" />
            <span className="text-xs font-bold text-white/60">
              {rec.timeAdvantage > 0 ? '+' : ''}{typeof rec.timeAdvantage === 'number' ? rec.timeAdvantage.toFixed(1) : rec.timeAdvantage}s
            </span>
          </div>
        )}

        {(rec.targetDriver || rec.threatDriver) && (
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/[0.03] rounded-lg border border-white/[0.05] ml-2">
            <Car className="w-3 h-3 text-white/25" />
            <span className="text-xs text-white/30">{rec.targetDriver || rec.threatDriver}</span>
          </div>
        )}

        {/* Compound Selector */}
        {rec.type === 'pit' && (
          <div className="mb-4">
            <button
              onClick={() => setShowCompoundSelector(!showCompoundSelector)}
              className="w-full flex items-center justify-between p-2.5 bg-white/[0.03] rounded-lg border border-white/[0.05] hover:bg-white/[0.05] transition-colors"
            >
              <span className="text-[10px] text-white/20 uppercase tracking-wider">Tire Compound</span>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold" style={{ color: TIRE_COMPOUNDS.find(t => t.id === selectedCompound)?.color }}>
                  {TIRE_COMPOUNDS.find(t => t.id === selectedCompound)?.name}
                </span>
                {showCompoundSelector ? <ChevronUp className="w-3.5 h-3.5 text-white/25" /> : <ChevronDown className="w-3.5 h-3.5 text-white/25" />}
              </div>
            </button>
            <AnimatePresence>
              {showCompoundSelector && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                  <div className="grid grid-cols-3 gap-1.5 mt-2">
                    {TIRE_COMPOUNDS.map((compound) => (
                      <button
                        key={compound.id}
                        onClick={() => setSelectedCompound(compound.id)}
                        className={`p-2 rounded-lg border transition-all text-center ${
                          selectedCompound === compound.id ? 'border-white/20 bg-white/[0.06]' : 'border-white/[0.05] bg-white/[0.02] hover:bg-white/[0.04]'
                        }`}
                      >
                        <div className="w-3 h-3 rounded-full mx-auto mb-1" style={{ backgroundColor: compound.color }} />
                        <div className="text-[10px] font-bold text-white/50">{compound.name}</div>
                        <div className="text-[9px] text-white/20">~{compound.laps}L</div>
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Action Button */}
        <motion.button
          whileHover={!isExecuting && executionStage !== 'success' ? { scale: 1.01 } : {}}
          whileTap={!isExecuting && executionStage !== 'success' ? { scale: 0.99 } : {}}
          onClick={handleExecuteAction}
          disabled={!isSimulating || isExecuting || executionStage === 'success' || !isConnected}
          className="w-full py-2.5 f1-btn f1-btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {getExecutionButtonContent()}
        </motion.button>
        
        {!isSimulating && <p className="text-center text-[10px] text-white/15 mt-2">Start simulation to execute</p>}

        {/* Probability Analysis */}
        <div className="border-t border-white/[0.06] mt-3 pt-3 space-y-2">
          {/* Probability Breakdown */}
          <div className="p-2.5 bg-white/[0.02] rounded-lg border border-white/[0.04]">
            <div className="flex items-center justify-between mb-2">
              <p className="text-[9px] text-white/20 uppercase tracking-wider flex items-center gap-1.5">
                <BarChart3 className="w-3 h-3" />
                Success Probability
              </p>
              <span className="text-[10px] font-mono font-bold text-white/50">
                {(rec.probability !== undefined ? rec.probability * 100 : rec.confidence !== undefined ? rec.confidence * 100 : 75).toFixed(1)}%
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400/60" />
                <span className="text-[9px] text-white/30">Position Gain</span>
                <span className="text-[10px] font-mono text-emerald-400/70 ml-auto">
                  {rec.positionGainProb !== undefined ? `${(rec.positionGainProb * 100).toFixed(0)}%` : '68%'}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400/60" />
                <span className="text-[9px] text-white/30">Time Benefit</span>
                <span className="text-[10px] font-mono text-blue-400/70 ml-auto">
                  {rec.timeBenefitProb !== undefined ? `${(rec.timeBenefitProb * 100).toFixed(0)}%` : '72%'}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-400/60" />
                <span className="text-[9px] text-white/30">Risk Mitigation</span>
                <span className="text-[10px] font-mono text-amber-400/70 ml-auto">
                  {rec.riskMitigationProb !== undefined ? `${(rec.riskMitigationProb * 100).toFixed(0)}%` : '81%'}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400/60" />
                <span className="text-[9px] text-white/30">Window Optimal</span>
                <span className="text-[10px] font-mono text-purple-400/70 ml-auto">
                  {rec.windowOptimalProb !== undefined ? `${(rec.windowOptimalProb * 100).toFixed(0)}%` : '89%'}
                </span>
              </div>
            </div>
          </div>

          {/* Expected Outcome */}
          {(rec.expectedPositionChange !== undefined || rec.expectedTimeGain !== undefined) && (
            <div className="grid grid-cols-2 gap-2">
              {rec.expectedPositionChange !== undefined && (
                <div className="p-2 bg-white/[0.02] rounded-lg">
                  <p className="text-[8px] text-white/15 uppercase tracking-wider flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    Expected Pos. Change
                  </p>
                  <p className={`text-[11px] font-mono font-medium ${rec.expectedPositionChange > 0 ? 'text-emerald-400/70' : rec.expectedPositionChange < 0 ? 'text-red-400/70' : 'text-white/50'}`}>
                    {rec.expectedPositionChange > 0 ? '+' : ''}{rec.expectedPositionChange} positions
                  </p>
                </div>
              )}
              {rec.expectedTimeGain !== undefined && (
                <div className="p-2 bg-white/[0.02] rounded-lg">
                  <p className="text-[8px] text-white/15 uppercase tracking-wider flex items-center gap-1">
                    <TrendingDown className="w-3 h-3" />
                    Expected Time Gain
                  </p>
                  <p className="text-[11px] font-mono font-medium text-emerald-400/70">
                    -{rec.expectedTimeGain.toFixed(1)}s
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Risk Assessment */}
          <div className="p-2 bg-white/[0.02] rounded-lg">
            <div className="flex items-center justify-between">
              <p className="text-[8px] text-white/15 uppercase tracking-wider flex items-center gap-1">
                <Activity className="w-3 h-3" />
                Risk Assessment
              </p>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                (rec.riskLevel || rec.risk || 'medium') === 'low' ? 'bg-emerald-500/15 text-emerald-400/70' :
                (rec.riskLevel || rec.risk || 'medium') === 'medium' ? 'bg-amber-500/15 text-amber-400/70' :
                'bg-red-500/15 text-red-400/70'
              }`}>
                {(rec.riskLevel || rec.risk || 'Medium').toUpperCase()}
              </span>
            </div>
            {rec.riskFactors && rec.riskFactors.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {rec.riskFactors.map((factor, idx) => (
                  <span key={idx} className="text-[8px] text-white/25 bg-white/[0.03] px-1.5 py-0.5 rounded">
                    {factor}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Player Status */}
          {player && (
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 bg-white/[0.02] rounded-lg">
                <p className="text-[8px] text-white/15 uppercase tracking-wider">Driver</p>
                <div className="flex items-center gap-1.5">
                  <div 
                    className="w-2 h-2 rounded-full" 
                    style={{ backgroundColor: player.teamColor || '#888888' }} 
                  />
                  <p className="text-[11px] text-white/60 font-medium">
                    {player.driverCode || 'YOU'}
                  </p>
                </div>
                <p className="text-[9px] text-white/40">{player.team || 'Player'}</p>
              </div>
              <div className="p-2 bg-white/[0.02] rounded-lg">
                <p className="text-[8px] text-white/15 uppercase tracking-wider">Current Status</p>
                <p className="text-[11px] text-white/60 font-medium">
                  P{player.position} | {player.tire?.toUpperCase()} L{player.tireAge}
                </p>
                <p className="text-[9px] text-white/40">
                  +{typeof player.gapToLeader === 'number' ? player.gapToLeader.toFixed(1) : '0.0'}s to leader
                </p>
              </div>
            </div>
          )}
          {rec.type === 'pit' && (
            <div className="p-2 bg-white/[0.02] rounded-lg border border-white/[0.04]">
              <p className="text-[8px] text-white/15 uppercase tracking-wider mb-1">Pit Strategy</p>
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: TIRE_COMPOUNDS.find(t => t.id === selectedCompound)?.color }} />
                <span className="text-xs text-white/60">Switch to {TIRE_COMPOUNDS.find(t => t.id === selectedCompound)?.name}</span>
              </div>
              {player?.tireAge && (
                <p className="text-[10px] text-white/30 mt-1">Tire at end of window (L{player.tireAge}/{TIRE_COMPOUNDS.find(t => t.id === player.tire)?.laps || 30})</p>
              )}
            </div>
          )}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full flex items-center justify-between text-white/20 hover:text-white/40 transition-colors py-1"
          >
            <span className="text-[10px] uppercase tracking-wider">Full Analysis</span>
            <motion.div animate={{ rotate: showDetails ? 180 : 0 }} transition={{ duration: 0.2 }}>
              <RefreshCw className="w-3 h-3" />
            </motion.div>
          </button>

          <AnimatePresence>
            {showDetails && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                <div className="pt-2 space-y-2">
                  {rec.reason && (
                    <div className="p-3 bg-white/[0.03] rounded-lg border border-white/[0.05]">
                      <p className="text-[9px] text-white/15 uppercase tracking-wider mb-1">Why this works</p>
                      <p className="text-xs text-white/30">{rec.reason}</p>
                    </div>
                  )}
                  {rec.alternatives && rec.alternatives.length > 0 && (
                    <div className="space-y-1.5">
                      <p className="text-[9px] text-white/15 uppercase tracking-wider">Other options</p>
                      {rec.alternatives.map((alt, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-white/[0.03] rounded-lg border border-white/[0.05]">
                          <span className="text-xs text-white/30">{alt.action}</span>
                          <div className="flex items-center gap-2">
                            <span className={`text-[9px] px-1.5 py-0.5 rounded ${
                              alt.risk === 'Extreme' ? 'bg-red-500/15 text-red-400/60' :
                              alt.risk === 'High' ? 'bg-red-500/10 text-red-400/40' :
                              alt.risk === 'Medium' ? 'bg-yellow-500/10 text-yellow-400/40' :
                              'bg-emerald-500/10 text-emerald-400/40'
                            }`}>{alt.risk}</span>
                            <span className={`text-xs font-mono ${alt.gain?.startsWith('+') ? 'text-emerald-400/60' : 'text-red-400/60'}`}>{alt.gain}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {rec.deadline > 0 && (
                    <div className="flex items-center gap-2 text-xs text-white/20">
                      <Clock className="w-3 h-3" />
                      <span>{rec.deadline} laps remaining</span>
                    </div>
                  )}
                  {rec.isSafetyCar && (
                    <div className="flex items-center gap-2 p-2 bg-yellow-500/10 rounded-lg border border-yellow-500/15">
                      <Flag className="w-3 h-3 text-yellow-400/50" />
                      <span className="text-[10px] text-yellow-400/40">SC deployed - Reduced pit time loss</span>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default memo(ActionPanel);
