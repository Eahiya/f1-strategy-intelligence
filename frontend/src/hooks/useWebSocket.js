import { useState, useCallback, useEffect, useRef, useMemo } from 'react';

export const WebSocketStatus = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error',
};

export const useWebSocket = (sessionId, options = {}) => {
  const {
    circuit,
    totalLaps,
    scenario,
    weather,
    speed,
    onMessage,
    autoConnect = false,
    autoReconnect = true,
  } = options;

  const [status, setStatus] = useState(WebSocketStatus.DISCONNECTED);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);
  const sessionIdRef = useRef(sessionId);
  const optionsRef = useRef({ circuit, totalLaps, scenario, weather, speed, onMessage, autoReconnect });

  // Keep refs in sync
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    optionsRef.current = { circuit, totalLaps, scenario, weather, speed, onMessage, autoReconnect };
  }, [circuit, totalLaps, scenario, weather, speed, onMessage, autoReconnect]);

  const isConnected = status === WebSocketStatus.CONNECTED;

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    let host = process.env.REACT_APP_WS_HOST;
    if (!host) {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      host = apiUrl.replace(/^https?:\/\//, '');
    }
    
    return `${protocol}//${host}/ws/${sessionIdRef.current}`;
  }, []);

  const connect = useCallback(() => {
    if (!sessionIdRef.current) {
      setError(new Error('No session ID provided'));
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clean up any existing connection first
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus(WebSocketStatus.CONNECTING);
    setError(null);
    reconnectAttemptsRef.current = 0;

    try {
      const wsUrl = getWebSocketUrl();
      const ws = new WebSocket(wsUrl);
      const opts = optionsRef.current;

      ws.onopen = () => {
        setStatus(WebSocketStatus.CONNECTED);
        setError(null);
        reconnectAttemptsRef.current = 0;

        ws.send(JSON.stringify({
          type: 'init',
          data: {
            circuit: opts.circuit,
            total_laps: opts.totalLaps,
            scenario: opts.scenario,
            weather: opts.weather,
            speed: opts.speed,
          },
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (optionsRef.current.onMessage) {
            optionsRef.current.onMessage(message);
          }
        } catch (err) {
          console.error('[useWebSocket] Failed to parse message:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('[useWebSocket] WebSocket error:', err);
        setError(new Error('WebSocket connection error'));
        setStatus(WebSocketStatus.ERROR);
      };

      ws.onclose = () => {
        setStatus(WebSocketStatus.DISCONNECTED);
        wsRef.current = null;

        if (optionsRef.current.autoReconnect && reconnectAttemptsRef.current < 5) {
          setStatus(WebSocketStatus.RECONNECTING);
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 2000 * reconnectAttemptsRef.current);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setError(err);
      setStatus(WebSocketStatus.ERROR);
    }
  }, [getWebSocketUrl]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus(WebSocketStatus.DISCONNECTED);
    reconnectAttemptsRef.current = 0;
  }, []);

  const sendMessage = useCallback((type, data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }));
    } else {
      console.warn('[useWebSocket] Cannot send message, WebSocket not open');
    }
  }, []);

  const startRace = useCallback(() => {
    sendMessage('start_race', {});
  }, [sendMessage]);

  const pauseRace = useCallback(() => {
    sendMessage('pause_race', {});
  }, [sendMessage]);

  const resumeRace = useCallback(() => {
    sendMessage('resume_race', {});
  }, [sendMessage]);

  const stopRace = useCallback(() => {
    sendMessage('stop_race', {});
  }, [sendMessage]);

  const sendAction = useCallback((action, context) => {
    sendMessage('action', { action, context });
  }, [sendMessage]);

  const getAnalysis = useCallback(() => {
    sendMessage('get_analysis', {});
  }, [sendMessage]);

  useEffect(() => {
    if (autoConnect && sessionId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, sessionId, connect, disconnect]);

  // Stable return object - only updates on meaningful changes
  const returnValues = useMemo(() => ({
    status,
    isConnected,
    error,
    connect,
    disconnect,
    startRace,
    pauseRace,
    resumeRace,
    stopRace,
    sendAction,
    getAnalysis,
  }), [status, isConnected, error, connect, disconnect, startRace, pauseRace, resumeRace, stopRace, sendAction, getAnalysis]);

  return returnValues;
};

export default useWebSocket;
