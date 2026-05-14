import React, { useMemo, memo } from 'react';
  // eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  ReferenceLine,
} from 'recharts';
import { Activity, AlertCircle, Zap } from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import AnimatedValue from '../common/AnimatedValue';

const generateFallbackData = (laps = 50) => {
  return Array.from({ length: laps }, (_, i) => ({
    lap: i + 1,
    '1-Stop': 90 + i * 0.08 + Math.sin(i * 0.2) * 0.5,
    '2-Stop': 90.2 + i * 0.06 + Math.sin(i * 0.15) * 0.4,
    'Aggressive': 89.8 + i * 0.1 + Math.sin(i * 0.25) * 0.6,
  }));
};

const CustomTooltip = memo(({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-[#0c0c0c]/95 border border-white/[0.08] rounded-lg p-3 shadow-[0_8px_24px_rgba(0,0,0,0.5)] backdrop-blur-sm">
      <div className="flex items-center justify-between gap-4 mb-2">
         <p className="text-white/30 text-[10px] font-mono uppercase tracking-wider">Lap {label}</p>
         {payload.some(p => p.name === 'Actual') && (
           <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-[8px] font-bold rounded uppercase">Live</span>
         )}
      </div>
      <div className="space-y-1.5">
        {payload.map((entry, index) => {
          if (entry.name?.includes('prediction') || entry.dataKey?.includes('Ghost')) return null;
          const isActual = entry.name === 'Actual';
          return (
            <div key={index} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className={`text-xs font-mono ${isActual ? 'text-white font-bold' : 'text-white/60'}`}>
                  {isActual ? 'Actual (You)' : entry.name}
                </span>
              </div>
              <span className={`text-xs font-mono ${isActual ? 'text-emerald-400' : 'text-white/80'}`}>
                {typeof entry.value === 'number' ? entry.value.toFixed(3) : entry.value}s
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
});
CustomTooltip.displayName = 'CustomTooltip';

const STRATEGY_CONFIG = {
  '1-Stop': { color: '#eab308', dashArray: '0', width: 2, opacity: 0.3 },
  '2-Stop': { color: '#10b981', dashArray: '0', width: 2, opacity: 0.3 },
  'Aggressive': { color: '#ef4444', dashArray: '5 5', width: 1.5, opacity: 0.3 },
  'Conservative': { color: '#3b82f6', dashArray: '5 5', width: 1.5, opacity: 0.3 },
  'AI-RL': { color: '#a855f7', dashArray: '0', width: 2, opacity: 0.3 },
  'Optimal': { color: '#e10600', dashArray: '0', width: 2, opacity: 0.3 },
};

export const SimulationChart = ({ data, strategies, pitStops }) => {
  const { raceState, lapHistory, contextChartData } = useRace();
  
  const processedData = useMemo(() => {
    const baseData = (data && data.length > 0) ? data : 
                     (contextChartData && contextChartData.length > 0) ? contextChartData :
                     generateFallbackData(raceState.totalLaps || 50);

    return baseData.map((point, idx) => {
      const historyPoint = lapHistory.find(h => h.lap === point.lap);
      return {
        ...point,
        'Actual': historyPoint?.player?.lap_time || null,
        isPrediction: idx >= (lapHistory.length),
      };
    });
  }, [data, lapHistory, raceState.totalLaps, contextChartData]);

  const activeStrategies = useMemo(() => {
    if (!processedData || processedData.length === 0) return [];
    const firstPoint = processedData[0];
    return Object.keys(firstPoint)
      .filter(key => key !== 'lap' && key !== 'isPrediction' && key !== 'Actual' && !key.includes('_'))
      .map((key, idx) => ({
        key,
        name: key,
        color: STRATEGY_CONFIG[key]?.color || ['#e10600', '#00d4ff', '#fbbf24', '#10b981'][idx % 4],
        dashArray: STRATEGY_CONFIG[key]?.dashArray || '0',
        width: STRATEGY_CONFIG[key]?.width || 2,
        opacity: STRATEGY_CONFIG[key]?.opacity || 0.3,
      }));
  }, [processedData]);

  const yDomain = useMemo(() => {
    if (!processedData || processedData.length === 0) return [85, 95];
    const allValues = processedData.flatMap(d => [
      ...activeStrategies.map(s => d[s.key]),
      d['Actual']
    ].filter(v => typeof v === 'number'));
    
    if (allValues.length === 0) return [85, 95];
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    return [Math.max(70, min - 2), max + 2];
  }, [processedData, activeStrategies]);

  const currentLap = raceState.currentLap || 0;

  if (!processedData || processedData.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center text-white/15">
        <div className="text-center">
          <AlertCircle className="w-10 h-10 mx-auto mb-2 opacity-20" />
          <p className="text-xs uppercase tracking-wider">No simulation data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="p-5 pb-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Activity className="w-4 h-4 text-[#e10600]/60" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Performance Tracker</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">
              {raceState.isRunning ? `Lap ${currentLap} • Real-time Pace Delta` : 'Predicted Strategy Baselines'}
            </p>
          </div>
        </div>
        
        <div className="flex gap-2 flex-wrap">
          {activeStrategies.map((strat) => (
            <div key={strat.key} className="flex items-center gap-2 px-2 py-0.5 bg-white/[0.02] rounded border border-white/[0.05]">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: strat.color + '66' }} />
              <span className="text-[9px] text-white/25 uppercase tracking-wider font-bold">{strat.name}</span>
            </div>
          ))}
          {raceState.isRunning && (
            <div className="flex items-center gap-2 px-2 py-0.5 bg-emerald-500/10 rounded border border-emerald-500/20">
              <Zap className="w-2.5 h-2.5 text-emerald-400 animate-pulse" />
              <span className="text-[9px] text-emerald-400 uppercase tracking-wider font-bold">Actual (You)</span>
            </div>
          )}
        </div>
      </div>

      <div className="px-5 pb-2">
        <div className="h-[300px] min-w-[600px]">
          <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={processedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            
            <XAxis 
              dataKey="lap" 
              stroke="rgba(255,255,255,0.1)" 
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            
            <YAxis 
              stroke="rgba(255,255,255,0.1)" 
              fontSize={10}
              tickLine={false}
              axisLine={false}
              domain={yDomain}
              tickFormatter={(v) => `${v.toFixed(1)}`}
            />
            
            <Tooltip content={<CustomTooltip />} />
            
            {currentLap > 0 && (
              <ReferenceLine 
                x={currentLap} 
                stroke="#e10600" 
                strokeDasharray="4 4"
                strokeWidth={1.5}
                label={{ 
                  value: 'LIVE', 
                  fill: '#e10600', 
                  fontSize: 9,
                  position: 'insideTopLeft',
                  fontWeight: 'bold'
                }}
              />
            )}
            
            {pitStops?.map((stop, idx) => (
              <ReferenceLine 
                key={idx}
                x={stop.lap || stop} 
                stroke="#fbbf24" 
                strokeDasharray="4 4"
                strokeWidth={1}
                label={{ value: 'PIT', fill: '#fbbf24', fontSize: 9, position: 'insideTopRight' }}
              />
            ))}
            
            {activeStrategies.map((strat) => (
              <Line
                key={strat.key}
                type="monotone"
                dataKey={strat.key}
                stroke={strat.color}
                strokeWidth={strat.width}
                strokeDasharray={strat.dashArray}
                strokeOpacity={raceState.isRunning ? strat.opacity : 1}
                dot={false}
                isAnimationActive={false}
              />
            ))}
            
            {raceState.isRunning && (
              <Line
                type="monotone"
                dataKey="Actual"
                stroke="#10b981"
                strokeWidth={3}
                dot={{ r: 3, fill: '#10b981', strokeWidth: 0 }}
                activeDot={{ r: 5, fill: '#10b981', stroke: '#fff', strokeWidth: 2 }}
                name="Actual"
                isAnimationActive={true}
                animationDuration={500}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
        </div>
      </div>
      
      {raceState.isRunning && lapHistory.length > 0 && (
        <div className="px-5 pb-4 grid grid-cols-3 gap-2">
          <div className="bg-white/[0.02] rounded-xl p-3 border border-white/[0.05]">
            <div className="text-[9px] text-white/15 uppercase tracking-wider mb-1">Average Pace</div>
            <div className="text-base font-bold font-mono text-white/70">
              <AnimatedValue 
                value={lapHistory.reduce((acc, curr) => acc + (curr.player?.lap_time || 90), 0) / lapHistory.length} 
                precision={3} 
                suffix="s" 
              />
            </div>
          </div>
          <div className="bg-white/[0.02] rounded-xl p-3 border border-white/[0.05]">
            <div className="text-[9px] text-white/15 uppercase tracking-wider mb-1">Last Lap</div>
            <div className="text-base font-bold font-mono text-emerald-400">
              <AnimatedValue value={lapHistory[lapHistory.length - 1]?.player?.lap_time || 0} precision={3} suffix="s" />
            </div>
          </div>
          <div className="bg-white/[0.02] rounded-xl p-3 border border-white/[0.05]">
            <div className="text-[9px] text-white/15 uppercase tracking-wider mb-1">Pace Delta</div>
            <div className="text-base font-bold font-mono text-white/40">
              {(() => {
                const actual = lapHistory[lapHistory.length - 1]?.player?.lap_time || 0;
                const predicted = processedData[lapHistory.length - 1]?.['Optimal'] || 90;
                const delta = actual - predicted;
                return <span className={delta < 0 ? 'text-emerald-400' : 'text-red-400'}>
                  {delta < 0 ? '-' : '+'}{Math.abs(delta).toFixed(3)}s
                </span>;
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default memo(SimulationChart);
