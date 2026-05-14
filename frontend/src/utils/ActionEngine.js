/**
 * ActionEngine - F1 Strategy Decision Engine
 * 
 * Detects:
 * - Pit windows (optimal, closing, missed)
 * - Undercut opportunities
 * - Tire cliff warnings
 * - Safety car strategies
 * - Weather transitions
 * - Track position battles
 */

export class ActionEngine {
  constructor() {
    this.lastRecommendation = null;
    this.lastRecommendationTime = 0;
    this.recommendationCooldown = 5000; // 5 seconds between recommendations
  }

  /**
   * Main analysis function - called every lap
   */
  analyze(lap, player, competitors, raceState, strategy) {
    const now = Date.now();
    
    // Cooldown check to prevent spam
    if (this.lastRecommendation && (now - this.lastRecommendationTime) < this.recommendationCooldown) {
      return this.lastRecommendation;
    }

    // Priority order: Critical > High > Normal > Low
    const checks = [
      () => this.checkTireCliff(lap, player, strategy),
      () => this.checkOptimalPitWindow(lap, player, competitors, strategy),
      () => this.checkUndercutOpportunity(lap, player, competitors, raceState),
      () => this.checkOvercutThreat(lap, player, competitors, strategy),
      () => this.checkSafetyCarStrategy(lap, player, raceState),
      () => this.checkPushOpportunity(lap, player, competitors),
      () => this.checkFuelSaveOpportunity(lap, player, strategy),
    ];

    for (const check of checks) {
      const recommendation = check();
      if (recommendation && recommendation.urgency !== 'none') {
        this.lastRecommendation = recommendation;
        this.lastRecommendationTime = now;
        return recommendation;
      }
    }

    return null;
  }

  /**
   * Check if tires are approaching the cliff
   */
  checkTireCliff(lap, player, strategy) {
    const tireLimits = {
      'soft': { limit: 25, cliff: 20, critical: 22 },
      'medium': { limit: 40, cliff: 35, critical: 38 },
      'hard': { limit: 55, cliff: 48, critical: 52 },
      'inter': { limit: 30, cliff: 25, critical: 28 },
      'wet': { limit: 40, cliff: 35, critical: 38 },
    };

    const limits = tireLimits[player.tire];
    if (!limits) return null;

    if (player.tireAge >= limits.critical) {
      return {
        type: 'pit',
        title: 'PIT NOW - TIRE CLIFF',
        subtitle: 'Critical tire degradation',
        description: `${player.tire.toUpperCase()} tires at ${player.tireAge} laps - beyond critical limit. Box immediately!`,
        reason: `Tires ${player.tireAge - limits.limit} laps past optimal. Losing ${(player.tireAge * 0.08).toFixed(2)}s per lap to degradation.`,
        confidence: 98,
        deadline: 1,
        urgency: 'critical',
        expiresIn: 1,
        alternatives: [
          { action: 'Continue (DANGER)', risk: 'Extreme', gain: '-5.0s per lap' },
          { action: 'Switch to hard', risk: 'High', gain: '+2.1s pit time' },
        ],
        timeAdvantage: -5.0,
        recommendedCompound: 'medium',
      };
    }

    if (player.tireAge >= limits.cliff) {
      return {
        type: 'pit',
        title: 'PIT THIS LAP',
        subtitle: 'Tire cliff approaching',
        description: `${player.tire.toUpperCase()} tires at ${player.tireAge} laps. Performance dropping rapidly.`,
        reason: `Optimal window closing. Currently losing ${(player.tireAge * 0.05).toFixed(2)}s per lap. Pit now for optimal position.`,
        confidence: 92,
        deadline: 2,
        urgency: 'high',
        expiresIn: 2,
        alternatives: [
          { action: 'Push 1 more lap', risk: 'High', gain: '-1.5s' },
          { action: 'Extend to lap ' + (lap + 2), risk: 'Medium', gain: '+0.8s track position' },
        ],
        timeAdvantage: -2.5,
        recommendedCompound: 'medium',
      };
    }

    return null;
  }

