import React, { useState, useCallback, useEffect, useRef } from 'react';
  // eslint-disable-next-line no-unused-vars
import { motion, AnimatePresence } from 'framer-motion';
  // eslint-disable-next-line no-unused-vars
  // eslint-disable-next-line no-unused-vars
import { Play, Square, Loader2, AlertCircle, Radio, Activity, CloudRain, Flag } from 'lucide-react';
import { useRace } from '../../context/RaceContext';
  // eslint-disable-next-line no-unused-vars
import api from '../../services/api';

const RaceStatusBadge = ({ status }) => {
  const config = {
    connected: { color: 'bg-emerald-500', text: 'Connected' },
    connecting: { color: 'bg-amber-500 animate-pulse', text: 'Connecting...' },
    disconnected: { color: 'bg-red-500', text: 'Disconnected' },
    reconnecting: { color: 'bg-amber-500 animate-pulse', text: 'Reconnecting...' },
    error: { color: 'bg-red-500', text: 'Error' },
  };
  const { color, text } = config[status] || config.disconnected;
  return (
    <span className="flex items-center gap-1.5 text-[10px] text-white/50">
      <span className={`w-1.5 h-1.5 rounded-full ${color}`} />
      {text}
    </span>
  );
};

const LiveLapCounter = ({ current, total }) => (
  <div className="flex items-center gap-3">
    <div className="text-center">
      <p className="text-4xl font-black text-white">{current}</p>
      <p className="text-[9px] text-white/30 uppercase tracking-[0.2em]">Current Lap</p>
    </div>
    <div className="w-px h-10 bg-white/10" />
    <div className="text-center">
      <p className="text-4xl font-black text-white/40">{total}</p>
      <p className="text-[9px] text-white/30 uppercase tracking-[0.2em]">Total</p>
    </div>
  </div>
);

const LiveWeatherBadge = ({ weather }) => {
  const isWet = weather?.state === 'wet' || weather?.state === 'rain' || weather?.state === 'light_rain';
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.03] border border-white/[0.06] rounded-xl">
      {isWet ? <CloudRain className="w-4 h-4 text-blue-400" /> : <Radio className="w-4 h-4 text-amber-400" />}
      <span className="text-[11px] text-white/60 capitalize">{weather?.state || 'dry'}</span>
      {weather?.temp && <span className="text-[10px] text-white/30">{weather.temp}°C</span>}
    </div>
  );
};

const CompetitorMiniCard = ({ driver, index }) => (
  <motion.div
    initial={{ opacity: 0, x: -8 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: index * 0.03 }}
    className="flex items-center gap-2.5 p-2 bg-white/[0.02] hover:bg-white/[0.04] rounded-lg transition-colors"
  >
    <span className="text-[10px] font-bold text-white/40 w-5 text-right">{driver.position}</span>
    <div className="flex-1 min-w-0">
      <p className="text-xs font-semibold text-white/70 truncate">{driver.driver || driver.name}</p>
      <p className="text-[9px] text-white/30">{driver.team}</p>
    </div>
    <div className="text-right">
      <span className="text-[10px] font-mono text-white/50">
        {driver.gap_to_leader > 0 ? `+${driver.gap_to_leader.toFixed(1)}` : 'LEADER'}
      </span>
    </div>
  </motion.div>
);

