import React, { memo, useMemo, useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Map, Users, Navigation, Activity, AlertTriangle, Shield, Flag } from 'lucide-react';
import { useRace } from '../../context/RaceContext';
import { useOpenF1Context } from '../../context/OpenF1Context';
import { TRACK_LAYOUTS } from '../../data/tracks/trackLayouts';

const DriverDot = memo(({ driver, position, isPlayer, showTelemetry, telemetry }) => {
  const color = driver.team_color || driver.teamColor || '#888888';

  return (
    <motion.div
      className="absolute z-20"
      initial={false}
      animate={{
        left: `${position.x}%`,
        top: `${position.y}%`
      }}
      transition={{ type: 'tween', ease: 'linear', duration: 1.0 }}
      style={{ transform: 'translate(-50%, -50%)' }}
    >
      <div className="relative group">
        <div
          className={`flex items-center justify-center rounded-full border-2 ${isPlayer ? 'w-5 h-5 sm:w-6 sm:h-6 z-30' : 'w-4 h-4 sm:w-5 sm:h-5 z-20'
            }`}
          style={{
            backgroundColor: color,
            borderColor: isPlayer ? '#fff' : 'rgba(255,255,255,0.4)',
            boxShadow: isPlayer ? `0 0 12px ${color}` : 'none',
          }}
        >
          <span className={`font-black text-black ${isPlayer ? 'text-[9px] sm:text-[10px]' : 'text-[8px] sm:text-[9px]'}`}>
            {driver.position}
          </span>

          {isPlayer && (
            <motion.div
              className="absolute -inset-1.5 rounded-full border border-white/40 pointer-events-none"
              animate={{ scale: [1, 1.4, 1], opacity: [0.6, 0, 0.6] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            />
          )}
        </div>

        {/* Telemetry Overlay / Label */}
        <div className={`absolute top-full left-1/2 -translate-x-1/2 mt-1.5 pointer-events-none transition-opacity ${showTelemetry || isPlayer ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
          } z-40`}>
          <div className="flex flex-col items-center bg-black/90 rounded border border-white/10 overflow-hidden shadow-xl">
            <div className="px-2 py-0.5 w-full text-center" style={{ backgroundColor: `${color}40` }}>
              <span className="text-[9px] font-black text-white whitespace-nowrap">
                {driver.driver_code || driver.driverCode || driver.driver?.substring(0, 3).toUpperCase()}
              </span>
            </div>

            {(showTelemetry || isPlayer) && telemetry && (
              <div className="px-2 py-1 flex items-center gap-2 text-[8px] sm:text-[9px] font-mono">
                <span className="text-white/80">{telemetry.speed || 0} <span className="text-white/40">km/h</span></span>
                {telemetry.drs && <span className="text-emerald-400 font-bold">DRS</span>}
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
});
DriverDot.displayName = 'DriverDot';

const IncidentMarker = memo(({ incident }) => {
  // Approximate incident location logic
  const top = 20 + Math.random() * 60;
  const left = 20 + Math.random() * 60;

  return (
    <motion.div
      className="absolute z-10"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      style={{ top: `${top}%`, left: `${left}%`, transform: 'translate(-50%, -50%)' }}
    >
      <div className="relative flex items-center justify-center w-6 h-6 rounded-full bg-red-500/20 border border-red-500/40 text-red-500">
        <AlertTriangle className="w-3 h-3" />
        <motion.div
          className="absolute inset-0 rounded-full border border-red-500/60"
          animate={{ scale: [1, 2], opacity: [1, 0] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
        />
      </div>
    </motion.div>
  );
});
IncidentMarker.displayName = 'IncidentMarker';

export const TrackMapVisualization = () => {
  const { raceState, allCompetitors, player, events } = useRace();
  const openF1 = useOpenF1Context();

  const [showTelemetry, setShowTelemetry] = useState(false);
  const pathRef = useRef(null);

  // Circuit geometry resolution
  let circuitId = (raceState.circuit || 'monza').toLowerCase().replace(/ /g, '_');
  if (openF1?.session?.circuit && openF1.session.circuit !== 'Unknown') {
    circuitId = openF1.session.circuit.toLowerCase().replace(/ /g, '_');
  }
  const trackLayout = TRACK_LAYOUTS[circuitId] || TRACK_LAYOUTS.default;

  // Active incidents from simulation + openF1
  const activeIncidents = useMemo(() => {
    const combined = [];
    if (raceState.safetyCarActive) {
      combined.push({ id: 'sc', type: 'sc' });
    }
    // Filter recent simulation incidents
    events?.forEach(e => {
      if ((e.type === 'incident' || e.type === 'warning') && raceState.currentLap - e.lap < 2) {
        combined.push({ id: Math.random().toString(), ...e });
      }
    });
    // Add OpenF1 flags
    if (openF1?.raceControl) {
      const recent = openF1.raceControl.filter(m =>
        (m.flag === 'YELLOW' || m.flag === 'DOUBLE YELLOW') &&
        (new Date() - new Date(m.time)) < 60000 // Last minute
      );
      recent.forEach(r => combined.push({ id: r.id, type: 'flag', data: r }));
    }
    return combined;
  }, [events, raceState.safetyCarActive, raceState.currentLap, openF1?.raceControl]);

  // Calculate positions
  const getTrackPosition = useCallback((progress) => {
    if (!pathRef.current) return { x: 50, y: 50 }; // Default center

    // Safety clamp
    const safeProgress = Math.max(0, Math.min(1, progress || 0));

    try {
      const length = pathRef.current.getTotalLength();
      const point = pathRef.current.getPointAtLength(safeProgress * length);
      return { x: point.x, y: point.y };
    } catch (e) {
      return { x: 50, y: 50 };
    }
  }, []);

  // Driver positions logic (Hybrid)
  const driverPositions = useMemo(() => {
    return allCompetitors.map((driver, index) => {
      let progress = 0;
      let telemetry = null;

      // OpenF1 Live Mode Logic
      if (openF1 && (openF1.mode === 'live' || openF1.mode === 'hybrid') && openF1.positions.length > 0) {
        const livePos = openF1.positions.find(p => p.driver_number === driver.id || p.position === driver.position);
        if (livePos) {
          // Approximate progress based on leader gap/interval (very rough)
          const gap = parseFloat(livePos.gap_to_leader) || (index * 2);
          progress = 1 - (gap / 100); // Hack for demo without real GPS
        }
      }

      // Simulation Mode Logic
      if (progress === 0) {
        const lapProgress = (raceState.currentLap / (raceState.totalLaps || 1)) % 1;
        const positionOffset = (index * 0.04) % 1; // Spread drivers
        progress = (lapProgress + (1 - positionOffset)) % 1;
      }

      return {
        driver,
        position: getTrackPosition(progress),
        isPlayer: driver.isPlayer || driver.id === player?.id,
        telemetry: {
          speed: Math.floor(220 + Math.random() * 80), // Simulated telemetry
          drs: progress > 0.8 && progress < 0.95
        }
      };
    });
  }, [allCompetitors, raceState.currentLap, raceState.totalLaps, openF1, getTrackPosition, player?.id]);

  return (
    <div className="flex flex-col h-full bg-black/20 rounded-xl border border-white/[0.06] overflow-hidden">
      {/* Header */}
      <div className="p-3 sm:p-4 pb-3 flex flex-wrap items-center justify-between gap-3 bg-white/[0.02] border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 sm:w-10 sm:h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center border border-emerald-500/20">
            <Map className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-bold text-white/90">{trackLayout.name}</h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">LIVE TRACK</span>
              <span className="w-1 h-1 rounded-full bg-white/20"></span>
              <span className="text-[10px] text-white/40 uppercase tracking-wider">{raceState.totalLaps} Laps</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowTelemetry(!showTelemetry)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[10px] font-bold uppercase transition-colors ${showTelemetry
                ? 'bg-blue-500/20 border-blue-500/40 text-blue-400'
                : 'bg-white/[0.04] border-white/[0.1] text-white/40 hover:text-white/70'
              }`}
          >
            <Activity className="w-3 h-3" />
            <span className="hidden sm:inline">Telemetry</span>
          </button>

          <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/[0.04] rounded-lg border border-white/[0.08]">
            <Users className="w-3 h-3 text-white/40" />
            <span className="text-[10px] font-bold text-white/70">{allCompetitors.length}</span>
          </div>
        </div>
      </div>

      {/* Track Area */}
      <div className="relative flex-1 min-h-[300px] sm:min-h-[400px] p-4 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:20px_20px]">

        {/* Safety Car Banner */}
        <AnimatePresence>
          {raceState.safetyCarActive && (
            <motion.div
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              className="absolute top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-1.5 bg-yellow-500/20 border border-yellow-500/40 rounded-full backdrop-blur-sm"
            >
              <Shield className="w-4 h-4 text-yellow-400" />
              <span className="text-xs font-black text-yellow-400 uppercase tracking-widest">Safety Car Active</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* SVG Track Container */}
        <div className="absolute inset-4 sm:inset-8 flex items-center justify-center">
          <svg
            viewBox="0 0 100 100"
            className="w-full h-full max-w-3xl overflow-visible"
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Defs for gradients/glows */}
            <defs>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Hidden path for position calculation */}
            <path
              ref={pathRef}
              d={trackLayout.path}
              fill="none"
              stroke="none"
            />

            {/* Outer track border (curbs) */}
            <path
              d={trackLayout.path}
              fill="none"
              stroke="rgba(255,255,255,0.15)"
              strokeWidth="5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Inner track surface */}
            <path
              d={trackLayout.path}
              fill="none"
              stroke="rgba(25,25,25,0.8)"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Pit Lane if available */}
            {trackLayout.pitLane && (
              <path
                d={trackLayout.pitLane}
                fill="none"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray="1 1"
              />
            )}

            {/* Sector Highlighting (using dasharray to draw segments) */}
            {trackLayout.sectors?.map((sector, idx) => (
              <path
                key={`sector-${idx}`}
                d={trackLayout.path}
                fill="none"
                stroke={sector.color}
                strokeWidth="1"
                strokeOpacity="0.5"
                strokeDasharray="4 8"
              // This is a visual approximation for sectors
              />
            ))}
          </svg>

          {/* Incidents Overlay */}
          <AnimatePresence>
            {activeIncidents.map(inc => (
              <IncidentMarker key={inc.id} incident={inc} />
            ))}
          </AnimatePresence>

          {/* Drivers Overlay */}
          {driverPositions.map(({ driver, position, isPlayer, telemetry }, index) => (
            <DriverDot
              key={driver.id || index}
              driver={driver}
              position={position}
              isPlayer={isPlayer}
              showTelemetry={showTelemetry}
              telemetry={telemetry}
            />
          ))}
        </div>

        {/* Legend Overlay */}
        <div className="absolute bottom-4 left-4 flex flex-col gap-2 z-40">
          <div className="flex items-center gap-2 p-1.5 bg-black/60 backdrop-blur-md rounded border border-white/10">
            {trackLayout.sectors?.map((sector, idx) => (
              <div key={idx} className="flex items-center gap-1.5 px-1.5">
                <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: sector.color }} />
                <span className="text-[9px] text-white/50 font-bold">{sector.name}</span>
              </div>
            ))}
          </div>
          {trackLayout.drsZones?.length > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 backdrop-blur-md rounded border border-emerald-500/20 w-fit">
              <Activity className="w-3 h-3 text-emerald-400" />
              <span className="text-[9px] text-emerald-400 font-bold uppercase tracking-wider">
                {trackLayout.drsZones.length} DRS Zones
              </span>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default memo(TrackMapVisualization);
