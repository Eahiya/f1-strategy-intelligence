import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Shield, Gauge } from 'lucide-react';
import { Cell, PieChart, Pie, ResponsiveContainer } from 'recharts';

const COLORS = ['#10b981', '#fbbf24', '#f97316', '#e10600', '#8b5cf6'];

export const RiskMeter = ({ riskLevel, factors }) => {
  const getRiskConfig = (level) => {
    if (level <= 30) return { color: '#10b981', label: 'LOW', icon: Shield, description: 'Strategy is safe under most conditions' };
    if (level <= 60) return { color: '#fbbf24', label: 'MEDIUM', icon: Gauge, description: 'Moderate risk, monitor conditions' };
    return { color: '#e10600', label: 'HIGH', icon: AlertTriangle, description: 'High risk, contingency plans recommended' };
  };

  const config = getRiskConfig(riskLevel || 0);
  const Icon = config.icon;

  const pieData = factors?.map((f) => ({ name: f.name, value: f.impact })) || [];
  const totalRisk = factors?.reduce((s, f) => s + f.impact, 0) || 0;
  const safeRemaining = Math.max(0, 100 - totalRisk);
  if (safeRemaining > 0) pieData.push({ name: 'Safety Margin', value: safeRemaining });

  return (
    <div className="f1-card relative overflow-hidden">
      <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl opacity-[0.08]" style={{ backgroundColor: config.color }} />

      <div className="relative z-10 p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: config.color + '15' }}>
              <Icon className="w-4 h-4" style={{ color: config.color }} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white/70">Risk Assessment</h3>
              <p className="text-[10px] text-white/20 uppercase tracking-wider">Strategy vulnerability</p>
            </div>
          </div>
          <span className="px-2 py-0.5 text-[9px] font-bold rounded uppercase tracking-wider" style={{ backgroundColor: config.color + '20', color: config.color }}>
            {config.label}
          </span>
        </div>

        <div className="flex items-center gap-5">
          <div className="relative w-24 h-24 flex-shrink-0">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="48" cy="48" r="40" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="7" />
              <motion.circle cx="48" cy="48" r="40" fill="none" stroke={config.color} strokeWidth="7" strokeLinecap="round"
                strokeDasharray={`${((riskLevel || 0) / 100) * 251.2} 251.2`}
                initial={{ strokeDasharray: '0 251.2' }}
                animate={{ strokeDasharray: `${((riskLevel || 0) / 100) * 251.2} 251.2` }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-lg font-bold text-white/70 font-mono">{riskLevel || 0}%</span>
              <span className="text-[8px] text-white/20 uppercase tracking-wider">Risk</span>
            </div>
          </div>

          {pieData.length > 1 && (
            <div className="flex-1 h-24">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={28} outerRadius={42} paddingAngle={2} dataKey="value" isAnimationActive stroke="none">
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.name === 'Safety Margin' ? 'rgba(255,255,255,0.04)' : COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <p className="text-xs text-white/25 text-center mb-4 leading-relaxed mt-2">{config.description}</p>

        {factors && factors.length > 0 && (
          <div className="space-y-2">
            <p className="text-[9px] text-white/15 uppercase tracking-wider">Breakdown</p>
            {factors.map((factor, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                <span className="text-[11px] text-white/35 flex-1 truncate">{factor.name}</span>
                <div className="w-16 h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${Math.min(factor.impact, 100)}%`, backgroundColor: COLORS[idx % COLORS.length] }} />
                </div>
                <span className="text-[10px] font-mono text-white/25 w-7 text-right">{factor.impact}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(RiskMeter);
