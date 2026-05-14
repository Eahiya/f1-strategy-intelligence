import React, { createContext, useContext, useReducer, useCallback, useMemo } from 'react';
import { useSettings } from './SettingsContext';
import { useNotifications } from './NotificationContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { safeGet } from '../utils/validation';
import { buildUiRecommendation } from '../utils/raceRecommendation';
import { DRIVERS, getDriverByCode, getDriverByName, getTeamColor } from '../data/drivers';

const RaceContext = createContext(null);

export const useRace = () => {
  const context = useContext(RaceContext);
  if (!context) {
    throw new Error('useRace must be used within RaceProvider');
  }
  return context;
};

// Initial states
const INITIAL_RACE_STATE = {
  isRunning: false,
  isPaused: false,
  isFinished: false,
  lifecycleStatus: 'IDLE',
  currentLap: 0,
  totalLaps: 53,
  circuit: 'monza',
  weather: 'dry',
  safetyCarActive: false,
  raceTime: 0,
  scenario: 'normal',
  sessionId: null,
};

// Default player as Lando Norris (user can select different driver)
const DEFAULT_DRIVER_CODE = 'NOR';
const defaultDriver = getDriverByCode(DEFAULT_DRIVER_CODE) || DRIVERS[6];

const INITIAL_PLAYER_STATE = {
  id: 'you',
  position: 3,
  driver: defaultDriver.name,
  driverCode: defaultDriver.driver_code,
  team: defaultDriver.team,
  teamColor: defaultDriver.team_color,
  driverNumber: defaultDriver.number,
  gapToLeader: 2.3,
  tire: 'soft',
  tireAge: 3,
  tireDegradation: 0,
  tireUncertainty: 0,
  lapTime: 0,
  raceTime: 0,
};

const INITIAL_STRATEGY = {
  type: 'auto',
  pitStops: [18, 38],
  nextPitLap: 18,
  currentStint: 1,
  totalStints: 3,
  compounds: ['soft', 'medium', 'hard'],
};

const initialState = {
  raceState: INITIAL_RACE_STATE,
  player: INITIAL_PLAYER_STATE,
  competitors: [],
  events: [],
  lapHistory: [],
  chartData: [],
  currentRecommendation: null,
  strategy: INITIAL_STRATEGY,
  actionState: {
    isExecuting: false,
    lastAction: null,
    lastActionTime: null,
    pendingDecision: null,
  },
  predictions: [],
  metrics: {},
  confidence: { overall: 0, breakdown: {} },
  /** Rolling snapshots for confidence evolution UI { lap, overall, ts } */
  confidenceHistory: [],
  decisionOutcomes: [],
};

