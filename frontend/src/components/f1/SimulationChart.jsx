import React, { useMemo, memo } from 'react';
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
import { Activity, AlertCircle } from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import AnimatedValue from '../common/AnimatedValue';

const generateFallbackData = (laps = 50) => {
  return Array.from({ length: laps }, (_, i) => ({
    lap: i + 1,
    '1-Stop': 90 + i * 0.08 + Math.sin(i * 0.2) * 0.5,
    '2-Stop': 90.2 + i * 0.06 + Math.sin(i * 0.15) * 0.4,
    'Aggressive': 89.8 + i * 0.1 + Math.sin(i * 0.25) * 0.6,
    isPrediction: false,
  }));
};

const CustomTooltip = memo(({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-[#0c0c0c]/95 border border-white/[0.08] rounded-lg p-3 shadow-[0_8px_24px_rgba(0,0,0,0.5)] backdrop-blur-sm">
      <p className="text-white/30 text-[10px] mb-2 font-mono uppercase tracking-wider">Lap {label}</p>
      {payload.map((entry, index) => {
        if (entry.name?.includes('prediction') || entry.dataKey?.includes('Ghost')) return null;
        return (
          <p key={index} className="text-xs font-mono flex items-center gap-2" style={{ color: entry.color }}>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}s
          </p>
        );
      })}
    </div>
  );
});
CustomTooltip.displayName = 'CustomTooltip';

const STRATEGY_CONFIG = {
  '1-Stop': { color: '#eab308', dashArray: '0', width: 3 },
  '2-Stop': { color: '#10b981', dashArray: '0', width: 3 },
  'Aggressive': { color: '#ef4444', dashArray: '5 5', width: 2 },
  'Conservative': { color: '#3b82f6', dashArray: '5 5', width: 2 },
  'AI-RL': { color: '#a855f7', dashArray: '0', width: 3 },
};

