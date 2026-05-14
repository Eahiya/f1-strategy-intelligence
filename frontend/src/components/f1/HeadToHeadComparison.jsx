import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Users, ChevronDown, TrendingUp, BarChart3, Timer, AlertCircle, Loader2 } from 'lucide-react';
import { fastf1Api } from '../../services/api';

const F1_DRIVERS = [
  { id: 'VER', name: 'Max Verstappen', team: 'Red Bull Racing' },
  { id: 'PER', name: 'Sergio Perez', team: 'Red Bull Racing' },
  { id: 'NOR', name: 'Lando Norris', team: 'McLaren' },
  { id: 'PIA', name: 'Oscar Piastri', team: 'McLaren' },
  { id: 'HAM', name: 'Lewis Hamilton', team: 'Ferrari' },
  { id: 'LEC', name: 'Charles Leclerc', team: 'Ferrari' },
  { id: 'RUS', name: 'George Russell', team: 'Mercedes' },
  { id: 'ANT', name: 'Kimi Antonelli', team: 'Mercedes' },
  { id: 'ALO', name: 'Fernando Alonso', team: 'Aston Martin' },
  { id: 'STR', name: 'Lance Stroll', team: 'Aston Martin' },
];

const CIRCUIT_OPTIONS = [
  { id: 'monza', name: 'Monza', gp: 'Italian Grand Prix' },
  { id: 'spa', name: 'Spa-Francorchamps', gp: 'Belgian Grand Prix' },
  { id: 'silverstone', name: 'Silverstone', gp: 'British Grand Prix' },
  { id: 'red_bull_ring', name: 'Red Bull Ring', gp: 'Austrian Grand Prix' },
  { id: 'interlagos', name: 'Interlagos', gp: 'Brazilian Grand Prix' },
  { id: 'suzuka', name: 'Suzuka', gp: 'Japanese Grand Prix' },
];

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const DriverSelector = ({ label, value, onChange }) => {
  const selectedDriver = F1_DRIVERS.find((d) => d.id === value);
  return (
    <div className="space-y-2">
      <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">{label}</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white text-sm appearance-none cursor-pointer focus:outline-none focus:border-[#e10600]/50 focus:ring-1 focus:ring-[#e10600]/20 transition-all"
        >
          {F1_DRIVERS.map((d) => (
            <option key={d.id} value={d.id} className="bg-[#0a0a0a] text-white">
              {d.id} - {d.name}
            </option>
          ))}
        </select>
        <ChevronDown className="w-4 h-4 text-white/30 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
      </div>
      {selectedDriver && (
        <p className="text-[11px] text-white/30">{selectedDriver.team}</p>
      )}
    </div>
  );
};

const StatRow = ({ label, driverA, driverB, bestIs }) => {
  const aBetter = bestIs === 'a' || bestIs === 'lower' ? driverA < driverB : driverA > driverB;
  const bBetter = bestIs === 'b' || bestIs === 'lower' ? driverB < driverA : driverB > driverA;
  return (
    <div className="grid grid-cols-3 gap-3 py-2.5 border-b border-white/[0.04] last:border-0">
      <span className={`text-sm font-medium text-right ${aBetter ? 'text-emerald-400' : 'text-white/60'}`}>
        {driverA}
      </span>
      <span className="text-[11px] text-white/40 font-semibold uppercase tracking-[0.1em] text-center">{label}</span>
      <span className={`text-sm font-medium text-left ${bBetter ? 'text-emerald-400' : 'text-white/60'}`}>
        {driverB}
      </span>
    </div>
  );
};

const PaceBar = ({ label, valueA, valueB, maxValue }) => {
  const pctA = (valueA / maxValue) * 100;
  const pctB = (valueB / maxValue) * 100;
  return (
    <div className="space-y-1.5">
      <span className="text-[10px] text-white/40 font-semibold uppercase tracking-[0.15em]">{label}</span>
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-white/[0.04] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pctA}%` }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="h-full bg-gradient-to-r from-[#e10600] to-orange-500 rounded-full"
          />
        </div>
        <span className="text-[11px] font-mono text-white/50 w-16 text-right">{valueA.toFixed(2)}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-white/[0.04] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pctB}%` }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full"
          />
        </div>
        <span className="text-[11px] font-mono text-white/50 w-16 text-right">{valueB.toFixed(2)}</span>
      </div>
    </div>
  );
};

