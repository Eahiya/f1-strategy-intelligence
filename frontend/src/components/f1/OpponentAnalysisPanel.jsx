import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
  // eslint-disable-next-line no-unused-vars
import { Shield, TrendingUp, AlertTriangle, Target, Loader2, AlertCircle, ChevronDown } from 'lucide-react';
import { eliteApi } from '../../services/api';

const TIRE_OPTIONS = ['soft', 'medium', 'hard', 'intermediate', 'wet'];

export const OpponentAnalysisPanel = () => {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    circuit: 'monza',
    our_position: 5,
    gap_to_ahead: 2.5,
    gap_to_behind: 3.0,
    our_tire: 'soft',
    our_tire_age: 8,
    opponent_tire: 'medium',
    opponent_tire_age: 12,
    laps_to_go: 40,
  });

  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    setAnalysis(null);
    try {
      const response = await eliteApi.opponentAnalysis({
        circuit: formData.circuit,
        our_position: formData.our_position,
        gap_to_ahead: formData.gap_to_ahead,
        gap_to_behind: formData.gap_to_behind,
        our_tire: formData.our_tire,
        our_tire_age: formData.our_tire_age,
        opponent_tire: formData.opponent_tire,
        opponent_tire_age: formData.opponent_tire_age,
        laps_to_go: formData.laps_to_go,
      });
      setAnalysis(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [formData]);

  const undercut = analysis?.undercut_analysis;
  const recommendations = analysis?.strategic_recommendations || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 px-1">
        <Shield className="w-4 h-4 text-orange-400" />
        <h3 className="text-sm font-bold text-white/80 uppercase tracking-[0.15em]">Opponent Analysis</h3>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1">
          <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Your Tire</label>
          <select
            value={formData.our_tire}
            onChange={(e) => updateField('our_tire', e.target.value)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-white text-xs appearance-none focus:outline-none focus:border-[#e10600]/50"
          >
            {TIRE_OPTIONS.map((t) => (
              <option key={t} value={t} className="bg-[#0a0a0a] text-white">{t}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Tire Age</label>
          <input
            type="number"
            min="0"
            max="50"
            value={formData.our_tire_age}
            onChange={(e) => updateField('our_tire_age', parseInt(e.target.value) || 0)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-white text-xs focus:outline-none focus:border-[#e10600]/50"
          />
        </div>
        <div className="space-y-1">
          <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Opponent Tire</label>
          <select
            value={formData.opponent_tire}
            onChange={(e) => updateField('opponent_tire', e.target.value)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-white text-xs appearance-none focus:outline-none focus:border-[#e10600]/50"
          >
            {TIRE_OPTIONS.map((t) => (
              <option key={t} value={t} className="bg-[#0a0a0a] text-white">{t}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Opp. Tire Age</label>
          <input
            type="number"
            min="0"
            max="50"
            value={formData.opponent_tire_age}
            onChange={(e) => updateField('opponent_tire_age', parseInt(e.target.value) || 0)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-white text-xs focus:outline-none focus:border-[#e10600]/50"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="space-y-1">
          <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Position</label>
          <input
            type="number"
            min="1"
            max="20"
            value={formData.our_position}
            onChange={(e) => updateField('our_position', parseInt(e.target.value) || 1)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-white text-xs focus:outline-none focus:border-[#e10600]/50"
          />
        </div>
        <div className="space-y-1">
          <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Gap Ahead</label>
          <input
            type="number"
            step="0.1"
            value={formData.gap_to_ahead}
            onChange={(e) => updateField('gap_to_ahead', parseFloat(e.target.value) || 0)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-white text-xs focus:outline-none focus:border-[#e10600]/50"
          />
        </div>
        <div className="space-y-1">
          <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Laps To Go</label>
          <input
            type="number"
            min="1"
            value={formData.laps_to_go}
            onChange={(e) => updateField('laps_to_go', parseInt(e.target.value) || 1)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-white text-xs focus:outline-none focus:border-[#e10600]/50"
          />
        </div>
      </div>

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={runAnalysis}
        disabled={loading}
        className="w-full f1-btn f1-btn-primary"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Target className="w-4 h-4" />
            Analyze Undercut
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

      {undercut && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-white/40 uppercase tracking-[0.15em]">Undercut Viable</span>
            <span
              className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] rounded-md border ${
                undercut.viable
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                  : 'bg-red-500/10 border-red-500/20 text-red-400'
              }`}
            >
              {undercut.viable ? 'Yes' : 'No'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="p-2.5 bg-white/[0.03] border border-white/[0.06] rounded-lg">
              <p className="text-[9px] text-white/30 uppercase tracking-[0.1em]">Success Rate</p>
              <p className="text-lg font-bold text-white/80">{Math.round(undercut.probability * 100)}%</p>
            </div>
            <div className="p-2.5 bg-white/[0.03] border border-white/[0.06] rounded-lg">
              <p className="text-[9px] text-white/30 uppercase tracking-[0.1em]">Time Gain</p>
              <p className="text-lg font-bold text-emerald-400">+{undercut.time_gain_potential.toFixed(2)}s</p>
            </div>
          </div>

          {undercut.optimal_lap && (
            <div className="flex items-center gap-2 p-2 bg-amber-500/[0.06] border border-amber-500/15 rounded-lg">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span className="text-[11px] text-amber-300/70">
                Optimal undercut window: Lap {undercut.optimal_lap}
              </span>
            </div>
          )}

          {undercut.reasoning && (
            <p className="text-[11px] text-white/50 leading-relaxed">{undercut.reasoning}</p>
          )}

          {recommendations.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] text-white/40 uppercase tracking-[0.15em]">Recommendations</span>
              {recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-2 p-2 bg-white/[0.02] rounded-lg">
                  <TrendingUp className="w-3 h-3 text-blue-400 mt-0.5 shrink-0" />
                  <span className="text-[11px] text-white/60">{rec.reasoning || rec}</span>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default OpponentAnalysisPanel;
