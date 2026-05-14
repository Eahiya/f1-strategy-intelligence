/**
 * Maps backend RL / websocket recommendation + live metrics into UI shapes
 * used by ActionPanel, StrategyCard, and DecisionPanel.
 */

function clamp01(v) {
  if (v == null || Number.isNaN(v)) return 0.5;
  return Math.min(1, Math.max(0, v));
}

function toConfidence01(overall) {
  if (overall == null || Number.isNaN(overall)) return 0.5;
  return overall > 1 ? overall / 100 : overall;
}

function toRiskPercent(metrics) {
  const r = metrics?.risk_score;
  if (r == null || Number.isNaN(r)) return 35;
  return r > 1 ? Math.round(r) : Math.round(r * 100);
}

function riskFactorsFromBreakdown(breakdown) {
  if (!breakdown || typeof breakdown !== 'object') return [];
  const labels = {
    tire_wear_risk: 'Tire wear',
    weather_risk: 'Weather',
    traffic_risk: 'Traffic',
    pit_window_risk: 'Pit window',
    safety_car_risk: 'Safety car',
  };
  return Object.entries(labels)
    .map(([key, name]) => {
      const raw = breakdown[key];
      const impact = raw > 1 ? Math.round(raw) : Math.round((raw || 0) * 100);
      return { name, impact: Math.min(100, Math.max(0, impact)) };
    })
    .filter((f) => f.impact > 3);
}

function qValueAlternatives(qValues, chosenActionName) {
  if (!qValues || typeof qValues !== 'object') return [];
  const entries = Object.entries(qValues);
  if (entries.length < 2) return [];
  const sorted = [...entries].sort((a, b) => b[1] - a[1]);
  const bestQ = sorted[0]?.[1] ?? 0;
  return sorted
    .filter(([name]) => name !== chosenActionName)
    .slice(0, 3)
    .map(([name, q]) => ({
      action: name.replace(/_/g, ' '),
      risk: q < bestQ - 0.25 ? 'High' : q < bestQ - 0.08 ? 'Medium' : 'Low',
      gain: `${(q - bestQ).toFixed(2)} ΔQ`,
    }));
}

/**
 * @param {object|null} raw - Backend recommendation (RL predict output)
 * @param {{ confidence?: object, metrics?: object, raceState?: object, player?: object }} opts
 * @returns {object|null}
 */
export function buildUiRecommendation(raw, opts = {}) {
  if (!raw || typeof raw !== 'object') return null;

  const { confidence = {}, metrics = {}, raceState = {}, player = {} } = opts;

  const conf01 = toConfidence01(confidence.overall ?? raw.confidence);
  const confPct = Math.round(conf01 * 100);
  const riskPct = toRiskPercent(metrics);
  const breakdown = confidence.breakdown || {};

  const actionName = raw.action_name || 'STAY_OUT';
  const shouldPit = raw.should_pit === true || /^PIT_/i.test(String(actionName));
  const tire = String(raw.recommended_tire || 'medium').toLowerCase();

  let type = 'push';
  if (shouldPit) type = 'pit';
  else if ((player.tireAge || 0) > 24 && conf01 < 0.52) type = 'conserve';

  let urgency = 'normal';
  if (shouldPit && ((player.tireAge || 0) > 27 || raceState.safetyCarActive)) urgency = 'critical';
  else if (shouldPit || riskPct > 68) urgency = 'high';
  else if (riskPct > 42) urgency = 'high';

  const title = shouldPit
    ? `Box — ${tire.charAt(0).toUpperCase() + tire.slice(1)}`
    : 'Stay out';

  const subtitle = `Lap ${raceState.currentLap ?? 0} • ${String(actionName).replace(/_/g, ' ')}`;

  const factorRows = riskFactorsFromBreakdown(metrics.risk_breakdown);
  const riskFactorTags = factorRows.length
    ? factorRows.map((f) => `${f.name} (${f.impact}%)`)
    : ['Tire stress', 'Weather volatility', 'Traffic density'];

  const agreement = clamp01(breakdown.model_agreement);
  const tireCert = clamp01(breakdown.tire_certainty);
  const weatherStab = clamp01(breakdown.weather_stability);
  const varianceConf = clamp01(breakdown.variance_confidence);

  const positionGainProb = clamp01(agreement * conf01 * (shouldPit ? 1.08 : 1));
  const timeBenefitProb = clamp01(tireCert * conf01);
  const riskMitigationProb = clamp01(varianceConf * (1 - riskPct / 130));
  const windowOptimalProb = clamp01(weatherStab * conf01 * (raceState.safetyCarActive ? 1.12 : 1));

  const alternatives = qValueAlternatives(raw.q_values, actionName);

  const expectedPositionChange =
    shouldPit && (player.tireAge || 0) > 20 ? -1 : 0;

  return {
    id: `lap-${raceState.currentLap}-${raw.action}-${actionName}`,
    type,
    title,
    subtitle,
    description: raw.explanation || '',
    urgency,
    expiresIn: urgency === 'critical' ? 5 : undefined,
    probability: conf01,
    confidence: conf01,
    recommendedCompound: tire,
    timeAdvantage: shouldPit ? Math.min(2.5, Math.max(0, ((player.tireAge || 0) - 12) * 0.07)) : 0,
    expectedPositionChange,
    riskLevel: riskPct > 60 ? 'high' : riskPct > 35 ? 'medium' : 'low',
    risk: riskPct > 60 ? 'high' : riskPct > 35 ? 'medium' : 'low',
    riskFactors: riskFactorTags,
    positionGainProb,
    timeBenefitProb,
    riskMitigationProb,
    windowOptimalProb,
    alternatives,
    reason: raw.explanation,
    confidencePercent: confPct,
    riskPercent: riskPct,
    rawRecommendation: raw,
  };
}

export function liveStrategyShape({ currentRecommendation, strategy, raceState, metrics, confidence }) {
  if (!currentRecommendation) return null;
  const actionName = currentRecommendation.action_name || 'RL_POLICY';
  const pitStops = strategy?.pitStops || [];
  const baseTime = (raceState?.totalLaps || 53) * 92;

  return {
    type: String(actionName).toLowerCase().includes('pit') ? `pit_${currentRecommendation.recommended_tire || 'medium'}` : 'rl_hold',
    predicted_time: metrics?.fuel != null ? baseTime * 0.98 : baseTime,
    pit_stops: pitStops,
    advantage: 0,
    risk: toRiskPercent(metrics),
  };
}
