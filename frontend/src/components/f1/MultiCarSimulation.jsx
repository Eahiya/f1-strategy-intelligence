import React, { useState, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Flag, Loader2, AlertCircle, Car, ChevronDown,
  Activity, TrendingUp, BarChart3, Zap, Target, Users,
  RefreshCw, WifiOff, ServerOff, Shield, Clock
} from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { simulationApi } from '../../services/api';

const CircuitOptions = [
  { id: 'monza', name: 'Monza', laps: 53 },
  { id: 'spa', name: 'Spa-Francorchamps', laps: 44 },
  { id: 'silverstone', name: 'Silverstone', laps: 52 },
  { id: 'red_bull_ring', name: 'Red Bull Ring', laps: 71 },
  { id: 'interlagos', name: 'Interlagos', laps: 71 },
  { id: 'suzuka', name: 'Suzuka', laps: 53 },
];

const PositionBadge = ({ pos }) => {
  if (pos === 1) return <span className="px-1.5 py-0.5 text-[10px] font-black bg-amber-400/15 text-amber-400 rounded">P1</span>;
  if (pos === 2) return <span className="px-1.5 py-0.5 text-[10px] font-black bg-gray-400/15 text-gray-400 rounded">P2</span>;
  if (pos === 3) return <span className="px-1.5 py-0.5 text-[10px] font-black bg-orange-400/15 text-orange-400 rounded">P3</span>;
  return <span className="px-1.5 py-0.5 text-[10px] font-mono text-white/50 rounded">P{pos}</span>;
};

const TireBadge = ({ compound }) => {
  const colors = {
    soft: 'bg-red-500/15 text-red-400 border-red-500/20',
    medium: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
    hard: 'bg-white/15 text-white/40 border-white/20',
    intermediate: 'bg-green-500/15 text-green-400 border-green-500/20',
    wet: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  };
  return (
    <span className={`px-1.5 py-0.5 text-[9px] font-bold uppercase border rounded ${colors[compound?.toLowerCase()] || colors.medium}`}>
      {compound}
    </span>
  );
};

const StandingsRow = ({ driver, index }) => (
  <motion.div
    initial={{ opacity: 0, x: -16 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: index * 0.05, duration: 0.3 }}
    className="flex items-center gap-3 p-2.5 bg-white/[0.02] hover:bg-white/[0.04] rounded-lg transition-colors"
  >
    <PositionBadge pos={driver.position} />
    <div className="flex-1 min-w-0">
      <p className="text-sm font-semibold text-white/80 truncate">{driver.name}</p>
      <p className="text-[10px] text-white/30 truncate">{driver.team}</p>
    </div>
    <div className="flex items-center gap-2">
      <TireBadge compound={driver.tire || driver.tire_compound} />
      <span className="text-[11px] font-mono text-white/50 w-16 text-right">
        {driver.gap_to_leader > 0 ? `+${driver.gap_to_leader.toFixed(3)}` : 'LEADER'}
      </span>
    </div>
  </motion.div>
);

// Error type detection helper
const getErrorType = (error) => {
  if (!error) return null;
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) return 'timeout';
  if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) return 'network';
  if (error.response?.status === 401 || error.response?.status === 403) return 'auth';
  if (error.response?.status >= 500) return 'server';
  return 'unknown';
};

