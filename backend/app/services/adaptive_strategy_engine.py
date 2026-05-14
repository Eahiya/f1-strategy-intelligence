"""
F1 Strategy Intelligence System - Elite Edition v3.0
Real-Time Adaptive Strategy Engine & Digital Twin Simulation

Continuously recalculates optimal strategy based on race events,
with parallel scenario evaluation (Digital Twin concept).
"""
import numpy as np
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app.core.config import CIRCUITS
from app.models.rl_strategy_engine import RLStrategyEngine, RaceState
from app.models.opponent_model import OpponentModelingEngine
from app.models.probabilistic_risk_engine import BayesianRiskModel
from app.services.multi_car_simulator import MultiCarSimulator
from app.models.advanced_strategy_optimizer import AdvancedStrategyOptimizer


class RaceEvent(Enum):
    """Types of race events that trigger strategy recalculation."""
    OVERTAKE = "overtake"
    SAFETY_CAR = "safety_car"
    WEATHER_CHANGE = "weather_change"
    PIT_STOP = "pit_stop"
    VSC = "virtual_safety_car"
    RED_FLAG = "red_flag"
    DRIVER_ERROR = "driver_error"
    TIRE_FAILURE = "tire_failure"


@dataclass
class StrategyUpdate:
    """Strategy update recommendation."""
    trigger_event: RaceEvent
    current_lap: int
    previous_strategy: Dict
    recommended_strategy: Dict
    confidence: float
    time_gain_potential: float
    risk_change: float
    explanation: str
    decision_deadline: int  # Lap by which decision must be made
    alternatives: List[Dict]


@dataclass
class DigitalTwinScenario:
    """A parallel simulated scenario for "what-if" analysis."""
    scenario_id: str
    description: str
    trigger_condition: str
    probability: float
    projected_outcome: Dict
    strategy_adjustment: Dict
    confidence: float