export const HeadToHeadComparison = () => {
  const [driverA, setDriverA] = useState('VER');
  const [driverB, setDriverB] = useState('NOR');
  const [circuit, setCircuit] = useState('monza');
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [error, setError] = useState(null);

  const runComparison = useCallback(async () => {
    if (driverA === driverB) {
      setError('Select two different drivers');
      return;
    }
    setLoading(true);
    setError(null);
    setComparison(null);
    try {
      const [telemetryA, telemetryB] = await Promise.allSettled([
        fastf1Api.driverTelemetry(circuit, driverA),
        fastf1Api.driverTelemetry(circuit, driverB),
      ]);

      const dataA = telemetryA.status === 'fulfilled' ? telemetryA.value.data : null;
      const dataB = telemetryB.status === 'fulfilled' ? telemetryB.value.data : null;

      if (!dataA && !dataB) {
        setError('No telemetry data available for this circuit/year');
        setLoading(false);
        return;
      }

      setComparison({
        driverA: { ...dataA, id: driverA },
        driverB: { ...dataB, id: driverB },
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch comparison data');
    } finally {
      setLoading(false);
    }
  }, [driverA, driverB, circuit]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 px-1">
        <Users className="w-4 h-4 text-[#e10600]" />
        <h3 className="text-sm font-bold text-white/80 uppercase tracking-[0.15em]">Head-to-Head Comparison</h3>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <DriverSelector label="Driver A" value={driverA} onChange={setDriverA} />
        <DriverSelector label="Driver B" value={driverB} onChange={setDriverB} />
      </div>

      <div className="space-y-2">
        <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Circuit</label>
        <div className="relative">
          <select
            value={circuit}
            onChange={(e) => setCircuit(e.target.value)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white text-sm appearance-none cursor-pointer focus:outline-none focus:border-[#e10600]/50 focus:ring-1 focus:ring-[#e10600]/20 transition-all"
          >
            {CIRCUIT_OPTIONS.map((c) => (
              <option key={c.id} value={c.id} className="bg-[#0a0a0a] text-white">
                {c.name} - {c.gp}
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-white/30 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={runComparison}
        disabled={loading}
        className="w-full f1-btn f1-btn-primary"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Fetching Data...
          </>
        ) : (
          <>
            <BarChart3 className="w-4 h-4" />
            Compare Drivers
          </>
        )}
      </motion.button>

      {error && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="p-3 bg-red-500/[0.08] border border-red-500/20 rounded-xl">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            <p className="text-xs text-red-300">{error}</p>
          </div>
        </motion.div>
      )}

      {comparison && (
        <motion.div variants={itemVariants} initial="hidden" animate="visible" className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-[#e10600]/[0.08] border border-[#e10600]/20 rounded-xl text-center">
              <p className="text-lg font-black text-[#e10600]">{comparison.driverA?.id || driverA}</p>
              <p className="text-[10px] text-white/40 truncate">{comparison.driverA?.team || ''}</p>
            </div>
            <div className="p-3 bg-blue-500/[0.08] border border-blue-500/20 rounded-xl text-center">
              <p className="text-lg font-black text-blue-400">{comparison.driverB?.id || driverB}</p>
              <p className="text-[10px] text-white/40 truncate">{comparison.driverB?.team || ''}</p>
            </div>
          </div>

          <div className="space-y-3">
            <StatRow
              label="Avg Pace"
              driverA={(comparison.driverA?.avg_pace || 90).toFixed(3)}
              driverB={(comparison.driverB?.avg_pace || 90).toFixed(3)}
              bestIs="lower"
            />
            <StatRow
              label="Consistency"
              driverA={(comparison.driverA?.consistency || 1.5).toFixed(3)}
              driverB={(comparison.driverB?.consistency || 1.5).toFixed(3)}
              bestIs="lower"
            />
          </div>

          {comparison.driverA?.avg_pace && comparison.driverB?.avg_pace && (
            <PaceBar
              label="Lap Time Comparison"
              valueA={comparison.driverA.avg_pace}
              valueB={comparison.driverB.avg_pace}
              maxValue={Math.max(comparison.driverA.avg_pace, comparison.driverB.avg_pace) * 1.1}
            />
          )}

          <div className="flex items-center justify-between p-2 bg-white/[0.03] rounded-lg">
            <div className="flex items-center gap-1.5">
              <TrendingUp className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] text-white/40 uppercase tracking-[0.15em]">Pace Delta</span>
            </div>
            <span className="text-sm font-bold text-white/70">
              {((comparison.driverA?.avg_pace || 90) - (comparison.driverB?.avg_pace || 90)).toFixed(3)}s
            </span>
          </div>

          <div className="flex items-center justify-between p-2 bg-white/[0.03] rounded-lg">
            <div className="flex items-center gap-1.5">
              <Timer className="w-3 h-3 text-[#e10600]" />
              <span className="text-[10px] text-white/40 uppercase tracking-[0.15em]">Stints</span>
            </div>
            <div className="flex gap-3 text-[11px]">
              <span className="text-[#e10600]/70">{comparison.driverA?.stints?.length || 0}</span>
              <span className="text-white/20">vs</span>
              <span className="text-blue-400/70">{comparison.driverB?.stints?.length || 0}</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default HeadToHeadComparison;