// Race Reducer
function raceReducer(state, action) {
  switch (action.type) {
    case 'START_RACE':
      return {
        ...initialState,
        raceState: {
          ...INITIAL_RACE_STATE,
          circuit: action.payload.circuit,
          totalLaps: action.payload.totalLaps,
          scenario: action.payload.scenario,
          weather: action.payload.weather,
          sessionId: action.payload.sessionId,
          isRunning: true, // Mark as running immediately for UI feedback
          lifecycleStatus: 'RUNNING',
        },
        strategy: action.payload.strategy || INITIAL_STRATEGY,
      };
      
    case 'PAUSE_RACE':
      return { ...state, raceState: { ...state.raceState, isPaused: true, lifecycleStatus: 'PAUSED' } };
      
    case 'RESUME_RACE':
      return { ...state, raceState: { ...state.raceState, isPaused: false, lifecycleStatus: 'RUNNING' } };
      
    case 'STOP_RACE':
      return { 
        ...state, 
        raceState: { 
          ...state.raceState, 
          isRunning: false, 
          isPaused: false, 
          isFinished: false, 
          currentLap: 0,
          lifecycleStatus: 'IDLE',
        },
        lapHistory: [],
        chartData: [],
        events: [],
        competitors: [],
        metrics: {},
        confidence: { overall: 0, breakdown: {} },
        confidenceHistory: [],
        actionState: {
          ...state.actionState,
          isExecuting: false,
          pendingDecision: null
        }
      };

    case 'WS_RACE_INIT': {
      // Enrich initial competitors with driver data
      const initialCompetitors = (action.payload.competitors || []).map(comp => {
        const driverCode = comp.driver_code || comp.driverCode || comp.driver?.substring(0, 3).toUpperCase();
        const driverInfo = getDriverByCode(driverCode) || getDriverByName(comp.driver);
        return {
          ...comp,
          driverCode: driverInfo?.driver_code || driverCode,
          driver_code: driverInfo?.driver_code || driverCode,
          team: driverInfo?.team || comp.team || 'Unknown',
          teamColor: driverInfo?.team_color || comp.team_color || comp.teamColor || getTeamColor(comp.team),
          team_color: driverInfo?.team_color || comp.team_color || comp.teamColor || getTeamColor(comp.team),
          driverNumber: driverInfo?.number || comp.number || '?',
        };
      });
      
      return {
        ...state,
        raceState: {
          ...state.raceState,
          circuit: action.payload.circuit,
          totalLaps: action.payload.total_laps,
          scenario: action.payload.scenario?.name || 'normal',
          weather: action.payload.weather,
          isRunning: true,
          isPaused: false,
          isFinished: false,
          lifecycleStatus: 'RUNNING',
        },
        competitors: initialCompetitors,
        chartData: [], // Reset chart data on new race
        metrics: {},
        confidence: { overall: 0, breakdown: {} },
        confidenceHistory: [],
      };
    }

    case 'WS_LAP_UPDATE': {
      const data = action.payload;
      const newPlayer = data.player ? {
        ...state.player,
        position: data.player.position,
        gapToLeader: data.player.gap_to_leader,
        lapTime: data.player.lap_time,
        tire: data.player.tire_compound,
        tireAge: data.player.tire_age,
        tireDegradation: data.player.tire_degradation,
        tireUncertainty: data.player.tire_uncertainty,
      } : state.player;

      // Enrich competitor data with driver info
      const enrichedCompetitors = (data.competitors || state.competitors).map(comp => {
        // Backend sends snake_case, normalize to camelCase for frontend
        const driverCode = comp.driver_code || comp.driverCode || comp.driver?.substring(0, 3).toUpperCase();
        const driverInfo = getDriverByCode(driverCode) || getDriverByName(comp.driver);
        return {
          ...comp,
          driverCode: driverInfo?.driver_code || driverCode,
          driver_code: driverInfo?.driver_code || driverCode,
          team: driverInfo?.team || comp.team || 'Unknown',
          teamColor: driverInfo?.team_color || comp.team_color || comp.teamColor || getTeamColor(comp.team),
          team_color: driverInfo?.team_color || comp.team_color || comp.teamColor || getTeamColor(comp.team),
          driverNumber: driverInfo?.number || comp.number || '?',
        };
      });
      
      // Generate realistic commentary for events
      const newEvents = (data.events && data.events.length > 0) 
        ? [...state.events, ...data.events.map(e => {
            let title = e.message || e.driver || 'Event';
            let description = e.message || '';
            
            // Format overtake messages with real driver names
            if (e.type === 'position_change' && e.attacker && e.defender) {
              const attacker = getDriverByCode(e.attacker);
              const defender = getDriverByCode(e.defender);
              if (attacker && defender) {
                title = `${attacker.name} overtook ${defender.name}`;
                description = `${attacker.driver_code} passed ${defender.driver_code} for P${e.position}`;
              }
            }
            
            return {
              type: e.type === 'position_change' ? 'overtake' : e.type === 'weather_change' ? 'weather' : e.type === 'safety_car' ? 'warning' : e.type === 'safety_car_end' ? 'warning' : e.type || 'info',
              lap: e.lap || data.lap,
              title,
              description,
              driverCode: e.driver_code,
              teamColor: e.team_color,
            };
          })] 
        : state.events;

      const mergedMetrics = { ...state.metrics, ...(data.metrics || {}) };
      const mergedConfidence = data.confidence != null ? data.confidence : state.confidence;
      const nextConfidenceHistory =
        mergedConfidence?.overall != null && typeof data.lap === 'number'
          ? [...state.confidenceHistory, { lap: data.lap, overall: mergedConfidence.overall, ts: Date.now() }].slice(-120)
          : state.confidenceHistory;

      return {
        ...state,
        player: newPlayer,
        competitors: enrichedCompetitors,
        raceState: {
          ...state.raceState,
          currentLap: data.lap,
          weather: data.weather,
          safetyCarActive: data.safety_car_active,
          raceTime: (state.raceState.raceTime || 0) + safeGet(data, 'player.lap_time', 90),
        },
        lapHistory: [...state.lapHistory, {
          lap: data.lap,
          player: data.player,
          competitors: data.competitors,
          timestamp: Date.now(),
        }],
        chartData: [...state.chartData, (() => {
          const point = { lap: data.lap };
          if (data.player) {
            point.player = data.player.lap_time;
            point.player_position = data.player.position;
            point.player_tire = data.player.tire_compound;
            point.player_driver_code = state.player.driverCode || 'YOU';
            point.player_team_color = state.player.teamColor;
          }
          enrichedCompetitors.forEach(comp => {
            // Use driverCode from enriched competitor data (should be uppercase like "VER", "PER", "NOR")
            const driverCode = comp.driverCode || comp.driver_code || 'DRV';
            const key = driverCode.toLowerCase(); // chart data keys are lowercase
            point[key] = comp.lap_time;
            point[`${key}_position`] = comp.position;
            point[`${key}_tire`] = comp.tire_compound;
            point[`${key}_team_color`] = comp.teamColor || comp.team_color;
            point[`${key}_driver_code`] = driverCode;
          });
          return point;
        })()],
        events: newEvents,
        currentRecommendation: data.recommendation || state.currentRecommendation,
        metrics: mergedMetrics,
        confidence: mergedConfidence,
        confidenceHistory: nextConfidenceHistory,
        decisionOutcomes: data.decision_outcome 
          ? [...state.decisionOutcomes, data.decision_outcome] 
          : state.decisionOutcomes,
      };
    }

    case 'WS_ACTION_RECEIVED':
      return {
        ...state,
        actionState: {
          ...state.actionState,
          isExecuting: false,
          lastAction: action.payload.action,
          lastActionTime: Date.now(),
          pendingDecision: {
            id: action.payload.decision_id,
            lap: action.payload.lap,
            predictedGain: action.payload.predicted_gain,
          },
        }
      };
    
    case 'WS_RACE_STATUS':
      const newStatus = action.payload.status || state.raceState.lifecycleStatus;
      // Ensure valid state transitions - never get stuck
      const validTransitions = {
        'PITTING': ['RUNNING', 'SAFETY_CAR', 'FINISHED'],
        'PAUSED': ['RUNNING', 'PITTING', 'SAFETY_CAR'],
        'RUNNING': ['PITTING', 'PAUSED', 'SAFETY_CAR', 'FINISHED'],
        'SAFETY_CAR': ['RUNNING', 'PITTING', 'FINISHED'],
      };

      // Validate transition
      const currentStatus = state.raceState.lifecycleStatus;
      const allowedNext = validTransitions[currentStatus] || [];
      const finalStatus = allowedNext.includes(newStatus) ? newStatus :
        (currentStatus === 'PITTING' && newStatus !== 'RUNNING' ? 'RUNNING' : newStatus);

      return {
        ...state,
        raceState: {
          ...state.raceState,
          lifecycleStatus: finalStatus,
          isPaused: finalStatus === 'PAUSED',
          // Ensure isRunning stays true unless explicitly finished
          isRunning: finalStatus === 'FINISHED' ? false : state.raceState.isRunning,
        },
      };

    case 'WS_PIT_STOP':
      // Pit stop complete - update tire state and ensure race continues
      const pitCompound = action.payload.compound || 'medium';
      const isPlayer = action.payload.driver === state.player.driver || action.payload.driver === 'YOU';
      
      const updatedCompetitors = isPlayer ? state.competitors : state.competitors.map(c => 
        (c.driver === action.payload.driver || c.driverCode === action.payload.driver) 
        ? { ...c, tire_compound: pitCompound, tire_age: 0 } 
        : c
      );

      return {
        ...state,
        raceState: {
          ...state.raceState,
          lifecycleStatus: 'RUNNING', // FORCE back to RUNNING
          isPaused: false, // Ensure not paused
        },
        player: isPlayer ? {
          ...state.player,
          tire: pitCompound,
          tireAge: 0, // Reset tire age after pit
          tireDegradation: 0, // Reset degradation
        } : state.player,
        competitors: updatedCompetitors,
        actionState: {
          ...state.actionState,
          isExecuting: isPlayer ? false : state.actionState.isExecuting,
          lastAction: isPlayer ? `PIT_${pitCompound.toUpperCase()}` : state.actionState.lastAction,
          lastActionTime: isPlayer ? Date.now() : state.actionState.lastActionTime,
          pendingDecision: isPlayer ? null : state.actionState.pendingDecision,
        },
        // Add pit stop event to events list
        events: [
          ...state.events,
          {
            type: 'pit_stop',
            lap: action.payload.lap,
            title: isPlayer ? 'PIT STOP COMPLETE' : `${action.payload.driver} PIT STOP`,
            description: `+${Number(action.payload.pit_time || 0).toFixed(1)}s • Rejoined P${action.payload.rejoined_position ?? '?'}`,
            driverCode: action.payload.driver_code || action.payload.driver?.substring(0, 3).toUpperCase() || 'YOU',
          }
        ],
      };

    case 'WS_RACE_FINISHED':
      return {
        ...state,
        raceState: {
          ...state.raceState,
          isRunning: false,
          isFinished: true,
          currentLap: action.payload.total_laps,
          lifecycleStatus: 'FINISHED',
        },
        metrics: action.payload.analysis 
          ? { ...state.metrics, postRaceAnalysis: action.payload.analysis } 
          : state.metrics,
      };

    case 'WS_ANALYSIS':
      return {
        ...state,
        metrics: { ...state.metrics, ...action.payload },
      };

    case 'EXECUTE_ACTION_START':
      return {
        ...state,
        actionState: {
          ...state.actionState,
          isExecuting: true,
        }
      };
      
    case 'EXECUTE_ACTION_ERROR':
      return {
        ...state,
        actionState: {
          ...state.actionState,
          isExecuting: false,
        }
      };

    default:
      return state;
  }
}

