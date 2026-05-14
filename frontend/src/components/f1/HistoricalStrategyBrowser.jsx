import React, { useState, useCallback, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Clock, ChevronDown, Loader2, AlertCircle, Award,
  Timer, TrendingUp, Repeat2, WifiOff
} from 'lucide-react';
import { fastf1Api } from '../../services/api';

const CIRCUIT_OPTIONS = [
  { id: 'monza',        name: 'Monza' },
  { id: 'spa',          name: 'Spa-Francorchamps' },
  { id: 'silverstone',  name: 'Silverstone' },
  { id: 'red_bull_ring',name: 'Red Bull Ring' },
  { id: 'interlagos',   name: 'Interlagos' },
  { id: 'suzuka',       name: 'Suzuka' },
  { id: 'bahrain',      name: 'Bahrain' },
  { id: 'jeddah',       name: 'Jeddah' },
  { id: 'miami',        name: 'Miami' },
  { id: 'barcelona',    name: 'Barcelona' },
  { id: 'monaco',       name: 'Monaco' },
  { id: 'zandvoort',    name: 'Zandvoort' },
  { id: 'singapore',    name: 'Singapore' },
  { id: 'abu_dhabi',    name: 'Abu Dhabi' },
];

const COMPOUND_COLORS = {
  soft:         'bg-red-500/15 text-red-400 border-red-500/20',
  medium:       'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  hard:         'bg-white/15 text-white/40 border-white/20',
  intermediate: 'bg-green-500/15 text-green-400 border-green-500/20',
  wet:          'bg-blue-500/15 text-blue-400 border-blue-500/20',
};

const TireTag = ({ compound }) => {
  const key = compound?.toLowerCase() || '';
  return (
    <span className={`px-1.5 py-0.5 text-[9px] font-bold uppercase border rounded ${COMPOUND_COLORS[key] || 'bg-white/10 text-white/50 border-white/10'}`}>
      {compound || '?'}
    </span>
  );
};

const StatChip = ({ icon: Icon, label, value, color = 'text-white/60' }) => (
  <div className="flex items-center gap-1.5 px-2 py-1 bg-white/[0.03] rounded-lg">
    <Icon className={`w-3 h-3 ${color} shrink-0`} />
    <span className="text-[9px] text-white/30 uppercase tracking-wider">{label}</span>
    <span className={`text-[11px] font-mono font-bold ml-0.5 ${color}`}>{value}</span>
  </div>
);

// Shows elapsed seconds while loading
const ElapsedTimer = ({ running }) => {
  const [secs, setSecs] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    if (running) {
      setSecs(0);
      ref.current = setInterval(() => setSecs(s => s + 1), 1000);
    } else {
      clearInterval(ref.current);
    }
    return () => clearInterval(ref.current);
  }, [running]);

  if (!running) return null;
  return (
    <span className="text-[10px] font-mono text-white/30 ml-1">
      {secs}s
    </span>
  );
};

