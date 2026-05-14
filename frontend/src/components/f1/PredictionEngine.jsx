import React, { useMemo, memo } from 'react';
import { motion } from 'framer-motion';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart } from 'recharts';
  // eslint-disable-next-line no-unused-vars
import { Brain, TrendingUp, Clock, Target, Activity } from 'lucide-react';
import { useRace } from '../../context/RaceContext';

const generateFallbackPredictions = (currentLap, currentLapTime, tire, tireAge, baseConfidencePct = 88) => {
  const predictions = [];
  const degradationRate = tire === 'soft' ? 0.08 : tire === 'medium' ? 0.05 : 0.03;
  const base = Math.min(98, Math.max(42, baseConfidencePct));
  for (let i = 1; i <= 5; i++) {
    predictions.push({
      lap: currentLap + i,
      projected_lap_time: currentLapTime + (degradationRate * i * tireAge),
      confidence: Math.max(45, Math.round(base - i * 5)),
      position_change: 0,
      gap_to_leader: null,
      tire_grip: Math.max(0, 100 - (tireAge + i) * 2.5),
    });
  }
  return predictions;
};

const ConfidenceBadge = memo(({ confidence }) => {
  let color = 'text-emerald-400/60 bg-emerald-500/10';
  let label = 'HIGH';
  if (confidence < 70) { color = 'text-red-400/60 bg-red-500/10'; label = 'LOW'; }
  else if (confidence < 85) { color = 'text-yellow-400/60 bg-yellow-500/10'; label = 'MED'; }
  return <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${color}`}>{label} {confidence}%</span>;
});
ConfidenceBadge.displayName = 'ConfidenceBadge';

const PredictionCard = memo(({ prediction }) => (
  <div className="flex items-center gap-2.5 p-2.5 bg-white/[0.02] rounded-lg border border-white/[0.05]">
    <div className="w-7 h-7 bg-white/[0.03] rounded-lg flex items-center justify-center border border-white/[0.05]">
      <span className="text-[10px] font-mono font-bold text-white/30">L{prediction.lap}</span>
    </div>
    <div className="flex-1">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-xs text-white/50 font-mono">
          {typeof prediction.projected_lap_time === 'number' ? prediction.projected_lap_time.toFixed(2) : prediction.projected_lap_time}s
        </span>
        <ConfidenceBadge confidence={prediction.confidence} />
      </div>
      <div className="flex items-center gap-2.5 text-[9px] text-white/15">
        {prediction.position_change !== 0 && (
          <span className={`flex items-center gap-1 ${prediction.position_change < 0 ? 'text-emerald-400/50' : 'text-red-400/50'}`}>
            <TrendingUp className="w-2.5 h-2.5" />
            {prediction.position_change > 0 ? '+' : ''}{prediction.position_change}
          </span>
        )}
        {prediction.tire_grip != null && <span>Grip: {typeof prediction.tire_grip === 'number' ? prediction.tire_grip.toFixed(0) : prediction.tire_grip}%</span>}
      </div>
    </div>
  </div>
));
PredictionCard.displayName = 'PredictionCard';

const CustomTooltip = memo(({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-[#0c0c0c]/95 border border-white/[0.08] rounded-lg p-3 shadow-[0_8px_24px_rgba(0,0,0,0.5)] backdrop-blur-sm">
      <p className="text-white/30 text-[10px] mb-2 font-mono uppercase tracking-wider">Lap {label}</p>
      {payload.map((entry, index) => (
        <p key={index} className="text-xs font-mono" style={{ color: entry.color }}>
          {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}s
        </p>
      ))}
    </div>
  );
});
CustomTooltip.displayName = 'PredictionTooltip';

export const PredictionEngine = ({ externalPredictions }) => {
  const { predictions: racePredictions, player, raceState, chartData: contextChartData, confidence } = useRace();

  const liveConfPct = useMemo(() => {
    const o = confidence?.overall;
    if (o == null) return null;
    return o > 1 ? o : o * 100;
  }, [confidence?.overall]);
  
  const predictions = useMemo(() => {
    if (externalPredictions?.length > 0) return externalPredictions;
    if (racePredictions?.length > 0) return racePredictions;
    if (player && raceState.currentLap > 0) {
      const lapT = typeof player.lapTime === 'number' && player.lapTime > 0 ? player.lapTime : 90;
      return generateFallbackPredictions(
        raceState.currentLap,
        lapT,
        player.tire,
        player.tireAge,
        liveConfPct ?? 88
      );
    }
    return [];
  }, [externalPredictions, racePredictions, player, raceState.currentLap, liveConfPct]);

  const chartData = useMemo(() => {
    const data = [];
    (contextChartData || []).forEach((lap) => {
      data.push({ lap: lap.lap, actual: lap.player, predicted: null, isPrediction: false });
    });
    predictions.forEach(pred => {
      data.push({ lap: pred.lap, actual: null, predicted: pred.projected_lap_time, confidence: pred.confidence, isPrediction: true });
    });
    return data;
  }, [contextChartData, predictions]);

  const currentLap = raceState.currentLap || 0;

  return (
    <div className="relative">
      <div className="p-5 pb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Brain className="w-4 h-4 text-purple-400/40" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Prediction Engine</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">
              Next 5 laps
              {liveConfPct != null && (
                <span className="ml-2 text-white/35 font-mono">· fuse {liveConfPct.toFixed(0)}%</span>
              )}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/8 rounded-lg border border-emerald-500/10">
          <motion.div animate={{ opacity: [1, 0.3, 1] }} transition={{ repeat: Infinity, duration: 2 }} className="w-1.5 h-1.5 bg-emerald-400/50 rounded-full" />
          <span className="text-[9px] text-emerald-400/50 font-semibold">ML Active</span>
        </div>
      </div>

      <div className="px-5 pb-2">
        <div className="h-40">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="predictionGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                
                <XAxis dataKey="lap" stroke="rgba(255,255,255,0.1)" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="rgba(255,255,255,0.1)" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(val) => `${typeof val === 'number' ? val.toFixed(0) : val}`} />
                <Tooltip content={<CustomTooltip />} />
                
                <ReferenceLine x={currentLap} stroke="#e10600" strokeDasharray="4 4" strokeWidth={1.5} label={{ value: 'NOW', fill: '#e10600', fontSize: 9 }} />
                
                <Line type="monotone" dataKey="actual" stroke="#e10600" strokeWidth={2} dot={{ r: 2.5, fill: '#e10600' }} name="Actual" connectNulls={false} isAnimationActive />
                <Line type="monotone" dataKey="predicted" stroke="#a855f7" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 2.5, fill: '#a855f7' }} name="Predicted" connectNulls={false} isAnimationActive />
                <Area type="monotone" dataKey="predicted" stroke="none" fill="url(#predictionGradient)" fillOpacity={0.5} isAnimationActive />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-white/10">
              <Target className="w-8 h-8 mb-2 opacity-20" />
              <p className="text-[10px] uppercase tracking-wider">Start race for predictions</p>
            </div>
          )}
        </div>
      </div>

      {predictions.length > 0 && (
        <div className="px-5 pb-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-3 h-3 text-white/15" />
            <span className="text-[9px] text-white/15 uppercase tracking-wider">Projections</span>
          </div>
          <div className="space-y-1 max-h-44 overflow-y-auto">
            {predictions.map((prediction, idx) => (
              <PredictionCard key={idx} prediction={prediction} index={idx} />
            ))}
          </div>
        </div>
      )}

      <div className="px-5 py-2.5 border-t border-white/[0.06] flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-[#e10600]/60" />
          <span className="text-[9px] text-white/15">Actual</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-purple-400/40 border border-dashed border-purple-400/50" />
          <span className="text-[9px] text-white/15">Predicted</span>
        </div>
      </div>
    </div>
  );
};

export default memo(PredictionEngine);