  /**
   * Check optimal pit window based on strategy
   */
  checkOptimalPitWindow(lap, player, competitors, strategy) {
    if (!strategy.nextPitLap || lap < strategy.nextPitLap - 3) return null;

    const windowOpen = lap >= strategy.nextPitLap - 2;
    const windowClose = lap >= strategy.nextPitLap + 2;

    if (windowClose) {
      return {
        type: 'pit',
        title: 'PIT WINDOW CLOSING',
        subtitle: 'Missed optimal window',
        description: `Target lap ${strategy.nextPitLap} passed. Box now to minimize time loss.`,
        reason: `Each additional lap costs ${(player.tireAge * 0.04).toFixed(2)}s. Delaying further reduces track position.`,
        confidence: 85,
        deadline: 1,
        urgency: 'high',
        expiresIn: 1,
        alternatives: [
          { action: 'Skip this stop', risk: 'High', gain: '+15s final time' },
        ],
        timeAdvantage: -1.8,
        recommendedCompound: strategy.compounds?.[strategy.currentStint] || 'medium',
      };
    }

    if (windowOpen) {
      // Check for clean air (gap to cars behind)
      const gapBehind = player.gap || 2.0;
      const cleanAir = gapBehind > 2.5;

      return {
        type: 'pit',
        title: cleanAir ? 'PIT NOW - CLEAN AIR' : 'PIT NOW - TRAFFIC',
        subtitle: cleanAir ? 'Optimal pit window' : 'Expect traffic',
        description: cleanAir 
          ? `Perfect timing! ${gapBehind.toFixed(1)}s gap to car behind.`
          : `Gap to car behind is ${gapBehind.toFixed(1)}s. May encounter traffic.`,
        reason: `Window open: laps ${strategy.nextPitLap - 2}-${strategy.nextPitLap + 2}. ${cleanAir ? 'Clean air allows optimal pit entry/exit.' : 'Consider extending 1 lap for clean air.'}`,
        confidence: cleanAir ? 88 : 75,
        deadline: 3,
        urgency: 'high',
        expiresIn: 3,
        alternatives: [
          { action: 'Wait 1 lap', risk: 'Low', gain: cleanAir ? '-0.3s' : '+0.5s clean air' },
          { action: 'Push extend', risk: 'Medium', gain: '+1.2s track position' },
        ],
        timeAdvantage: cleanAir ? 1.2 : 0,
        recommendedCompound: strategy.compounds?.[strategy.currentStint] || 'medium',
      };
    }

    return null;
  }

  /**
   * Check for undercut opportunities
   */
  checkUndercutOpportunity(lap, player, competitors, raceState) {
    // Find car ahead
    const carAhead = competitors.find(c => c.position === player.position - 1);
    if (!carAhead || player.position === 1) return null;

    const gapToAhead = carAhead.gapToLeader - player.gapToLeader;
    
    // Undercut conditions:
    // 1. Gap is 2-4 seconds (perfect undercut window)
    // 2. Car ahead hasn't pitted yet
    // 3. Fresh tires will gain 0.5-1s per lap
    const undercutWindow = gapToAhead >= 2.0 && gapToAhead <= 4.5;
    const tireAgeDiff = carAhead.tireAge - player.tireAge;
    
    if (undercutWindow && tireAgeDiff > 3) {
      const estimatedGain = (tireAgeDiff * 0.4).toFixed(1);
      
      return {
        type: 'undercut',
        title: 'UNDERCUT OPPORTUNITY',
        subtitle: `Gap to ${carAhead.driver}: ${gapToAhead.toFixed(1)}s`,
        description: `Pit now to undercut ${carAhead.driver}. Your fresh tires will gain ~${estimatedGain}s per lap.`,
        reason: `${carAhead.driver} on ${carAhead.tireAge}-lap-old ${carAhead.tire}s. Fresh softs will close ${estimatedGain}s per lap. Target exit ahead of them.`,
        confidence: Math.min(95, 80 + tireAgeDiff * 2),
        deadline: 3,
        urgency: 'high',
        expiresIn: 3,
        alternatives: [
          { action: 'Wait for overcut', risk: 'Medium', gain: '+0.8s if they pit first' },
          { action: 'Track position', risk: 'Low', gain: 'Maintain P' + player.position },
        ],
        timeAdvantage: parseFloat(estimatedGain),
        targetDriver: carAhead.driver,
        recommendedCompound: 'soft',
      };
    }

    return null;
  }