export const HistoricalStrategyBrowser = () => {
  const [circuit, setCircuit]           = useState('monza');
  const [selectedYears, setSelectedYears] = useState('2023');
  const [loading, setLoading]           = useState(false);
  const [data, setData]                 = useState(null);
  const [error, setError]               = useState(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const response = await fastf1Api.historicalStrategies(circuit, selectedYears);
      setData(response.data);
    } catch (err) {
      const status = err.response?.status;
      if (status === 504 || err.code === 'ECONNABORTED') {
        setError(
          'FastF1 timed out loading this data. ' +
          'First-time fetches can take 60–90 s while the session is downloaded. ' +
          'Try fetching a single year (e.g. 2023) or try again — subsequent fetches use the local cache and are fast.'
        );
      } else {
        setError(
          err.response?.data?.detail ||
          err.message ||
          'Failed to fetch historical data'
        );
      }
    } finally {
      setLoading(false);
    }
  }, [circuit, selectedYears]);

  const strategies = data?.strategies || [];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 px-1">
        <Clock className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-bold text-white/80 uppercase tracking-[0.15em]">Historical Strategies</h3>
        {data && (
          <span className="ml-auto text-[9px] text-emerald-400/60 bg-emerald-500/10 px-1.5 py-0.5 rounded font-mono uppercase">
            FastF1
          </span>
        )}
      </div>

      {/* Controls */}
      <div className="grid grid-cols-2 gap-3">
        {/* Circuit */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Circuit</label>
          <div className="relative">
            <select
              value={circuit}
              onChange={e => setCircuit(e.target.value)}
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2.5 text-white text-sm appearance-none cursor-pointer focus:outline-none focus:border-[#e10600]/50"
            >
              {CIRCUIT_OPTIONS.map(c => (
                <option key={c.id} value={c.id} className="bg-[#0a0a0a] text-white">{c.name}</option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-white/30 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* Season(s) */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Seasons</label>
          <div className="relative">
            <select
              value={selectedYears}
              onChange={e => setSelectedYears(e.target.value)}
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2.5 text-white text-sm appearance-none cursor-pointer focus:outline-none focus:border-[#e10600]/50"
            >
              <option value="2024"          className="bg-[#0a0a0a] text-white">2024 only</option>
              <option value="2023"          className="bg-[#0a0a0a] text-white">2023 only</option>
              <option value="2022"          className="bg-[#0a0a0a] text-white">2022 only</option>
              <option value="2023,2024"     className="bg-[#0a0a0a] text-white">2023 – 2024</option>
              <option value="2022,2023,2024"className="bg-[#0a0a0a] text-white">2022 – 2024</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-white/30 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Fetch button */}
      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={fetchHistory}
        disabled={loading}
        className="w-full f1-btn f1-btn-primary"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Fetching from FastF1…
            <ElapsedTimer running={loading} />
          </>
        ) : (
          <>
            <Award className="w-4 h-4" />
            Load Historical Data
          </>
        )}
      </motion.button>

      {/* Slow-fetch hint */}
      {loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-3 bg-amber-500/[0.06] border border-amber-500/20 rounded-xl"
        >
          <p className="text-[11px] text-amber-400/70 leading-relaxed">
            ⏳ FastF1 downloads full session data on first fetch. This can take
            30–90 s depending on the season. Cached seasons are instant.
          </p>
        </motion.div>
      )}

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-3 bg-red-500/[0.08] border border-red-500/20 rounded-xl"
        >
          <div className="flex items-start gap-2">
            {error.includes('timed out') ? (
              <WifiOff className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            )}
            <p className="text-xs text-red-300 leading-relaxed">{error}</p>
          </div>
        </motion.div>
      )}

      {/* Empty state */}
      {data && strategies.length === 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-6 text-center">
          <Clock className="w-8 h-8 text-white/10 mx-auto mb-2" />
          <p className="text-sm text-white/30">No historical data available for this circuit/years</p>
          <p className="text-xs text-white/20 mt-1">FastF1 may not have this event in its database.</p>
        </motion.div>
      )}

      {/* Results */}
      {strategies.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
          <p className="text-[10px] text-white/25 px-1">
            {strategies.length} race{strategies.length > 1 ? 's' : ''} found
          </p>

          {strategies.map((race, i) => {
            const stints = Array.isArray(race.strategy) ? race.strategy : [];
            return (
              <div
                key={i}
                className="p-3 bg-white/[0.03] border border-white/[0.06] rounded-xl space-y-2.5"
              >
                {/* Title row */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-white/70">
                    {race.year} · {race.name || circuit}
                  </span>
                  {race.winner && (
                    <span className="flex items-center gap-1 text-[10px] text-amber-400 font-bold">
                      <Award className="w-3 h-3" />
                      {race.winner}
                    </span>
                  )}
                </div>

                {/* Stint / strategy timeline */}
                {stints.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {stints.map((stop, j) => (
                      <div key={j} className="flex items-center gap-1 px-2 py-1 bg-white/[0.04] rounded-lg">
                        <TireTag compound={stop.compound} />
                        <span className="text-[10px] text-white/35 font-mono">L{stop.lap}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Stats chips */}
                <div className="flex items-center gap-2 flex-wrap">
                  {race.num_pit_stops !== undefined && (
                    <StatChip
                      icon={Repeat2}
                      label="Stops"
                      value={race.num_pit_stops}
                      color="text-purple-400/80"
                    />
                  )}
                  {race.avg_pace > 0 && (
                    <StatChip
                      icon={TrendingUp}
                      label="Avg lap"
                      value={`${race.avg_pace.toFixed(2)}s`}
                      color="text-emerald-400/80"
                    />
                  )}
                  {race.total_time && (
                    <StatChip
                      icon={Timer}
                      label="Est. time"
                      value={race.total_time}
                      color="text-sky-400/80"
                    />
                  )}
                </div>
              </div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
};

export default HistoricalStrategyBrowser;
