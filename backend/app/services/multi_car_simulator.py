"""
Multi-Car Race Simulator with overtaking, dirty air, and track position effects.
"""
import numpy as np
import pandas as pd
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

from app.core.config import CIRCUITS, TIRE_COMPOUNDS
from app.services.driver_manager import driver_manager, format_overtake_message
from app.utils.json_sanitizer import sanitize_for_json


class TrackPosition(Enum):
    CLEAN_AIR = "clean"
    SLIPSTREAM = "slipstream"
    DIRTY_AIR = "dirty"


@dataclass
class Driver:
    """Driver with individual characteristics."""
    driver_id: int
    name: str
    team: str
    skill: float = 0.5  # 0-1
    consistency: float = 0.5
    aggression: float = 0.5
    tire_management: float = 0.5
    
    # Race state
    position: int = 0
    gap_to_leader: float = 0.0
    gap_to_ahead: float = 0.0
    current_tire: str = "soft"
    tire_age: int = 0
    pit_stops: int = 0
    total_race_time: float = 0.0
    

@dataclass
class OvertakingAttempt:
    """Record of an overtaking attempt."""
    lap: int
    attacker: int
    defender: int
    success: bool
    location: str  # e.g., "turn_1", "DRS_zone"
    time_gained: float


class MultiCarSimulator:
    """
    Advanced multi-car race simulator with realistic racing dynamics.
    """
    
    # Constants
    DIRTY_AIR_PENALTY = 0.015  # % slower in dirty air
    SLIPSTREAM_BONUS = 0.008   # % faster when close behind
    DRS_BONUS = 0.015          # % faster in DRS zone
    OVERTAKE_THRESHOLD = 0.3   # seconds needed to overtake
    
    # Track sectors for overtaking (simplified)
    OVERTAKING_ZONES = {
        "Monza": ["DRS_1", "turn_1", "DRS_2", "turn_4"],
        "Silverstone": ["DRS_1", "turn_6", "DRS_2", "turn_15"],
        "Spa": ["DRS_1", "les_combes", "DRS_2", "bus_stop"],
        "Monaco": ["turn_1", "turn_10", "turn_19"],
        "Suzuka": ["turn_1", "turn_11", "turn_16"],
        "Barcelona": ["DRS_1", "turn_1", "DRS_2", "turn_10"]
    }
    
    def __init__(self, circuit: str, total_laps: int, num_cars: int = 10):
        self.circuit = circuit
        self.total_laps = total_laps
        self.num_cars = num_cars
        self.circuit_config = CIRCUITS[circuit]
        
        self.drivers: List[Driver] = []
        self.lap_history: List[Dict] = []
        self.overtakes: List[OvertakingAttempt] = []
        self.current_lap = 0
        
        # Weather conditions
        self.weather = "dry"
        self.track_temp = 40.0
        
    def initialize_race(self, 
                         driver_configs: List[Dict] = None,
                         weather: str = "dry",
                         track_temp: float = 40.0):
        """Initialize race with real F1 drivers."""
        self.weather = weather
        self.track_temp = track_temp
        self.current_lap = 0
        
        # Create drivers using real F1 data if none provided
        if driver_configs is None:
            grid = driver_manager.generate_race_grid(self.num_cars)
            
            for driver_data in grid:
                self.drivers.append(Driver(
                    driver_id=driver_data['id'],
                    name=driver_data['name'],
                    team=driver_data['team'],
                    skill=driver_data['skill'],
                    consistency=driver_data['consistency'] / 100,
                    aggression=driver_data['aggression'] / 100,
                    tire_management=driver_data['tire_management'] / 100,
                    position=driver_data['position'],
                    gap_to_leader=driver_data['gap_to_leader'],
                    current_tire="soft",
                    tire_age=0,
                    total_race_time=driver_data['gap_to_leader']
                ))
            self.num_cars = len(self.drivers)
        else:
            for config in driver_configs:
                driver = Driver(**config)
                if driver.total_race_time == 0.0 and driver.gap_to_leader != 0.0:
                    driver.total_race_time = driver.gap_to_leader
                self.drivers.append(driver)
                self.num_cars = len(self.drivers)
        
        # Sort by position for initial grid
        self.drivers.sort(key=lambda d: d.position)
        for i, driver in enumerate(self.drivers):
            driver.position = i + 1
    
    def calculate_lap_time(self, driver: Driver, position_effect: TrackPosition) -> float:
        """Calculate lap time for a driver with position effects."""
        base_time = self.circuit_config["base_lap_time"]
        
        # Base skill effect (±1 second)
        skill_effect = (0.5 - driver.skill) * 2.0
        
        # Tire effects
        tire_config = TIRE_COMPOUNDS[driver.current_tire]
        tire_pace = tire_config["base_pace"]
        degradation = tire_config["degradation_rate"] * (driver.tire_age ** 1.5)
        
        # Track position effects
        position_multiplier = 1.0
        if position_effect == TrackPosition.DIRTY_AIR:
            position_multiplier += self.DIRTY_AIR_PENALTY
        elif position_effect == TrackPosition.SLIPSTREAM:
            position_multiplier -= self.SLIPSTREAM_BONUS
        
        # Weather effect
        weather_mult = 1.0
        if self.weather == "wet":
            weather_mult = 1.15
        elif self.weather == "mixed":
            weather_mult = 1.08
        
        # Temperature effect
        temp_effect = abs(self.track_temp - 35) * 0.02
        
        # Random variation based on consistency
        noise = np.random.normal(0, 0.3 * (1.5 - driver.consistency))
        
        lap_time = (base_time + skill_effect + tire_pace + degradation + temp_effect) * position_multiplier * weather_mult + noise
        
        return max(lap_time, base_time * 0.9)  # Cap minimum time
    
    def get_track_position(self, driver: Driver) -> TrackPosition:
        """Determine track position effect for driver."""
        # Find car ahead
        ahead = [d for d in self.drivers if d.position == driver.position - 1]
        if not ahead:
            return TrackPosition.CLEAN_AIR
        
        gap = ahead[0].gap_to_ahead if ahead[0].position > 1 else ahead[0].gap_to_leader
        
        # Within 1 second - dirty air
        if gap < 1.0:
            return TrackPosition.DIRTY_AIR
        # Within 2 seconds - slipstream opportunity
        elif gap < 2.0:
            return TrackPosition.SLIPSTREAM
        
        return TrackPosition.CLEAN_AIR
    
    def attempt_overtake(self, attacker: Driver, defender: Driver, lap: int) -> bool:
        """Attempt an overtake."""
        # Only possible if close enough
        gap = defender.gap_to_ahead if defender.position > 1 else defender.gap_to_leader
        
        if gap > self.OVERTAKE_THRESHOLD:
            return False
        
        # Calculate success probability
        skill_diff = attacker.skill - defender.skill
        aggression_bonus = attacker.aggression * 0.2
        tire_bonus = (attacker.tire_management - defender.tire_management) * 0.1
        
        # Base probability 40%, modified by factors
        success_prob = 0.4 + skill_diff + aggression_bonus + tire_bonus
        success_prob = np.clip(success_prob, 0.1, 0.9)
        
        success = np.random.random() < success_prob
        
        # Record the attempt
        zones = self.OVERTAKING_ZONES.get(self.circuit, ["DRS_zone"])
        zone = np.random.choice(zones)
        
        # Get driver codes for commentary
        attacker_driver = driver_manager.get_driver_by_name(attacker.name)
        defender_driver = driver_manager.get_driver_by_name(defender.name)
        attacker_code = attacker_driver.driver_code if attacker_driver else attacker.name[:3].upper()
        defender_code = defender_driver.driver_code if defender_driver else defender.name[:3].upper()
        
        self.overtakes.append(OvertakingAttempt(
            lap=lap,
            attacker=attacker_code,
            defender=defender_code,
            success=success,
            location=zone,
            time_gained=gap
        ))
        
        if success:
            # Swap positions
            attacker_pos = attacker.position
            attacker.position = defender.position
            defender.position = attacker_pos
            
            # Update gaps
            attacker.gap_to_ahead = defender.gap_to_ahead
            defender.gap_to_ahead = 0.0
        
        return success
    
    def simulate_lap(self) -> Dict:
        """Simulate one lap for all cars."""
        self.current_lap += 1
        lap_results = []
        
        # 1. Calculate lap times and add to total race time
        for driver in self.drivers:
            position_effect = self.get_track_position(driver)
            lap_time = self.calculate_lap_time(driver, position_effect)
            
            driver.total_race_time += lap_time
            driver.tire_age += 1
            
            lap_results.append({
                'driver': driver,
                'lap_time': lap_time,
                'position_effect': position_effect
            })
        
        # 2. Sort by total race time to determine new positions
        self.drivers.sort(key=lambda d: d.total_race_time)
        
        # 3. Update gaps and positions
        leader_time = self.drivers[0].total_race_time
        for i, driver in enumerate(self.drivers):
            driver.position = i + 1
            driver.gap_to_leader = driver.total_race_time - leader_time
            if i > 0:
                driver.gap_to_ahead = driver.total_race_time - self.drivers[i-1].total_race_time
            else:
                driver.gap_to_ahead = 0.0
            
            # Find the result for this driver to record position_effect
            result = next(r for r in lap_results if r['driver'] is driver)
            
            # Try overtake if in slipstream/dirty air (using old positions or simplified logic)
            # Actually overtakes are now naturally handled by lap times and sorting,
            # but we can still trigger the overtake event for commentary.
            if i > 0 and result['position_effect'] in [TrackPosition.SLIPSTREAM, TrackPosition.DIRTY_AIR]:
                ahead_driver = self.drivers[i-1]
                self.attempt_overtake(driver, ahead_driver, self.current_lap)
        
        # Record lap history
        for driver in self.drivers:
            result = next(r for r in lap_results if r['driver'] is driver)
            self.lap_history.append({
                'lap': self.current_lap,
                'driver_id': driver.driver_id,
                'position': driver.position,
                'lap_time': round(result['lap_time'], 3),
                'gap_to_leader': round(driver.gap_to_leader, 3),
                'tire_age': driver.tire_age,
                'tire': driver.current_tire,
                'position_effect': result['position_effect'].value
            })
        
        return {'lap': self.current_lap, 'results': lap_results}
    
    def simulate_pit_stop(self, driver: Driver, new_tire: str):
        """Execute pit stop for a driver."""
        # Add pit loss time to total race time
        pit_loss = self.circuit_config["pit_loss"]
        driver.total_race_time += pit_loss
        driver.gap_to_leader += pit_loss
        
        # Reset tire
        driver.current_tire = new_tire
        driver.tire_age = 0
        driver.pit_stops += 1
    
    def simulate_race(self, strategies: Dict[int, Dict] = None) -> Dict:
        """
        Simulate complete race with optional strategies.
        
        Args:
            strategies: Dict mapping driver_id to strategy dict with 'pit_laps' and 'tires'
        """
        if strategies is None:
            strategies = {}
        
        for lap in range(1, self.total_laps + 1):
            # Check for pit stops
            for driver in self.drivers:
                strategy = strategies.get(driver.driver_id, {})
                pit_laps = strategy.get('pit_laps', [])
                tires = strategy.get('tires', [])
                
                if lap in pit_laps:
                    # Find tire for this stint
                    stint_idx = pit_laps.index(lap) + 1
                    if stint_idx < len(tires):
                        self.simulate_pit_stop(driver, tires[stint_idx])
            
            # Simulate the lap
            self.simulate_lap()
        
        return self.get_race_results()
    
    def get_race_results(self) -> Dict:
        """Get final race results."""
        # Sort drivers by position
        final_standings = sorted(self.drivers, key=lambda d: d.position)
        
        return {
            'circuit': self.circuit,
            'total_laps': self.total_laps,
            'weather': self.weather,
            'final_standings': [
                {
                    'position': d.position,
                    'driver_id': d.driver_id,
                    'name': d.name,
                    'team': d.team,
                    'gap_to_leader': round(d.gap_to_leader, 3),
                    'pit_stops': d.pit_stops,
                    'tire': d.current_tire,
                    'tire_age': d.tire_age
                }
                for d in final_standings
            ],
            'overtakes': [
                {
                    'lap': o.lap,
                    'attacker': o.attacker,
                    'defender': o.defender,
                    'success': o.success,
                    'location': o.location
                }
                for o in self.overtakes
            ],
            'total_overtakes': sum(1 for o in self.overtakes if o.success),
            'lap_history': self.lap_history
        }
    
    def get_driver_timeline(self, driver_id: int) -> pd.DataFrame:
        """Get lap-by-lap timeline for a specific driver."""
        records = [h for h in self.lap_history if h['driver_id'] == driver_id]
        return pd.DataFrame(records)


