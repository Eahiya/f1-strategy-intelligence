import axios from 'axios';
import axiosRetry from 'axios-retry';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

axiosRetry(api, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return (
      axiosRetry.isNetworkOrIdempotentRequestError(error) ||
      (error.response && (error.response.status >= 500 || error.response.status === 429))
    );
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    // Emit synthetic data notification if server indicates synthetic data is used
    const header = response.headers ? (response.headers['x-data-source'] || response.headers['X-Data-Source']) : null;
    if (header && header.toLowerCase() === 'synthetic') {
      const evt = new CustomEvent('synthetic-data', { detail: { message: 'Synthetic data loaded' } });
      window.dispatchEvent(evt);
    }
    return response;
  },
  (error) => {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      console.warn('Session expired or unauthorized. Redirecting to login...');
      localStorage.removeItem('token');
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

export const circuitsApi = {
  getAll: () => api.get('/circuits'),
  getTires: () => api.get('/tires'),
};

export const simulationApi = {
  run: (params) => api.post('/simulate', params),
  detailedRace: (params) => api.post('/race-simulation', params),
  multiCar: (params, config = {}) => api.post('/simulate/multi-car', params, { 
    timeout: 45000, // 45s timeout for multi-car simulation
    ...config 
  }),
  weather: (params) => api.post('/simulate/weather', params),
  liveStream: (params) => api.post('/simulate/live', params, { responseType: 'stream' }),
};

export const eliteApi = {
  rlStrategy: (params) => api.post('/elite/rl-strategy', params),
  opponentAnalysis: (params) => api.post('/elite/opponent-analysis', params),
  digitalTwin: (params) => api.post('/elite/digital-twin', params),
  telemetry: (params) => api.post('/elite/telemetry', params),
  explain: (params) => api.post('/elite/explain', params),
  advancedMetrics: (circuit, totalLaps) => api.post(`/elite/advanced-metrics?circuit=${circuit}&total_laps=${totalLaps}`),
  advancedOptimize: (params) => api.post('/optimize/advanced', params),
};

export const fastf1Api = {
  status: () => api.get('/fastf1/status'),
  circuitInfo: (circuit, year = 2024) => api.get(`/fastf1/circuit-info?circuit=${circuit}&year=${year}`),
  historicalStrategies: (circuit, years = '2022,2023,2024') =>
    api.get(`/fastf1/historical-strategies?circuit=${circuit}&years=${years}`, {
      timeout: 150000, // 150s — FastF1 session loads are slow on first fetch
    }),
  driverTelemetry: (circuit, driver, year = 2024) => api.get(`/fastf1/driver-telemetry?circuit=${circuit}&driver=${driver}&year=${year}`, { timeout: 60000 }),
  validatePrediction: (predictedTime, circuit, year = 2024) => api.post(`/fastf1/validate-prediction?predicted_time=${predictedTime}&circuit=${circuit}&year=${year}`),
};

export default api;
