import React, { useState, useMemo, useCallback, memo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { Play, RotateCcw, Download, Share2, Loader2, Activity, Users, Clock, AlertCircle, AlertTriangle, Radio } from 'lucide-react';

import { useAuth } from '../context/AuthContext';
import { useRace } from '../context/RaceContext';
import { OpenF1Provider } from '../context/OpenF1Context';

// F1 Components
import {
  CommandHeader,
  CircuitSelector,
  StrategyModeSelector,
  StrategyCard,
  SimulationChart,
  TireDegradationChart,
  RiskMeter,
  DecisionPanel,
  LiveSimulationChart,
  RaceTimeline,
  CompetitorPanel,
  ActionPanel,
  StrategyComparisonPanel,
  PredictionEngine,
  PitWindowVisualization,
  RaceDirectorFeed,
  IncidentTracker,
  TrackMapVisualization,
  ReplaySnapshot,
  WeekendSession,
  DriverIntelligence,
  RaceControlCenter,
} from '../components/f1';
import ToastContainer from '../components/notifications/ToastContainer';
import { liveStrategyShape } from '../utils/raceRecommendation';

const API_URL = api.defaults.baseURL;

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { staggerChildren: 0.06, duration: 0.4 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] }
  }
};

// Error boundary fallback
const ErrorFallback = memo(({ error, onRetry }) => (
  <div className="p-6 bg-red-500/[0.08] border border-red-500/20 rounded-2xl">
    <div className="flex items-center gap-3 mb-3">
      <AlertCircle className="w-6 h-6 text-red-400" />
      <h3 className="font-bold text-red-400">Error Loading Dashboard</h3>
    </div>
    <p className="text-sm text-white/40 mb-4">{error?.message || 'Unknown error occurred'}</p>
    <button
      onClick={onRetry}
      className="px-4 py-2 bg-red-500/15 hover:bg-red-500/25 text-red-400 rounded-xl transition-colors text-sm font-medium"
    >
      Retry
    </button>
  </div>
));
ErrorFallback.displayName = 'ErrorFallback';

// Section label component
const SectionLabel = memo(({ children }) => (
  <div className="flex items-center gap-3 mb-4 px-1">
    <span className="w-0.5 h-5 bg-[#e10600] rounded-full" />
    <h2 className="text-sm font-bold text-white/80 uppercase tracking-[0.15em]">{children}</h2>
  </div>
));
SectionLabel.displayName = 'SectionLabel';