  /**
   * Check for overcut threats (car behind might undercut us)
   */
  checkOvercutThreat(lap, player, competitors, strategy) {
    const carBehind = competitors.find(c => c.position === player.position + 1);
    if (!carBehind) return null;

    const gapBehind = carBehind.gapToLeader - player.gapToLeader;
    const threatWindow = gapBehind >= 2.0 && gapBehind <= 4.0;
    const theirTireAdvantage = player.tireAge - carBehind.tireAge > 5;

    if (threatWindow && theirTireAdvantage) {
      return {
        type: 'defend',
        title: 'DEFEND POSITION',
        subtitle: `${carBehind.driver} closing: ${gapBehind.toFixed(1)}s behind`,
        description: `${carBehind.driver} on fresher tires (${carBehind.tireAge} vs ${player.tireAge} laps). Threat of undercut.`,
        reason: `Fresh tire advantage gives ${carBehind.driver} ${(theirTireAdvantage * 0.3).toFixed(1)}s per lap. Consider early pit to cover.`,
        confidence: 78,
        deadline: 3,
        urgency: 'normal',
        expiresIn: 5,
        alternatives: [
          { action: 'Pit to cover', risk: 'Medium', gain: 'Maintain position' },
          { action: 'Push on track', risk: 'High', gain: '+0.5s gap' },
        ],
        threatDriver: carBehind.driver,
      };
    }

    return null;
  }

  /**
   * Check for safety car strategy opportunities
   */
  checkSafetyCarStrategy(lap, player, raceState) {
    if (!raceState.safetyCar) return null;

    // Safety car reduces pit time loss from ~22s to ~8s
    const pitTimeSaved = 14;
    
    // If tires are getting old, safety car is perfect pit opportunity
    const shouldPit = player.tireAge > 12;

    if (shouldPit) {
      return {
        type: 'pit',
        title: 'SAFETY CAR - PIT NOW!',
        subtitle: `Save ${pitTimeSaved}s on pit stop`,
        description: 'SAFETY CAR DEPLOYED. Pit window opportunity - minimal time loss!',
        reason: `Safety car reduces pit delta from 22s to ~8s. Combined with ${player.tireAge}-lap-old tires, net gain of ~${(pitTimeSaved + player.tireAge * 0.3).toFixed(1)}s.`,
        confidence: 96,
        deadline: 2,
        urgency: 'critical',
        expiresIn: 2,
        alternatives: [
          { action: 'Stay out', risk: 'Low', gain: 'Track position' },
        ],
        timeAdvantage: pitTimeSaved,
        isSafetyCar: true,
        recommendedCompound: 'hard', // Safety car = longer stint likely
      };
    }

    return {
      type: 'conserve',
      title: 'SAFETY CAR - CONSERVE',
      subtitle: 'Maintain position, save fuel',
      description: 'Safety car deployed. Use this period to conserve fuel and tires.',
      reason: 'Reduced pace allows tire cooling and fuel saving. Prepare for restart.',
      confidence: 90,
      deadline: 0,
      urgency: 'low',
      expiresIn: 0,
    };
  }