const ErrorDisplay = ({ error, onRetry }) => {
  const errorType = getErrorType(error);

  const errorConfig = {
    timeout: { icon: Clock, title: 'Request Timeout', color: 'text-yellow-400', bg: 'bg-yellow-500/[0.08]', border: 'border-yellow-500/20' },
    network: { icon: WifiOff, title: 'Network Error', color: 'text-red-400', bg: 'bg-red-500/[0.08]', border: 'border-red-500/20' },
    auth: { icon: Shield, title: 'Authentication Failed', color: 'text-orange-400', bg: 'bg-orange-500/[0.08]', border: 'border-orange-500/20' },
    server: { icon: ServerOff, title: 'Server Error', color: 'text-red-400', bg: 'bg-red-500/[0.08]', border: 'border-red-500/20' },
    unknown: { icon: AlertCircle, title: 'Error', color: 'text-red-400', bg: 'bg-red-500/[0.08]', border: 'border-red-500/20' },
  };

  const config = errorConfig[errorType] || errorConfig.unknown;
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 ${config.bg} border ${config.border} rounded-xl`}
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${config.color} mt-0.5 shrink-0`} />
        <div className="flex-1">
          <p className={`text-sm font-semibold ${config.color}`}>{config.title}</p>
          <p className="text-xs text-white/40 mt-1">
            {error?.response?.data?.detail || error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={onRetry}
            className="mt-3 flex items-center gap-2 px-3 py-1.5 bg-white/[0.06] hover:bg-white/[0.1] rounded-lg transition-colors text-xs text-white/60"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export const MultiCarSimulation = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [circuit, setCircuit] = useState('monza');
  const [numCars, setNumCars] = useState(10);
  const [retryCount, setRetryCount] = useState(0);
  const [activeTab, setActiveTab] = useState('standings'); // standings | analytics | overtakes

  const runSimulation = useCallback(async (isRetry = false) => {
    setLoading(true);
    if (!isRetry) {
      setError(null);
      setResults(null);
      setRetryCount(0);
    }

    try {
      // Add timeout and better error handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const response = await simulationApi.multiCar({
        circuit,
        num_cars: numCars,
        weather: 'dry',
      }, { signal: controller.signal });

      clearTimeout(timeoutId);
      setResults(response.data);
      setError(null);
      setRetryCount(0);
    } catch (err) {
      console.error('Multi-car simulation error:', err);
      setError(err);

      // Auto-retry on network errors (max 3 retries)
      if (getErrorType(err) === 'network' && retryCount < 3) {
        setRetryCount(prev => prev + 1);
        setTimeout(() => runSimulation(true), 2000 * (retryCount + 1));
      }
    } finally {
      setLoading(false);
    }
  }, [circuit, numCars, retryCount]);

  // Sorted final standings (safe even if field is missing)
  const sortedResults = useMemo(() => {
    if (!results?.final_standings) return [];
    return [...results.final_standings].sort(
      (a, b) => (a.position ?? 99) - (b.position ?? 99)
    );
  }, [results]);

  // Analytics data processing
  const analyticsData = useMemo(() => {
    if (!results?.final_standings) return null;

    const standings = results.final_standings;

    // Position history chart data (mock - would come from backend lap_history)
    const positionHistory = standings.map((driver, idx) => ({
      name: driver.name?.split(' ').pop() || `D${idx}`,
      position: driver.position,
      gap: driver.gap_to_leader || 0,
    }));

    // Gap analysis
    const gapData = standings.slice(0, 5).map((driver, idx) => ({
      position: driver.position,
      gap: driver.gap_to_leader || 0,
      name: driver.name?.split(' ').pop() || `D${idx}`,
    }));

    // Overtake statistics
    const overtakeStats = results.overtake_log ? {
      total: results.total_overtakes || 0,
      byLap: results.overtake_log.reduce((acc, overtake) => {
        acc[overtake.lap] = (acc[overtake.lap] || 0) + 1;
        return acc;
      }, {}),
    } : { total: 0, byLap: {} };

    return { positionHistory, gapData, overtakeStats };
  }, [results]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 px-1">
        <Car className="w-4 h-4 text-purple-400" />
        <h3 className="text-sm font-bold text-white/80 uppercase tracking-[0.15em]">Multi-Car Simulation</h3>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Circuit</label>
          <div className="relative">
            <select
              value={circuit}
              onChange={(e) => setCircuit(e.target.value)}
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2.5 text-white text-sm appearance-none cursor-pointer focus:outline-none focus:border-[#e10600]/50"
            >
              {CircuitOptions.map((c) => (
                <option key={c.id} value={c.id} className="bg-[#0a0a0a] text-white">{c.name}</option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-white/30 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Grid Size</label>
          <select
            value={numCars}
            onChange={(e) => setNumCars(parseInt(e.target.value))}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2.5 text-white text-sm appearance-none cursor-pointer focus:outline-none focus:border-[#e10600]/50"
          >
            {[5, 10, 15, 20].map((n) => (
              <option key={n} value={n} className="bg-[#0a0a0a] text-white">{n} Cars</option>
            ))}
          </select>
        </div>
      </div>

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={() => runSimulation(false)}
        disabled={loading}
        className="w-full f1-btn f1-btn-primary"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            {retryCount > 0 ? `Retrying (${retryCount}/3)...` : 'Simulating Race...'}
          </>
        ) : (
          <>
            <Flag className="w-4 h-4" />
            Start Race
          </>
        )}
      </motion.button>

      {error && <ErrorDisplay error={error} onRetry={() => runSimulation(false)} />}

      {results && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          <div className="grid grid-cols-3 gap-2">
            <div className="p-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-center">
              <p className="text-lg font-bold text-white/80">{results.total_overtakes || 0}</p>
              <p className="text-[9px] text-white/30 uppercase tracking-[0.1em]">Overtakes</p>
            </div>
            <div className="p-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-center">
              <p className="text-lg font-bold text-white/80">{results.total_laps}</p>
              <p className="text-[9px] text-white/30 uppercase tracking-[0.1em]">Laps</p>
            </div>
            <div className="p-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-center">
              <p className="text-lg font-bold text-white/80">{sortedResults.length}</p>
              <p className="text-[9px] text-white/30 uppercase tracking-[0.1em]">Finished</p>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1 p-1 bg-white/[0.03] rounded-lg">
            {[
              { id: 'standings', icon: Users, label: 'Standings' },
              { id: 'analytics', icon: BarChart3, label: 'Analytics' },
              { id: 'overtakes', icon: Zap, label: 'Overtakes' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-md transition-all text-[10px] font-medium uppercase tracking-wider ${activeTab === tab.id
                    ? 'bg-white/[0.08] text-white/70'
                    : 'text-white/30 hover:text-white/50'
                  }`}
              >
                <tab.icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Standings Tab */}
          {activeTab === 'standings' && (
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {sortedResults.map((driver, i) => (
                <StandingsRow key={driver.id || i} driver={driver} index={i} />
              ))}
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && analyticsData && (
            <div className="space-y-3">
              {/* Gap to Leader Chart */}
              <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400/60" />
                  <p className="text-[10px] font-bold text-white/40 uppercase tracking-wider">Gap to Leader</p>
                </div>
                <div className="h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analyticsData.gapData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis dataKey="position" stroke="rgba(255,255,255,0.1)" fontSize={9} tickLine={false} />
                      <YAxis stroke="rgba(255,255,255,0.1)" fontSize={9} tickLine={false} tickFormatter={(v) => `${v}s`} />
                      <Tooltip
                        contentStyle={{ background: '#0c0c0c', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', fontSize: '11px' }}
                        formatter={(value) => [`${value.toFixed(2)}s`, 'Gap']}
                      />
                      <Bar dataKey="gap" fill="rgba(16, 185, 129, 0.5)" stroke="rgba(16, 185, 129, 0.8)" strokeWidth={1} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Race Statistics */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-white/[0.02] border border-white/[0.06] rounded-xl">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Target className="w-3 h-3 text-blue-400/60" />
                    <span className="text-[9px] text-white/30 uppercase">Avg Gap</span>
                  </div>
                  <p className="text-sm font-bold text-white/60 font-mono">
                    {analyticsData.gapData.length > 0
                      ? (analyticsData.gapData.reduce((a, b) => a + b.gap, 0) / analyticsData.gapData.length).toFixed(1)
                      : '0.0'}s
                  </p>
                </div>
                <div className="p-2.5 bg-white/[0.02] border border-white/[0.06] rounded-xl">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Activity className="w-3 h-3 text-purple-400/60" />
                    <span className="text-[9px] text-white/30 uppercase">Overtakes</span>
                  </div>
                  <p className="text-sm font-bold text-white/60 font-mono">
                    {analyticsData.overtakeStats.total}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Overtakes Tab */}
          {activeTab === 'overtakes' && (
            <div className="space-y-3">
              {results.overtake_log && results.overtake_log.length > 0 ? (
                <>
                  {/* Overtake Summary */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="p-2.5 bg-white/[0.02] border border-white/[0.06] rounded-xl text-center">
                      <p className="text-lg font-bold text-purple-400/80">{results.total_overtakes || 0}</p>
                      <p className="text-[9px] text-white/30 uppercase">Total</p>
                    </div>
                    <div className="p-2.5 bg-white/[0.02] border border-white/[0.06] rounded-xl text-center">
                      <p className="text-lg font-bold text-emerald-400/80">
                        {Math.round((results.total_overtakes || 0) / results.total_laps * 10) / 10}
                      </p>
                      <p className="text-[9px] text-white/30 uppercase">Per Lap</p>
                    </div>
                    <div className="p-2.5 bg-white/[0.02] border border-white/[0.06] rounded-xl text-center">
                      <p className="text-lg font-bold text-amber-400/80">
                        {results.overtake_log.filter(o => o.success).length}
                      </p>
                      <p className="text-[9px] text-white/30 uppercase">Successful</p>
                    </div>
                  </div>

                  {/* Overtake Log */}
                  <div className="p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl max-h-48 overflow-y-auto">
                    <p className="text-[10px] font-bold text-white/40 uppercase tracking-[0.15em] mb-2">Overtake Log</p>
                    <div className="space-y-1.5">
                      {results.overtake_log.slice(0, 10).map((overtake, i) => (
                        <div key={i} className="flex items-center gap-2 text-[11px] p-1.5 bg-white/[0.02] rounded">
                          <div className={`w-1.5 h-1.5 rounded-full ${overtake.success ? 'bg-emerald-400/60' : 'bg-red-400/40'}`} />
                          <span className="text-white/30 w-8">L{overtake.lap}</span>
                          <span className="text-white/50">{overtake.attacker || overtake.driver || 'Driver'}</span>
                          <span className="text-white/20">→</span>
                          <span className="text-white/70">{overtake.defender || overtake.target || 'Target'}</span>
                          {overtake.location && <span className="text-white/10 text-[9px] ml-auto">{overtake.location}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center">
                  <Zap className="w-8 h-8 text-white/10 mx-auto mb-2" />
                  <p className="text-sm text-white/30">No overtakes recorded</p>
                  <p className="text-xs text-white/20 mt-1">The race may have been too clean!</p>
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default MultiCarSimulation;
