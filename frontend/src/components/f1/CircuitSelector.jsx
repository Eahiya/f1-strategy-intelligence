import React, { useState, memo, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, ChevronDown, Flag } from 'lucide-react';

const CIRCUITS = [
  // European Rounds
  { id: 'monza', name: 'Monza', country: 'Italy', flag: '🇮🇹', laps: 53, length: '5.79 km' },
  { id: 'silverstone', name: 'Silverstone', country: 'UK', flag: '🇬🇧', laps: 52, length: '5.89 km' },
  { id: 'spa', name: 'Spa-Francorchamps', country: 'Belgium', flag: '🇧🇪', laps: 44, length: '7.00 km' },
  { id: 'monaco', name: 'Monaco', country: 'Monaco', flag: '🇲🇨', laps: 78, length: '3.34 km' },
  { id: 'suzuka', name: 'Suzuka', country: 'Japan', flag: '🇯🇵', laps: 53, length: '5.81 km' },
  { id: 'red_bull_ring', name: 'Red Bull Ring', country: 'Austria', flag: '🇦🇹', laps: 71, length: '4.32 km' },
  { id: 'hungaroring', name: 'Hungaroring', country: 'Hungary', flag: '🇭🇺', laps: 70, length: '4.38 km' },
  { id: 'catalunya', name: 'Barcelona', country: 'Spain', flag: '🇪🇸', laps: 66, length: '4.66 km' },
  { id: 'zandvoort', name: 'Zandvoort', country: 'Netherlands', flag: '🇳🇱', laps: 72, length: '4.26 km' },
  { id: 'imola', name: 'Imola', country: 'Italy', flag: '🇮🇹', laps: 63, length: '4.91 km' },
  // Middle East
  { id: 'bahrain', name: 'Bahrain', country: 'Bahrain', flag: '🇧🇭', laps: 57, length: '5.41 km' },
  { id: 'jeddah', name: 'Jeddah', country: 'Saudi Arabia', flag: '🇸🇦', laps: 50, length: '6.17 km' },
  { id: 'abu_dhabi', name: 'Abu Dhabi', country: 'UAE', flag: '🇦🇪', laps: 58, length: '5.28 km' },
  { id: 'qatar', name: 'Qatar', country: 'Qatar', flag: '🇶🇦', laps: 57, length: '5.38 km' },
  // Americas
  { id: 'miami', name: 'Miami', country: 'USA', flag: '🇺🇸', laps: 57, length: '5.41 km' },
  { id: 'austin', name: 'Austin (COTA)', country: 'USA', flag: '🇺🇸', laps: 56, length: '5.51 km' },
  { id: 'montreal', name: 'Montreal', country: 'Canada', flag: '🇨🇦', laps: 70, length: '4.36 km' },
  { id: 'mexico_city', name: 'Mexico City', country: 'Mexico', flag: '🇲🇽', laps: 71, length: '4.30 km' },
  { id: 'interlagos', name: 'Interlagos', country: 'Brazil', flag: '🇧🇷', laps: 71, length: '4.31 km' },
  { id: 'las_vegas', name: 'Las Vegas', country: 'USA', flag: '🇺🇸', laps: 50, length: '6.20 km' },
  // Asia-Pacific
  { id: 'melbourne', name: 'Melbourne', country: 'Australia', flag: '🇦🇺', laps: 58, length: '5.28 km' },
  { id: 'shanghai', name: 'Shanghai', country: 'China', flag: '🇨🇳', laps: 56, length: '5.45 km' },
  { id: 'singapore', name: 'Singapore', country: 'Singapore', flag: '🇸🇬', laps: 62, length: '4.94 km' },
  // Additional
  { id: 'baku', name: 'Baku', country: 'Azerbaijan', flag: '🇦🇿', laps: 51, length: '6.00 km' },
];

export const CircuitSelector = ({ selected, onSelect }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const containerRef = useRef(null);
  const selectedCircuit = CIRCUITS.find(c => c.id === selected) || CIRCUITS[0];

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div ref={containerRef} className="relative">
      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={() => setIsOpen(!isOpen)}
        onHoverStart={() => setIsFocused(true)}
        onHoverEnd={() => setIsFocused(false)}
        className="w-full f1-card p-3 flex items-center gap-3 transition-all"
      >
        <div className="w-10 h-10 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
          <MapPin className="w-4 h-4 text-white/30" />
        </div>
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <span className="text-lg leading-none">{selectedCircuit.flag}</span>
            <span className="text-sm font-bold text-white/80">{selectedCircuit.name}</span>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-white/25 mt-0.5">
            <span>{selectedCircuit.country}</span>
            <span className="w-0.5 h-0.5 bg-white/15 rounded-full" />
            <span>{selectedCircuit.laps} laps</span>
            <span className="w-0.5 h-0.5 bg-white/15 rounded-full" />
            <span>{selectedCircuit.length}</span>
          </div>
        </div>
        <ChevronDown className={`w-4 h-4 text-white/20 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="absolute top-full left-0 right-0 mt-2 bg-[#0c0c0c] border border-white/[0.08] rounded-xl overflow-hidden z-50 shadow-[0_12px_40px_rgba(0,0,0,0.6)]"
          >
            <div className="max-h-[280px] overflow-y-auto p-1">
              {CIRCUITS.map((circuit, idx) => {
                const isSelected = selected === circuit.id;
                return (
                  <motion.button
                    key={circuit.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    onClick={() => {
                      onSelect(circuit.id);
                      setIsOpen(false);
                    }}
                    className={`w-full p-3 rounded-lg flex items-center gap-3 transition-all ${
                      isSelected 
                        ? 'bg-[#e10600]/10 border-l-2 border-[#e10600]' 
                        : 'hover:bg-white/[0.03] border-l-2 border-transparent'
                    }`}
                  >
                    <span className="text-lg leading-none">{circuit.flag}</span>
                    <div className="flex-1 text-left">
                      <p className="text-sm font-semibold text-white/70">{circuit.name}</p>
                      <p className="text-[10px] text-white/20">{circuit.laps} laps • {circuit.length}</p>
                    </div>
                    {isSelected && <Flag className="w-4 h-4 text-[#e10600]" />}
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default memo(CircuitSelector);
