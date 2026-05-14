/**
 * F1 Strategy Platform - Validation Utilities
 * 
 * Provides input validation, state validation, and error handling
 * for production-ready system operation.
 */

// Validation helpers
export const isValidNumber = (value) => {
  return typeof value === 'number' && !isNaN(value) && isFinite(value);
};

export const isValidString = (value) => {
  return typeof value === 'string' && value.length > 0;
};

export const isValidArray = (value) => {
  return Array.isArray(value) && value.length > 0;
};

export const isValidObject = (value) => {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
};

// Race state validation
export const validateRaceState = (state) => {
  const errors = [];
  
  if (!isValidObject(state)) {
    errors.push('Race state must be an object');
    return { isValid: false, errors };
  }
  
  if (!isValidNumber(state.currentLap)) {
    errors.push('currentLap must be a valid number');
  }
  
  if (!isValidNumber(state.totalLaps)) {
    errors.push('totalLaps must be a valid number');
  }
  
  if (state.currentLap > state.totalLaps) {
    errors.push('currentLap cannot exceed totalLaps');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// Player state validation
export const validatePlayerState = (player) => {
  const errors = [];
  
  if (!isValidObject(player)) {
    errors.push('Player must be an object');
    return { isValid: false, errors };
  }
  
  if (!isValidNumber(player.position) || player.position < 1) {
    errors.push('position must be a positive number');
  }
  
  if (!['soft', 'medium', 'hard', 'inter', 'wet'].includes(player.tire)) {
    errors.push('tire must be a valid compound');
  }
  
  if (!isValidNumber(player.tireAge) || player.tireAge < 0) {
    errors.push('tireAge must be a non-negative number');
  }
  
  if (!isValidNumber(player.raceTime) || player.raceTime < 0) {
    errors.push('raceTime must be a non-negative number');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// Competitor validation
export const validateCompetitor = (competitor) => {
  const errors = [];
  
  if (!isValidObject(competitor)) {
    errors.push('Competitor must be an object');
    return { isValid: false, errors };
  }
  
  if (!isValidString(competitor.id)) {
    errors.push('id is required');
  }
  
  if (!isValidString(competitor.driver)) {
    errors.push('driver name is required');
  }
  
  if (!isValidNumber(competitor.position)) {
    errors.push('position must be a number');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// Action validation
export const validateAction = (action) => {
  const validTypes = ['pit', 'push', 'conserve', 'undercut', 'defend'];
  
  if (!validTypes.includes(action.type)) {
    return {
      isValid: false,
      error: `Action type must be one of: ${validTypes.join(', ')}`
    };
  }
  
  return { isValid: true };
};

// Safe number formatter
export const safeToFixed = (value, decimals = 2, fallback = '--') => {
  if (!isValidNumber(value)) {
    return fallback;
  }
  
  try {
    return value.toFixed(decimals);
  } catch (e) {
    return fallback;
  }
};

// Safe getter with default
export const safeGet = (obj, path, defaultValue = null) => {
  try {
    const keys = path.split('.');
    let result = obj;
    
    for (const key of keys) {
      if (result == null || typeof result !== 'object') {
        return defaultValue;
      }
      result = result[key];
    }
    
    return result !== undefined ? result : defaultValue;
  } catch (e) {
    return defaultValue;
  }
};

// Deep clone for immutable updates
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }
  
  if (Array.isArray(obj)) {
    return obj.map(item => deepClone(item));
  }
  
  const cloned = {};
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key]);
    }
  }
  
  return cloned;
};

// Throttle function for performance
export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

// Debounce function for performance
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Performance monitor
export class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
  }
  
  start(label) {
    this.metrics.set(label, performance.now());
  }
  
  end(label) {
    const start = this.metrics.get(label);
    if (start) {
      const duration = performance.now() - start;
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Performance] ${label}: ${duration.toFixed(2)}ms`);
      }
      this.metrics.delete(label);
      return duration;
    }
    return null;
  }
  
  measure(label, fn) {
    this.start(label);
    const result = fn();
    this.end(label);
    return result;
  }
}

const validationUtils = {
  isValidNumber,
  isValidString,
  isValidArray,
  isValidObject,
  validateRaceState,
  validatePlayerState,
  validateCompetitor,
  validateAction,
  safeToFixed,
  safeGet,
  deepClone,
  throttle,
  debounce,
  PerformanceMonitor
};

export default validationUtils;
