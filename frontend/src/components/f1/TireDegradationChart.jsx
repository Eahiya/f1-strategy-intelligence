import React, { useMemo, memo } from 'react';
  // eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Disc, Activity } from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import AnimatedValue from '../common/AnimatedValue';

const CustomTooltip = memo(({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#0c0c0c]/95 border border-white/[0.08] rounded-lg p-3 shadow-[0_8px_24px_rgba(0,0,0,0.5)] backdrop-blur-sm">
        <p className="text-white/30 text-[10px] mb-2 font-mono uppercase tracking-wider">Lap {label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs font-mono flex items-center gap-2" style={{ color: entry.color }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: entry.color }} />
            {entry.name}: {entry.value?.toFixed(1)}%
          </p>
        ))}
      </div>
    );
  }
  return null;
});
CustomTooltip.displayName = 'TireTooltip';

export const TireDegradationChart = ({ tireData, pitStops }) => {
  const { raceState, player, lapHistory } = useRace();

  const data = useMemo(() => {
    const baseData = tireData || Array.from({ length: 50 }, (_, i) => ({
      lap: i + 1,
      'Soft': Math.max(100 - i * 2.5, 0),
      'Medium': Math.max(100 - i * 1.8, 0),
      'Hard': Math.max(100 - i * 1.2, 0),
    }));

    // Inject actual degradation if available
    return baseData.map((point, idx) => {
      const historyPoint = lapHistory.find(h => h.lap === point.lap);
      return {
        ...point,
        'Actual': historyPoint ? (100 - (historyPoint.player?.tire_degradation || 0) * 100) : null
      };
    });
  }, [tireData, lapHistory]);

  const colors = { 'Soft': '#e10600', 'Medium': '#fbbf24', 'Hard': '#ffffff' };
  const currentGrip = 100 - (player.tireDegradation || 0) * 100;

  return (
    <div className="relative">
      <div className="p-5 pb-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Disc className="w-4 h-4 text-yellow-400/40" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Tire Degradation</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">
              {raceState.isRunning ? `Current Health: ${currentGrip.toFixed(0)}%` : 'Grip over race distance'}
            </p>
          </div>
        </div>
        <div className="flex gap-3 flex-wrap">
          {Object.entries(colors).map(([compound, color]) => (
            <div key={compound} className="flex items-center gap-1.5 px-2 py-0.5 bg-white/[0.02] rounded border border-white/[0.04]">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color + '99' }} />
              <span className="text-[9px] text-white/25 uppercase tracking-wider font-bold">{compound}</span>
            </div>
          ))}
          {raceState.isRunning && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-500/10 rounded border border-emerald-500/20">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[9px] text-emerald-400 uppercase tracking-wider font-bold">Actual</span>
            </div>
          )}
        </div>
      </div>

      <div className="px-5 pb-2">
        <div className="h-[200px] min-w-[500px]">
          <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              {Object.entries(colors).map(([compound, color]) => (
                <linearGradient key={compound} id={`tireGradient${compound}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.1}/>
                  <stop offset="95%" stopColor={color} stopOpacity={0}/>
                </linearGradient>
              ))}
              <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
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
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {raceState.currentLap > 0 && (
              <ReferenceLine 
                x={raceState.currentLap} 
                stroke="#666" 
                strokeDasharray="4 4"
                strokeWidth={1}
              />
            )}

            {pitStops?.map((stop, idx) => (
              <ReferenceLine 
                key={idx}
                x={stop.lap || stop} 
                stroke="#e10600" 
                strokeDasharray="4 4"
                strokeWidth={1.5}
                label={{ value: 'PIT', fill: '#e10600', fontSize: 9, position: 'insideTopLeft' }}
              />
            ))}
            
            {Object.keys(colors).map((compound) => (
              <Area
                key={compound}
                type="monotone"
                dataKey={compound}
                stroke={colors[compound]}
                strokeWidth={2}
                strokeOpacity={0.4}
                fill={`url(#tireGradient${compound})`}
                dot={false}
                isAnimationActive={false}
              />
            ))}

            {raceState.isRunning && (
              <Area
                type="monotone"
                dataKey="Actual"
                stroke="#10b981"
                strokeWidth={3}
                fill="url(#actualGradient)"
                dot={{ r: 2, fill: '#10b981', strokeWidth: 0 }}
                isAnimationActive={true}
                animationDuration={1000}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
        </div>
      </div>

      <div className="px-5 pb-4 grid grid-cols-3 gap-2">
        {Object.entries(colors).map(([compound, color]) => {
          const point = data[data.length - 1];
          const gripValue = (raceState.isRunning && player.tire.toLowerCase() === compound.toLowerCase()) 
            ? currentGrip 
            : (point?.[compound] || 0);
            
          return (
            <div key={compound} className={`rounded-xl p-2 text-center border transition-colors ${
              raceState.isRunning && player.tire.toLowerCase() === compound.toLowerCase()
              ? 'bg-emerald-500/10 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]'
              : 'bg-white/[0.02] border-white/[0.05]'
            }`}>
              <div className="flex items-center justify-center gap-1.5 mb-1">
                 {raceState.isRunning && player.tire.toLowerCase() === compound.toLowerCase() && (
                   <Activity className="w-2.5 h-2.5 text-emerald-400 animate-pulse" />
                 )}
                 <div className="text-[9px] text-white/15 uppercase tracking-wider">{compound}</div>
              </div>
              <div className="text-sm font-bold font-mono" style={{ color: color + 'cc' }}>
                <AnimatedValue value={gripValue} precision={0} suffix="%" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default memo(TireDegradationChart);
