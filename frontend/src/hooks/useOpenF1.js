import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../services/api';

const POLLING_INTERVALS = {
  live: 4000,       // 4s for live race
  historical: 15000 // 15s for historical/offline
};

export const useOpenF1 = () => {
  const [mode, setMode] = useState('sim'); // 'sim', 'live', 'hybrid'
  const [session, setSession] = useState(null);
  const [positions, setPositions] = useState([]);
  const [timing, setTiming] = useState([]);
  const [raceControl, setRaceControl] = useState([]);
  const [weather, setWeather] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const pollingRef = useRef(null);
  const backoffRef = useRef(1);

  // 1. Initial Session Check
  useEffect(() => {
    let mounted = true;

    const checkSession = async () => {
      try {
        const response = await api.get('/openf1/session');
        if (mounted) {
          setSession(response.data);
          // If a live session is available, we don't auto-switch mode, but we make it available to the UI.
          setError(null);
        }
      } catch (err) {
        console.warn('[OpenF1] Failed to fetch session info:', err.message);
        if (mounted) {
          setSession({ available: false, status: 'offline', is_live: false });
          setError('OpenF1 service unavailable');
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    checkSession();
    return () => { mounted = false; };
  }, []);

  // 2. Data Polling
  const fetchData = useCallback(async () => {
    if (mode === 'sim') return; // Don't fetch if strictly sim mode
    
    try {
      // Parallel fetch to minimize latency
      const [posRes, timingRes, rcRes, weatherRes] = await Promise.allSettled([
        api.get('/openf1/positions'),
        api.get('/openf1/timing'),
        api.get('/openf1/race-control'),
        api.get('/openf1/weather')
      ]);

      if (posRes.status === 'fulfilled') setPositions(posRes.value.data);
      if (timingRes.status === 'fulfilled') setTiming(timingRes.value.data);
      if (rcRes.status === 'fulfilled') setRaceControl(rcRes.value.data);
      if (weatherRes.status === 'fulfilled') setWeather(weatherRes.value.data);

      // Reset backoff on success
      backoffRef.current = 1;
      setError(null);
    } catch (err) {
      console.warn('[OpenF1] Polling error:', err.message);
      // Exponential backoff up to 60s
      backoffRef.current = Math.min(backoffRef.current * 1.5, 15);
      setError('Connection to OpenF1 unstable');
    }
  }, [mode]);

  // 3. Polling Loop
  useEffect(() => {
    if (mode === 'sim') {
      if (pollingRef.current) clearInterval(pollingRef.current);
      return;
    }

    // Initial fetch
    fetchData();

    // Determine interval based on session live status and backoff
    const baseInterval = session?.is_live ? POLLING_INTERVALS.live : POLLING_INTERVALS.historical;
    
    const startPolling = () => {
      const interval = baseInterval * backoffRef.current;
      pollingRef.current = setTimeout(async () => {
        await fetchData();
        startPolling(); // Recursive timeout for dynamic interval
      }, interval);
    };

    startPolling();

    return () => {
      if (pollingRef.current) clearTimeout(pollingRef.current);
    };
  }, [mode, session?.is_live, fetchData]);

  return {
    mode,
    setMode,
    session,
    positions,
    timing,
    raceControl,
    weather,
    loading,
    error,
    isLive: session?.is_live || false
  };
};

export default useOpenF1;
