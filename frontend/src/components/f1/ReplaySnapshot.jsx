import React, { memo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
  // eslint-disable-next-line no-unused-vars
  // eslint-disable-next-line no-unused-vars
import { Camera, Play, Download, X, Clock, Flag, Activity, ChevronLeft, ChevronRight } from 'lucide-react';
import { useRace } from '../../context/RaceContext';

const SnapshotCard = memo(({ snapshot, index, onLoad, onDelete }) => {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="group relative p-3 bg-white/[0.03] hover:bg-white/[0.05] rounded-xl border border-white/[0.06] hover:border-white/[0.12] transition-all cursor-pointer"
      onClick={() => onLoad(snapshot)}
    >
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 bg-white/[0.04] rounded-lg flex items-center justify-center border border-white/[0.06] flex-shrink-0">
          <Camera className="w-5 h-5 text-white/30" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Flag className="w-3 h-3 text-[#e10600]/60" />
            <span className="text-xs font-bold text-white/70">Lap {snapshot.lap}</span>
          </div>
          
          <p className="text-[10px] text-white/40 truncate">{snapshot.description}</p>
          
          <div className="flex items-center gap-2 mt-2 text-[9px] text-white/30">
            <Clock className="w-3 h-3" />
            {snapshot.timestamp}
          </div>
        </div>
        
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(snapshot.id);
          }}
          className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/10 rounded-lg transition-all"
        >
          <X className="w-3.5 h-3.5 text-white/30 hover:text-red-400" />
        </button>
      </div>
      
      {/* Hover play overlay */}
      <div className="absolute inset-0 bg-black/40 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <Play className="w-6 h-6 text-white/70" />
      </div>
    </motion.div>
  );
});
SnapshotCard.displayName = 'SnapshotCard';

