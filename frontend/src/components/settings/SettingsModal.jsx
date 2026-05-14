import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Settings, Gauge, Bell, Volume2, Moon, Activity, Shield, Download, Upload, RotateCcw, Monitor, RefreshCw } from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';

// Extracted UI Components to prevent re-mounting on every render
const SettingRow = ({ icon: Icon, label, description, children }) => (
  <div className="flex items-center gap-4 p-4 bg-white/[0.03] rounded-xl border border-white/[0.06] hover:bg-white/[0.05] transition-colors">
    <div className="w-10 h-10 bg-white/[0.05] rounded-lg flex items-center justify-center flex-shrink-0">
      <Icon className="w-5 h-5 text-white/60" />
    </div>
    <div className="flex-1 min-w-0">
      <label className="font-medium text-white/90 block truncate">{label}</label>
      {description && <p className="text-xs text-white/40 mt-0.5 truncate">{description}</p>}
    </div>
    <div className="flex-shrink-0 ml-4">
      {children}
    </div>
  </div>
);

const Toggle = ({ checked, onChange }) => (
  <button
    type="button"
    onClick={() => onChange(!checked)}
    className={`relative w-12 h-6 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#e10600]/50 ${
      checked ? 'bg-[#e10600]' : 'bg-white/10'
    }`}
  >
    <motion.div
      initial={false}
      className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow-sm"
      animate={{ x: checked ? 24 : 0 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
    />
  </button>
);

const Slider = ({ value, min, max, step, onChange, unit = '' }) => (
  <div className="flex items-center gap-3">
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      className="w-24 md:w-32 h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/50"
    />
    <span className="text-sm font-mono text-white/80 w-16 text-right tabular-nums">
      {value}{unit}
    </span>
  </div>
);

const Select = ({ value, options, onChange }) => (
  <select
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className="bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-[#e10600]"
  >
    {options.map(opt => (
      <option key={opt.value} value={opt.value} className="bg-[#0a0a0a] text-white">
        {opt.label}
      </option>
    ))}
  </select>
);

const SettingsModal = ({ isOpen, onClose }) => {
  const { 
    settings, 
    updateSetting, 
    resetSettings, 
    exportSettings, 
    importSettings,
    isDirty 
  } = useSettings();

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleImport = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const result = importSettings(event.target.result);
        if (result.success) {
          console.log('Settings imported successfully');
        } else {
          console.error('Failed to import settings: ' + result.error);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleExport = () => {
    const data = exportSettings();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'f1-strategy-settings.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-3xl max-h-[90vh] bg-[#0a0a0a] border border-white/[0.1] rounded-2xl shadow-[0_0_40px_rgba(0,0,0,0.5)] overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 md:p-6 border-b border-white/[0.08] bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#e10600]/10 rounded-xl flex items-center justify-center border border-[#e10600]/20 shadow-[0_0_15px_rgba(225,6,0,0.15)]">
                  <Settings className="w-5 h-5 text-[#e10600]" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight">System Settings</h2>
                  <p className="text-xs text-white/40">
                    Customize platform experience
                    {isDirty && <span className="text-[#e10600] ml-2 font-medium">(Unsaved Changes)</span>}
                  </p>
                </div>
              </div>
              <button 
                onClick={onClose} 
                className="p-2 hover:bg-white/10 rounded-xl transition-colors text-white/40 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-5 md:p-6 space-y-8 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
              
              {/* Simulation Section */}
              <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.15em] mb-3 flex items-center gap-2">
                  <Gauge className="w-4 h-4 text-emerald-400" /> Core Simulation
                </h3>
                <div className="space-y-2">
                  <SettingRow icon={Activity} label="Simulation Speed" description="Playback delay between lap updates">
                    <Slider value={settings.simulationSpeed / 1000} min={0.1} max={5} step={0.1} unit="s" onChange={(v) => updateSetting('simulationSpeed', v * 1000)} />
                  </SettingRow>
                  <SettingRow icon={RefreshCw} label="Chart Refresh Rate" description="Frequency of telemetry updates">
                    <Slider value={settings.dataRefreshRate / 1000} min={1} max={10} step={1} unit="s" onChange={(v) => updateSetting('dataRefreshRate', v * 1000)} />
                  </SettingRow>
                  <SettingRow icon={Shield} label="Risk Threshold" description="AI alert level for risky strategies">
                    <Slider value={settings.riskThreshold} min={0} max={100} step={5} unit="%" onChange={(v) => updateSetting('riskThreshold', v)} />
                  </SettingRow>
                  <SettingRow icon={RotateCcw} label="Auto Refresh Data" description="Fetch live updates automatically">
                    <Toggle checked={settings.autoRefresh} onChange={(v) => updateSetting('autoRefresh', v)} />
                  </SettingRow>
                </div>
              </section>

              {/* Interface Section */}
              <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.15em] mb-3 flex items-center gap-2">
                  <Monitor className="w-4 h-4 text-blue-400" /> Interface & Display
                </h3>
                <div className="space-y-2">
                  <SettingRow icon={Moon} label="Theme" description="Application visual style">
                    <Select 
                      value={settings.theme} 
                      onChange={(v) => updateSetting('theme', v)}
                      options={[
                        { value: 'dark', label: 'Dark Mode' },
                        { value: 'light', label: 'Light Mode' },
                        { value: 'system', label: 'System Default' }
                      ]}
                    />
                  </SettingRow>
                  <SettingRow icon={Activity} label="Chart Animations" description="Smooth rendering for telemetry graphs">
                    <Toggle checked={settings.chartAnimations} onChange={(v) => updateSetting('chartAnimations', v)} />
                  </SettingRow>
                  <SettingRow icon={Gauge} label="Show Predictions" description="Display AI-driven strategic foresight">
                    <Toggle checked={settings.showPredictions} onChange={(v) => updateSetting('showPredictions', v)} />
                  </SettingRow>
                </div>
              </section>

              {/* Notifications Section */}
              <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.15em] mb-3 flex items-center gap-2">
                  <Bell className="w-4 h-4 text-amber-400" /> Alerts
                </h3>
                <div className="space-y-2">
                  <SettingRow icon={Bell} label="Enable Notifications" description="Show popups for critical race events">
                    <Toggle checked={settings.notificationsEnabled} onChange={(v) => updateSetting('notificationsEnabled', v)} />
                  </SettingRow>
                  <SettingRow icon={Volume2} label="Sound Effects" description="Audio cues for warnings and alerts">
                    <Toggle checked={settings.soundEnabled} onChange={(v) => updateSetting('soundEnabled', v)} />
                  </SettingRow>
                </div>
              </section>

              {/* Data Management Section */}
              <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.15em] mb-3 flex items-center gap-2">
                  <Download className="w-4 h-4 text-purple-400" /> Data Management
                </h3>
                <div className="flex flex-col sm:flex-row gap-3">
                  <button onClick={handleExport} className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-white/[0.04] hover:bg-white/[0.08] rounded-xl text-white transition-colors border border-white/[0.06] font-medium">
                    <Download className="w-4 h-4" /> Export Preferences
                  </button>
                  <label className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-white/[0.04] hover:bg-white/[0.08] rounded-xl text-white transition-colors border border-white/[0.06] cursor-pointer font-medium">
                    <Upload className="w-4 h-4" /> Import Configuration
                    <input type="file" accept=".json" onChange={handleImport} className="hidden" />
                  </label>
                </div>
              </section>

            </div>

            {/* Footer */}
            <div className="flex items-center justify-between p-5 md:p-6 border-t border-white/[0.08] bg-[#050505]">
              <button 
                onClick={() => { if (window.confirm('Reset all settings to default values?')) resetSettings(); }} 
                className="flex items-center gap-2 px-4 py-2.5 text-red-400 hover:bg-red-500/10 hover:text-red-300 rounded-xl transition-colors font-medium text-sm"
              >
                <RotateCcw className="w-4 h-4" /> Reset Defaults
              </button>
              <button 
                onClick={onClose} 
                className="px-8 py-2.5 bg-[#e10600] hover:bg-red-600 rounded-xl text-white font-bold transition-colors shadow-[0_4px_12px_rgba(225,6,0,0.3)] hover:shadow-[0_6px_16px_rgba(225,6,0,0.4)]"
              >
                Done
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );

  if (typeof window === 'undefined') return null;
  return createPortal(modalContent, document.body);
};

export default SettingsModal;
