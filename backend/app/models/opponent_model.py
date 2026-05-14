"""
F1 Strategy Intelligence System - Elite Edition v3.0
Game Theory & Opponent Modeling Engine

Implements competitive race dynamics, opponent behavior prediction,
and strategic game theory concepts (undercut, overcut, blocking).
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from app.core.config import CIRCUITS, TIRE_COMPOUNDS


class StrategyType(Enum):
    """Classification of driver strategy approaches."""
    CONSERVATIVE = "conservative"    # Minimize risk, late pit stops
    AGGRESSIVE = "aggressive"        # Early stops, tire advantage plays
    BALANCED = "balanced"            # Standard approach
    REACTIVE = "reactive"            # Respond to others' moves
    UNDERCUT_FOCUSED = "undercut"    # Always look for undercut opportunities
    OVERTAKE_HEAVY = "overtake"      # Prioritize track position


class DriverBehaviorProfile:
    """
    Detailed behavioral model of a racing driver.
    Used to predict decisions and competitive interactions.
    """
    
    def __init__(self,
                 driver_id: int,
                 name: str,
                 team: str,
                 base_skill: float = 0.5,
                 aggression: float = 0.5,
                 tire_management: float = 0.5,
                 consistency: float = 0.5,
                 strategy_type: StrategyType = StrategyType.BALANCED,
                 pit_timing_bias: float = 0.0,  # Negative = early, Positive = late
                 undercut_sensitivity: float = 0.7,  # How likely to respond to undercut threat
                 overcut_willingness: float = 0.5,  # Willingness to try overcut
                 defensive_driving: float = 0.5,  # Blocking ability
                 racecraft: float = 0.5):  # General racing intelligence
        
        self.driver_id = driver_id
        self.name = name
        self.team = team
        
        # Core attributes
        self.base_skill = np.clip(base_skill, 0, 1)
        self.aggression = np.clip(aggression, 0, 1)
        self.tire_management = np.clip(tire_management, 0, 1)
        self.consistency = np.clip(consistency, 0, 1)
        self.racecraft = np.clip(racecraft, 0, 1)
        
        # Strategy characteristics
        self.strategy_type = strategy_type
        self.pit_timing_bias = np.clip(pit_timing_bias, -0.2, 0.2)
        self.undercut_sensitivity = np.clip(undercut_sensitivity, 0, 1)
        self.overcut_willingness = np.clip(overcut_willingness, 0, 1)
        self.defensive_driving = np.clip(defensive_driving, 0, 1)
        
        # Historical data for learning
        self.pit_history = []  # [(lap, tire_age, position)]
        self.overtake_attempts = []  # [(lap, success, opponent)]
        self.strategy_success = []  # [finish_positions]
        
    def predict_pit_window(self, total_laps: int, current_lap: int, 
                          tire_age: int, tire_compound: str) -> Tuple[int, int]:
        """
        Predict when this driver will likely pit.
        
        Returns:
            (earliest_pit, latest_pit) lap range
        """
        # Base pit window
        optimal = TIRE_COMPOUNDS[tire_compound]['optimal_laps']
        base_window = int(optimal * 0.8), int(optimal * 1.2)
        
        # Adjust for strategy type
        if self.strategy_type == StrategyType.AGGRESSIVE:
            bias = -5 + int(self.pit_timing_bias * 10)
        elif self.strategy_type == StrategyType.CONSERVATIVE:
            bias = 5 + int(self.pit_timing_bias * 10)
        else:
            bias = int(self.pit_timing_bias * 5)
        
        earliest = max(current_lap + 1, base_window[0] + bias)
        latest = min(total_laps - 5, base_window[1] + bias)
        
        return earliest, latest
    
    def undercut_probability(self, gap_to_ahead: float, 
                            our_tire_age: int, their_tire_age: int) -> float:
        """
        Calculate probability this driver will attempt undercut.
        
        Args:
            gap_to_ahead: Gap to car ahead (seconds)
            our_tire_age: Our current tire age
            their_tire_age: Tire age of car ahead
            
        Returns:
            Probability (0-1) of undercut attempt
        """
        # Can't undercut if too far back
        if gap_to_ahead > 3.0:
            return 0.0
        
        base_prob = 0.3
        
        # Closer = higher probability
        proximity_bonus = max(0, (3.0 - gap_to_ahead) / 3.0) * 0.4
        
        # Strategy type modifier
        type_multiplier = {
            StrategyType.AGGRESSIVE: 1.5,
            StrategyType.UNDERCUT_FOCUSED: 2.0,
            StrategyType.BALANCED: 1.0,
            StrategyType.CONSERVATIVE: 0.5,
        }.get(self.strategy_type, 1.0)
        
        # Tire advantage potential
        tire_advantage = max(0, (their_tire_age - our_tire_age) / 10) * 0.2
        
        prob = (base_prob + proximity_bonus + tire_advantage) * type_multiplier
        prob *= self.undercut_sensitivity
        
        return np.clip(prob, 0, 1)
    
    def blocking_probability(self, gap_to_behind: float, 
                            track_difficulty: str = 'medium') -> float:
        """
        Calculate probability this driver will successfully block.
        
        Returns:
            Probability (0-1) of maintaining position
        """
        base_defense = self.defensive_driving
        
        # Closer gap = harder to defend
        gap_factor = np.clip(gap_to_behind / 2.0, 0, 1)
        
        # Track difficulty modifier
        difficulty_mult = {'easy': 0.7, 'medium': 1.0, 'hard': 1.3}
        mult = difficulty_mult.get(track_difficulty, 1.0)
        
        prob = base_defense * gap_factor * mult
        
        # Aggressive drivers defend harder
        if self.aggression > 0.7:
            prob *= 1.2
        
        return np.clip(prob, 0, 1)
    
    def overcut_viability(self, gap_to_ahead: float, 
                         our_pit_loss: float, their_pit_loss: float) -> float:
        """
        Calculate viability of overcut strategy.
        
        Returns:
            Score (0-1) of overcut potential
        """
        if self.overcut_willingness < 0.3:
            return 0.0
        
        # Need to be close enough
        if gap_to_ahead > 2.0:
            return 0.0
        
        # Overcut works best when we can push hard on fresh tires
        # and they have to pit soon
        base_viability = 0.4
        
        # Gap factor - sweet spot is 1.0-1.5s
        gap_score = 1.0 - abs(gap_to_ahead - 1.25) / 1.25
        
        # Pit loss differential
        pit_advantage = max(0, (their_pit_loss - our_pit_loss) / 5)
        
        viability = (base_viability + gap_score * 0.3 + pit_advantage * 0.2)
        viability *= self.overcut_willingness
        
        return np.clip(viability, 0, 1)


@dataclass
class UndercutAnalysis:
    """Analysis of undercut opportunity."""
    viable: bool
    probability: float  # Success probability
    optimal_lap: int
    time_gain_potential: float
    risk_score: float
    reasoning: str
    # Additional metrics for comprehensive analysis
    effectiveness_score: float = 0.0  # 0-100 composite score
    opponent_reaction_time: Optional[int] = None  # Laps until opponent responds
    gap_before: float = 0.0
    gap_after: float = 0.0
    gap_change: float = 0.0
    success: bool = False
    tire_advantage_at_exit: float = 0.0


@dataclass
class CompetitiveSituation:
    """Current competitive context for strategy decisions."""
    our_position: int
    car_ahead_id: Optional[int]
    car_behind_id: Optional[int]
    gap_to_ahead: float
    gap_to_behind: float
    laps_to_go: int
    our_tire_age: int
    our_tire_compound: str
    ahead_tire_age: Optional[int]
    ahead_tire_compound: Optional[str]
    behind_tire_age: Optional[int]
    behind_tire_compound: Optional[str]


class OpponentModelingEngine:
    """
    Elite opponent modeling engine with game theory implementation.
    Predicts competitor moves and optimizes counter-strategies.
    """
    
    def __init__(self):
        self.driver_profiles: Dict[int, DriverBehaviorProfile] = {}
        self.interaction_history = []
        self.predicted_pit_laps = {}
        
    def register_driver(self, profile: DriverBehaviorProfile):
        """Register a driver for modeling."""
        self.driver_profiles[profile.driver_id] = profile
        
    def analyze_undercut_opportunity(self,
                                    situation: CompetitiveSituation,
                                    circuit: str) -> UndercutAnalysis:
        """
        Comprehensive undercut analysis with probability estimation.
        
        Args:
            situation: Current race situation
            circuit: Circuit name
            
        Returns:
            UndercutAnalysis with viability and recommendations
        """
        circuit_config = CIRCUITS[circuit]
        pit_loss = circuit_config['pit_loss']
        
        # Basic viability checks
        if situation.gap_to_ahead > 2.5:
            return UndercutAnalysis(
                viable=False,
                probability=0.0,
                optimal_lap=0,
                time_gain_potential=0.0,
                risk_score=1.0,
                reasoning="Gap too large (>2.5s) for undercut"
            )
        
        if situation.laps_to_go < 10:
            return UndercutAnalysis(
                viable=False,
                probability=0.0,
                optimal_lap=0,
                time_gain_potential=0.0,
                risk_score=1.0,
                reasoning="Too few laps remaining"
            )
        
        # Calculate time gain potential
        # Undercut gains ~2-3 seconds from tire advantage on out-lap
        tire_advantage_gain = 2.5
        
        # Adjust for gap
        if situation.gap_to_ahead < 1.0:
            # Very close - undercut highly effective
            success_prob = 0.75
            optimal_timing = "immediate"
        elif situation.gap_to_ahead < 1.5:
            # Good range for undercut
            success_prob = 0.60
            optimal_timing = "next 2 laps"
        elif situation.gap_to_ahead < 2.0:
            # Possible but risky
            success_prob = 0.45
            optimal_timing = "within 3 laps"
        else:
            success_prob = 0.30
            optimal_timing = "only if tire advantage large"
        
        # Calculate time gain
        time_gain = tire_advantage_gain - situation.gap_to_ahead
        
        # Risk assessment
        risk_score = 0.3 + (situation.gap_to_ahead / 3.0) * 0.4
        if situation.our_tire_age < 15:
            risk_score += 0.2  # Pitting early is risky
        
        # Determine optimal lap
        if situation.gap_to_ahead < 1.0:
            optimal_lap = situation.our_tire_age + 2
        else:
            optimal_lap = situation.our_tire_age + 4
        
        reasoning = (
            f"Gap to ahead: {situation.gap_to_ahead:.2f}s. "
            f"Time gain potential: {time_gain:.2f}s. "
            f"Optimal timing: {optimal_timing}. "
            f"Pit loss: {pit_loss}s vs Tire gain: {tire_advantage_gain}s."
        )
        
        return UndercutAnalysis(
            viable=success_prob > 0.4,
            probability=success_prob,
            optimal_lap=optimal_lap,
            time_gain_potential=max(0, time_gain),
            risk_score=risk_score,
            reasoning=reasoning
        )
    
    def predict_opponent_pit_strategy(self,
                                     driver_id: int,
                                     total_laps: int,
                                     current_lap: int) -> Dict:
        """
        Predict when opponent will pit based on their profile.
        
        Returns:
            Prediction with confidence intervals
        """
        profile = self.driver_profiles.get(driver_id)
        if not profile:
            return {'error': 'Driver not registered'}
        
        # Get their likely current tire
        # (In real use, this would come from race state)
        estimated_tire = 'medium'  # Default assumption
        
        # Predict window
        earliest, latest = profile.predict_pit_window(
            total_laps, current_lap, 20, estimated_tire
        )
        
        # Most likely lap (based on strategy type)
        if profile.strategy_type == StrategyType.AGGRESSIVE:
            most_likely = earliest + 2
        elif profile.strategy_type == StrategyType.CONSERVATIVE:
            most_likely = latest - 2
        else:
            most_likely = (earliest + latest) // 2
        
        confidence = 0.6 + profile.racecraft * 0.2
        
        return {
            'driver_id': driver_id,
            'driver_name': profile.name,
            'strategy_type': profile.strategy_type.value,
            'estimated_pit_window': [earliest, latest],
            'most_likely_lap': most_likely,
            'confidence': confidence,
            'undercut_threat': profile.undercut_sensitivity > 0.7,
            'defensive_skill': profile.defensive_driving
        }
    
    def simulate_strategic_battle(self,
                                 our_profile: DriverBehaviorProfile,
                                 opponent_profile: DriverBehaviorProfile,
                                 initial_gap: float,
                                 total_laps: int,
                                 circuit: str) -> Dict:
        """
        Simulate strategic interaction between two drivers.
        
        Returns:
            Battle simulation results
        """
        # Simple strategic simulation
        laps = []
        gap = initial_gap
        our_position = 2 if initial_gap > 0 else 1
        
        for lap in range(1, total_laps + 1):
            # Check for undercut opportunities
            if gap > 0 and gap < 2.0:
                undercut_prob = our_profile.undercut_probability(gap, 20, 25)
                if np.random.random() < undercut_prob:
                    # Attempt undercut
                    gap -= np.random.uniform(1.5, 3.0)
                    our_position = 1
            
            # Opponent defense
            if gap < 0 and abs(gap) < 1.0:
                block_prob = opponent_profile.blocking_probability(abs(gap))
                if np.random.random() < block_prob:
                    gap += np.random.uniform(0.2, 0.5)
            
            # Natural gap evolution
            gap += np.random.normal(0, 0.1)
            
            laps.append({
                'lap': lap,
                'gap': round(gap, 3),
                'position': our_position
            })
        
        final_gap = laps[-1]['gap']
        
        return {
            'initial_gap': initial_gap,
            'final_gap': final_gap,
            'gap_change': final_gap - initial_gap,
            'our_wins': final_gap < 0,
            'laps': laps[:10]  # First 10 laps for brevity
        }
    
    def get_strategic_recommendations(self,
                                     situation: CompetitiveSituation,
                                     circuit: str) -> Dict:
        """
        Get comprehensive strategic recommendations.
        
        Returns:
            Recommendations with game theory analysis
        """
        recommendations = []
        
        # 1. Undercut analysis
        undercut = self.analyze_undercut_opportunity(situation, circuit)
        if undercut.viable:
            recommendations.append({
                'type': 'undercut',
                'priority': 'high' if undercut.probability > 0.6 else 'medium',
                'probability': undercut.probability,
                'optimal_lap': undercut.optimal_lap,
                'reasoning': undercut.reasoning
            })
        
        # 2. Defensive recommendations
        if situation.gap_to_behind < 2.0:
            # Under threat
            if situation.car_behind_id in self.driver_profiles:
                threat_profile = self.driver_profiles[situation.car_behind_id]
                undercut_threat = threat_profile.undercut_sensitivity > 0.6
                
                if undercut_threat:
                    recommendations.append({
                        'type': 'defend_undercut',
                        'priority': 'high',
                        'reasoning': f"Driver behind ({threat_profile.name}) is undercut-sensitive. "
                                   f"Consider early pit to cover."
                    })
        
        # 3. Track position value
        if situation.our_position <= 3:
            recommendations.append({
                'type': 'position_defense',
                'priority': 'high',
                'reasoning': f"P{situation.our_position} is valuable. Prioritize position maintenance."
            })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return {
            'situation': {
                'position': situation.our_position,
                'gap_to_ahead': situation.gap_to_ahead,
                'gap_to_behind': situation.gap_to_behind,
                'laps_to_go': situation.laps_to_go
            },
            'recommendations': recommendations,
            'primary_strategy': recommendations[0] if recommendations else None
        }


def create_elite_driver_grid() -> List[DriverBehaviorProfile]:
    """Create a grid of elite drivers with varied characteristics."""
    drivers = [
        DriverBehaviorProfile(
            0, "Max Verstappen", "Red Bull",
            base_skill=0.95, aggression=0.9, tire_management=0.9,
            consistency=0.95, strategy_type=StrategyType.AGGRESSIVE,
            undercut_sensitivity=0.9, defensive_driving=0.9
        ),
        DriverBehaviorProfile(
            1, "Lewis Hamilton", "Mercedes",
            base_skill=0.93, aggression=0.7, tire_management=0.95,
            consistency=0.92, strategy_type=StrategyType.BALANCED,
            undercut_sensitivity=0.8, racecraft=0.95
        ),
        DriverBehaviorProfile(
            2, "Charles Leclerc", "Ferrari",
            base_skill=0.90, aggression=0.85, tire_management=0.85,
            consistency=0.85, strategy_type=StrategyType.AGGRESSIVE,
            overcut_willingness=0.7
        ),
        DriverBehaviorProfile(
            3, "Lando Norris", "McLaren",
            base_skill=0.88, aggression=0.75, tire_management=0.88,
            consistency=0.88, strategy_type=StrategyType.UNDERCUT_FOCUSED,
            undercut_sensitivity=0.95
        ),
        DriverBehaviorProfile(
            4, "Carlos Sainz", "Ferrari",
            base_skill=0.87, aggression=0.65, tire_management=0.90,
            consistency=0.90, strategy_type=StrategyType.CONSERVATIVE,
            pit_timing_bias=0.1
        ),
    ]
    return drivers


if __name__ == "__main__":
    # Test opponent modeling
    print("Testing Opponent Modeling Engine")
    print("=" * 60)
    
    # Create engine
    engine = OpponentModelingEngine()
    
    # Register drivers
    drivers = create_elite_driver_grid()
    for driver in drivers:
        engine.register_driver(driver)
    
    # Test undercut analysis
    print("\n1. Undercut Analysis")
    situation = CompetitiveSituation(
        our_position=2,
        car_ahead_id=0,
        car_behind_id=3,
        gap_to_ahead=1.2,
        gap_to_behind=2.5,
        laps_to_go=30,
        our_tire_age=22,
        our_tire_compound='medium',
        ahead_tire_age=25,
        ahead_tire_compound='medium',
        behind_tire_age=20,
        behind_tire_compound='soft'
    )
    
    undercut = engine.analyze_undercut_opportunity(situation, 'Monza')
    print(f"Viable: {undercut.viable}")
    print(f"Success Probability: {undercut.probability:.1%}")
    print(f"Optimal Lap: {undercut.optimal_lap}")
    print(f"Time Gain: {undercut.time_gain_potential:.2f}s")
    print(f"Risk Score: {undercut.risk_score:.2f}")
    print(f"Reasoning: {undercut.reasoning}")
    
    # Test pit prediction
    print("\n2. Pit Strategy Prediction")
    prediction = engine.predict_opponent_pit_strategy(0, 53, 20)
    print(f"Driver: {prediction['driver_name']}")
    print(f"Strategy Type: {prediction['strategy_type']}")
    print(f"Pit Window: Laps {prediction['estimated_pit_window'][0]}-{prediction['estimated_pit_window'][1]}")
    print(f"Most Likely: Lap {prediction['most_likely_lap']}")
    print(f"Undercut Threat: {prediction['undercut_threat']}")
    
    # Test strategic battle
    print("\n3. Strategic Battle Simulation")
    battle = engine.simulate_strategic_battle(drivers[3], drivers[0], 1.5, 53, 'Monza')
    print(f"Initial Gap: {battle['initial_gap']:.2f}s")
    print(f"Final Gap: {battle['final_gap']:.2f}s")
    print(f"Gap Change: {battle['gap_change']:.2f}s")
    print(f"We Win: {battle['our_wins']}")
    
    # Test recommendations
    print("\n4. Strategic Recommendations")
    recs = engine.get_strategic_recommendations(situation, 'Monza')
    print(f"Primary Strategy: {recs['primary_strategy']['type'] if recs['primary_strategy'] else 'None'}")
    for rec in recs['recommendations']:
        print(f"  - {rec['type']} ({rec['priority']}): {rec.get('reasoning', '')[:60]}...")
    
    print("\n" + "=" * 60)
    print("Opponent Modeling test complete!")
