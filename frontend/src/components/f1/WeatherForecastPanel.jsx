import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Cloud, CloudRain, Sun, Droplets, Wind, Thermometer, Loader2, AlertCircle } from 'lucide-react';
import { simulationApi } from '../../services/api';

const WeatherIcon = ({ state, size = 'w-5 h-5' }) => {
  switch (state?.toLowerCase()) {
    case 'dry':
      return <Sun className={`${size} text-amber-400`} />;
    case 'light_rain':
    case 'rain':
      return <CloudRain className={`${size} text-blue-400`} />;
    case 'wet':
      return <Droplets className={`${size} text-blue-500`} />;
    case 'intermediate':
      return <Cloud className={`${size} text-gray-400`} />;
    default:
      return <Cloud className={`${size} text-gray-500`} />;
  }
};

const WeatherTimeline = ({ timeline }) => {
  const sample = timeline.slice(0, 20);
  return (
    <div className="space-y-1">
      <div className="flex gap-0.5 overflow-x-auto pb-2">
        {sample.map((entry, i) => (
          <div
            key={i}
            className="flex flex-col items-center gap-1 min-w-[28px] p-1.5 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
          >
            <span className="text-[9px] text-white/30 font-mono">L{entry.lap}</span>
            <WeatherIcon state={entry.state} size="w-4 h-4" />
            <span className="text-[9px] text-white/50 font-mono">{entry.track_temp}°C</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const RiskBadge = ({ level, label }) => {
  const colors = {
    low: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    medium: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
    high: 'bg-red-500/10 border-red-500/20 text-red-400',
  };
  return (
    <span className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] rounded-md border ${colors[level] || colors.low}`}>
      {label}
    </span>
  );
};

export const WeatherForecastPanel = () => {
  const [loading, setLoading] = useState(false);
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [circuit, setCircuit] = useState('monza');
  const [rainProb, setRainProb] = useState(30);

  const runForecast = useCallback(async () => {
    setLoading(true);
    setError(null);
    setForecast(null);
    try {
      const response = await simulationApi.weather({
        circuit,
        initial_weather: 'dry',
        rain_probability: rainProb / 100,
      });
      setForecast(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to run weather simulation');
    } finally {
      setLoading(false);
    }
  }, [circuit, rainProb]);

  const rainLaps = forecast?.weather_timeline?.filter((w) => w.state !== 'dry').length || 0;
  const dryLaps = (forecast?.weather_timeline?.length || 0) - rainLaps;
  const rainPercentage = forecast?.weather_timeline?.length
    ? Math.round((rainLaps / forecast.weather_timeline.length) * 100)
    : 0;

  const riskLevel = rainPercentage > 40 ? 'high' : rainPercentage > 20 ? 'medium' : 'low';

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 px-1">
        <CloudRain className="w-4 h-4 text-blue-400" />
        <h3 className="text-sm font-bold text-white/80 uppercase tracking-[0.15em]">Weather Forecast</h3>
      </div>

      <div className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Rain Probability</label>
            <span className="text-[11px] font-mono text-blue-400">{rainProb}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={rainProb}
            onChange={(e) => setRainProb(parseInt(e.target.value))}
            className="w-full h-1.5 bg-white/[0.06] rounded-full appearance-none cursor-pointer accent-blue-500"
          />
          <div className="flex justify-between text-[9px] text-white/20">
            <span>Dry</span>
            <span>Wet</span>
          </div>
        </div>

        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          onClick={runForecast}
          disabled={loading}
          className="w-full f1-btn f1-btn-primary"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Simulating Weather...
            </>
          ) : (
            <>
              <Thermometer className="w-4 h-4" />
              Run Forecast
            </>
          )}
        </motion.button>
      </div>

      {error && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="p-3 bg-red-500/[0.08] border border-red-500/20 rounded-xl">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            <p className="text-xs text-red-300">{error}</p>
          </div>
        </motion.div>
      )}

      {forecast && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          <div className="grid grid-cols-3 gap-2">
            <div className="p-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-center">
              <Sun className="w-4 h-4 text-amber-400 mx-auto mb-1" />
              <p className="text-lg font-bold text-white/80">{dryLaps}</p>
              <p className="text-[9px] text-white/30 uppercase tracking-[0.1em]">Dry Laps</p>
            </div>
            <div className="p-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-center">
              <CloudRain className="w-4 h-4 text-blue-400 mx-auto mb-1" />
              <p className="text-lg font-bold text-white/80">{rainLaps}</p>
              <p className="text-[9px] text-white/30 uppercase tracking-[0.1em]">Rain Laps</p>
            </div>
            <div className="p-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-center">
              <Wind className="w-4 h-4 text-gray-400 mx-auto mb-1" />
              <p className="text-lg font-bold text-white/80">{rainPercentage}%</p>
              <p className="text-[9px] text-white/30 uppercase tracking-[0.1em]">Risk</p>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[10px] text-white/40 uppercase tracking-[0.15em]">Rain Risk</span>
            <RiskBadge level={riskLevel} label={riskLevel} />
          </div>

          <WeatherTimeline timeline={forecast.weather_timeline || []} />

          {forecast.recommended_strategy && (
            <div className="p-3 bg-blue-500/[0.06] border border-blue-500/15 rounded-xl">
              <p className="text-[10px] font-bold text-blue-400 uppercase tracking-[0.15em] mb-2">Recommended Strategy</p>
              
              {/* Pit Stops */}
              <div className="mb-2">
                <p className="text-[9px] text-white/30 mb-1">Pit Stops ({forecast.recommended_strategy.estimated_pit_stops || 0})</p>
                <div className="flex flex-wrap gap-1">
                  {forecast.recommended_strategy.pit_laps?.map((lap, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-blue-500/10 rounded text-[10px] text-blue-300/70 font-mono">
                      L{lap}
                    </span>
                  )) || <span className="text-[10px] text-white/20">No pit stops</span>}
                </div>
              </div>
              
              {/* Tire Strategy */}
              <div className="mb-2">
                <p className="text-[9px] text-white/30 mb-1">Tire Strategy</p>
                <div className="flex items-center gap-1 flex-wrap">
                  {forecast.recommended_strategy.tires?.map((tire, idx) => (
                    <span key={idx} className="text-[10px] text-white/50 capitalize">
                      {tire}
                      {idx < (forecast.recommended_strategy.tires?.length || 0) - 1 && (
                        <span className="text-white/20 mx-1">→</span>
                      )}
                    </span>
                  )) || <span className="text-[10px] text-white/20">No tire data</span>}
                </div>
              </div>
              
              {/* Weather Segments */}
              {forecast.recommended_strategy.weather_segments > 0 && (
                <div className="flex items-center gap-2 mt-2 pt-2 border-t border-white/[0.06]">
                  <span className="text-[9px] text-white/30">Weather Changes:</span>
                  <span className="text-[10px] text-white/50">{forecast.recommended_strategy.weather_segments} segments</span>
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default WeatherForecastPanel;