export const LiveRaceWeekend = () => {
  const {
    raceState,
    startRace,
    stopRace,
    wsStatus,
    allCompetitors,
    currentRecommendation,
    uiRecommendation,
    confidence,
    metrics,
    strategy,
  } = useRace();
  const [error, setError] = useState(null);
  const [raceSetup, setRaceSetup] = useState({
    circuit: 'monza',
    laps: 53,
    strategy_type: 'auto',
    weather: 'dry',
  });
  const [liveError, setLiveError] = useState(null);
  const eventSourceRef = useRef(null);

  const startLiveRace = useCallback(async () => {
    setError(null);
    setLiveError(null);
    try {
      startRace(raceSetup.circuit, raceSetup.laps, {
        type: raceSetup.strategy_type,
        pitStops: [18, 38],
        nextPitLap: 18,
        compounds: ['soft', 'medium', 'hard'],
      });
    } catch (err) {
      setLiveError(err.response?.data?.detail || err.message || 'Failed to start live race');
    }
  }, [raceSetup, startRace]);

  const stopLiveRace = useCallback(() => {
    stopRace();
  }, [stopRace]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
  // eslint-disable-next-line react-hooks/exhaustive-deps
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-black text-white">Live Race Weekend</h2>
          <p className="text-xs text-white/30 mt-0.5">Real-time strategy simulation and monitoring</p>
        </div>
        <RaceStatusBadge status={wsStatus} />
      </div>

      {(liveError || error) && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="p-3 bg-red-500/[0.08] border border-red-500/20 rounded-xl">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            <p className="text-xs text-red-300">{liveError || error}</p>
          </div>
        </motion.div>
      )}

      {!raceState.isRunning && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="f1-card p-6"
        >
          <h3 className="text-sm font-bold text-white/70 mb-4 uppercase tracking-[0.15em]">Race Configuration</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <div className="space-y-1.5">
              <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Circuit</label>
              <select
                value={raceSetup.circuit}
                onChange={(e) => setRaceSetup((p) => ({ ...p, circuit: e.target.value }))}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-white text-sm appearance-none focus:outline-none focus:border-[#e10600]/50"
              >
                <option value="monza" className="bg-[#0a0a0a]">Monza</option>
                <option value="spa" className="bg-[#0a0a0a]">Spa</option>
                <option value="silverstone" className="bg-[#0a0a0a]">Silverstone</option>
                <option value="red_bull_ring" className="bg-[#0a0a0a]">Red Bull Ring</option>
                <option value="interlagos" className="bg-[#0a0a0a]">Interlagos</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Laps</label>
              <input
                type="number"
                min="1"
                max="80"
                value={raceSetup.laps}
                onChange={(e) => setRaceSetup((p) => ({ ...p, laps: parseInt(e.target.value) || 53 }))}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-[#e10600]/50"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Weather</label>
              <select
                value={raceSetup.weather}
                onChange={(e) => setRaceSetup((p) => ({ ...p, weather: e.target.value }))}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-white text-sm appearance-none focus:outline-none focus:border-[#e10600]/50"
              >
                <option value="dry" className="bg-[#0a0a0a]">Dry</option>
                <option value="wet" className="bg-[#0a0a0a]">Wet</option>
                <option value="mixed" className="bg-[#0a0a0a]">Mixed</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] text-white/30 font-semibold uppercase tracking-[0.1em]">Strategy</label>
              <select
                value={raceSetup.strategy_type}
                onChange={(e) => setRaceSetup((p) => ({ ...p, strategy_type: e.target.value }))}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-white text-sm appearance-none focus:outline-none focus:border-[#e10600]/50"
              >
                <option value="auto" className="bg-[#0a0a0a]">Auto</option>
                <option value="conservative" className="bg-[#0a0a0a]">Conservative</option>
                <option value="aggressive" className="bg-[#0a0a0a]">Aggressive</option>
              </select>
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            onClick={startLiveRace}
            className="w-full f1-btn f1-btn-primary text-base py-3"
          >
            <Play className="w-5 h-5" />
            Start Live Race
          </motion.button>
        </motion.div>
      )}

      {raceState.isRunning && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          <div className="f1-card p-5">
            <div className="flex items-center justify-between mb-4">
              <LiveLapCounter current={raceState.currentLap} total={raceState.totalLaps} />
              <div className="flex items-center gap-3">
                <LiveWeatherBadge weather={raceState.weather} />
                {raceState.safetyCarActive && (
                  <span className="px-2 py-1 bg-yellow-500/15 border border-yellow-500/20 rounded-lg text-[10px] font-bold text-yellow-400 uppercase animate-pulse">
                    Safety Car
                  </span>
                )}
              </div>
            </div>

            <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
              <motion.div
                animate={{ width: `${(raceState.currentLap / raceState.totalLaps) * 100}%` }}
                className="h-full bg-gradient-to-r from-[#e10600] to-orange-500 rounded-full"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="f1-card p-4">
              <h4 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.15em] mb-3">Live Standings</h4>
              <div className="space-y-1 max-h-80 overflow-y-auto">
                {allCompetitors?.slice(0, 10).map((driver, i) => (
                  <CompetitorMiniCard key={driver.id || i} driver={driver} index={i} />
                ))}
              </div>
            </div>

            <div className="space-y-4">
              {(uiRecommendation || currentRecommendation) && (
                <div className="f1-card p-4">
                  <h4 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.15em] mb-2 flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5 text-[#e10600]" />
                    AI Recommendation
                  </h4>
                  <p className="text-sm font-semibold text-white/85">{uiRecommendation?.title || currentRecommendation.action_name}</p>
                  {uiRecommendation?.subtitle && (
                    <p className="text-[11px] text-white/35 mt-0.5">{uiRecommendation.subtitle}</p>
                  )}
                  {(uiRecommendation?.description || currentRecommendation?.explanation) && (
                    <p className="text-xs text-white/50 mt-2 leading-relaxed">
                      {uiRecommendation?.description || currentRecommendation.explanation}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-2 mt-3">
                    {confidence?.overall != null && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/[0.06] border border-white/[0.08] font-mono">
                        Conf {(confidence.overall > 1 ? confidence.overall : confidence.overall * 100).toFixed(0)}%
                      </span>
                    )}
                    {metrics?.risk_score != null && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/[0.06] border border-white/[0.08] font-mono">
                        Risk {(metrics.risk_score > 1 ? metrics.risk_score : metrics.risk_score * 100).toFixed(0)}%
                      </span>
                    )}
                    {uiRecommendation?.urgency && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md uppercase tracking-wider bg-[#e10600]/15 text-[#e10600]/90 border border-[#e10600]/25">
                        {uiRecommendation.urgency}
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div className="f1-card p-4">
                <h4 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.15em] mb-3">Strategy</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/40">Type</span>
                    <span className="text-white/70 capitalize">{strategy?.type || 'auto'}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/40">Next Pit</span>
                    <span className="text-white/70">Lap {strategy?.nextPitLap || 'N/A'}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/40">Stint</span>
                    <span className="text-white/70">{strategy?.currentStint || 1}/{strategy?.totalStints || 3}</span>
                  </div>
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={stopLiveRace}
                className="w-full px-4 py-2.5 bg-white/[0.04] hover:bg-red-500/10 border border-white/[0.08] hover:border-red-500/20 rounded-xl transition-all flex items-center justify-center gap-2 text-sm text-white/50 hover:text-red-400"
              >
                <Square className="w-3.5 h-3.5" />
                Stop Race
              </motion.button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default LiveRaceWeekend;
