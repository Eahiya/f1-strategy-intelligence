"""Strategy Optimizer - Layer 3: Determines best pit stop strategy."""
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

from app.core.config import CIRCUITS, TIRE_COMPOUNDS
from app.models.lap_time_predictor import LapTimePredictor
from app.models.tire_degradation import TireDegradationModel


@dataclass
class StrategyResult:
    """Result of a strategy simulation."""
    strategy_type: str  # "1_stop", "2_stop", "3_stop"
    pit_laps: List[int]
    total_time: float
    lap_times: List[float]
    tire_degradation: List[float]
    tires_used: List[str]
    explanation: str


class StrategyOptimizer:
    """
    Layer 3: Strategy Optimizer
    
    Simulates multiple strategies (1-stop, 2-stop, 3-stop) and
    selects the one with minimum total race time.
    """
    
    def __init__(self, lap_time_model: LapTimePredictor = None,
                 degradation_model: TireDegradationModel = None):
        self.lap_time_model = lap_time_model or LapTimePredictor()
        self.degradation_model = degradation_model or TireDegradationModel()
        
        # Available tire strategies
        self.tire_options = {
            "1_stop": [
                ("soft", "hard"),
                ("medium", "hard"),
                ("soft", "medium"),
            ],
            "2_stop": [
                ("soft", "medium", "soft"),
                ("soft", "hard", "soft"),
                ("medium", "hard", "medium"),
                ("soft", "medium", "hard"),
            ],
            "3_stop": [
                ("soft", "soft", "medium", "soft"),
                ("soft", "medium", "soft", "medium"),
            ]
        }
    
    def generate_pit_windows(self, total_laps: int, num_stops: int) -> List[List[int]]:
        """
        Generate possible pit lap combinations for a given number of stops.
        
        Args:
            total_laps: Total race laps
            num_stops: Number of pit stops
            
        Returns:
            List of pit lap combinations
        """
        pit_windows = []
        
        if num_stops == 1:
            # Single stop: between 25% and 65% of race
            min_pit = int(total_laps * 0.25)
            max_pit = int(total_laps * 0.65)
            for pit in range(min_pit, max_pit + 1, 3):
                pit_windows.append([pit])
                
        elif num_stops == 2:
            # Two stops: first at 20-35%, second at 55-70%
            first_min = int(total_laps * 0.20)
            first_max = int(total_laps * 0.35)
            second_min = int(total_laps * 0.55)
            second_max = int(total_laps * 0.70)
            
            for first in range(first_min, first_max + 1, 3):
                for second in range(max(first + 15, second_min), second_max + 1, 3):
                    pit_windows.append([first, second])
                    
        elif num_stops == 3:
            # Three stops: distribute evenly
            for first in range(10, int(total_laps * 0.25), 4):
                for second in range(first + 12, int(total_laps * 0.5), 4):
                    for third in range(second + 12, int(total_laps * 0.75), 4):
                        if third < total_laps - 8:
                            pit_windows.append([first, second, third])
        
        return pit_windows
    
    def simulate_strategy(self, circuit: str, total_laps: int,
                         pit_laps: List[int], tire_strategy: Tuple[str],
                         weather_factor: float = 1.0,
                         safety_car_laps: List[int] = None) -> StrategyResult:
        """
        Simulate a complete race with given pit strategy.
        
        Args:
            circuit: Circuit name
            total_laps: Total race laps
            pit_laps: List of lap numbers for pit stops
            tire_strategy: Tuple of tire compounds per stint
            weather_factor: Multiplier for conditions (1.0 = dry)
            safety_car_laps: Laps with safety car (reduced pit loss)
            
        Returns:
            StrategyResult with total time and details
        """
        if safety_car_laps is None:
            safety_car_laps = []
            
        circuit_config = CIRCUITS[circuit]
        base_pit_loss = circuit_config["pit_loss"]
        
        lap_times = []
        tire_degradation = []
        current_tire_idx = 0
        tires_used = []
        
        total_time = 0.0
        
        for lap in range(1, total_laps + 1):
            # Determine current tire
            while current_tire_idx < len(pit_laps) and lap > pit_laps[current_tire_idx]:
                current_tire_idx += 1
            
            current_tire = tire_strategy[min(current_tire_idx, len(tire_strategy) - 1)]
            tires_used.append(current_tire)
            
            # Calculate tire age in current stint
            if current_tire_idx == 0:
                tire_age = lap
            else:
                tire_age = lap - pit_laps[current_tire_idx - 1]
            
            # Predict lap time using simplified formula-based model
            base_time = circuit_config["base_lap_time"]
            tire_pace = TIRE_COMPOUNDS[current_tire]["base_pace"]
            deg_rate = TIRE_COMPOUNDS[current_tire]["degradation_rate"]
            
            # Base lap time
            lap_time = base_time + tire_pace
            
            # Tire degradation (non-linear)
            degradation = deg_rate * (tire_age ** 1.5)
            lap_time += degradation
            
            # Fuel effect (decreases through race)
            fuel_remaining = 1.0 - (lap / total_laps)
            lap_time += fuel_remaining * 0.08
            
            # Weather factor
            lap_time *= weather_factor
            
            # Random variation
            noise = np.random.normal(0, 0.2)
            lap_time += noise
            
            lap_times.append(round(lap_time, 3))
            tire_degradation.append(round(degradation, 3))
            total_time += lap_time
            
            # Add pit stop time
            if lap in pit_laps:
                # Reduced pit loss during safety car
                if lap in safety_car_laps:
                    total_time += base_pit_loss * 0.3  # 70% reduction
                else:
                    total_time += base_pit_loss
        
        # Generate explanation
        explanation = self._generate_explanation(
            circuit, pit_laps, tire_strategy, total_time, tire_degradation
        )
        
        return StrategyResult(
            strategy_type=f"{len(pit_laps)}_stop",
            pit_laps=pit_laps,
            total_time=round(total_time, 2),
            lap_times=lap_times,
            tire_degradation=tire_degradation,
            tires_used=list(dict.fromkeys(tires_used)),  # Unique preserving order
            explanation=explanation
        )
    
    def optimize(self, circuit: str, total_laps: int,
                strategy_type: str = "auto",
                weather: str = "dry",
                safety_car_prob: float = 0.1) -> Dict:
        """
        Find optimal strategy for given circuit and conditions.
        
        Args:
            circuit: Circuit name
            total_laps: Total race laps
            strategy_type: "1_stop", "2_stop", "3_stop", or "auto"
            weather: "dry", "wet", "mixed"
            safety_car_prob: Probability of safety car (0-1)
            
        Returns:
            Dictionary with best strategy and comparison
        """
        # Set weather factor
        weather_factors = {"dry": 1.0, "wet": 1.15, "mixed": 1.08}
        weather_factor = weather_factors.get(weather, 1.0)
        
        # Simulate safety car laps
        safety_car_laps = []
        if np.random.random() < safety_car_prob:
            # Add 3-8 laps of safety car
            sc_start = np.random.randint(5, total_laps - 10)
            sc_duration = np.random.randint(3, 9)
            safety_car_laps = list(range(sc_start, sc_start + sc_duration))
        
        # Determine which strategies to test
        if strategy_type == "auto":
            strategies_to_test = ["1_stop", "2_stop", "3_stop"]
        else:
            strategies_to_test = [strategy_type]
        
        all_results = []
        
        for strategy in strategies_to_test:
            pit_windows = self.generate_pit_windows(total_laps, int(strategy.split("_")[0]))
            tire_options = self.tire_options.get(strategy, [])
            
            for pit_laps in pit_windows:
                for tires in tire_options:
                    if len(tires) != len(pit_laps) + 1:
                        continue
                    
                    result = self.simulate_strategy(
                        circuit, total_laps, pit_laps, tires,
                        weather_factor, safety_car_laps
                    )
                    all_results.append(result)
        
        if not all_results:
            raise ValueError(f"No valid strategies found for {strategy_type}")
        
        # Find best strategy
        best_result = min(all_results, key=lambda x: x.total_time)
        
        # Group results by strategy type for comparison
        comparison = {}
        for strategy in strategies_to_test:
            strategy_results = [r for r in all_results if r.strategy_type == strategy]
            if strategy_results:
                best_for_type = min(strategy_results, key=lambda x: x.total_time)
                comparison[strategy] = {
                    "time": best_for_type.total_time,
                    "pit_laps": best_for_type.pit_laps,
                    "tires": best_for_type.tires_used
                }
        
        return {
            "best_strategy": best_result.strategy_type,
            "pit_laps": best_result.pit_laps,
            "total_time": best_result.total_time,
            "explanation": best_result.explanation,
            "tires_used": best_result.tires_used,
            "lap_times": best_result.lap_times,
            "tire_degradation": best_result.tire_degradation,
            "strategy_comparison": comparison,
            "safety_car_laps": safety_car_laps,
            "weather": weather
        }
    
    def _generate_explanation(self, circuit: str, pit_laps: List[int],
                             tires: Tuple[str], total_time: float,
                             degradation: List[float]) -> str:
        """Generate human-readable explanation for strategy choice."""
        num_stops = len(pit_laps)
        
        # Find where degradation spikes
        max_deg_idx = np.argmax(degradation)
        max_deg_lap = max_deg_idx + 1
        
        explanations = []
        
        # Base explanation
        if num_stops == 1:
            explanations.append(
                f"1-stop strategy with {tires[0]} to {tires[1]} tire change on lap {pit_laps[0]}."
            )
        elif num_stops == 2:
            explanations.append(
                f"2-stop strategy using {', '.join(tires)} with pit stops on laps {pit_laps[0]} and {pit_laps[1]}."
            )
        else:
            explanations.append(
                f"3-stop aggressive strategy with {len(tires)} tire changes."
            )
        
        # Degradation reason
        if max_deg_lap > 15:
            explanations.append(
                f"Tire degradation increased significantly after lap {max_deg_lap}, "
                f"peaking at {max(degradation):.2f}s."
            )
        
        # Tire choice reason
        if "soft" in tires:
            if tires.count("soft") >= 2:
                explanations.append(
                    "Multiple soft tire stints provide qualifying-like pace for key portions of the race."
                )
            else:
                explanations.append(
                    "Soft tire used for maximum pace in opening stint."
                )
        
        if "hard" in tires:
            explanations.append(
                "Hard compound provides durability for long final stint."
            )
        
        # Circuit specific
        circuit_name = circuit
        if circuit in ["Monza", "Spa"]:
            explanations.append(
                f"High-speed {circuit_name} circuit favors fewer stops due to large pit loss."
            )
        elif circuit in ["Monaco", "Hungaroring"]:
            explanations.append(
                f"Tight {circuit_name} street circuit allows more aggressive strategies."
            )
        
        # Overall time summary
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        explanations.append(
            f"Total race time: {minutes}:{seconds:02d} (simulated)."
        )
        
        return " ".join(explanations)


if __name__ == "__main__":
    # Test the optimizer
    optimizer = StrategyOptimizer()
    
    print("Testing Strategy Optimizer...")
    print("\n" + "="*60)
    
    for circuit in ["Monza", "Silverstone", "Monaco"]:
        print(f"\nCircuit: {circuit}")
        print("-" * 40)
        
        result = optimizer.optimize(
            circuit=circuit,
            total_laps=CIRCUITS[circuit]["laps"],
            strategy_type="auto",
            weather="dry",
            safety_car_prob=0.0
        )
        
        print(f"Best Strategy: {result['best_strategy']}")
        print(f"Pit Laps: {result['pit_laps']}")
        print(f"Total Time: {result['total_time']:.2f}s")
        print(f"Tires: {result['tires_used']}")
        print(f"\nExplanation: {result['explanation']}")
        
        print("\nStrategy Comparison:")
        for strat, details in result['strategy_comparison'].items():
            print(f"  {strat}: {details['time']:.2f}s - pits: {details['pit_laps']}")
