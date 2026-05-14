"""
Advanced Strategy Optimizer with Monte Carlo simulation and risk analysis.
"""
import numpy as np
from typing import List, Dict
from dataclasses import dataclass

from app.core.config import CIRCUITS, TIRE_COMPOUNDS
from app.services.weather_system import DynamicWeatherSystem, WeatherState


@dataclass
class StrategySimulation:
    """Result of a single strategy simulation."""
    strategy_type: str
    pit_laps: List[int]
    tires: List[str]
    total_time: float
    final_position: int
    lap_times: List[float]
    pit_stops: int
    weather_impacts: List[float]


@dataclass
class StrategyResult:
    """Aggregated strategy results from Monte Carlo simulations."""
    strategy_type: str
    pit_laps: List[int]
    tires: List[str]
    
    # Performance metrics
    mean_time: float
    median_time: float
    std_time: float
    min_time: float
    max_time: float
    
    # Risk metrics
    time_variance: float
    risk_score: float  # 0-1 scale
    success_probability: float  # Probability of finishing top 3
    
    # Comparison
    expected_gap_to_best: float
    
    # All simulations for analysis
    all_simulations: List[StrategySimulation]


class AdvancedStrategyOptimizer:
    """
    Professional-grade strategy optimizer using Monte Carlo simulation.
    Evaluates strategies based on expected performance AND risk.
    """
    
    def __init__(self, 
                 num_monte_carlo_runs: int = 100,
                 risk_aversion: float = 0.3):
        """
        Initialize optimizer.
        
        Args:
            num_monte_carlo_runs: Number of simulations per strategy
            risk_aversion: 0-1, higher = more conservative (avoid risky strategies)
        """
        self.num_runs = num_monte_carlo_runs
        self.risk_aversion = risk_aversion
        
        # Tire strategy templates
        self.strategy_templates = {
            '1_stop': [
                {'pit_laps': [0.40], 'tires': ['soft', 'hard']},
                {'pit_laps': [0.45], 'tires': ['soft', 'medium']},
                {'pit_laps': [0.50], 'tires': ['medium', 'hard']},
            ],
            '2_stop': [
                {'pit_laps': [0.25, 0.55], 'tires': ['soft', 'medium', 'hard']},
                {'pit_laps': [0.22, 0.50], 'tires': ['soft', 'soft', 'medium']},
                {'pit_laps': [0.30, 0.60], 'tires': ['soft', 'hard', 'soft']},
                {'pit_laps': [0.28, 0.52], 'tires': ['medium', 'soft', 'hard']},
            ],
            '3_stop': [
                {'pit_laps': [0.18, 0.40, 0.65], 'tires': ['soft', 'medium', 'soft', 'hard']},
                {'pit_laps': [0.15, 0.38, 0.62], 'tires': ['soft', 'soft', 'medium', 'soft']},
                {'pit_laps': [0.20, 0.45, 0.70], 'tires': ['medium', 'soft', 'medium', 'hard']},
            ]
        }
        
    def generate_pit_windows(self, 
                           total_laps: int, 
                           strategy_type: str) -> List[Dict]:
        """Generate pit window configurations for a strategy type."""
        templates = self.strategy_templates.get(strategy_type, [])
        
        configurations = []
        for template in templates:
            pit_laps = [int(p * total_laps) for p in template['pit_laps']]
            configurations.append({
                'pit_laps': pit_laps,
                'tires': template['tires']
            })
        
        return configurations
    
    def simulate_single_race(self,
                            circuit: str,
                            total_laps: int,
                            pit_laps: List[int],
                            tires: List[str],
                            weather_system: DynamicWeatherSystem,
                            add_randomness: bool = True) -> StrategySimulation:
        """
        Simulate a single race execution with stochastic elements.
        
        Args:
            circuit: Circuit name
            total_laps: Total race distance
            pit_laps: List of pit stop lap numbers
            tires: Tire compound for each stint
            weather_system: Weather simulation
            add_randomness: Whether to add variability
            
        Returns:
            StrategySimulation with race results
        """
        circuit_config = CIRCUITS[circuit]
        base_time = circuit_config['base_lap_time']
        pit_loss = circuit_config['pit_loss']
        
        # Get weather timeline
        # weather_snapshots = weather_system.get_race_weather()  # Unused variable removed
        
        lap_times = []
        weather_impacts = []
        current_tire_idx = 0
        total_race_time = 0.0
        
        for lap in range(1, total_laps + 1):
            # Get weather for this lap
            weather = weather_system.get_weather_impact(lap)
            weather_impacts.append(weather['lap_time_multiplier'])
            
            # Determine current tire
            while (current_tire_idx < len(pit_laps) and 
                   lap > pit_laps[current_tire_idx]):
                current_tire_idx += 1
            
            current_tire = tires[min(current_tire_idx, len(tires) - 1)]
            
            # Calculate tire age
            if current_tire_idx == 0:
                tire_age = lap
            else:
                tire_age = lap - pit_laps[current_tire_idx - 1]
            
            # Base lap time
            tire_config = TIRE_COMPOUNDS[current_tire]
            lap_time = base_time + tire_config['base_pace']
            
            # Tire degradation (with randomness)
            deg_rate = tire_config['degradation_rate']
            if add_randomness:
                deg_rate *= np.random.normal(1.0, 0.1)  # 10% variation
            
            degradation = deg_rate * (tire_age ** 1.5)
            lap_time += degradation
            
            # Weather impact
            lap_time *= weather['lap_time_multiplier']
            
            # Fuel effect
            fuel_remaining = 1.0 - (lap / total_laps)
            lap_time += fuel_remaining * 0.08
            
            # Track evolution (track gets faster)
            lap_time -= 0.02 * np.sqrt(lap)
            
            # Random noise (driver errors, traffic, etc.)
            if add_randomness:
                noise = np.random.normal(0, 0.25)
                lap_time += noise
            
            # Safety car effect (random occurrence)
            if add_randomness and np.random.random() < 0.02:  # 2% chance per lap
                lap_time += 25.0  # Slower lap behind SC
            
            lap_times.append(max(lap_time, base_time * 0.85))
            total_race_time += lap_time
            
            # Add pit stop time
            if lap in pit_laps:
                # Reduced pit loss during certain conditions
                actual_pit_loss = pit_loss * np.random.uniform(0.9, 1.1)
                total_race_time += actual_pit_loss
        
        # Simulate final position (based on total time vs theoretical competitors)
        # Add 10-20 random competitors with varying strategies
        competitor_times = []
        for _ in range(15):
            comp_variance = np.random.normal(0, 15)  # Different strategy outcomes
            competitor_times.append(total_race_time + comp_variance)
        
        competitor_times.append(total_race_time)
        competitor_times.sort()
        final_position = competitor_times.index(total_race_time) + 1
        
        return StrategySimulation(
            strategy_type=f"{len(pit_laps)}_stop",
            pit_laps=pit_laps,
            tires=tires,
            total_time=round(total_race_time, 2),
            final_position=final_position,
            lap_times=[round(t, 3) for t in lap_times],
            pit_stops=len(pit_laps),
            weather_impacts=weather_impacts
        )
    
    def monte_carlo_simulation(self,
                               circuit: str,
                               total_laps: int,
                               pit_laps: List[int],
                               tires: List[str],
                               initial_weather: str = 'dry',
                               rain_probability: float = 0.3) -> List[StrategySimulation]:
        """
        Run Monte Carlo simulations for a strategy.
        
        Returns:
            List of StrategySimulation results
        """
        simulations = []
        
        for run in range(self.num_runs):
            # Create fresh weather system for each run
            weather_system = DynamicWeatherSystem(rng_seed=42 + run)
            
            weather_map = {
                'dry': WeatherState.DRY,
                'light_rain': WeatherState.LIGHT_RAIN,
                'heavy_rain': WeatherState.HEAVY_RAIN
            }
            
            weather_system.initialize(
                initial_state=weather_map.get(initial_weather, WeatherState.DRY),
                total_laps=total_laps,
                rain_probability=rain_probability if run % 3 == 0 else 0.0  # Variable rain
            )
            
            sim = self.simulate_single_race(
                circuit, total_laps, pit_laps, tires, weather_system
            )
            simulations.append(sim)
        
        return simulations
    
    def evaluate_strategy(self,
                         simulations: List[StrategySimulation],
                         best_possible_time: float = None) -> StrategyResult:
        """
        Evaluate strategy performance from Monte Carlo results.
        
        Args:
            simulations: List of simulation results
            best_possible_time: Reference best time for gap calculation
            
        Returns:
            StrategyResult with aggregated metrics
        """
        times = [s.total_time for s in simulations]
        positions = [s.final_position for s in simulations]
        
        mean_time = np.mean(times)
        median_time = np.median(times)
        std_time = np.std(times)
        
        # Risk score (coefficient of variation + position variance)
        cv = std_time / mean_time if mean_time > 0 else 0
        position_variance = np.var(positions) / 100  # Normalize
        risk_score = min(1.0, (cv * 0.7 + position_variance * 0.3) * 2)
        
        # Success probability (finish top 3)
        success_probability = sum(1 for p in positions if p <= 3) / len(positions)
        
        # Gap to best
        if best_possible_time:
            expected_gap = mean_time - best_possible_time
        else:
            expected_gap = 0.0
        
        # Reference simulation for details
        ref_sim = simulations[0]
        
        return StrategyResult(
            strategy_type=ref_sim.strategy_type,
            pit_laps=ref_sim.pit_laps,
            tires=ref_sim.tires,
            mean_time=round(mean_time, 2),
            median_time=round(median_time, 2),
            std_time=round(std_time, 2),
            min_time=round(min(times), 2),
            max_time=round(max(times), 2),
            time_variance=round(std_time ** 2, 2),
            risk_score=round(risk_score, 3),
            success_probability=round(success_probability, 3),
            expected_gap_to_best=round(expected_gap, 2),
            all_simulations=simulations
        )
    
    def optimize(self,
                circuit: str,
                total_laps: int,
                strategy_type: str = 'auto',
                initial_weather: str = 'dry',
                rain_probability: float = 0.3,
                parallel: bool = True) -> Dict:
        """
        Optimize strategy using Monte Carlo simulation.
        
        Args:
            circuit: Circuit name
            total_laps: Total race distance
            strategy_type: 'auto', '1_stop', '2_stop', '3_stop'
            initial_weather: Starting weather condition
            rain_probability: Probability of rain
            parallel: Use parallel processing
            
        Returns:
            Optimization results with best strategy and comparison
        """
        # Determine strategies to test
        if strategy_type == 'auto':
            strategies_to_test = ['1_stop', '2_stop', '3_stop']
        else:
            strategies_to_test = [strategy_type]
        
        all_results = []
        
        for strat_type in strategies_to_test:
            configs = self.generate_pit_windows(total_laps, strat_type)
            
            for config in configs:
                print(f"  Simulating {strat_type}: pits at {config['pit_laps']}")
                
                # Run Monte Carlo simulations
                simulations = self.monte_carlo_simulation(
                    circuit, total_laps,
                    config['pit_laps'], config['tires'],
                    initial_weather, rain_probability
                )
                
                # Evaluate
                result = self.evaluate_strategy(simulations)
                all_results.append(result)
        
        if not all_results:
            raise ValueError("No valid strategies generated")
        
        # Find best strategy considering risk
        # Utility = -mean_time - risk_aversion * risk_score * 100
        def utility(result: StrategyResult) -> float:
            return -result.mean_time - self.risk_aversion * result.risk_score * 100
        
        best_result = max(all_results, key=utility)
        
        # Generate explanation
        explanation = self._generate_explanation(
            best_result, all_results, initial_weather, rain_probability
        )
        
        # Format comparison
        comparison = {}
        for result in all_results:
            key = f"{result.strategy_type}_{'_'.join(map(str, result.pit_laps))}"
            comparison[key] = {
                'mean_time': result.mean_time,
                'risk_score': result.risk_score,
                'success_probability': result.success_probability,
                'pit_laps': result.pit_laps,
                'tires': result.tires
            }
        
        return {
            'best_strategy': best_result.strategy_type,
            'pit_laps': best_result.pit_laps,
            'tires': best_result.tires,
            'expected_time': best_result.mean_time,
            'time_variance': best_result.time_variance,
            'risk_score': best_result.risk_score,
            'success_probability': best_result.success_probability,
            'explanation': explanation,
            'strategy_comparison': comparison,
            'monte_carlo_runs': self.num_runs,
            'risk_aversion': self.risk_aversion
        }
    
    def _generate_explanation(self,
                             best: StrategyResult,
                             all_results: List[StrategyResult],
                             initial_weather: str,
                             rain_prob: float) -> str:
        """Generate detailed explanation for strategy choice."""
        parts = []
        
        # Base strategy description
        parts.append(
            f"{best.strategy_type.replace('_', '-')} strategy selected with "
            f"pit stops at laps {', '.join(map(str, best.pit_laps))} "
            f"using {' → '.join(best.tires)} tire sequence."
        )
        
        # Performance explanation
        best_time = min(r.mean_time for r in all_results)
        if best.mean_time <= best_time + 5:
            parts.append(
                f"Expected race time of {best.mean_time:.1f}s is within "
                f"{(best.mean_time - best_time):.1f}s of theoretical optimum."
            )
        
        # Risk explanation
        if best.risk_score < 0.3:
            parts.append(
                f"Low risk strategy (score: {best.risk_score:.2f}) provides "
                f"consistency across varying conditions."
            )
        elif best.risk_score > 0.6:
            parts.append(
                f"Higher risk strategy (score: {best.risk_score:.2f}) offers "
                f"potential upside but with greater variance."
            )
        
        # Weather considerations
        if rain_prob > 0.3:
            parts.append(
                f"With {rain_prob*100:.0f}% rain probability, tire flexibility "
                f"in the {best.tires[-1]} final stint is prioritized."
            )
        
        # Success probability
        if best.success_probability > 0.5:
            parts.append(
                f"Monte Carlo simulation shows {best.success_probability*100:.0f}% "
                f"probability of podium finish."
            )
        
        return " ".join(parts)


