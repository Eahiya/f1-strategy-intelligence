"""Race Simulation Engine - simulates lap-by-lap race progression."""
import numpy as np
from typing import List, Dict
from dataclasses import dataclass, field

from app.core.config import CIRCUITS, TIRE_COMPOUNDS


@dataclass
class LapState:
    """State of the car at a given lap."""
    lap_number: int
    lap_time: float
    tire_compound: str
    tire_age: int
    tire_degradation: float
    fuel_load: float
    position: int = 1
    gap_to_leader: float = 0.0


@dataclass
class RaceState:
    """Complete race state."""
    circuit: str
    total_laps: int
    current_lap: int = 0
    total_time: float = 0.0
    pit_laps: List[int] = field(default_factory=list)
    lap_states: List[LapState] = field(default_factory=list)
    current_tire: str = "soft"
    tire_stints: List[Dict] = field(default_factory=list)
    
    # Race events
    safety_car_active: bool = False
    safety_car_laps: List[int] = field(default_factory=list)
    weather: str = "dry"


class RaceSimulator:
    """
    Race Simulation Engine
    
    Simulates a complete F1 race lap by lap, tracking:
    - Tire degradation
    - Fuel consumption
    - Pit stops
    - Lap times
    - Race events (safety car, weather)
    """
    
    def __init__(self, circuit: str, total_laps: int,
                 initial_tire: str = "soft",
                 strategy: Dict = None):
        self.circuit = circuit
        self.total_laps = total_laps
        self.circuit_config = CIRCUITS[circuit]
        self.initial_tire = initial_tire
        self.strategy = strategy or {}
        
        self.race_state = None
    
    def initialize_race(self, weather: str = "dry",
                       safety_car_prob: float = 0.0) -> RaceState:
        """
        Initialize a new race simulation.
        
        Args:
            weather: "dry", "wet", or "mixed"
            safety_car_prob: Probability of safety car events
            
        Returns:
            Initialized RaceState
        """
        # Generate potential safety car laps
        safety_car_laps = []
        if np.random.random() < safety_car_prob:
            num_sc_periods = np.random.randint(1, 3)
            for _ in range(num_sc_periods):
                sc_start = np.random.randint(5, self.total_laps - 15)
                sc_duration = np.random.randint(3, 8)
                safety_car_laps.extend(range(sc_start, sc_start + sc_duration))
        
        self.race_state = RaceState(
            circuit=self.circuit,
            total_laps=self.total_laps,
            current_lap=0,
            current_tire=self.initial_tire,
            safety_car_laps=list(set(safety_car_laps)),
            weather=weather
        )
        
        return self.race_state
    
    def calculate_lap_time(self, lap: int, tire: str, tire_age: int,
                          fuel_load: float, weather_factor: float = 1.0) -> tuple:
        """
        Calculate lap time and tire degradation for a single lap.
        
        Args:
            lap: Lap number
            tire: Tire compound
            tire_age: Laps on current tire
            fuel_load: Current fuel load (0-1)
            weather_factor: Weather impact multiplier
            
        Returns:
            (lap_time, degradation) tuple
        """
        base_time = self.circuit_config["base_lap_time"]
        tire_pace = TIRE_COMPOUNDS[tire]["base_pace"]
        deg_rate = TIRE_COMPOUNDS[tire]["degradation_rate"]
        
        # Base lap time
        lap_time = base_time + tire_pace
        
        # Tire degradation (non-linear with age)
        degradation = deg_rate * (tire_age ** 1.5)
        lap_time += degradation
        
        # Fuel effect (linear decrease)
        lap_time += fuel_load * 0.08 * (1 - lap / self.total_laps)
        
        # Weather factor
        lap_time *= weather_factor
        
        # Random variation (track evolution, small errors)
        noise = np.random.normal(0, 0.15)
        lap_time += noise
        
        return round(lap_time, 3), round(degradation, 3)
    
    def simulate_lap(self) -> LapState:
        """
        Simulate a single lap.
        
        Returns:
            LapState with lap details
        """
        if self.race_state is None:
            raise ValueError("Race not initialized. Call initialize_race() first.")
        
        self.race_state.current_lap += 1
        lap = self.race_state.current_lap
        
        # Check if safety car is active
        sc_active = lap in self.race_state.safety_car_laps
        self.race_state.safety_car_active = sc_active
        
        # Calculate weather factor
        weather_factors = {"dry": 1.0, "wet": 1.15, "mixed": 1.08}
        weather_factor = weather_factors.get(self.race_state.weather, 1.0)
        
        # Calculate tire age
        tire_age = self._get_tire_age(lap)
        
        # Calculate fuel load
        fuel_load = 1.0 - (lap / self.total_laps)
        
        # Calculate lap time
        lap_time, degradation = self.calculate_lap_time(
            lap, self.race_state.current_tire, tire_age,
            fuel_load, weather_factor
        )
        
        # Safety car lap is much slower
        if sc_active:
            lap_time += 25.0  # +25 seconds for SC delta
        
        # Update total time
        self.race_state.total_time += lap_time
        
        # Check for pit stop
        if lap in self.race_state.pit_laps:
            pit_time = self._calculate_pit_time(lap, sc_active)
            self.race_state.total_time += pit_time
            
            # Change tire (simplified - always change compound)
            self._change_tire(lap)
        
        # Create lap state
        lap_state = LapState(
            lap_number=lap,
            lap_time=lap_time,
            tire_compound=self.race_state.current_tire,
            tire_age=tire_age,
            tire_degradation=degradation,
            fuel_load=fuel_load
        )
        
        self.race_state.lap_states.append(lap_state)
        
        return lap_state
    
    def simulate_race(self, pit_laps: List[int] = None,
                     tire_strategy: List[str] = None) -> RaceState:
        """
        Simulate complete race.
        
        Args:
            pit_laps: List of lap numbers for pit stops
            tire_strategy: List of tire compounds per stint
            
        Returns:
            Final RaceState
        """
        if self.race_state is None:
            self.initialize_race()
        
        # Set strategy
        if pit_laps:
            self.race_state.pit_laps = pit_laps
        if tire_strategy:
            self.race_state.tire_stints = tire_strategy
        
        # Simulate each lap
        for _ in range(self.total_laps):
            self.simulate_lap()
        
        return self.race_state
    
    def _get_tire_age(self, current_lap: int) -> int:
        """Calculate laps on current tire."""
        # Find last pit lap
        last_pit = 0
        for pit_lap in self.race_state.pit_laps:
            if pit_lap < current_lap:
                last_pit = pit_lap
            else:
                break
        
        return current_lap - last_pit
    
    def _change_tire(self, lap: int):
        """Change tire compound after pit stop."""
        # Simple logic: cycle through compounds
        compounds = ["soft", "medium", "hard"]
        current_idx = compounds.index(self.race_state.current_tire)
        next_idx = (current_idx + 1) % len(compounds)
        self.race_state.current_tire = compounds[next_idx]
        
        # Record stint
        self.race_state.tire_stints.append({
            "lap": lap,
            "new_tire": self.race_state.current_tire
        })
    
    def _calculate_pit_time(self, lap: int, sc_active: bool) -> float:
        """Calculate pit stop time including entry/exit."""
        base_pit_loss = self.circuit_config["pit_loss"]
        
        # Safety car reduces pit loss significantly
        if sc_active:
            return base_pit_loss * 0.3
        
        # Add small random variation
        variation = np.random.normal(0, 0.5)
        return base_pit_loss + variation
    
    def get_race_summary(self) -> Dict:
        """Generate race summary statistics."""
        if not self.race_state or not self.race_state.lap_states:
            return {}
        
        lap_times = [ls.lap_time for ls in self.race_state.lap_states]
        degradations = [ls.tire_degradation for ls in self.race_state.lap_states]
        
        return {
            "circuit": self.circuit,
            "total_laps": self.total_laps,
            "total_time": round(self.race_state.total_time, 2),
            "pit_laps": self.race_state.pit_laps,
            "avg_lap_time": round(np.mean(lap_times), 2),
            "best_lap": round(min(lap_times), 2),
            "worst_lap": round(max(lap_times), 2),
            "max_degradation": round(max(degradations), 3),
            "safety_car_laps": self.race_state.safety_car_laps,
            "tire_stints": self.race_state.tire_stints
        }
    
    def reset(self):
        """Reset simulator for new race."""
        self.race_state = None