class RealTimeStrategyAdapter:
    """
    Real-time adaptive strategy system that recalculates optimal
    strategy every lap based on race developments.
    """
    
    def __init__(self, circuit: str, total_laps: int, driver_id: int = 0):
        self.circuit = circuit
        self.total_laps = total_laps
        self.driver_id = driver_id
        self.circuit_config = CIRCUITS[circuit]
        
        # Sub-engines
        self.rl_engine = RLStrategyEngine(use_dqn=True)
        self.opponent_model = OpponentModelingEngine()
        self.risk_model = BayesianRiskModel()
        self.optimizer = AdvancedStrategyOptimizer(num_monte_carlo_runs=50)
        
        # Race state tracking
        self.lap_history = []
        self.strategy_history = []
        self.current_strategy = None
        self.recommendation_queue = deque(maxlen=10)
        
        # Event tracking
        self.event_log = []
        self.last_recalculation = 0
        
    def update_race_state(self, 
                         lap_number: int,
                         position: int,
                         gap_to_ahead: float,
                         gap_to_behind: float,
                         gap_to_leader: float,
                         tire_age: int,
                         tire_compound: str,
                         weather: str,
                         safety_car_active: bool = False,
                         fuel_load: float = 50.0) -> Dict:
        """
        Update race state and trigger strategy recalculation if needed.
        
        Returns:
            Current strategy recommendation
        """
        # Record state
        state = {
            'lap': lap_number,
            'position': position,
            'gap_to_ahead': gap_to_ahead,
            'gap_to_behind': gap_to_behind,
            'gap_to_leader': gap_to_leader,
            'tire_age': tire_age,
            'tire_compound': tire_compound,
            'weather': weather,
            'safety_car': safety_car_active,
            'fuel_load': fuel_load,
            'timestamp': datetime.now().isoformat()
        }
        self.lap_history.append(state)
        
        # Check for significant changes requiring recalculation
        should_recalculate = self._should_recalculate_strategy(lap_number)
        
        if should_recalculate:
            recommendation = self._recalculate_strategy(state)
            self.recommendation_queue.append(recommendation)
            self.last_recalculation = lap_number
            return recommendation
        
        return self._get_current_recommendation()
    
    def _should_recalculate_strategy(self, lap_number: int) -> bool:
        """Determine if strategy recalculation is needed."""
        # Always recalculate every 5 laps minimum
        if lap_number - self.last_recalculation >= 5:
            return True
        
        if len(self.lap_history) < 2:
            return True
        
        current = self.lap_history[-1]
        previous = self.lap_history[-2]
        
        # Check for position changes
        if current['position'] != previous['position']:
            return True
        
        # Check for gap changes > 1 second
        if abs(current['gap_to_ahead'] - previous['gap_to_ahead']) > 1.0:
            return True
        
        # Check for weather changes
        if current['weather'] != previous['weather']:
            return True
        
        # Check for safety car
        if current['safety_car'] != previous['safety_car']:
            return True
        
        # Check for tire age milestones
        if current['tire_age'] in [15, 20, 25, 30, 35]:
            return True
        
        return False
    
    def _recalculate_strategy(self, current_state: Dict) -> Dict:
        """Recalculate optimal strategy based on current state."""
        lap = current_state['lap']
        
        # Create RL state
        race_state = RaceState(
            lap_number=lap,
            total_laps=self.total_laps,
            tire_age=current_state['tire_age'],
            tire_compound={'soft': 0, 'medium': 1, 'hard': 2}.get(current_state['tire_compound'], 0),
            current_position=current_state['position'],
            gap_to_ahead=current_state['gap_to_ahead'],
            gap_to_behind=current_state['gap_to_behind'],
            gap_to_leader=current_state['gap_to_leader'],
            weather_condition={'dry': 0, 'light_rain': 1, 'heavy_rain': 2}.get(current_state['weather'], 0),
            track_temperature=35.0,
            safety_car_active=current_state['safety_car'],
            fuel_load=current_state['fuel_load'],
            tire_degradation=current_state['tire_age'] * 0.05,
            track_evolution=lap * 0.001
        )
        
        # Get RL recommendation
        rl_rec = self.rl_engine.predict(race_state)
        
        # Get traditional optimization
        opt_rec = self.optimizer.optimize(
            self.circuit, self.total_laps, 
            strategy_type='auto',
            initial_weather=current_state['weather']
        )
        
        # Combine recommendations (weighted ensemble)
        # rl_weight = 0.6
        # opt_weight = 0.4
        
        # Determine if RL says pit
        rl_pit = rl_rec['should_pit']
        opt_pit_laps = opt_rec['pit_laps']
        
        # If RL strongly recommends pit and we're near an opt pit lap, do it
        if rl_pit and rl_rec['confidence'] > 0.7:
            # Check if we're near an optimal pit window
            for pit_lap in opt_pit_laps:
                if abs(lap - pit_lap) <= 3:
                    recommendation = {
                        'action': 'PIT_NOW',
                        'tire': rl_rec['recommended_tire'] or opt_rec['tires'][0],
                        'confidence': rl_rec['confidence'],
                        'reasoning': f"RL ({rl_rec['confidence']:.0%} confidence) + Monte Carlo optimization align.",
                        'lap': lap,
                        'rl_recommendation': rl_rec,
                        'optimizer_recommendation': opt_rec
                    }
                    break
            else:
                # RL says pit but not in optimal window
                if rl_rec['confidence'] > 0.85:
                    recommendation = {
                        'action': 'PIT_NOW',
                        'tire': rl_rec['recommended_tire'],
                        'confidence': rl_rec['confidence'] * 0.8,
                        'reasoning': f"High-confidence RL override: {rl_rec['explanation']}",
                        'lap': lap,
                        'rl_recommendation': rl_rec,
                        'optimizer_recommendation': opt_rec
                    }
                else:
                    recommendation = {
                        'action': 'STAY_OUT',
                        'tire': None,
                        'confidence': 1 - rl_rec['confidence'],
                        'reasoning': "Continue current stint per optimization model.",
                        'lap': lap,
                        'rl_recommendation': rl_rec,
                        'optimizer_recommendation': opt_rec
                    }
        else:
            recommendation = {
                'action': 'STAY_OUT' if not opt_rec['pit_laps'] or lap < opt_rec['pit_laps'][0] - 3 else 'PREPARE_PIT',
                'next_pit': opt_rec['pit_laps'][0] if opt_rec['pit_laps'] else None,
                'confidence': 0.7,
                'reasoning': opt_rec['explanation'][:100] + "...",
                'lap': lap,
                'rl_recommendation': rl_rec,
                'optimizer_recommendation': opt_rec
            }
        
        self.current_strategy = recommendation
        return recommendation
    
    def _get_current_recommendation(self) -> Dict:
        """Get current strategy recommendation."""
        if self.current_strategy:
            return self.current_strategy
        
        return {
            'action': 'CONTINUE',
            'reasoning': 'No update needed.',
            'confidence': 0.5
        }
    
    def handle_race_event(self, event: RaceEvent, event_data: Dict) -> StrategyUpdate:
        """
        Handle significant race event and generate strategy update.
        
        Args:
            event: Type of race event
            event_data: Event-specific data
            
        Returns:
            StrategyUpdate with recommendations
        """
        current_lap = event_data.get('lap', len(self.lap_history))
        
        # Store event
        self.event_log.append({
            'event': event.value,
            'lap': current_lap,
            'data': event_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate strategy update based on event type
        if event == RaceEvent.SAFETY_CAR:
            return self._handle_safety_car(event_data)
        elif event == RaceEvent.WEATHER_CHANGE:
            return self._handle_weather_change(event_data)
        elif event == RaceEvent.OVERTAKE:
            return self._handle_overtake(event_data)
        elif event == RaceEvent.VSC:
            return self._handle_vsc(event_data)
        else:
            return StrategyUpdate(
                trigger_event=event,
                current_lap=current_lap,
                previous_strategy=self.current_strategy or {},
                recommended_strategy=self.current_strategy or {},
                confidence=0.5,
                time_gain_potential=0.0,
                risk_change=0.0,
                explanation=f"Event {event.value} logged. No immediate strategy change required.",
                decision_deadline=current_lap + 3,
                alternatives=[]
            )
    
    def _handle_safety_car(self, event_data: Dict) -> StrategyUpdate:
        """Generate strategy update for safety car deployment."""
        lap = event_data.get('lap', 1)
        current_strategy = self.current_strategy or {}
        
        # Safety car = prime pit opportunity
        # Recalculate with pit now vs later
        
        # Option 1: Pit immediately under SC
        pit_now_strategy = {
            'action': 'PIT_NOW',
            'tire': 'medium',  # Default safe choice
            'reasoning': 'Safety car deployed - optimal pit window',
            'expected_gain': 15.0  # ~15 seconds saved
        }
        
        # Option 2: Stay out (if tires fresh)
        stay_out_strategy = {
            'action': 'STAY_OUT',
            'reasoning': 'Tires still fresh, maintain track position',
            'expected_gain': 0.0
        }
        
        # Decide based on tire age
        current_tire_age = self.lap_history[-1]['tire_age'] if self.lap_history else 0
        
        if current_tire_age > 20:
            recommended = pit_now_strategy
            confidence = 0.9
            time_gain = 15.0
        else:
            recommended = stay_out_strategy
            confidence = 0.7
            time_gain = 0.0
        
        return StrategyUpdate(
            trigger_event=RaceEvent.SAFETY_CAR,
            current_lap=lap,
            previous_strategy=current_strategy,
            recommended_strategy=recommended,
            confidence=confidence,
            time_gain_potential=time_gain,
            risk_change=-0.3 if recommended['action'] == 'PIT_NOW' else 0.0,
            explanation="Safety car creates strategic opportunity. Pit loss time reduced significantly.",
            decision_deadline=lap + 2,  # Must decide quickly
            alternatives=[pit_now_strategy, stay_out_strategy]
        )
    
    def _handle_weather_change(self, event_data: Dict) -> StrategyUpdate:
        """Generate strategy update for weather change."""
        lap = event_data.get('lap', 1)
        new_weather = event_data.get('new_weather', 'dry')
        
        # Weather change requires tire change
        if new_weather in ['light_rain', 'heavy_rain']:
            recommended = {
                'action': 'PIT_FOR_INTERMEDIATES' if new_weather == 'light_rain' else 'PIT_FOR_WETS',
                'urgency': 'HIGH' if new_weather == 'heavy_rain' else 'MEDIUM'
            }
            confidence = 0.95
            explanation = f"Weather changed to {new_weather}. Immediate tire change required."
        else:
            recommended = {
                'action': 'MONITOR',
                'urgency': 'LOW'
            }
            confidence = 0.6
            explanation = "Track drying. Monitor conditions before switching to slicks."
        
        return StrategyUpdate(
            trigger_event=RaceEvent.WEATHER_CHANGE,
            current_lap=lap,
            previous_strategy=self.current_strategy or {},
            recommended_strategy=recommended,
            confidence=confidence,
            time_gain_potential=0.0,  # Weather changes are defensive
            risk_change=0.4 if new_weather == 'heavy_rain' else 0.1,
            explanation=explanation,
            decision_deadline=lap + 1 if recommended.get('urgency') == 'HIGH' else lap + 5,
            alternatives=[]
        )
    
    def _handle_overtake(self, event_data: Dict) -> StrategyUpdate:
        """Generate strategy update after overtake (gained or lost position)."""
        lap = event_data.get('lap', 1)
        position_change = event_data.get('position_change', 0)
        
        if position_change > 0:  # Gained position
            recommended = {
                'action': 'DEFEND_POSITION',
                'tactics': 'CONSERVATIVE_TIRE_USAGE'
            }
            explanation = "Position gained. Switch to defensive mode, protect tires."
            risk_change = -0.2
        else:  # Lost position
            recommended = {
                'action': 'ATTACK',
                'tactics': 'AGGRESSIVE_TIRE_USAGE'
            }
            explanation = "Position lost. Push hard on tires to regain position."
            risk_change = 0.3
        
        return StrategyUpdate(
            trigger_event=RaceEvent.OVERTAKE,
            current_lap=lap,
            previous_strategy=self.current_strategy or {},
            recommended_strategy=recommended,
            confidence=0.75,
            time_gain_potential=abs(position_change) * 2,  # 2s per position
            risk_change=risk_change,
            explanation=explanation,
            decision_deadline=lap + 10,
            alternatives=[]
        )
    
    def _handle_vsc(self, event_data: Dict) -> StrategyUpdate:
        """Handle Virtual Safety Car."""
        lap = event_data.get('lap', 1)
        
        # VSC = partial pit benefit
        recommended = {
            'action': 'EVALUATE_PIT',
            'tire_age_threshold': 22,  # Pit if tires > 22 laps
            'partial_gain': 8.0  # ~8 seconds partial benefit
        }
        
        return StrategyUpdate(
            trigger_event=RaceEvent.VSC,
            current_lap=lap,
            previous_strategy=self.current_strategy or {},
            recommended_strategy=recommended,
            confidence=0.7,
            time_gain_potential=8.0,
            risk_change=-0.1,
            explanation="Virtual Safety Car provides partial pit opportunity.",
            decision_deadline=lap + 3,
            alternatives=[]
        )


class DigitalTwinSimulator:
    """
    Digital Twin concept: Run parallel simulations to evaluate
    multiple future scenarios concurrently.
    """
    
    def __init__(self, circuit: str, total_laps: int, num_workers: int = 4):
        self.circuit = circuit
        self.total_laps = total_laps
        self.num_workers = num_workers
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.scenarios = []
        
    def define_scenarios(self, current_state: Dict) -> List[Dict]:
        """Define scenarios to simulate."""
        lap = current_state.get('lap', 1)
        
        scenarios = [
            {
                'id': 'baseline',
                'name': 'Baseline (No Events)',
                'description': 'Race continues without incidents',
                'probability': 0.40,
                'events': []
            },
            {
                'id': 'sc_late',
                'name': 'Safety Car (Laps 30-40)',
                'description': 'Safety car between laps 30-40',
                'probability': 0.20,
                'events': [{'type': 'safety_car', 'lap': 35, 'duration': 5}]
            },
            {
                'id': 'rain_mid',
                'name': 'Rain (Laps 20-30)',
                'description': 'Rain starts mid-race',
                'probability': 0.15,
                'events': [{'type': 'weather_change', 'lap': 25, 'to': 'light_rain'}]
            },
            {
                'id': 'undercut_threat',
                'name': 'Undercut Threat',
                'description': 'Car behind pits early for undercut',
                'probability': 0.15,
                'events': [{'type': 'opponent_pit', 'lap': lap + 3, 'driver': 'behind'}]
            },
            {
                'id': 'vsc_early',
                'name': 'VSC (Laps 15-25)',
                'description': 'Virtual safety car early in race',
                'probability': 0.10,
                'events': [{'type': 'vsc', 'lap': 20, 'duration': 3}]
            }
        ]
        
        return scenarios
    
    def run_parallel_simulations(self, 
                                scenarios: List[Dict],
                                current_state: Dict,
                                base_strategy: Dict) -> List[DigitalTwinScenario]:
        """
        Run parallel simulations for all scenarios.
        
        Returns:
            List of scenario outcomes
        """
        futures = []
        
        for scenario in scenarios:
            future = self.executor.submit(
                self._simulate_scenario,
                scenario,
                current_state,
                base_strategy
            )
            futures.append((scenario, future))
        
        results = []
        for scenario, future in futures:
            try:
                outcome = future.result(timeout=10)
                results.append(DigitalTwinScenario(
                    scenario_id=scenario['id'],
                    description=scenario['description'],
                    trigger_condition=scenario['name'],
                    probability=scenario['probability'],
                    projected_outcome=outcome,
                    strategy_adjustment=outcome.get('recommended_adjustment', {}),
                    confidence=outcome.get('confidence', 0.5)
                ))
            except Exception as e:
                print(f"Scenario {scenario['id']} failed: {e}")
        
        return results
    
    def _simulate_scenario(self, scenario: Dict, 
                          current_state: Dict, 
                          base_strategy: Dict) -> Dict:
        """Simulate a single scenario."""
        # Initialize simulator
        simulator = MultiCarSimulator(
            self.circuit, 
            self.total_laps, 
            num_cars=5
        )
        simulator.initialize_race(weather=current_state.get('weather', 'dry'))
        
        # Set initial state
        agent_driver = simulator.drivers[0]
        agent_driver.position = current_state.get('position', 5)
        agent_driver.current_tire = current_state.get('tire_compound', 'medium')
        agent_driver.tire_age = current_state.get('tire_age', 10)
        
        # Apply base strategy
        # strategies = {0: base_strategy}
        
        # Simulate with events
        current_lap = current_state.get('lap', 1)
        
        for lap in range(current_lap, self.total_laps + 1):
            # Check for events this lap
            for event in scenario.get('events', []):
                if event['lap'] == lap:
                    self._apply_event(simulator, event, agent_driver)
            
            # Regular simulation
            simulator.simulate_lap()
        
        # Get results
        results = simulator.get_race_results()
        
        # Find our driver
        our_result = next(
            (d for d in results['final_standings'] if d['driver_id'] == 0),
            None
        )
        
        # Generate recommendation
        if our_result['position'] > 3:
            adjustment = {
                'type': 'AGGRESSIVE',
                'pit_earlier': True,
                'push_tires': True
            }
        else:
            adjustment = {
                'type': 'MAINTAIN',
                'defend_position': True
            }
        
        return {
            'final_position': our_result['position'],
            'gap_to_leader': our_result['gap_to_leader'],
            'recommended_adjustment': adjustment,
            'confidence': 0.7 if scenario['id'] == 'baseline' else 0.5
        }
    
    def _apply_event(self, simulator: MultiCarSimulator, 
                    event: Dict, agent_driver):
        """Apply an event to the simulation."""
        if event['type'] == 'safety_car':
            # Safety car slows everyone down
            for driver in simulator.drivers:
                driver.gap_to_leader += 25  # Approximate SC loss
        
        elif event['type'] == 'weather_change':
            # Change weather
            simulator.weather = event.get('to', 'light_rain')
        
        elif event['type'] == 'opponent_pit':
            # Opponent pits
            opponent = simulator.drivers[1]  # Car behind
            simulator.simulate_pit_stop(opponent, 'soft')
    
    def get_contingency_plan(self, 
                            scenario_results: List[DigitalTwinScenario],
                            risk_tolerance: float = 0.5) -> Dict:
        """
        Generate contingency plan based on scenario analysis.
        
        Returns:
            Contingency recommendations
        """
        # Sort by probability-weighted outcome
        weighted_scores = []
        for scenario in scenario_results:
            score = scenario.probability * (
                100 if scenario.projected_outcome.get('final_position', 10) == 1 
                else 50 / scenario.projected_outcome.get('final_position', 10)
            )
            weighted_scores.append((scenario, score))
        
        weighted_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Generate recommendations
        top_scenarios = weighted_scores[:3]
        
        return {
            'most_likely_scenario': top_scenarios[0][0].scenario_id if top_scenarios else 'baseline',
            'expected_position': np.mean([
                s.projected_outcome.get('final_position', 5) 
                for s, _ in top_scenarios
            ]),
            'contingencies': [
                {
                    'if': s.trigger_condition,
                    'then': s.strategy_adjustment,
                    'probability': s.probability
                }
                for s, _ in top_scenarios
            ],
            'risk_assessment': 'HIGH' if risk_tolerance < 0.3 else 'MODERATE' if risk_tolerance < 0.7 else 'LOW'
        }


def run_real_time_adaptation_demo():
    """Demonstrate real-time strategy adaptation."""
    print("Real-Time Strategy Adaptation Demo")
    print("=" * 60)
    
    # Create adapter
    adapter = RealTimeStrategyAdapter('Monza', 53, driver_id=0)
    
    # Simulate race progression
    states = [
        {'lap': 1, 'position': 3, 'gap_to_ahead': 1.5, 'gap_to_behind': 2.0, 
         'tire_age': 1, 'tire_compound': 'soft', 'weather': 'dry'},
        {'lap': 10, 'position': 3, 'gap_to_ahead': 1.8, 'gap_to_behind': 1.5,
         'tire_age': 10, 'tire_compound': 'soft', 'weather': 'dry'},
        {'lap': 18, 'position': 2, 'gap_to_ahead': 0.8, 'gap_to_behind': 3.0,
         'tire_age': 18, 'tire_compound': 'soft', 'weather': 'dry'},  # Undercut opportunity!
        {'lap': 25, 'position': 3, 'gap_to_ahead': 2.5, 'gap_to_behind': 1.2,
         'tire_age': 7, 'tire_compound': 'medium', 'weather': 'dry'},  # After pit
    ]
    
    for state in states:
        rec = adapter.update_race_state(**state)
        print(f"\nLap {state['lap']}: P{state['position']}")
        print(f"  Action: {rec['action']}")
        print(f"  Confidence: {rec.get('confidence', 0):.0%}")
        print(f"  Reasoning: {rec.get('reasoning', 'N/A')[:60]}...")
    
    # Test event handling
    print("\n--- Event Handling ---")
    
    sc_update = adapter.handle_race_event(
        RaceEvent.SAFETY_CAR,
        {'lap': 30, 'duration': 5}
    )
    print("\nSafety Car at Lap 30:")
    print(f"  Recommended: {sc_update.recommended_strategy['action']}")
    print(f"  Deadline: Lap {sc_update.decision_deadline}")
    
    # Test Digital Twin
    print("\n--- Digital Twin Simulation ---")
    twin = DigitalTwinSimulator('Monza', 53)
    
    current_state = {'lap': 20, 'position': 3, 'tire_age': 20, 'weather': 'dry'}
    base_strategy = {'pit_laps': [22, 40], 'tires': ['soft', 'medium', 'hard']}
    
    scenarios = twin.define_scenarios(current_state)
    print(f"Defined {len(scenarios)} scenarios")
    
    # Run parallel sims
    results = twin.run_parallel_simulations(scenarios, current_state, base_strategy)
    print(f"Completed {len(results)} simulations")
    
    for result in results:
        print(f"  {result.scenario_id}: P{result.projected_outcome.get('final_position', 'N/A')} "
              f"(prob: {result.probability:.0%})")
    
    # Get contingency plan
    plan = twin.get_contingency_plan(results)
    print(f"\nContingency Plan: Most likely = {plan['most_likely_scenario']}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    run_real_time_adaptation_demo()
