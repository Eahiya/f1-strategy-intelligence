import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Disc } from 'lucide-react';

const CustomTooltip = memo(({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#0c0c0c]/95 border border-white/[0.08] rounded-lg p-3 shadow-[0_8px_24px_rgba(0,0,0,0.5)] backdrop-blur-sm">
        <p className="text-white/30 text-[10px] mb-2 font-mono uppercase tracking-wider">Lap {label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs font-mono" style={{ color: entry.color }}>
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
  const data = tireData || Array.from({ length: 50 }, (_, i) => ({
    lap: i + 1,
    'Soft': Math.max(100 - i * 2.5, 0),
    'Medium': Math.max(100 - i * 1.8, 0),
    'Hard': Math.max(100 - i * 1.2, 0),
  }));

  const colors = { 'Soft': '#e10600', 'Medium': '#fbbf24', 'Hard': '#ffffff' };

  return (
    <div className="relative">
      <div className="p-5 pb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Disc className="w-4 h-4 text-yellow-400/40" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Tire Degradation</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">Grip over race distance</p>
          </div>
        </div>
        <div className="flex gap-3">
          {Object.entries(colors).map(([compound, color]) => (
            <div key={compound} className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color + '99' }} />
              <span className="text-[10px] text-white/25 uppercase tracking-wider">{compound}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="px-5 pb-2">
        <div className="h-[200px] min-w-[500px]">
          <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              {Object.entries(colors).map(([compound, color]) => (
                <linearGradient key={compound} id={`tireGradient${compound}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.2}/>
                  <stop offset="95%" stopColor={color} stopOpacity={0}/>
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
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {pitStops?.map((stop) => (
              <ReferenceLine 
                key={stop.lap}
                x={stop.lap} 
                stroke="#e10600" 
                strokeDasharray="4 4"
                strokeWidth={1.5}
                label={{ value: `L${stop.lap}`, fill: '#e10600', fontSize: 9 }}
              />
            ))}
            
            {Object.keys(colors).map((compound) => (
              <Area
                key={compound}
                type="monotone"
                dataKey={compound}
                stroke={colors[compound]}
                strokeWidth={2}
                fill={`url(#tireGradient${compound})`}
                fillOpacity={1}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
        </div>
      </div>

      <div className="px-5 pb-4 grid grid-cols-3 gap-2">
        {Object.entries(colors).map(([compound, color]) => {
          const currentGrip = data[data.length - 1]?.[compound] || 0;
          return (
            <div key={compound} className="bg-white/[0.02] rounded-xl p-2 text-center border border-white/[0.05]">
              <div className="text-[9px] text-white/15 uppercase tracking-wider mb-1">{compound}</div>
              <div className="text-sm font-bold font-mono" style={{ color: color + 'cc' }}>
                {currentGrip.toFixed(0)}%
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default memo(TireDegradationChart);
