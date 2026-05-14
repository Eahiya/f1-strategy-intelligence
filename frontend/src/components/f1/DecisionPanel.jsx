import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { Lightbulb, CheckCircle, AlertCircle } from 'lucide-react';

const DEFAULT_WHY = [
  'Optimal tire window utilization',
  'Undercut opportunity on planned stint boundaries',
  'Aligned with live weather and safety-car exposure',
];

export const DecisionPanel = ({ decision, explanation, alternatives, confidence, whyPoints }) => {
  const bullets = whyPoints?.length ? whyPoints : DEFAULT_WHY;
  return (
    <div className="f1-card">
      <div className="p-5">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Lightbulb className="w-4 h-4 text-blue-400/50" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Strategy Insight</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">AI recommendation</p>
          </div>
        </div>

        {/* Main Decision */}
        <div className="bg-[#e10600]/[0.06] border-l-2 border-[#e10600]/50 rounded-r-xl p-4 mb-5">
          <p className="text-[10px] text-[#e10600]/50 uppercase tracking-wider mb-1">Recommended Action</p>
          <p className="text-sm font-bold text-white/80 leading-tight">
            {decision || "Execute 2-stop strategy with early first pit"}
          </p>
        </div>

        {explanation && (
          <p className="text-xs text-white/25 leading-relaxed mb-5">
            {explanation}
          </p>
        )}

        {/* Why This Works */}
        <div className="mb-5">
          <p className="text-[9px] text-white/15 uppercase tracking-wider mb-3">Why This Works</p>
          <div className="space-y-1.5">
            {bullets.map((text, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + idx * 0.1 }}
                className="flex items-center gap-2 p-2 bg-white/[0.02] rounded-lg"
              >
                <CheckCircle className="w-3 h-3 text-emerald-400/50 flex-shrink-0" />
                <span className="text-xs text-white/30">{text}</span>
              </motion.div>
            ))}
          </div>
        </div>

        {alternatives && alternatives.length > 0 && (
          <div className="mb-5">
            <p className="text-[9px] text-white/15 uppercase tracking-wider mb-3">Alternatives Analyzed</p>
            <div className="space-y-1.5">
              {alternatives.map((alt, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-white/[0.02] rounded-lg">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-3 h-3 text-yellow-400/40" />
                    <span className="text-xs text-white/30">{alt.name}</span>
                  </div>
                  <span className={`text-xs font-mono ${
                    alt.delta > 0 ? 'text-red-400/60' : 'text-emerald-400/60'
                  }`}>
                    {alt.delta > 0 ? '+' : ''}{alt.delta?.toFixed(1)}s
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center gap-4 pt-4 border-t border-white/[0.06]">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-white/15 uppercase tracking-wider">AI Confidence</span>
              <span className="text-xs font-bold text-white/50">
                {confidence != null ? (confidence > 1 ? Math.round(confidence) : Math.round(confidence * 100)) : 87}%
              </span>
            </div>
            <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${confidence != null ? (confidence > 1 ? confidence : confidence * 100) : 87}%`,
                }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="h-full bg-gradient-to-r from-[#e10600] to-red-400"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default memo(DecisionPanel);