const SnapshotDetail = memo(({ snapshot, onClose, onExport }) => {
  if (!snapshot) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="w-full max-w-2xl bg-[#0c0c0c] border border-white/[0.08] rounded-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Camera className="w-5 h-5 text-[#e10600]/60" />
            <div>
              <h3 className="text-sm font-bold text-white/80">Replay Lap {snapshot.lap}</h3>
              <p className="text-[10px] text-white/30">{snapshot.timestamp}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => onExport(snapshot)}
              className="p-2 hover:bg-white/[0.05] rounded-lg transition-colors"
              title="Export"
            >
              <Download className="w-4 h-4 text-white/40" />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/[0.05] rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-white/40" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Snapshot data visualization */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-white/[0.03] rounded-xl border border-white/[0.06]">
              <p className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Position</p>
              <p className="text-2xl font-bold text-white/80">P{snapshot.data?.position || '-'}</p>
            </div>
            <div className="p-4 bg-white/[0.03] rounded-xl border border-white/[0.06]">
              <p className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Lap Time</p>
              <p className="text-2xl font-bold text-emerald-400">
                {snapshot.data?.lapTime ? `${snapshot.data.lapTime.toFixed(2)}s` : '-'}
              </p>
            </div>
            <div className="p-4 bg-white/[0.03] rounded-xl border border-white/[0.06]">
              <p className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Tire</p>
              <p className="text-2xl font-bold text-white/80 capitalize">
                {snapshot.data?.tire || '-'}
              </p>
            </div>
          </div>

          {snapshot.data?.competitors && (
            <div className="p-4 bg-white/[0.03] rounded-xl border border-white/[0.06]">
              <h4 className="text-xs font-bold text-white/50 uppercase tracking-wider mb-3">Competitors</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {snapshot.data.competitors.map((comp, idx) => (
                  <div key={idx} className="flex items-center justify-between py-1.5 border-b border-white/[0.04] last:border-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-white/40 w-6">P{comp.position}</span>
                      <span className="text-xs text-white/70">{comp.driver || comp.name}</span>
                    </div>
                    <span className="text-xs text-white/40">+{comp.gap_to_leader?.toFixed(1) || '-'}s</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <p className="text-[10px] text-white/30">{snapshot.description}</p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-4 py-2 bg-[#e10600]/10 hover:bg-[#e10600]/20 border border-[#e10600]/30 rounded-lg text-xs text-[#e10600] transition-colors"
            >
              Load This State
            </motion.button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
});
SnapshotDetail.displayName = 'SnapshotDetail';

export const ReplaySnapshot = () => {
  const { raceState, player, allCompetitors, chartData } = useRace();
  const [snapshots, setSnapshots] = useState([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [autoCapture, setAutoCapture] = useState(true);

  // Auto-capture on significant events
  React.useEffect(() => {
    if (!autoCapture || !raceState.isRunning) return;
    
    // Capture on pit stops, position changes, or every 5 laps
    const shouldCapture = 
      raceState.currentLap % 5 === 0 ||
      raceState.lifecycleStatus === 'PITTING';
    
    if (shouldCapture && raceState.currentLap > 0) {
      const existingSnapshot = snapshots.find(s => s.lap === raceState.currentLap);
      if (!existingSnapshot) {
        captureSnapshot();
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raceState.currentLap, raceState.lifecycleStatus, autoCapture, raceState.isRunning]);

  const captureSnapshot = useCallback(() => {
    const newSnapshot = {
      id: `snapshot_${Date.now()}`,
      lap: raceState.currentLap,
      timestamp: new Date().toLocaleTimeString(),
      description: getSnapshotDescription(raceState, player),
      data: {
        position: player?.position,
        lapTime: player?.lapTime,
        tire: player?.tire,
        tireAge: player?.tireAge,
        gapToLeader: player?.gapToLeader,
        competitors: allCompetitors.slice(0, 5).map(c => ({
          position: c.position,
          driver: c.driver || c.name,
          gap_to_leader: c.gap_to_leader || c.gapToLeader,
        })),
        chartDataPoint: chartData[chartData.length - 1],
      },
    };

    setSnapshots(prev => [newSnapshot, ...prev].slice(0, 20)); // Keep last 20
  }, [raceState, player, allCompetitors, chartData]);

  const deleteSnapshot = useCallback((id) => {
    setSnapshots(prev => prev.filter(s => s.id !== id));
  }, []);

  const exportSnapshot = useCallback((snapshot) => {
    const dataStr = JSON.stringify(snapshot, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `f1-snapshot-lap-${snapshot.lap}-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, []);

  const getSnapshotDescription = (raceState, player) => {
    if (raceState.lifecycleStatus === 'PITTING') return 'Pit stop recorded';
    if (player?.position === 1) return 'Leading the race';
    if (raceState.safetyCarActive) return 'Safety Car period';
    return `Lap ${raceState.currentLap} - Race progress`;
  };

  return (
    <div className="f1-card">
      <div className="p-4 pb-3 flex items-center justify-between border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/[0.04] rounded-xl flex items-center justify-center border border-white/[0.06]">
            <Camera className="w-4 h-4 text-purple-400/60" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white/70">Replay Snapshots</h3>
            <p className="text-[10px] text-white/20 uppercase tracking-wider">Auto-captured moments</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={captureSnapshot}
            disabled={!raceState.isRunning}
            className="p-2 bg-white/[0.03] hover:bg-white/[0.06] disabled:opacity-30 rounded-lg border border-white/[0.06] transition-colors"
            title="Capture Now"
          >
            <Camera className="w-4 h-4 text-white/50" />
          </button>
          
          <button
            onClick={() => setAutoCapture(!autoCapture)}
            className={`p-2 rounded-lg border transition-colors ${
              autoCapture 
                ? 'bg-emerald-500/10 border-emerald-500/20' 
                : 'bg-white/[0.03] border-white/[0.06]'
            }`}
            title={autoCapture ? 'Auto-capture ON' : 'Auto-capture OFF'}
          >
            <Activity className={`w-4 h-4 ${autoCapture ? 'text-emerald-400' : 'text-white/30'}`} />
          </button>
        </div>
      </div>

      <div className="p-3 space-y-2 max-h-64 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {snapshots.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-8"
            >
              <Camera className="w-8 h-8 text-white/[0.08] mx-auto mb-2" />
              <p className="text-white/15 text-xs uppercase tracking-wider">No snapshots yet</p>
              <p className="text-white/10 text-[10px] mt-1">
                {raceState.isRunning ? 'Capturing automatically...' : 'Start race to capture'}
              </p>
            </motion.div>
          ) : (
            <>
              {snapshots.slice(0, 5).map((snapshot, index) => (
                <SnapshotCard
                  key={snapshot.id}
                  snapshot={snapshot}
                  index={index}
                  onLoad={setSelectedSnapshot}
                  onDelete={deleteSnapshot}
                />
              ))}
              
              {snapshots.length > 5 && (
                <p className="text-center text-[10px] text-white/20 pt-2">
                  +{snapshots.length - 5} more snapshots
                </p>
              )}
            </>
          )}
        </AnimatePresence>
      </div>

      <div className="px-3 py-2 border-t border-white/[0.06] flex items-center justify-between text-[10px]">
        <span className="text-white/20">
          {snapshots.length} snapshot{snapshots.length !== 1 ? 's' : ''}
        </span>
        <span className="text-white/15">
          {autoCapture ? 'Auto-capturing' : 'Manual mode'}
        </span>
      </div>

      <AnimatePresence>
        {selectedSnapshot && (
          <SnapshotDetail
            snapshot={selectedSnapshot}
            onClose={() => setSelectedSnapshot(null)}
            onExport={exportSnapshot}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default memo(ReplaySnapshot);
