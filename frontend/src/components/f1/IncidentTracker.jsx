import React, { memo, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Car, Clock, MapPin, Shield, Flag, Activity } from 'lucide-react';
import { useRace } from '../../context/RaceContext';

const INCIDENT_TYPES = {
  collision: { label: 'Collision', severity: 'high', icon: Car },
  spin: { label: 'Spin', severity: 'medium', icon: Activity },
  off_track: { label: 'Off Track', severity: 'low', icon: MapPin },
  mechanical: { label: 'Mechanical', severity: 'high', icon: AlertTriangle },
  debris: { label: 'Debris', severity: 'medium', icon: Flag },
  yellow_flag: { label: 'Yellow Flag', severity: 'low', icon: Shield },
};

const SEVERITY_CONFIG = {
  high: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', pulse: true },
  medium: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', pulse: false },
  low: { color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', pulse: false },
};

const IncidentCard = memo(({ incident, index }) => {
  const typeConfig = INCIDENT_TYPES[incident.type] || INCIDENT_TYPES.debris;
  const severityConfig = SEVERITY_CONFIG[typeConfig.severity];
  const Icon = typeConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ delay: index * 0.05 }}
      className={`relative p-3 rounded-lg border ${severityConfig.bg} ${severityConfig.border} overflow-hidden`}
    >
      {severityConfig.pulse && (
        <motion.div
          className="absolute inset-0 bg-red-500/5"
          animate={{ opacity: [0, 1, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
        />
      )}
      
      <div className="relative flex items-start gap-3">
        <div className={`p-2 rounded-lg bg-white/5 ${severityConfig.color}`}>
          <Icon className="w-4 h-4" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${severityConfig.color}`}>
              {typeConfig.label}
            </span>
            <span className="text-[9px] text-white/20">
              Lap {incident.lap}
            </span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded ${severityConfig.bg} ${severityConfig.color} uppercase`}>
              {typeConfig.severity}
            </span>
          </div>
          
          <p className="text-xs text-white/70">{incident.description}</p>
          
          <div className="flex items-center gap-3 mt-2 text-[10px] text-white/40">
            {incident.location && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {incident.location}
              </span>
            )}
            {incident.duration && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {incident.duration}s
              </span>
            )}
            {incident.drivers_involved && (
              <span>{incident.drivers_involved.join(', ')}</span>
            )}
          </div>
        </div>
        
        {incident.resolved && (
          <div className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded text-[9px] text-emerald-400 uppercase">
            Resolved
          </div>
        )}
      </div>
    </motion.div>
  );
});
IncidentCard.displayName = 'IncidentCard';

export const IncidentTracker = ({ externalIncidents = [] }) => {
  const { raceState, events } = useRace();

  // Generate incidents from race events and state
  const incidents = useMemo(() => {
    const incidentList = [...(externalIncidents || [])];

    // Safety car deployment counts as high severity incident
    if (raceState.safetyCarActive) {
      incidentList.push({
        id: 'sc-incident',
        type: 'debris',
        lap: raceState.currentLap,
        description: 'Safety Car deployed due to incident on track',
        location: 'Track',
        severity: 'high',
        resolved: false,
      });
    }

    // Convert relevant events to incidents
    events?.forEach((event, idx) => {
      if (event.type === 'warning' || event.type === 'weather') {
        incidentList.push({
          id: `incident-${idx}`,
          type: event.type === 'weather' ? 'debris' : 'yellow_flag',
          lap: event.lap,
          description: event.description || event.title,
          location: 'Various',
          severity: event.type === 'warning' ? 'medium' : 'low',
          resolved: raceState.currentLap > (event.lap + 2),
        });
      }
    });

    // Sort by lap (newest first)
    return incidentList.sort((a, b) => b.lap - a.lap);
  }, [events, raceState.safetyCarActive, raceState.currentLap, externalIncidents]);

  const activeIncidents = incidents.filter(i => !i.resolved);
  const resolvedIncidents = incidents.filter(i => i.resolved);

  return (
    <div className="f1-card">
      <div className="p-4 pb-3 flex items-center justify-between border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <AlertTriangle className="w-4 h-4 text-yellow-400/60" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Incident Tracker</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">Race incidents & flags</p>
          </div>
        </div>
        
        {activeIncidents.length > 0 && (
          <motion.span
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="px-2 py-1 bg-yellow-500/15 border border-yellow-500/20 rounded-md text-[10px] font-bold text-yellow-400"
          >
            {activeIncidents.length} Active
          </motion.span>
        )}
      </div>

      <div className="p-3 space-y-2 max-h-80 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {incidents.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-8"
            >
              <Shield className="w-8 h-8 text-emerald-500/20 mx-auto mb-2" />
              <p className="text-emerald-400/60 text-xs uppercase tracking-wider">No incidents</p>
              <p className="text-white/10 text-[10px] mt-1">Race proceeding cleanly</p>
            </motion.div>
          ) : (
            <>
              {activeIncidents.map((incident, index) => (
                <IncidentCard key={incident.id} incident={incident} index={index} />
              ))}
              
              {resolvedIncidents.length > 0 && (
                <div className="pt-2 border-t border-white/[0.06]">
                  <p className="text-[10px] text-white/30 uppercase tracking-wider mb-2">
                    Resolved ({resolvedIncidents.length})
                  </p>
                  {resolvedIncidents.map((incident, index) => (
                    <IncidentCard
                      key={incident.id}
                      incident={incident}
                      index={index + activeIncidents.length}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </AnimatePresence>
      </div>

      <div className="px-3 py-2 border-t border-white/[0.06] flex items-center justify-between text-[10px]">
        <div className="flex items-center gap-3">
          <span className="text-white/20">
            {incidents.length} total
          </span>
          {activeIncidents.length > 0 && (
            <span className="text-yellow-400/60">
              {activeIncidents.length} active
            </span>
          )}
        </div>
        <span className="text-white/15">
          Real-time
        </span>
      </div>
    </div>
  );
};

export default memo(IncidentTracker);
