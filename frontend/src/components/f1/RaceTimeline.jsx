import React, { memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Flag, AlertTriangle, Umbrella, Zap, Timer, ChevronRight } from 'lucide-react';
import { useRace } from '../../context/RaceContext';

const RaceTimeline = () => {
  const { events, raceState } = useRace();
  const currentLap = raceState.currentLap;

  const getEventIcon = (type) => {
    switch (type) {
      case 'start': return Flag;
      case 'pit': return Timer;
      case 'warning': return AlertTriangle;
      case 'weather': return Umbrella;
      case 'overtake': return Zap;
      default: return ChevronRight;
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case 'start': return 'bg-emerald-500/10 text-emerald-400/70 border-emerald-500/20';
      case 'pit': return 'bg-blue-500/10 text-blue-400/70 border-blue-500/20';
      case 'warning': return 'bg-yellow-500/10 text-yellow-400/70 border-yellow-500/20';
      case 'weather': return 'bg-cyan-500/10 text-cyan-400/70 border-cyan-500/20';
      case 'overtake': return 'bg-[#e10600]/10 text-[#e10600]/70 border-[#e10600]/20';
      default: return 'bg-white/[0.03] text-white/30 border-white/[0.05]';
    }
  };

  return (
    <div className="f1-card">
      <div className="p-4 pb-3 flex items-center gap-3 border-b border-white/[0.06]">
        <div className="w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
          <Flag className="w-4 h-4 text-white/30" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white/70">Race Timeline</h3>
          <p className="text-[10px] text-white/20 uppercase tracking-wider">Key events</p>
        </div>
      </div>

      <div className="p-4 max-h-80 overflow-y-auto">
        <div className="relative">
          <div className="absolute left-[18px] top-2 bottom-2 w-px bg-white/[0.04]" />

          <AnimatePresence>
            {events.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-10"
              >
                <Flag className="w-7 h-7 text-white/[0.08] mx-auto mb-2" />
                <p className="text-white/15 text-xs uppercase tracking-wider">No events yet</p>
              </motion.div>
            ) : events.map((event, index) => {
              const Icon = getEventIcon(event.type);
              const isPast = currentLap >= event.lap;
              const isCurrent = currentLap === event.lap;

              return (
                <motion.div
                  key={`${event.lap}-${index}`}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`relative flex items-start gap-3 mb-4 last:mb-0 ${
                    isCurrent ? 'opacity-100' : isPast ? 'opacity-50' : 'opacity-30'
                  }`}
                >
                  <div className={`relative z-10 w-9 h-9 rounded-xl flex items-center justify-center border flex-shrink-0 ${getEventColor(event.type)} ${
                    isCurrent ? 'ring-1 ring-white/10' : ''
                  }`}>
                    <Icon className="w-4 h-4" />
                    {isCurrent && (
                      <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-[#e10600] rounded-full animate-pulse" />
                    )}
                  </div>

                  <div className="flex-1 pt-0.5">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[10px] font-mono text-white/20">Lap {event.lap}</span>
                      {isCurrent && (
                        <span className="px-1.5 py-0.5 bg-[#e10600]/15 text-[#e10600]/80 text-[9px] rounded font-bold uppercase tracking-wider">
                          Now
                        </span>
                      )}
                    </div>
                    <h4 className="font-semibold text-white/60 text-xs">{event.title}</h4>
                    <p className="text-[10px] text-white/20 mt-0.5 leading-relaxed">{event.description}</p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>

      <div className="px-4 py-2.5 border-t border-white/[0.06] flex items-center justify-between text-[10px]">
        <span className="text-white/15 uppercase tracking-wider">Current Lap</span>
        <span className="font-mono text-white/30">{currentLap}</span>
      </div>
    </div>
  );
};

export default memo(RaceTimeline);
