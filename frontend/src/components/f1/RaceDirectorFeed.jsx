import React, { memo, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, AlertTriangle, Flag, CloudRain, Shield, Clock, Activity } from 'lucide-react';
import { useRace } from '../../context/RaceContext';

const MESSAGE_TYPES = {
  race_control: { icon: Radio, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  incident: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  safety_car: { icon: Shield, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
  vsc: { icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
  weather: { icon: CloudRain, color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
  flag: { icon: Flag, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
  system: { icon: Activity, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
};

const RaceDirectorMessage = memo(({ message, index }) => {
  const config = MESSAGE_TYPES[message.type] || MESSAGE_TYPES.system;
  const Icon = config.icon;
  const isNew = message.isNew || false;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ delay: index * 0.05 }}
      className={`relative flex items-start gap-3 p-3 rounded-lg border ${config.bg} ${config.border} ${
        isNew ? 'ring-1 ring-white/10' : ''
      }`}
    >
      {isNew && (
        <motion.span
          initial={{ scale: 1 }}
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ repeat: 2, duration: 0.5 }}
          className="absolute -top-1 -right-1 w-2 h-2 bg-[#e10600] rounded-full"
        />
      )}
      
      <div className={`p-2 rounded-lg bg-white/5 ${config.color}`}>
        <Icon className="w-4 h-4" />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-[10px] font-bold uppercase tracking-wider ${config.color}`}>
            {message.type.replace('_', ' ')}
          </span>
          <span className="text-[9px] text-white/20">
            {message.time || `L${message.lap || '?'}`}
          </span>
        </div>
        <p className="text-xs text-white/70 leading-relaxed">{message.text}</p>
        {message.details && (
          <p className="text-[10px] text-white/40 mt-1">{message.details}</p>
        )}
      </div>
    </motion.div>
  );
});
RaceDirectorMessage.displayName = 'RaceDirectorMessage';

export const RaceDirectorFeed = ({ externalMessages = [] }) => {
  const { raceState, events } = useRace();

  // Convert events to race director messages with enhanced context
  const directorMessages = useMemo(() => {
    const messages = [...(externalMessages || [])];
    
    // Add safety car / VSC status as persistent message
    if (raceState.safetyCarActive) {
      messages.push({
        id: 'sc-active',
        type: 'safety_car',
        text: 'Safety Car deployed - Field bunched',
        details: 'Overtaking prohibited. Pit stops may be advantageous.',
        lap: raceState.currentLap,
        persistent: true,
        priority: 'high',
      });
    }

    // Add VSC if active (can be inferred from weather or other conditions)
    if (raceState.weather?.state === 'mixed' && raceState.currentLap > 10) {
      messages.push({
        id: 'vsc-check',
        type: 'vsc',
        text: 'Virtual Safety Car conditions monitored',
        details: 'Delta times enforced. Maintain position gaps.',
        lap: raceState.currentLap,
        priority: 'medium',
      });
    }

    // Convert race events to director messages
    events?.forEach((event, idx) => {
      let message = null;
      
      switch (event.type) {
        case 'overtake':
          message = {
            id: `event-${idx}`,
            type: 'race_control',
            text: event.title || 'Position change detected',
            details: event.description,
            lap: event.lap,
            priority: 'normal',
          };
          break;
        case 'pit_stop':
          message = {
            id: `event-${idx}`,
            type: 'system',
            text: event.title || 'Pit stop completed',
            details: event.description,
            lap: event.lap,
            priority: 'normal',
          };
          break;
        case 'weather':
          message = {
            id: `event-${idx}`,
            type: 'weather',
            text: event.title || 'Weather update',
            details: event.description,
            lap: event.lap,
            priority: 'high',
          };
          break;
        case 'warning':
          message = {
            id: `event-${idx}`,
            type: 'incident',
            text: event.title || 'Track incident',
            details: event.description,
            lap: event.lap,
            priority: 'high',
          };
          break;
        default:
          if (event.title) {
            message = {
              id: `event-${idx}`,
              type: 'race_control',
              text: event.title,
              details: event.description,
              lap: event.lap,
              priority: 'normal',
            };
          }
      }
      
      if (message) {
        messages.push(message);
      }
    });

    // Sort by priority and lap
    return messages.sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, normal: 2 };
      if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }
      return (b.lap || 0) - (a.lap || 0);
    });
  }, [events, raceState.safetyCarActive, raceState.currentLap, raceState.weather, externalMessages]);

  return (
    <div className="f1-card">
      <div className="p-4 pb-3 flex items-center justify-between border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Radio className="w-4 h-4 text-[#e10600]/60" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Race Director</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">Live feed</p>
          </div>
        </div>
        
        {raceState.safetyCarActive && (
          <motion.span
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ repeat: Infinity, duration: 1 }}
            className="px-2 py-1 bg-yellow-500/15 border border-yellow-500/20 rounded-md text-[10px] font-bold text-yellow-400 uppercase tracking-wider"
          >
            SC Active
          </motion.span>
        )}
      </div>

      <div className="p-3 space-y-2 max-h-80 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {directorMessages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-8"
            >
              <Radio className="w-8 h-8 text-white/[0.08] mx-auto mb-2" />
              <p className="text-white/15 text-xs uppercase tracking-wider">No active messages</p>
              <p className="text-white/10 text-[10px] mt-1">Race proceeding normally</p>
            </motion.div>
          ) : (
            directorMessages.map((message, index) => (
              <RaceDirectorMessage
                key={message.id}
                message={message}
                index={index}
              />
            ))
          )}
        </AnimatePresence>
      </div>

      <div className="px-3 py-2 border-t border-white/[0.06] flex items-center justify-between text-[10px]">
        <span className="text-white/20 uppercase tracking-wider">
          {directorMessages.length} message{directorMessages.length !== 1 ? 's' : ''}
        </span>
        <span className="text-white/15">
          Auto-updating
        </span>
      </div>
    </div>
  );
};

export default memo(RaceDirectorFeed);