def simulate_multi_car_race(
    circuit: str,
    total_laps: int,
    num_cars: int = 10,
    strategies: Dict = None,
    weather: str = "dry"
) -> Dict:
    """
    Convenience function to run multi-car simulation.
    
    Example:
        strategies = {
            0: {'pit_laps': [18, 36], 'tires': ['soft', 'medium', 'hard']},
            1: {'pit_laps': [25], 'tires': ['soft', 'hard']}
        }
        results = simulate_multi_car_race('Monza', 53, 10, strategies)
    """
    simulator = MultiCarSimulator(circuit, total_laps, num_cars)
    simulator.initialize_race(weather=weather)
    
    return simulator.simulate_race(strategies)


if __name__ == "__main__":
    # Test multi-car simulation
    print("Testing Multi-Car Simulator")
    print("=" * 60)
    
    # Define strategies for top drivers
    strategies = {
        0: {'pit_laps': [18, 36], 'tires': ['soft', 'medium', 'hard']},
        1: {'pit_laps': [25], 'tires': ['soft', 'hard']},
        2: {'pit_laps': [15, 35], 'tires': ['soft', 'medium', 'soft']}
    }
    
    results = simulate_multi_car_race(
        circuit='Monza',
        total_laps=53,
        num_cars=10,
        strategies=strategies,
        weather='dry'
    )
    
    print(f"\nCircuit: {results['circuit']}")
    print(f"Total Overtakes: {results['total_overtakes']}")
    
    print("\nFinal Standings:")
    for driver in results['final_standings'][:5]:
        print(f"  P{driver['position']}: {driver['name']} ({driver['team']}) +{driver['gap_to_leader']:.3f}s")
    
    print("\nOvertaking Log (first 5):")
    for overtake in results['overtakes'][:5]:
        status = "✓" if overtake['success'] else "✗"
        # Generate realistic commentary
        commentary = format_overtake_message(
            overtake['attacker'], 
            overtake['defender'], 
            overtake['location']
        )
        print(f"  Lap {overtake['lap']}: {commentary} {status}")