const DashboardInner = () => {
  const { user, logout } = useAuth();
  const {
    raceState,
    startRace,
    stopRace,
    wsStatus,
    confidence,
    metrics,
    currentRecommendation,
    strategy,
    confidenceHistory,
  } = useRace();
  
  const [circuit, setCircuit] = useState('monza');
  const [strategyMode, setStrategyMode] = useState('auto');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeTab, setActiveTab] = useState('strategy');

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/simulate', {
        circuit,
        strategy_type: strategyMode === 'auto' ? 'auto' : strategyMode,
        tire_compound: 'soft',
        weather: 'dry'
      });
      setResult(response.data);
      startRace(circuit, response.data.lap_times?.length || 53, {
        type: strategyMode,
        pitStops: response.data.pit_laps || [18, 38],
        nextPitLap: response.data.pit_laps?.[0] || 18,
        compounds: ['soft', 'medium', 'hard'],
      });
    } catch (err) {
      console.error('Simulation error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to run simulation');
      startRace(circuit, 53, {
        type: strategyMode,
        pitStops: [18, 38],
        nextPitLap: 18,
        compounds: ['soft', 'medium', 'hard'],
      });
    } finally {
      setLoading(false);
    }
  }, [circuit, strategyMode, startRace]);

  const resetSimulation = useCallback(() => {
    stopRace();
    setResult(null);
    setError(null);
  }, [stopRace]);

  const chartData = useMemo(() => {
    if (!result?.lap_times || result.lap_times.length === 0) {
      return Array.from({ length: 50 }, (_, i) => ({
        lap: i + 1,
        '1-Stop': 90 + i * 0.1 + Math.sin(i * 0.2) * 0.5,
        '2-Stop': 90.2 + i * 0.08 + Math.sin(i * 0.15) * 0.4,
        'Aggressive': 89.8 + i * 0.12 + Math.sin(i * 0.25) * 0.6,
      }));
    }
    const laps = result.lap_times.length;
    const sc = result.strategy_comparison || {};
    return result.lap_times.map((lt, i) => ({
      lap: i + 1,
      'Optimal': lt,
      ...(sc['1-stop'] ? { '1-Stop': lt + (i < result.pit_laps?.[0] ? 0 : 1.5) } : {}),
      ...(sc['2-stop'] ? { '2-Stop': lt + (i < result.pit_laps?.[0] ? 0.3 : i < result.pit_laps?.[1] ? -0.5 : 1.0) } : {}),
    }));
  }, [result]);

  const tireData = useMemo(() => {
    if (result?.tire_degradation && result.tire_degradation.length > 0) {
      return result.tire_degradation.map((deg, i) => ({
        lap: i + 1,
        'Soft': deg,
        'Medium': deg * 0.7,
        'Hard': deg * 0.4,
      }));
    }
    return Array.from({ length: 50 }, (_, i) => ({
      lap: i + 1,
      'Soft': Math.max(100 - i * 2.5, 0),
      'Medium': Math.max(100 - i * 1.8, 0),
      'Hard': Math.max(100 - i * 1.2, 0),
    }));
  }, [result]);

  const strategyComparisonData = useMemo(() => {
    const sc = result?.strategy_comparison || {};
    const pitLaps = result?.pit_laps || [18, 38];
    const strategies = [];
    if (sc['1-stop']) strategies.push({ type: 'conservative', race_time: sc['1-stop'].predicted_time || 5250, advantage: 2.1, risk: 35, pit_stops: pitLaps.slice(0, 1), fuel_usage: 92 });
    if (sc['2-stop']) strategies.push({ type: 'ai_rl', race_time: sc['2-stop'].predicted_time || 5220, advantage: 0, risk: 50, pit_stops: pitLaps.slice(0, 2), fuel_usage: 95 });
    if (sc['3-stop'] || sc.aggressive) strategies.push({ type: 'aggressive', race_time: sc['3-stop']?.predicted_time || sc.aggressive?.predicted_time || 5200, advantage: -2.3, risk: 75, pit_stops: pitLaps.slice(0, 3), fuel_usage: 98 });
    return strategies.length >= 2 ? strategies : [
      { type: 'aggressive', race_time: 5200, advantage: -2.3, risk: 75, pit_stops: [16, 36], fuel_usage: 98 },
      { type: 'conservative', race_time: 5250, advantage: 2.1, risk: 35, pit_stops: [22, 42], fuel_usage: 92 },
      { type: 'ai_rl', race_time: 5220, advantage: 0, risk: 50, pit_stops: [18, 38], fuel_usage: 95 },
    ];
  }, [result]);

  const bestStrategy = useMemo(() => {
    if (result?.best_strategy && result?.total_time) {
      return {
        name: result.best_strategy,
        race_time: result.total_time,
        pit_laps: result.pit_laps || [],
        tires_used: result.tires_used || [],
        explanation: result.explanation || '',
        advantage: 0,
      };
    }
    return strategyComparisonData.find(s => s.type === 'ai_rl') || strategyComparisonData[0];
  }, [result, strategyComparisonData]);

  const riskFactors = useMemo(() => result?.risk_factors || [
    { name: 'Tire Wear', impact: 40 },
    { name: 'Weather', impact: 25 },
    { name: 'Traffic', impact: 35 },
  ], [result]);
  const pitStops = useMemo(() => result?.pit_laps || bestStrategy?.pit_laps || [18, 38], [result, bestStrategy]);

  const strategyForCard = useMemo(() => {
    if (raceState.isRunning && raceState.currentLap >= 1 && currentRecommendation) {
      return liveStrategyShape({
        currentRecommendation,
        strategy,
        raceState,
        metrics,
        confidence,
      });
    }
    return {
      type: bestStrategy?.type || bestStrategy?.name || 'strategy',
      predicted_time: bestStrategy?.race_time,
      pit_stops: pitStops,
      advantage: bestStrategy?.advantage ?? 0,
      risk: bestStrategy?.risk ?? 50,
    };
  }, [raceState, currentRecommendation, strategy, metrics, confidence, bestStrategy, pitStops]);

  const displayConfidence = useMemo(() => {
    if (raceState.isRunning && confidence?.overall != null) {
      const o = confidence.overall;
      return o > 1 ? Math.round(o) : Math.round(o * 100);
    }
    return result?.confidence ?? 87;
  }, [raceState.isRunning, confidence, result?.confidence]);

  const displayRiskFactors = useMemo(() => {
    const b = metrics?.risk_breakdown;
    if (raceState.isRunning && b && typeof b === 'object') {
      const rows = [
        { name: 'Tire wear', impact: Math.min(100, Math.round((b.tire_wear_risk || 0) * 100)) },
        { name: 'Weather', impact: Math.min(100, Math.round((b.weather_risk || 0) * 100)) },
        { name: 'Traffic', impact: Math.min(100, Math.round((b.traffic_risk || 0) * 100)) },
        { name: 'Pit window', impact: Math.min(100, Math.round((b.pit_window_risk || 0) * 100)) },
      ].filter((f) => f.impact > 2);
      if (rows.length) return rows;
    }
    return riskFactors;
  }, [raceState.isRunning, metrics, riskFactors]);

  const displayRiskLevel = useMemo(() => {
    if (raceState.isRunning && metrics?.risk_score != null) {
      const r = metrics.risk_score;
      return r > 1 ? Math.round(r) : Math.round(r * 100);
    }
    return result?.risk_level ?? 35;
  }, [raceState.isRunning, metrics, result?.risk_level]);

  const confidenceTrend = useMemo(() => {
    if (!confidenceHistory?.length) return null;
    return confidenceHistory.map((h) => {
      const o = h.overall;
      return o > 1 ? o : o * 100;
    });
  }, [confidenceHistory]);

  const liveWhyStrategy = useMemo(() => {
    if (raceState.isRunning && currentRecommendation?.explanation) {
      return currentRecommendation.explanation;
    }
    return result?.explanation || 'AI analysis shows this strategy optimizes tire windows and minimizes time loss in traffic.';
  }, [raceState.isRunning, currentRecommendation, result?.explanation]);

  const liveDecisionTitle = useMemo(() => {
    if (raceState.isRunning && currentRecommendation?.action_name) {
      return String(currentRecommendation.action_name).replace(/_/g, ' ');
    }
    return result?.recommendation || null;
  }, [raceState.isRunning, currentRecommendation, result?.recommendation]);

  const decisionWhyPoints = useMemo(() => {
    if (!raceState.isRunning || !confidence?.breakdown) return null;
    const b = confidence.breakdown;
    const lines = [];
    if (b.model_confidence != null) lines.push(`Model confidence ${(b.model_confidence * 100).toFixed(0)}%`);
    if (b.tire_certainty != null) lines.push(`Tire certainty ${(b.tire_certainty * 100).toFixed(0)}%`);
    if (b.weather_stability != null) lines.push(`Weather stability ${(b.weather_stability * 100).toFixed(0)}%`);
    if (b.model_agreement != null) lines.push(`Strategy heuristic agreement ${(b.model_agreement * 100).toFixed(0)}%`);
    return lines.length ? lines : null;
  }, [raceState.isRunning, confidence]);

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Background effects */}
      <div className="fixed inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:80px_80px] pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(225,6,0,0.06)_0%,transparent_60%)] pointer-events-none" />
      
      <ToastContainer />
      
      {/* Header */}
      <CommandHeader 
        user={{ name: user?.username || 'Race Engineer', role: user?.role || 'Engineer' }} 
        status={wsStatus || 'disconnected'} 
        onLogout={logout}
      />

      {/* Safety Car Banner */}
      <AnimatePresence>
        {raceState.safetyCarActive && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-yellow-500 text-black px-4 py-2.5 flex items-center justify-center gap-3 font-bold uppercase tracking-[0.2em] overflow-hidden shadow-[0_0_30px_rgba(234,179,8,0.3)] relative z-10"
          >
            <AlertTriangle className="w-5 h-5 animate-pulse" />
            Safety Car Deployed
            <AlertTriangle className="w-5 h-5 animate-pulse" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="relative z-10 p-4 md:p-6">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-4 mb-6 border-b border-white/[0.06] pb-0 max-w-[1920px] mx-auto">
          <button 
            onClick={() => setActiveTab('strategy')} 
            className={`px-6 py-3 text-sm font-bold uppercase tracking-wider transition-colors border-b-2 ${
              activeTab === 'strategy' 
                ? 'text-white border-[#e10600]' 
                : 'text-white/40 border-transparent hover:text-white/70'
            }`}
          >
            Strategy Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('race_control')} 
            className={`px-6 py-3 text-sm font-bold uppercase tracking-wider transition-colors border-b-2 ${
              activeTab === 'race_control' 
                ? 'text-white border-emerald-500' 
                : 'text-white/40 border-transparent hover:text-white/70'
            }`}
          >
            Race Control Center
          </button>
        </div>

        {activeTab === 'strategy' ? (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-5 max-w-[1920px] mx-auto"
          >
            {/* LEFT PANEL */}
          <motion.div variants={itemVariants} className="lg:col-span-3 space-y-4 md:space-y-5">
            {/* Race Setup */}
            <div className="f1-card">
              <div className="p-5">
                <SectionLabel>Race Setup</SectionLabel>
                <div className="space-y-4">
                  <CircuitSelector selected={circuit} onSelect={setCircuit} />
                  <StrategyModeSelector selected={strategyMode} onSelect={setStrategyMode} />
                  
                  {/* Simulate Button */}
                  <motion.button
                    whileHover={!loading && !raceState.isRunning ? { scale: 1.01 } : {}}
                    whileTap={!loading && !raceState.isRunning ? { scale: 0.99 } : {}}
                    onClick={runSimulation}
                    disabled={loading || raceState.isRunning}
                    className="f1-btn f1-btn-primary w-full"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Simulating...
                      </>
                    ) : raceState.isRunning ? (
                      <>
                        <Activity className="w-4 h-4 animate-pulse" />
                        Race In Progress
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        Run Simulation
                      </>
                    )}
                  </motion.button>
                  
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-3 bg-yellow-500/[0.08] border border-yellow-500/20 rounded-xl text-sm text-yellow-300"
                    >
                      <p className="font-semibold text-yellow-400">Running with local data</p>
                      <p className="text-xs text-yellow-400/60 mt-1">{error}</p>
                    </motion.div>
                  )}
                </div>
              </div>
            </div>

            {/* Race Timeline */}
            <RaceTimeline />

            {/* Quick Actions */}
            <div className="f1-card">
              <div className="p-4">
                <div className="flex items-center gap-3 mb-3 px-1">
                  <span className="f1-label">Quick Actions</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <motion.button 
                    onClick={resetSimulation}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    className="p-3 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] hover:border-white/[0.12] rounded-xl transition-all flex flex-col items-center gap-1.5 group"
                  >
                    <RotateCcw className="w-4 h-4 text-white/30 group-hover:text-white/60 transition-colors" />
                    <span className="text-[10px] text-white/30 group-hover:text-white/50 transition-colors font-semibold uppercase tracking-wider">Reset</span>
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    className="p-3 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] hover:border-white/[0.12] rounded-xl transition-all flex flex-col items-center gap-1.5 group"
                  >
                    <Download className="w-4 h-4 text-white/30 group-hover:text-white/60 transition-colors" />
                    <span className="text-[10px] text-white/30 group-hover:text-white/50 transition-colors font-semibold uppercase tracking-wider">Export</span>
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    className="p-3 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] hover:border-white/[0.12] rounded-xl transition-all flex flex-col items-center gap-1.5 group"
                  >
                    <Share2 className="w-4 h-4 text-white/30 group-hover:text-white/60 transition-colors" />
                    <span className="text-[10px] text-white/30 group-hover:text-white/50 transition-colors font-semibold uppercase tracking-wider">Share</span>
                  </motion.button>
                </div>
              </div>
            </div>

            {/* Pit Window */}
            <PitWindowVisualization />
            
            {/* Race Director Feed */}
            <RaceDirectorFeed />
            
            {/* Incident Tracker */}
            <IncidentTracker />
          </motion.div>

          {/* CENTER PANEL */}
          <motion.div variants={itemVariants} className="lg:col-span-6 space-y-4 md:space-y-5">
            {/* Live Chart */}
            <div className="f1-card">
              <LiveSimulationChart />
            </div>
            
            {/* Strategy Comparison */}
            <div className="f1-card">
              <StrategyComparisonPanel strategies={strategyComparisonData} />
            </div>
            
            {/* Simulation Chart */}
            <div className="f1-card">
              <SimulationChart 
                data={chartData} 
                strategies={result?.all_strategies || strategyComparisonData}
                pitStops={pitStops}
              />
            </div>
            
            {/* Tire Degradation */}
            <div className="f1-card">
              <TireDegradationChart 
                tireData={tireData}
                pitStops={pitStops.map(lap => ({ lap }))}
              />
            </div>
            
            {/* Track Map Visualization */}
            <div className="f1-card">
              <TrackMapVisualization />
            </div>
          </motion.div>

          {/* RIGHT PANEL */}
          <motion.div variants={itemVariants} className="lg:col-span-3 space-y-4 md:space-y-5">
            {/* Action Panel */}
            <ActionPanel />

            {/* Prediction Engine */}
            <div className="f1-card">
              <PredictionEngine />
            </div>

            {/* Best Strategy Card */}
            <StrategyCard
              strategy={strategyForCard}
              confidence={displayConfidence}
              timeGain={strategyForCard?.advantage ?? bestStrategy?.advantage ?? 0}
              isBest={true}
              alternatives={strategyComparisonData.slice(1)}
              riskFactors={displayRiskFactors}
              whyThisStrategy={liveWhyStrategy}
              confidenceTrend={confidenceTrend}
            />

            {/* Competitor Panel */}
            <CompetitorPanel />

            {/* Risk Assessment */}
            <RiskMeter 
              riskLevel={displayRiskLevel}
              factors={displayRiskFactors}
            />

            {/* AI Decision Panel */}
            <DecisionPanel
              decision={liveDecisionTitle || "Execute optimal pit strategy with undercut opportunity"}
              explanation={currentRecommendation?.explanation || result?.explanation || "Analysis shows clear tire advantage window opening"}
              alternatives={result?.alternatives?.map((alt, idx) => ({
                name: alt.type || `Alternative ${idx + 1}`,
                delta: alt.delta || 0,
              }))}
              confidence={displayConfidence}
              whyPoints={decisionWhyPoints || undefined}
            />
            
            {/* Replay Snapshots */}
            <ReplaySnapshot />
            
            {/* Driver Intelligence */}
            <DriverIntelligence />
          </motion.div>
        </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-[1920px] mx-auto"
          >
            <RaceControlCenter />
          </motion.div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/[0.06] px-4 md:px-6 py-3 bg-[#050505]/80 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row items-center justify-between text-[11px] text-white/25 gap-2">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <Radio className="w-3 h-3 text-[#e10600]/60" />
              API: {API_URL}
            </span>
            <span className="w-1 h-1 bg-white/10 rounded-full" />
            <span>v6.3</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <motion.div
                animate={{ scale: [1, 1.3, 1], opacity: [1, 0.5, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
              >
                <Activity className="w-3 h-3 text-emerald-400/60" />
              </motion.div>
              ML Active
            </span>
            <span className="w-1 h-1 bg-white/10 rounded-full" />
            <span className="flex items-center gap-1.5">
              <Users className="w-3 h-3" />
              {user?.role || 'Engineer'}
            </span>
            <span className="w-1 h-1 bg-white/10 rounded-full" />
            <span className="flex items-center gap-1.5">
              <Clock className="w-3 h-3" />
              {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

const Dashboard = () => (
  <OpenF1Provider>
    <DashboardInner />
  </OpenF1Provider>
);

export default memo(Dashboard);