export const SimulationChart = ({ data, strategies, pitStops }) => {
  const { raceState, lapHistory, predictions, chartData: contextChartData } = useRace();
  
  const chartData = useMemo(() => {
    const baseData = (data && data.length > 0) ? data : 
                     (contextChartData && contextChartData.length > 0) ? contextChartData :
                     generateFallbackData(raceState.totalLaps || 50);
    return baseData.map((point, idx) => ({
      ...point,
      isPrediction: lapHistory.length > 0 && idx >= lapHistory.length,
      hasActual: lapHistory.length > 0 && idx < lapHistory.length,
    }));
  }, [data, lapHistory, predictions, raceState.currentLap, raceState.totalLaps, contextChartData]);

  const activeStrategies = useMemo(() => {
    if (!chartData || chartData.length === 0) return [];
    const firstPoint = chartData[0];
    return Object.keys(firstPoint)
      .filter(key => key !== 'lap' && key !== 'isPrediction' && key !== 'hasActual' && !key.includes('prediction') && !key.includes('Ghost'))
      .map((key, idx) => ({
        key,
        name: key,
        color: STRATEGY_CONFIG[key]?.color || ['#e10600', '#00d4ff', '#fbbf24', '#10b981'][idx % 4],
        dashArray: STRATEGY_CONFIG[key]?.dashArray || '0',
        width: STRATEGY_CONFIG[key]?.width || 2,
      }));
  }, [chartData]);

  const yDomain = useMemo(() => {
    if (!chartData || chartData.length === 0) return [85, 95];
    const allValues = chartData.flatMap(d => activeStrategies.map(s => d[s.key]).filter(v => v !== undefined && v !== null));
    if (allValues.length === 0) return [85, 95];
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    return [Math.max(70, min - 3), max + 3];
  }, [chartData, activeStrategies]);

  const currentLap = raceState.currentLap || (lapHistory?.length || 0);

  if (!chartData || chartData.length === 0) {
    return (
      <div className="relative">
        <div className="p-5 pb-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Activity className="w-4 h-4 text-[#e10600]/60" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Strategy Simulation</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">Run simulation to begin</p>
          </div>
        </div>
        <div className="h-[300px] flex items-center justify-center text-white/15">
          <div className="text-center">
            <AlertCircle className="w-10 h-10 mx-auto mb-2 opacity-20" />
            <p className="text-xs uppercase tracking-wider">No simulation data available</p>
          </div>
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
            <h3 className="text-sm font-bold text-white/70">Strategy Simulation</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">
              {activeStrategies.length > 0 ? `Comparing ${activeStrategies.length} strategies` : 'Lap time comparison'}
            </p>
          </div>
        </div>
        
        <div className="flex gap-2 flex-wrap">
          {activeStrategies.map((strat) => (
            <div key={strat.key} className="flex items-center gap-2 px-2.5 py-1 bg-white/[0.03] rounded-lg border border-white/[0.05]">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: strat.color }} />
              <span className="text-[10px] text-white/30 uppercase tracking-wider">{strat.name}</span>
            </div>
          ))}
          {predictions && predictions.length > 0 && (
            <div className="flex items-center gap-2 px-2.5 py-1 bg-white/[0.03] rounded-lg border border-white/[0.08] border-dashed">
              <div className="w-2 h-2 rounded-full bg-white/30" />
              <span className="text-[10px] text-white/20 uppercase tracking-wider">Prediction</span>
            </div>
          )}
        </div>
      </div>

      <div className="px-5 pb-2">
        <div className="h-[300px] min-w-[600px]">
          <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              {activeStrategies.map((strat, idx) => (
                <linearGradient key={strat.key} id={`gradient${idx}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={strat.color} stopOpacity={0.2}/>
                  <stop offset="95%" stopColor={strat.color} stopOpacity={0}/>
                </linearGradient>
              ))}
            </defs>
            
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
              tickFormatter={(value) => `${typeof value === 'number' ? value.toFixed(0) : value}`}
            />
            
            <Tooltip content={<CustomTooltip />} />
            
            {currentLap > 0 && (
              <ReferenceLine 
                x={currentLap} 
                stroke="#e10600" 
                strokeDasharray="4 4"
                strokeWidth={1.5}
                label={{ 
                  value: `L${currentLap}`, 
                  fill: '#e10600', 
                  fontSize: 9,
                  position: 'insideTopLeft'
                }}
              />
            )}
            
            {pitStops?.map((stop, idx) => (
              <ReferenceLine 
                key={idx}
                x={stop.lap || stop} 
                stroke="#fbbf24" 
                strokeDasharray="3 3"
                strokeWidth={1}
                label={{ 
                  value: 'PIT', 
                  fill: '#fbbf24', 
                  fontSize: 9,
                  position: 'insideTopRight'
                }}
              />
            ))}
            
            {activeStrategies.map((strat, idx) => (
              <Line
                key={strat.key}
                type="monotone"
                dataKey={strat.key}
                stroke={strat.color}
                strokeWidth={strat.width}
                strokeDasharray={strat.dashArray}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2, stroke: '#fff' }}
                isAnimationActive={true}
                animationDuration={500}
              />
            ))}
            
            {predictions && predictions.length > 0 && (
              <Line
                type="monotone"
                dataKey="prediction_player"
                stroke="#ffffff"
                strokeWidth={2}
                strokeDasharray="8 4"
                dot={{ r: 3, fill: '#ffffff', strokeWidth: 0 }}
                name="prediction"
                isAnimationActive={true}
                animationDuration={300}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
        </div>
      </div>
      
      {activeStrategies.length > 0 && chartData.length > 0 && (
        <div className="px-5 pb-4 grid grid-cols-3 gap-2">
          {activeStrategies.slice(0, 3).map((strat) => {
            const lastPoint = chartData[chartData.length - 1];
            const finalTime = lastPoint?.[strat.key];
            return (
              <div key={strat.key} className="bg-white/[0.02] rounded-xl p-3 border border-white/[0.05]">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: strat.color }} />
                  <span className="text-[10px] text-white/25 uppercase tracking-wider">{strat.name}</span>
                </div>
                <div className="text-base font-bold font-mono text-white/70">
                  {finalTime ? <AnimatedValue value={((finalTime * chartData.length) / 60)} precision={1} suffix="m" /> : '--'}
                </div>
                <div className="text-[9px] text-white/15 uppercase tracking-wider">
                  Est. race time
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default memo(SimulationChart);
