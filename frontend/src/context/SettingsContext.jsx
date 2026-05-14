import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';

const SettingsContext = createContext(null);

const DEFAULT_SETTINGS = {
  simulationSpeed: 1000, // milliseconds per lap update
  notificationsEnabled: true,
  soundEnabled: false,
  autoRefresh: true,
  theme: 'dark',
  chartAnimations: true,
  showPredictions: true,
  riskThreshold: 50, // percentage
  units: 'metric', // metric or imperial
  dataRefreshRate: 5000, // milliseconds
};

const STORAGE_KEY = 'f1_strategy_settings_v6';

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(() => {
    // Load from localStorage on initial render
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        try {
          return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
        } catch (e) {
          console.error('Failed to parse settings:', e);
        }
      }
    }
    return DEFAULT_SETTINGS;
  });

  const [isDirty, setIsDirty] = useState(false);

  // Persist to localStorage whenever settings change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      setIsDirty(false);
    }
  }, [settings]);

  const updateSetting = useCallback((key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setIsDirty(true);
  }, []);

  const updateSettings = useCallback((newSettings) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
    setIsDirty(true);
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
    setIsDirty(true);
  }, []);

  const exportSettings = useCallback(() => {
    return JSON.stringify(settings, null, 2);
  }, [settings]);

  const importSettings = useCallback((jsonString) => {
    try {
      const parsed = JSON.parse(jsonString);
      updateSettings(parsed);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }, [updateSettings]);

  const value = useMemo(() => ({
    settings,
    isDirty,
    updateSetting,
    updateSettings,
    resetSettings,
    exportSettings,
    importSettings,
    simulationSpeed: settings.simulationSpeed,
    notificationsEnabled: settings.notificationsEnabled,
    soundEnabled: settings.soundEnabled,
    autoRefresh: settings.autoRefresh,
    theme: settings.theme,
    chartAnimations: settings.chartAnimations,
    showPredictions: settings.showPredictions,
    riskThreshold: settings.riskThreshold,
    units: settings.units,
    dataRefreshRate: settings.dataRefreshRate,
  }), [settings, isDirty, updateSetting, updateSettings, resetSettings, exportSettings, importSettings]);

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

export default SettingsContext;