if __name__ == "__main__":
    # Test the simulator
    print("Testing Race Simulator...")
    print("=" * 60)
    
    # Test 1: Simple race
    sim = RaceSimulator("Monza", 53, initial_tire="soft")
    state = sim.initialize_race(weather="dry", safety_car_prob=0.2)
    
    # Simulate with 2-stop strategy
    final_state = sim.simulate_race(
        pit_laps=[18, 36],
        tire_strategy=["soft", "medium", "hard"]
    )
    
    summary = sim.get_race_summary()
    
    print(f"\nCircuit: {summary['circuit']}")
    print(f"Total Laps: {summary['total_laps']}")
    print(f"Total Time: {summary['total_time']:.2f}s")
    print(f"Pit Laps: {summary['pit_laps']}")
    print(f"Average Lap: {summary['avg_lap_time']:.3f}s")
    print(f"Best Lap: {summary['best_lap']:.3f}s")
    print(f"Worst Lap: {summary['worst_lap']:.3f}s")
    print(f"Max Degradation: {summary['max_degradation']:.3f}s")
    print(f"Safety Car Laps: {summary['safety_car_laps']}")
    
    # Test 2: Different circuits
    print("\n" + "=" * 60)
    print("Comparing Circuits:")
    
    for circuit in ["Monza", "Silverstone", "Monaco"]:
        sim = RaceSimulator(circuit, CIRCUITS[circuit]["laps"], initial_tire="soft")
        sim.initialize_race()
        sim.simulate_race(pit_laps=[int(CIRCUITS[circuit]["laps"] * 0.5)])
        summary = sim.get_race_summary()
        
        minutes = int(summary['total_time'] // 60)
        seconds = int(summary['total_time'] % 60)
        print(f"  {circuit}: {minutes}:{seconds:02d} (avg: {summary['avg_lap_time']:.1f}s)")