def quick_optimize(circuit: str,
                   total_laps: int,
                   rain_probability: float = 0.2,
                   num_simulations: int = 50) -> Dict:
    """
    Quick optimization with fewer simulations for faster results.
    
    Example:
        result = quick_optimize('Monza', 53, rain_probability=0.3)
    """
    optimizer = AdvancedStrategyOptimizer(
        num_monte_carlo_runs=num_simulations,
        risk_aversion=0.3
    )
    
    return optimizer.optimize(
        circuit=circuit,
        total_laps=total_laps,
        strategy_type='auto',
        rain_probability=rain_probability
    )


if __name__ == "__main__":
    # Test advanced optimizer
    print("Testing Advanced Strategy Optimizer")
    print("=" * 70)
    
    # Test 1: Dry race at Monza
    print("\n1. Monza - Dry Conditions")
    print("-" * 40)
    result1 = quick_optimize('Monza', 53, rain_probability=0.0, num_simulations=30)
    
    print(f"Best Strategy: {result1['best_strategy']}")
    print(f"Pit Laps: {result1['pit_laps']}")
    print(f"Tires: {result1['tires']}")
    print(f"Expected Time: {result1['expected_time']:.1f}s")
    print(f"Risk Score: {result1['risk_score']:.2f}")
    print(f"Success Probability: {result1['success_probability']*100:.0f}%")
    print(f"\nExplanation: {result1['explanation']}")
    
    # Test 2: Rain probability at Silverstone
    print("\n2. Silverstone - Rain Probability 40%")
    print("-" * 40)
    result2 = quick_optimize('Silverstone', 52, rain_probability=0.4, num_simulations=30)
    
    print(f"Best Strategy: {result2['best_strategy']}")
    print(f"Pit Laps: {result2['pit_laps']}")
    print(f"Tires: {result2['tires']}")
    print(f"Expected Time: {result2['expected_time']:.1f}s")
    print(f"Risk Score: {result2['risk_score']:.2f}")
    
    # Strategy comparison
    print("\n3. Strategy Comparison Summary")
    print("-" * 40)
    for name, data in result2['strategy_comparison'].items():
        print(f"  {name}:")
        print(f"    Time: {data['mean_time']:.1f}s, Risk: {data['risk_score']:.2f}, "
              f"Success: {data['success_probability']*100:.0f}%")
    
    print("\n" + "=" * 70)
    print("Strategy optimizer tests completed!")