export const RaceProvider = ({ children }) => {
  const { simulationSpeed } = useSettings();
  const { notify } = useNotifications();
  
  // Use unified reducer instead of multiple state hooks
  const [state, dispatch] = useReducer(raceReducer, initialState);
  
  // Session ID state
  const [sessionId, setSessionId] = React.useState(null);

  // Generate session ID
  const generateSessionId = useCallback(() => {
    return `race_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((message) => {
    const { type, data } = message;
    
    switch (type) {
      case 'race_init':
        dispatch({ type: 'WS_RACE_INIT', payload: data });
        notify.success('Race Started', `Simulating ${data.total_laps} laps at ${data.circuit}`);
        break;
        
      case 'lap_update':
        dispatch({ type: 'WS_LAP_UPDATE', payload: data });
        
        // Trigger notifications for important events
        if (data.events && data.events.length > 0) {
          data.events.forEach(event => {
            if (event.type === 'safety_car') {
              notify.critical('Safety Car', event.message);
            } else if (event.type === 'weather_change') {
              notify.weather('Weather Change', event.message);
            } else if (event.type === 'tire_cliff') {
              notify.warning('Tire Alert', event.message);
            }
          });
        }
        
        // Handle decision outcome notifications
        if (data.decision_outcome) {
          const outcome = data.decision_outcome;
          if (Math.abs(outcome.regret) < 1.0) {
            notify.success('Decision Verified', `Prediction accurate! Regret: ${outcome.regret.toFixed(2)}s`);
          } else if (outcome.regret > 0) {
            notify.warning('Decision Review', `Underestimated by ${outcome.regret.toFixed(2)}s`);
          }
        }
        break;
        
      case 'action_received':
        dispatch({ type: 'WS_ACTION_RECEIVED', payload: data });
        notify.success('Action Confirmed', `${data.action} executed at lap ${data.lap}`);
        break;

      case 'pit_stop':
        dispatch({ type: 'WS_PIT_STOP', payload: data });
        notify.pitStop(
          'PIT STOP COMPLETE',
          `+${Number(data.pit_time || 0).toFixed(1)}s • Rejoined P${data.rejoined_position ?? '?'}`
        );
        break;

      case 'race_status':
        dispatch({ type: 'WS_RACE_STATUS', payload: data });
        break;
        
      case 'race_finished':
        dispatch({ type: 'WS_RACE_FINISHED', payload: data });
        notify.success(
          'Race Complete',
          `Finished P${data.final_position} with ${data.total_laps} laps!`
        );
        break;
        
      case 'analysis':
        if (data) {
          dispatch({ type: 'WS_ANALYSIS', payload: data });
        }
        break;
        
      case 'error':
        console.error('[RaceContext] WebSocket error:', data.message);
        notify.error('Race Error', data.message || 'An error occurred');
        break;
        
      default:
        console.log('[RaceContext] Unknown message type:', type);
    }
  }, [notify]);

  // WebSocket connection
  const wsOptions = useMemo(() => ({
    circuit: state.raceState.circuit,
    totalLaps: state.raceState.totalLaps,
    scenario: state.raceState.scenario,
    weather: state.raceState.weather,
    speed: simulationSpeed / 1000,
    onMessage: handleWebSocketMessage,
    autoConnect: false,
    autoReconnect: true,
  }), [state.raceState.circuit, state.raceState.totalLaps, state.raceState.scenario, 
      state.raceState.weather, simulationSpeed, handleWebSocketMessage]);

  const ws = useWebSocket(sessionId, wsOptions);

  // Start race
  const startRace = useCallback((circuit, totalLaps, raceStrategy, scenario = 'normal', weather = 'dry') => {
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    
    dispatch({
      type: 'START_RACE',
      payload: {
        circuit,
        totalLaps,
        scenario,
        weather,
        sessionId: newSessionId,
        strategy: raceStrategy
      }
    });
  }, [generateSessionId]);

  // Track if we've already initiated the race start for this session
  const raceStartedRef = React.useRef(false);
  const wsRef = React.useRef(ws);

  // Keep ws ref in sync
  React.useEffect(() => {
    wsRef.current = ws;
  }, [ws]);

  // Effect to handle WS connection when sessionId or raceState.isRunning changes
  React.useEffect(() => {
    if (state.raceState.isRunning && sessionId) {
      if (ws.status === 'disconnected' || ws.status === 'error') {
        raceStartedRef.current = false;
        wsRef.current.connect();
      }
    }
  }, [state.raceState.isRunning, sessionId, ws.status]); // Using wsRef for method calls to avoid loop

  // Effect to start race once connected (only once per session)
  React.useEffect(() => {
    if (state.raceState.isRunning && ws.status === 'connected' && !raceStartedRef.current) {
      raceStartedRef.current = true;
      wsRef.current.startRace();
    }
  }, [state.raceState.isRunning, ws.status]); // Using wsRef for method calls to avoid loop

  // SAFETY WATCHDOG: Detect and recover from stuck simulation states
  const lastLapUpdateRef = React.useRef(Date.now());
  const stuckCheckIntervalRef = React.useRef(null);

  // Track lap updates
  React.useEffect(() => {
    if (state.raceState.currentLap > 0) {
      lastLapUpdateRef.current = Date.now();
    }
  }, [state.raceState.currentLap]);

  // Watchdog timer to detect stuck race
  React.useEffect(() => {
    if (!state.raceState.isRunning || state.raceState.isFinished) {
      if (stuckCheckIntervalRef.current) {
        clearInterval(stuckCheckIntervalRef.current);
        stuckCheckIntervalRef.current = null;
      }
      return;
    }

    stuckCheckIntervalRef.current = setInterval(() => {
      const timeSinceLastUpdate = Date.now() - lastLapUpdateRef.current;
      const isStuck = timeSinceLastUpdate > 10000; // 10 seconds without update

      if (isStuck && state.raceState.lifecycleStatus !== 'PAUSED') {
        console.warn('[Race Watchdog] Detected stuck simulation, attempting recovery');

        // Force resume if stuck in PITTING or other invalid state
        if (state.raceState.lifecycleStatus === 'PITTING') {
          dispatch({ type: 'RESUME_RACE' });
          notify.warning('Race Recovery', 'Simulation resumed after pit stop');
        }
      }
    }, 5000); // Check every 5 seconds

    return () => {
      if (stuckCheckIntervalRef.current) {
        clearInterval(stuckCheckIntervalRef.current);
      }
    };
  }, [state.raceState.isRunning, state.raceState.isFinished, state.raceState.lifecycleStatus, dispatch, notify]);

  // Pause race
  const pauseRace = useCallback(() => {
    wsRef.current.pauseRace();
    dispatch({ type: 'PAUSE_RACE' });
  }, []);

  // Resume race
  const resumeRace = useCallback(() => {
    wsRef.current.resumeRace();
    dispatch({ type: 'RESUME_RACE' });
  }, []);

  // Stop race
  const stopRace = useCallback(() => {
    wsRef.current.stopRace();
    wsRef.current.disconnect();
    dispatch({ type: 'STOP_RACE' });
  }, []);

  // Execute action
  const executeAction = useCallback(async (actionType, actionData = {}) => {
    if (!state.raceState.isRunning || state.raceState.isPaused) {
      return { success: false, error: 'Race not running' };
    }
    
    dispatch({ type: 'EXECUTE_ACTION_START' });
    
    try {
      const confRaw =
        state.confidence?.overall != null
          ? state.confidence.overall
          : state.currentRecommendation?.confidence;
      const confidence01 =
        confRaw == null ? 0.75 : confRaw > 1 ? confRaw / 100 : confRaw;

      const context = {
        predicted_gain: actionData.predictedGain || 0,
        tire_compound: actionData.compound || 'medium',
        confidence: confidence01,
        lap: state.raceState.currentLap,
      };
      
      const normalizedAction = actionType === 'pit'
        ? `PIT_${(actionData.compound || 'medium').toUpperCase()}`
        : actionType;
      wsRef.current.sendAction(normalizedAction, context);
      
      return { 
        success: true, 
        message: `${normalizedAction} action sent`,
        decisionId: null,
      };
      
    } catch (error) {
      dispatch({ type: 'EXECUTE_ACTION_ERROR' });
      notify.error('Action Failed', error.message);
      return { success: false, error: error.message };
    }
  }, [state.raceState.isRunning, state.raceState.isPaused, state.raceState.currentLap, 
      state.currentRecommendation, state.confidence, notify]);

  // Get post-race analysis
  const getPostRaceAnalysis = useCallback(() => {
    wsRef.current.getAnalysis();
  }, []);

  // Derived state
  const allCompetitors = useMemo(() => {
    return [...state.competitors, { ...state.player, isPlayer: true }]
      .sort((a, b) => a.position - b.position);
  }, [state.competitors, state.player]);

  const getPlayer = useCallback(() => state.player, [state.player]);
  const getLeader = useCallback(() => allCompetitors[0], [allCompetitors]);

  const uiRecommendation = useMemo(
    () =>
      buildUiRecommendation(state.currentRecommendation, {
        confidence: state.confidence,
        metrics: state.metrics,
        raceState: state.raceState,
        player: state.player,
      }),
    [state.currentRecommendation, state.confidence, state.metrics, state.raceState, state.player]
  );

  // Value object
  const value = useMemo(() => ({
    ...state,
    allCompetitors,
    uiRecommendation,
    wsStatus: ws.status,
    isConnected: ws.isConnected,
    wsError: ws.error,
    startRace,
    pauseRace,
    resumeRace,
    stopRace,
    executeAction,
    getPostRaceAnalysis,
    isPlayer: (competitor) => competitor?.isPlayer,
    getPlayer,
    getLeader,
  }), [
    state,
    allCompetitors,
    uiRecommendation,
    ws.status,
    ws.isConnected,
    ws.error,
    startRace,
    pauseRace,
    resumeRace,
    stopRace,
    executeAction,
    getPostRaceAnalysis,
    getPlayer,
    getLeader,
  ]);

  return (
    <RaceContext.Provider value={value}>
      {children}
    </RaceContext.Provider>
  );
};

export default RaceContext;
