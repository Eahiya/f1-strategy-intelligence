"""
F1 Strategy Intelligence System - Elite Edition v3.0
Advanced Race Metrics & Analytics

Implements sophisticated metrics including undercut effectiveness,
tire delta analysis, track position value, and strategy regret.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.core.config import TIRE_COMPOUNDS


@dataclass
class UndercutMetrics:
    """Detailed undercut analysis metrics."""
    undercut_lap: int
    gap_before: float
    gap_after: float
    gap_change: float
    time_gained: float
    success: bool
    opponent_reaction_time: Optional[int]  # How many laps until opponent pitted
    tire_advantage_at_exit: float  # Seconds
    effectiveness_score: float  # 0-100


@dataclass
class TireDeltaMetrics:
    """Tire performance delta metrics."""
    our_tire: str
    our_age: int
    opponent_tire: str
    opponent_age: int
    lap_time_delta: float  # Positive = we're slower
    delta_per_lap: float
    cumulative_delta: float
    overtake_window_open: bool
    undercut_viable: bool
    estimated_laps_to_overtake: Optional[int]


@dataclass
class TrackPositionValue:
    """Value of current track position."""
    position: int
    clean_air_bonus: float  # Seconds per lap gained from clean air
    dirty_air_penalty: float  # Seconds lost in traffic
    drs_access: bool
    overtake_difficulty: float  # 0-1 scale
    championship_points_at_risk: int
    strategic_options_count: int


@dataclass
class StrategyRegretMetrics:
    """Regret analysis for completed race."""
    actual_strategy: str
    actual_finish_position: int
    actual_race_time: float
    optimal_hindsight_strategy: str
    optimal_hindsight_position: int
    position_regret: int
    time_regret_seconds: float
    points_regret: int
    key_mistakes: List[Dict]
    learning_insights: List[str]


class AdvancedMetricsEngine:
    """
    Elite metrics engine for deep race analysis.
    """
    
    def __init__(self):
        self.metric_history = []
        
    def calculate_undercut_effectiveness(self,
                                        our_pit_lap: int,
                                        opponent_pit_lap: int,
                                        gap_before_pit: float,
                                        gap_after_opponent_pit: float,
                                        tire_compound: str,
                                        total_laps: int) -> UndercutMetrics:
        """
        Calculate comprehensive undercut effectiveness.
        
        Args:
            our_pit_lap: Lap we pitted
            opponent_pit_lap: Lap opponent pitted (if None, they didn't)
            gap_before_pit: Gap to opponent before our pit (seconds)
            gap_after_opponent_pit: Gap after opponent's pit response
            tire_compound: Tire we switched to
            total_laps: Total race distance
            
        Returns:
            UndercutMetrics with detailed analysis
        """
        # Calculate gap change
        if gap_before_pit > 0:  # We were behind
            # Gap closing = positive change
            gap_change = gap_before_pit - gap_after_opponent_pit
            success = gap_after_opponent_pit < 0  # We got ahead
        else:  # We were ahead
            gap_change = abs(gap_after_opponent_pit) - abs(gap_before_pit)
            success = gap_after_opponent_pit < gap_before_pit
        
        # Calculate time gained from tire advantage
        # Fresh tires gain ~0.5-1.5s per lap initially
        tire_config = TIRE_COMPOUNDS[tire_compound]
        advantage_per_lap = tire_config['base_pace'] * -1  # Soft is negative
        laps_with_advantage = opponent_pit_lap - our_pit_lap if opponent_pit_lap else 5
        time_gained = advantage_per_lap * laps_with_advantage + np.random.uniform(1, 3)
        
        # Calculate effectiveness score
        # Factors: Gap closed, time gained, overtake success, track position
        score_components = {
            'gap_closed': min(1.0, gap_change / 3.0) * 30,  # 30 points max
            'time_gained': min(1.0, time_gained / 5.0) * 30,  # 30 points max
            'overtake_success': 20 if success else 0,  # 20 points
            'optimal_timing': 20 if our_pit_lap < total_laps * 0.7 else 10  # Timing bonus
        }
        
        effectiveness_score = sum(score_components.values())
        
        # Opponent reaction time
        if opponent_pit_lap:
            reaction_time = opponent_pit_lap - our_pit_lap
        else:
            reaction_time = None  # No reaction (bad for them)
        
        return UndercutMetrics(
            undercut_lap=our_pit_lap,
            gap_before=gap_before_pit,
            gap_after=gap_after_opponent_pit,
            gap_change=gap_change,
            time_gained=time_gained,
            success=success,
            opponent_reaction_time=reaction_time,
            tire_advantage_at_exit=time_gained,
            effectiveness_score=effectiveness_score
        )
    
    def analyze_tire_delta(self,
                          our_tire: str,
                          our_age: int,
                          opponent_tire: str,
                          opponent_age: int,
                          current_gap: float,
                          circuit: str,
                          laps_to_go: int) -> TireDeltaMetrics:
        """
        Analyze tire performance delta between two cars.
        
        Returns:
            TireDeltaMetrics with strategic implications
        """
        # Get tire configurations
        our_config = TIRE_COMPOUNDS[our_tire]
        opp_config = TIRE_COMPOUNDS[opponent_tire]
        
        # Base pace difference
        base_delta = our_config['base_pace'] - opp_config['base_pace']
        
        # Degradation curves
        our_deg = our_config['degradation_rate'] * (our_age ** 1.5)
        opp_deg = opp_config['degradation_rate'] * (opponent_age ** 1.5)
        
        # Total delta per lap
        delta_per_lap = base_delta + (our_deg - opp_deg)
        
        # Cumulative delta over remaining race
        cumulative_delta = delta_per_lap * laps_to_go
        
        # Overtake window analysis
        # Overtake viable if gap < 2s and we have tire advantage
        overtake_window = current_gap < 2.0 and delta_per_lap < -0.3
        
        # Undercut viable if gap < 3s and our tires not too old
        undercut_viable = (current_gap < 3.0 and 
                          our_age < 30 and 
                          our_age > opponent_age)
        
        # Estimate laps to overtake (if window open)
        if overtake_window and delta_per_lap < 0:
            laps_needed = int(current_gap / abs(delta_per_lap))
            estimated_laps = max(1, min(laps_needed, laps_to_go))
        else:
            estimated_laps = None
        
        return TireDeltaMetrics(
            our_tire=our_tire,
            our_age=our_age,
            opponent_tire=opponent_tire,
            opponent_age=opponent_age,
            lap_time_delta=delta_per_lap,
            delta_per_lap=delta_per_lap,
            cumulative_delta=cumulative_delta,
            overtake_window_open=overtake_window,
            undercut_viable=undercut_viable,
            estimated_laps_to_overtake=estimated_laps
        )
    
    def calculate_track_position_value(self,
                                      position: int,
                                      total_cars: int = 20,
                                      gap_to_ahead: float = 2.0,
                                      gap_to_behind: float = 3.0,
                                      drs_available: bool = True) -> TrackPositionValue:
        """
        Calculate strategic value of current track position.
        
        Returns:
            TrackPositionValue with strategic implications
        """
        # Clean air bonus (first few positions)
        if position <= 3:
            clean_air = (4 - position) * 0.02  # 0.06, 0.04, 0.02
        else:
            clean_air = 0.0
        
        # Dirty air penalty (in traffic)
        if gap_to_ahead < 1.0:
            dirty_air = 0.015 * (1.0 - gap_to_ahead)  # Up to 0.015s penalty
        elif gap_to_ahead < 2.0:
            dirty_air = 0.008 * (2.0 - gap_to_ahead)
        else:
            dirty_air = 0.0
        
        # DRS access (typically top 10 and within 1 second)
        drs_access = position <= 10 and gap_to_ahead < 1.0 and drs_available
        
        # Overtake difficulty (circuit dependent)
        if position <= 3:
            overtake_diff = 0.3  # Harder to overtake at front (defensive driving)
        elif position <= 10:
            overtake_diff = 0.5
        else:
            overtake_diff = 0.7  # Easier in midfield
        
        # Championship points at risk
        points_positions = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 
                          6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
        current_points = points_positions.get(position, 0)
        next_points = points_positions.get(position - 1, current_points) if position > 1 else current_points
        points_at_risk = next_points - current_points
        
        # Strategic options (more options in midfield)
        if position == 1:
            options = 2  # Defend or extend lead
        elif position <= 3:
            options = 3  # Attack, defend, or maintain
        elif position <= 10:
            options = 4  # Multiple strategies
        else:
            options = 5  # Maximum flexibility
        
        return TrackPositionValue(
            position=position,
            clean_air_bonus=clean_air,
            dirty_air_penalty=dirty_air,
            drs_access=drs_access,
            overtake_difficulty=overtake_diff,
            championship_points_at_risk=points_at_risk,
            strategic_options_count=options
        )
    
    def calculate_strategy_regret(self,
                                 race_data: pd.DataFrame,
                                 our_driver_id: int,
                                 alternative_strategies: List[Dict]) -> StrategyRegretMetrics:
        """
        Calculate regret - what we should have done vs what we did.
        
        Args:
            race_data: Complete race telemetry DataFrame
            our_driver_id: Our driver identifier
            alternative_strategies: List of strategies that could have been used
            
        Returns:
            StrategyRegretMetrics with hindsight analysis
        """
        # Extract our actual performance
        our_data = race_data[race_data['driver_id'] == our_driver_id]
        
        if len(our_data) == 0:
            return StrategyRegretMetrics(
                actual_strategy='unknown',
                actual_finish_position=20,
                actual_race_time=9999.0,
                optimal_hindsight_strategy='unknown',
                optimal_hindsight_position=20,
                position_regret=0,
                time_regret_seconds=0.0,
                points_regret=0,
                key_mistakes=[],
                learning_insights=['No data available']
            )
        
        actual_position = our_data['position'].iloc[-1]
        actual_time = our_data['lap_time'].sum()
        
        # Simulate alternative strategies
        best_alternative = None
        best_position = actual_position
        
        for strategy in alternative_strategies:
            # Simulate outcome (simplified)
            simulated_position = self._simulate_strategy_outcome(
                strategy, race_data, our_driver_id
            )
            
            if simulated_position < best_position:
                best_position = simulated_position
                best_alternative = strategy
        
        # Calculate regrets
        position_regret = actual_position - best_position
        time_regret = 0.0  # Would need full simulation
        
        # Points regret
        points_table = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 
                       6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
        actual_points = points_table.get(actual_position, 0)
        optimal_points = points_table.get(best_position, 0)
        points_regret = optimal_points - actual_points
        
        # Identify key mistakes
        mistakes = self._identify_mistakes(our_data)
        
        # Generate insights
        insights = self._generate_insights(mistakes, best_alternative)
        
        return StrategyRegretMetrics(
            actual_strategy='executed_strategy',
            actual_finish_position=actual_position,
            actual_race_time=actual_time,
            optimal_hindsight_strategy=best_alternative.get('type', 'unknown') if best_alternative else 'none',
            optimal_hindsight_position=best_position,
            position_regret=position_regret,
            time_regret_seconds=time_regret,
            points_regret=points_regret,
            key_mistakes=mistakes,
            learning_insights=insights
        )
    
    def _simulate_strategy_outcome(self, 
                                  strategy: Dict, 
                                  race_data: pd.DataFrame,
                                  driver_id: int) -> int:
        """Simulate outcome of alternative strategy."""
        # Simplified simulation
        base_position = race_data[race_data['driver_id'] == driver_id]['position'].iloc[-1]
        
        # Adjust based on strategy quality
        pit_count = len(strategy.get('pit_laps', []))
        if pit_count == 1:
            improvement = np.random.randint(-2, 4)  # 1-stop can be good or bad
        elif pit_count == 2:
            improvement = np.random.randint(-1, 3)  # 2-stop usually balanced
        else:
            improvement = np.random.randint(0, 2)  # 3-stop rarely optimal
        
        return max(1, base_position - improvement)
    
    def _identify_mistakes(self, our_data: pd.DataFrame) -> List[Dict]:
        """Identify key strategy mistakes from race data."""
        mistakes = []
        
        # Check for late pit stops when tire age > 30
        old_tire_laps = our_data[our_data['tire_age'] > 30]
        if len(old_tire_laps) > 3:
            mistakes.append({
                'type': 'delayed_pit_stop',
                'lap': int(old_tire_laps.iloc[0]['lap_number']),
                'severity': 'medium',
                'description': f"Ran {len(old_tire_laps)} laps on very old tires, losing pace"
            })
        
        # Check for missed undercut opportunities
        # (Gap to ahead < 2s and we didn't pit first)
        # Simplified check
        
        return mistakes
    
    def _generate_insights(self, mistakes: List[Dict], 
                          best_alternative: Optional[Dict]) -> List[str]:
        """Generate learning insights from mistakes."""
        insights = []
        
        if best_alternative:
            insights.append(
                f"Alternative {best_alternative.get('type', 'strategy')} "
                f"could have improved result. Consider for similar situations."
            )
        
        for mistake in mistakes:
            if mistake['type'] == 'delayed_pit_stop':
                insights.append(
                    "Pit window optimization needs improvement. "
                    "Current model too conservative on tire age."
                )
        
        if not insights:
            insights.append("Strategy execution was optimal for given circumstances.")
        
        return insights
    
    def generate_comprehensive_report(self,
                                     race_telemetry: pd.DataFrame,
                                     our_driver_id: int,
                                     circuit: str) -> Dict:
        """
        Generate comprehensive race metrics report.
        
        Returns:
            Complete metrics report
        """
        our_data = race_telemetry[race_telemetry['driver_id'] == our_driver_id]
        
        if len(our_data) == 0:
            return {'error': 'No data for driver'}
        
        # Basic stats
        avg_lap_time = our_data['lap_time'].mean()
        best_lap = our_data['lap_time'].min()
        consistency = our_data['lap_time'].std()
        
        # Tire management
        tire_changes = our_data['tire_compound'].nunique()
        max_tire_age = our_data['tire_age'].max()
        
        # Position progression
        positions = our_data['position'].tolist()
        positions_gained = sum(1 for i in range(1, len(positions)) 
                              if positions[i] < positions[i-1])
        positions_lost = sum(1 for i in range(1, len(positions)) 
                            if positions[i] > positions[i-1])
        
        # Track position value analysis
        latest = our_data.iloc[-1]
        position_value = self.calculate_track_position_value(
            latest['position'],
            gap_to_ahead=latest.get('gap_to_ahead', 2.0),
            gap_to_behind=3.0
        )
        
        return {
            'race_summary': {
                'total_laps': len(our_data),
                'finish_position': int(latest['position']),
                'average_lap_time': round(avg_lap_time, 3),
                'best_lap_time': round(best_lap, 3),
                'lap_time_consistency': round(consistency, 3)
            },
            'strategy_metrics': {
                'pit_stops': tire_changes - 1,
                'max_tire_age': int(max_tire_age),
                'positions_gained': positions_gained,
                'positions_lost': positions_lost,
                'net_positions': positions_gained - positions_lost
            },
            'track_position_analysis': {
                'final_position_value': position_value.__dict__,
                'clean_air_advantage': round(position_value.clean_air_bonus, 4),
                'drs_opportunities': sum(our_data.get('drs_active', pd.Series([0] * len(our_data))))
            },
            'performance_rating': self._calculate_performance_rating(
                our_data, race_telemetry, circuit
            )
        }
    
    def _calculate_performance_rating(self,
                                     our_data: pd.DataFrame,
                                     all_data: pd.DataFrame,
                                     circuit: str) -> Dict:
        """Calculate overall performance rating."""
        # Compare to field
        our_avg = our_data['lap_time'].mean()
        field_avg = all_data['lap_time'].mean()
        
        # Pace rating (vs field)
        if our_avg < field_avg * 0.99:
            pace_rating = 'EXCELLENT'
        elif our_avg < field_avg:
            pace_rating = 'GOOD'
        else:
            pace_rating = 'AVERAGE'
        
        # Consistency rating
        consistency = our_data['lap_time'].std()
        if consistency < 0.3:
            cons_rating = 'EXCELLENT'
        elif consistency < 0.5:
            cons_rating = 'GOOD'
        else:
            cons_rating = 'AVERAGE'
        
        # Tire management
        deg_rates = []
        for _, stint in our_data.groupby('tire_compound'):
            if len(stint) > 5:
                lap_times = stint['lap_time'].tolist()
                deg = (lap_times[-1] - lap_times[0]) / len(lap_times)
                deg_rates.append(deg)
        
        avg_deg = np.mean(deg_rates) if deg_rates else 0.5
        if avg_deg < 0.1:
            tire_rating = 'EXCELLENT'
        elif avg_deg < 0.2:
            tire_rating = 'GOOD'
        else:
            tire_rating = 'AVERAGE'
        
        return {
            'pace': pace_rating,
            'consistency': cons_rating,
            'tire_management': tire_rating,
            'overall': 'ELITE' if pace_rating == 'EXCELLENT' and cons_rating == 'EXCELLENT' else 'PRO'
        }


if __name__ == "__main__":
    # Test advanced metrics
    print("Testing Advanced Metrics Engine")
    print("=" * 60)
    
    engine = AdvancedMetricsEngine()
    
    # Test 1: Undercut effectiveness
    print("\n1. Undercut Effectiveness")
    undercut = engine.calculate_undercut_effectiveness(
        our_pit_lap=22,
        opponent_pit_lap=25,
        gap_before_pit=1.5,
        gap_after_opponent_pit=-0.3,  # We got ahead!
        tire_compound='medium',
        total_laps=53
    )
    print(f"  Undercut Lap: {undercut.undercut_lap}")
    print(f"  Success: {undercut.success}")
    print(f"  Time Gained: {undercut.time_gained:.2f}s")
    print(f"  Effectiveness Score: {undercut.effectiveness_score:.1f}/100")
    print(f"  Opponent Reaction: {undercut.opponent_reaction_time} laps")
    
    # Test 2: Tire delta
    print("\n2. Tire Delta Analysis")
    delta = engine.analyze_tire_delta(
        our_tire='soft', our_age=10,
        opponent_tire='medium', opponent_age=25,
        current_gap=1.8,
        circuit='Monza',
        laps_to_go=30
    )
    print(f"  Lap Time Delta: {delta.lap_time_delta:.3f}s")
    print(f"  Cumulative Delta: {delta.cumulative_delta:.2f}s")
    print(f"  Overtake Window: {'OPEN' if delta.overtake_window_open else 'CLOSED'}")
    print(f"  Undercut Viable: {'YES' if delta.undercut_viable else 'NO'}")
    if delta.estimated_laps_to_overtake:
        print(f"  Est. Laps to Overtake: {delta.estimated_laps_to_overtake}")
    
    # Test 3: Track position value
    print("\n3. Track Position Value")
    pos_value = engine.calculate_track_position_value(
        position=3,
        gap_to_ahead=1.2,
        gap_to_behind=2.5,
        drs_available=True
    )
    print(f"  Position: P{pos_value.position}")
    print(f"  Clean Air Bonus: {pos_value.clean_air_bonus:.4f}s/lap")
    print(f"  Dirty Air Penalty: {pos_value.dirty_air_penalty:.4f}s/lap")
    print(f"  DRS Access: {'YES' if pos_value.drs_access else 'NO'}")
    print(f"  Overtake Difficulty: {pos_value.overtake_difficulty:.2f}")
    print(f"  Points at Risk: {pos_value.championship_points_at_risk}")
    
    # Test 4: Comprehensive report (with dummy data)
    print("\n4. Comprehensive Report")
    dummy_data = pd.DataFrame({
        'driver_id': [0] * 20,
        'lap_number': range(1, 21),
        'position': [5, 5, 4, 4, 4, 3, 3, 3, 3, 2,
                    2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        'lap_time': [90 + np.random.normal(0, 0.3) for _ in range(20)],
        'tire_compound': ['soft'] * 10 + ['medium'] * 10,
        'tire_age': list(range(1, 11)) + list(range(1, 11)),
        'drs_active': [True] * 15 + [False] * 5,
        'gap_to_ahead': [2.0 - i*0.1 for i in range(20)]
    })
    
    all_dummy = pd.concat([dummy_data, pd.DataFrame({
        'driver_id': [1] * 20,
        'lap_number': range(1, 21),
        'position': [1] * 20,
        'lap_time': [89.5 + np.random.normal(0, 0.3) for _ in range(20)],
        'tire_compound': ['soft'] * 20,
        'tire_age': list(range(1, 21)),
        'drs_active': [False] * 20,
        'gap_to_ahead': [0] * 20
    })])
    
    report = engine.generate_comprehensive_report(all_dummy, 0, 'Monza')
    print(f"  Finish Position: P{report['race_summary']['finish_position']}")
    print(f"  Avg Lap Time: {report['race_summary']['average_lap_time']:.3f}s")
    print(f"  Net Positions: {report['strategy_metrics']['net_positions']:+d}")
    print(f"  Performance: {report['performance_rating']['overall']}")
    
    print("\n" + "=" * 60)
    print("Advanced metrics test complete!")