  /**
   * Check for push opportunities (fresh tires, clear track)
   */
  checkPushOpportunity(lap, player, competitors) {
    // Fresh tires + clear air = push mode
    const freshTires = player.tireAge < 5;
    const chasing = competitors.some(c => c.position === player.position - 1 && c.gap < 3.0);

    if (freshTires && !chasing) {
      return {
        type: 'push',
        title: 'PUSH MODE AVAILABLE',
        subtitle: 'Fresh tires, clear air',
        description: `Your ${player.tire}s are at ${player.tireAge} laps - peak performance window.`,
        reason: 'Tires in optimal window. Clear air ahead. Extract maximum pace now before degradation.',
        confidence: 82,
        deadline: 5,
        urgency: 'normal',
        expiresIn: 8,
        alternatives: [
          { action: 'Conserve tires', risk: 'Low', gain: '+2 lap stint life' },
          { action: 'Push for gap', risk: 'Medium', gain: '+1.5s gap to behind' },
        ],
      };
    }

    return null;
  }

  /**
   * Check if fuel saving is beneficial
   */
  checkFuelSaveOpportunity(lap, player, strategy) {
    // If we're ahead of schedule and fuel is tight
    const lapsRemaining = strategy.totalLaps - lap;
    const fuelNeeded = lapsRemaining * 1.8;
    const fuelMargin = player.fuel - fuelNeeded;

    if (fuelMargin < 5 && fuelMargin > -5) {
      return {
        type: 'conserve',
        title: 'FUEL SAVE REQUIRED',
        subtitle: `Margin: ${fuelMargin.toFixed(1)}%`,
        description: `Fuel tight for remaining ${lapsRemaining} laps. Switch to conserve mode.`,
        reason: `Current consumption rate will leave ${fuelMargin.toFixed(1)}% fuel at finish. Reduce fuel mix to avoid emergency save.`,
        confidence: 88,
        deadline: lapsRemaining,
        urgency: 'high',
        expiresIn: lapsRemaining,
        alternatives: [
          { action: 'Continue push', risk: 'High', gain: 'Pace now, risk later' },
        ],
      };
    }

    return null;
  }

  /**
   * Get tire performance projection
   */
  getTirePerformanceProjection(tire, currentAge, laps) {
    const degradationRates = {
      'soft': { base: 0.03, cliffStart: 18, cliffRate: 0.12 },
      'medium': { base: 0.02, cliffStart: 32, cliffRate: 0.08 },
      'hard': { base: 0.015, cliffStart: 45, cliffRate: 0.06 },
    };

    const rate = degradationRates[tire] || degradationRates['medium'];
    const projections = [];

    for (let i = 0; i <= laps; i++) {
      const age = currentAge + i;
      const isCliff = age > rate.cliffStart;
      const perfLoss = isCliff 
        ? (rate.cliffStart * rate.base) + ((age - rate.cliffStart) * rate.cliffRate)
        : age * rate.base;
      
      projections.push({
        lap: i,
        age,
        performance: Math.max(0, 100 - perfLoss * 10),
        lapTimeDelta: perfLoss,
      });
    }

    return projections;
  }

  /**
   * Calculate pit window
   */
  calculatePitWindow(currentLap, totalLaps, tire, tireAge, strategy) {
    const tireLimits = {
      'soft': 25,
      'medium': 40,
      'hard': 55,
    };

    const limit = tireLimits[tire] || 40;
    const remainingTireLife = limit - tireAge;
    const lapsRemaining = totalLaps - currentLap;
    
    const earlyWindow = currentLap + Math.max(2, remainingTireLife - 5);
    const lateWindow = currentLap + Math.min(remainingTireLife, lapsRemaining);

    return {
      open: earlyWindow,
      optimal: currentLap + Math.floor((earlyWindow + lateWindow) / 2),
      close: lateWindow,
      reason: remainingTireLife < lapsRemaining ? 'tire_limited' : 'race_distance',
    };
  }
}

export default ActionEngine;
