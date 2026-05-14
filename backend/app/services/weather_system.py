"""
Dynamic Weather System for F1 Race Simulation.
Models weather transitions and their impact on racing conditions.
"""
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class WeatherState(Enum):
    DRY = "dry"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"


class TireType(Enum):
    SLICK = "slick"  # Dry tires
    INTER = "intermediate"  # Light rain
    WET = "wet"  # Heavy rain


@dataclass
class WeatherSnapshot:
    """Weather conditions at a specific point in time."""
    lap: int
    state: WeatherState
    track_temp: float
    air_temp: float
    humidity: float
    precipitation_chance: float  # 0-1
    wind_speed: float
    visibility: float  # km


class DynamicWeatherSystem:
    """
    Dynamic weather simulation with realistic transitions.
    """
    
    # Weather transition probabilities (Markov chain)
    # Current state -> [Stay, Improve, Worsen]
    TRANSITION_MATRIX = {
        WeatherState.DRY: [0.95, 0.0, 0.05],  # Usually stays dry
        WeatherState.LIGHT_RAIN: [0.70, 0.20, 0.10],  # Can improve or worsen
        WeatherState.HEAVY_RAIN: [0.60, 0.35, 0.05]  # Usually improves
    }
    
    # Impact on lap times (multipliers)
    LAP_TIME_IMPACT = {
        WeatherState.DRY: 1.0,
        WeatherState.LIGHT_RAIN: 1.08,
        WeatherState.HEAVY_RAIN: 1.20
    }
    
    # Impact on tire degradation (multipliers)
    DEGRADATION_IMPACT = {
        WeatherState.DRY: 1.0,
        WeatherState.LIGHT_RAIN: 0.85,
        WeatherState.HEAVY_RAIN: 0.70
    }
    
    # Grip levels (0-1 scale)
    GRIP_LEVELS = {
        WeatherState.DRY: 1.0,
        WeatherState.LIGHT_RAIN: 0.75,
        WeatherState.HEAVY_RAIN: 0.55
    }
    
    # Temperature ranges by weather
    TEMP_RANGES = {
        WeatherState.DRY: (30, 55),
        WeatherState.LIGHT_RAIN: (20, 35),
        WeatherState.HEAVY_RAIN: (15, 28)
    }
    
    def __init__(self, rng_seed: int = 42):
        self.rng = np.random.RandomState(rng_seed)
        self.history: List[WeatherSnapshot] = []
        self.current_state: Optional[WeatherState] = None
        self.lap_count = 0
        
    def initialize(self, 
                   initial_state: WeatherState = WeatherState.DRY,
                   total_laps: int = 53,
                   rain_probability: float = 0.2):
        """
        Initialize weather system.
        
        Args:
            initial_state: Starting weather condition
            total_laps: Total race laps
            rain_probability: Probability of rain at some point
        """
        self.total_laps = total_laps
        self.rain_probability = rain_probability
        self.current_state = initial_state
        
        # If rain is expected, override initial state
        if self.rng.random() < rain_probability and initial_state == WeatherState.DRY:
            # Start dry, rain will come later
            self.rain_start_lap = self.rng.randint(int(total_laps * 0.2), int(total_laps * 0.7))
        else:
            self.rain_start_lap = None
        
        self.history = []
        
    def get_initial_weather(self) -> WeatherSnapshot:
        """Get starting weather conditions."""
        temp_range = self.TEMP_RANGES[self.current_state]
        track_temp = self.rng.uniform(*temp_range)
        air_temp = track_temp - self.rng.uniform(5, 15)
        
        return WeatherSnapshot(
            lap=0,
            state=self.current_state,
            track_temp=round(track_temp, 1),
            air_temp=round(air_temp, 1),
            humidity=round(self.rng.uniform(0.3, 0.9), 2),
            precipitation_chance=0.1 if self.current_state == WeatherState.DRY else 0.8,
            wind_speed=round(self.rng.exponential(8), 1),
            visibility=10.0 if self.current_state == WeatherState.DRY else 5.0
        )
    
    def evolve_weather(self, current_lap: int) -> WeatherSnapshot:
        """
        Evolve weather to next state based on transition probabilities.
        
        Returns:
            WeatherSnapshot for the current lap
        """
        # Check if rain should start
        if (self.rain_start_lap and 
            current_lap >= self.rain_start_lap and 
            self.current_state == WeatherState.DRY):
            # Start raining
            if self.rng.random() < 0.7:
                self.current_state = WeatherState.LIGHT_RAIN
            else:
                self.current_state = WeatherState.HEAVY_RAIN
        else:
            # Normal Markov transition
            probs = self.TRANSITION_MATRIX[self.current_state]
            transition = self.rng.choice(['stay', 'improve', 'worsen'], p=probs)
            
            if transition == 'improve':
                if self.current_state == WeatherState.HEAVY_RAIN:
                    self.current_state = WeatherState.LIGHT_RAIN
                elif self.current_state == WeatherState.LIGHT_RAIN:
                    self.current_state = WeatherState.DRY
            elif transition == 'worsen':
                if self.current_state == WeatherState.DRY:
                    self.current_state = WeatherState.LIGHT_RAIN
                elif self.current_state == WeatherState.LIGHT_RAIN:
                    self.current_state = WeatherState.HEAVY_RAIN
        
        # Update temperatures based on weather
        temp_range = self.TEMP_RANGES[self.current_state]
        
        if self.history:
            prev_temp = self.history[-1].track_temp
            # Gradual temperature change
            target_temp = self.rng.uniform(*temp_range)
            track_temp = prev_temp + (target_temp - prev_temp) * 0.1
        else:
            track_temp = self.rng.uniform(*temp_range)
        
        air_temp = track_temp - self.rng.uniform(5, 15)
        
        # Update other parameters
        if self.current_state == WeatherState.DRY:
            humidity = max(0.2, self.rng.uniform(0.3, 0.6))
            precip_chance = 0.05
            visibility = 10.0
        elif self.current_state == WeatherState.LIGHT_RAIN:
            humidity = self.rng.uniform(0.6, 0.85)
            precip_chance = 0.6
            visibility = self.rng.uniform(3.0, 7.0)
        else:  # Heavy rain
            humidity = self.rng.uniform(0.85, 1.0)
            precip_chance = 0.95
            visibility = self.rng.uniform(1.0, 4.0)
        
        snapshot = WeatherSnapshot(
            lap=current_lap,
            state=self.current_state,
            track_temp=round(track_temp, 1),
            air_temp=round(air_temp, 1),
            humidity=round(humidity, 2),
            precipitation_chance=round(precip_chance, 2),
            wind_speed=round(self.rng.exponential(10) + (5 if self.current_state != WeatherState.DRY else 0), 1),
            visibility=round(visibility, 1)
        )
        
        self.history.append(snapshot)
        return snapshot
    
    def get_race_weather(self) -> List[WeatherSnapshot]:
        """Generate complete race weather timeline."""
        self.history = []
        
        # Initial conditions
        initial = self.get_initial_weather()
        self.history.append(initial)
        
        # Evolve through race
        for lap in range(1, self.total_laps + 1):
            self.evolve_weather(lap)
        
        return self.history
    
    def get_weather_impact(self, lap: int) -> Dict:
        """Get weather impact metrics for a specific lap."""
        snapshot = next((h for h in self.history if h.lap == lap), None)
        if not snapshot:
            # Return dry defaults
            return {
                'lap_time_multiplier': 1.0,
                'degradation_multiplier': 1.0,
                'grip_level': 1.0,
                'recommended_tire': TireType.SLICK
            }
        
        state = snapshot.state
        
        # Tire recommendation
        if state == WeatherState.DRY:
            recommended_tire = TireType.SLICK
        elif state == WeatherState.LIGHT_RAIN:
            recommended_tire = TireType.INTER
        else:
            recommended_tire = TireType.WET
        
        return {
            'lap_time_multiplier': self.LAP_TIME_IMPACT[state],
            'degradation_multiplier': self.DEGRADATION_IMPACT[state],
            'grip_level': self.GRIP_LEVELS[state],
            'recommended_tire': recommended_tire,
            'track_temp': snapshot.track_temp,
            'air_temp': snapshot.air_temp,
            'humidity': snapshot.humidity,
            'visibility': snapshot.visibility
        }
    
    def recommend_pit_strategy(self, current_lap: int, 
                               current_tire: TireType) -> Optional[TireType]:
        """
        Recommend tire change based on current and upcoming weather.
        
        Returns:
            Recommended tire type or None if no change needed
        """
        # Look ahead 5-10 laps
        future_laps = range(current_lap, min(current_lap + 10, self.total_laps + 1))
        
        weather_states = []
        for lap in future_laps:
            snapshot = next((h for h in self.history if h.lap == lap), None)
            if snapshot:
                weather_states.append(snapshot.state)
        
        if not weather_states:
            return None
        
        # Check if weather is changing
        dominant_weather = max(set(weather_states), key=weather_states.count)
        
        if dominant_weather == WeatherState.DRY and current_tire != TireType.SLICK:
            return TireType.SLICK
        elif dominant_weather == WeatherState.HEAVY_RAIN and current_tire != TireType.WET:
            return TireType.WET
        elif dominant_weather == WeatherState.LIGHT_RAIN and current_tire == TireType.SLICK:
            return TireType.INTER
        
        return None
    
    def get_summary(self) -> Dict:
        """Get weather summary for the race."""
        if not self.history:
            return {}
        
        states = [h.state for h in self.history]
        
        return {
            'initial_state': states[0].value,
            'final_state': states[-1].value,
            'state_changes': sum(1 for i in range(1, len(states)) if states[i] != states[i-1]),
            'dry_laps': sum(1 for s in states if s == WeatherState.DRY),
            'light_rain_laps': sum(1 for s in states if s == WeatherState.LIGHT_RAIN),
            'heavy_rain_laps': sum(1 for s in states if s == WeatherState.HEAVY_RAIN),
            'min_temp': min(h.track_temp for h in self.history),
            'max_temp': max(h.track_temp for h in self.history),
            'avg_humidity': np.mean([h.humidity for h in self.history])
        }


class TireStrategyAdvisor:
    """
    Advises on optimal tire strategy given weather conditions.
    """
    
    def __init__(self, weather_system: DynamicWeatherSystem):
        self.weather = weather_system
    
    def optimize_tire_strategy(self, 
                              total_laps: int,
                              pit_loss_time: float = 22.0) -> Dict:
        """
        Optimize tire strategy for changing weather conditions.
        
        Args:
            total_laps: Total race distance
            pit_loss_time: Time lost per pit stop
            
        Returns:
            Optimal pit strategy
        """
        # Get weather timeline
        weather_snapshots = self.weather.get_race_weather()
        
        # Group consecutive laps by weather
        weather_segments = []
        current_segment = {'start': 0, 'weather': weather_snapshots[0].state}
        
        for i, snapshot in enumerate(weather_snapshots[1:], 1):
            if snapshot.state != current_segment['weather']:
                current_segment['end'] = i
                weather_segments.append(current_segment)
                current_segment = {'start': i, 'weather': snapshot.state}
        
        current_segment['end'] = len(weather_snapshots)
        weather_segments.append(current_segment)
        
        # Generate tire strategy based on segments
        pit_laps = []
        tires = []
        
        for i, segment in enumerate(weather_segments):
            # Determine tire for this segment
            if segment['weather'] == WeatherState.DRY:
                if i == 0:
                    tires.append('soft')  # Start on softs
                else:
                    # Check segment length
                    length = segment['end'] - segment['start']
                    if length > 30:
                        tires.append('hard')
                    elif length > 20:
                        tires.append('medium')
                    else:
                        tires.append('soft')
            elif segment['weather'] == WeatherState.LIGHT_RAIN:
                tires.append('intermediate' if i > 0 else 'soft')
            else:  # Heavy rain
                tires.append('wet' if i > 0 else 'intermediate')
            
            # Pit at start of segment (except first)
            if i > 0:
                pit_laps.append(segment['start'])
        
        return {
            'pit_laps': pit_laps,
            'tires': tires,
            'weather_segments': len(weather_segments),
            'estimated_pit_stops': len(pit_laps)
        }


def simulate_weather_scenario(circuit: str, 
                                total_laps: int,
                                initial_weather: str = "dry",
                                rain_probability: float = 0.3) -> Dict:
    """
    Simulate a complete race with dynamic weather.
    
    Example:
        results = simulate_weather_scenario('Monza', 53, 'dry', 0.4)
    """
    weather_system = DynamicWeatherSystem()
    
    weather_map = {
        'dry': WeatherState.DRY,
        'light_rain': WeatherState.LIGHT_RAIN,
        'heavy_rain': WeatherState.HEAVY_RAIN
    }
    
    weather_system.initialize(
        initial_state=weather_map.get(initial_weather, WeatherState.DRY),
        total_laps=total_laps,
        rain_probability=rain_probability
    )
    
    # Generate race weather
    race_weather = weather_system.get_race_weather()
    
    # Get strategy advice
    advisor = TireStrategyAdvisor(weather_system)
    strategy = advisor.optimize_tire_strategy(total_laps)
    
    return {
        'weather_timeline': [
            {
                'lap': h.lap,
                'state': h.state.value,
                'track_temp': h.track_temp,
                'humidity': h.humidity,
                'visibility': h.visibility
            }
            for h in race_weather
        ],
        'summary': weather_system.get_summary(),
        'recommended_strategy': strategy
    }


if __name__ == "__main__":
    # Test weather system
    print("Testing Dynamic Weather System")
    print("=" * 60)
    
    # Scenario 1: Dry race
    print("\n1. Dry Race (Monza)")
    dry_results = simulate_weather_scenario('Monza', 53, 'dry', 0.0)
    print(f"   State changes: {dry_results['summary']['state_changes']}")
    print(f"   Dry laps: {dry_results['summary']['dry_laps']}")
    
    # Scenario 2: Rain during race
    print("\n2. Variable Weather (Silverstone)")
    rain_results = simulate_weather_scenario('Silverstone', 52, 'dry', 0.5)
    summary = rain_results['summary']
    print(f"   Initial: {summary['initial_state']}")
    print(f"   Final: {summary['final_state']}")
    print(f"   State changes: {summary['state_changes']}")
    print(f"   Dry: {summary['dry_laps']}, Light rain: {summary['light_rain_laps']}, Heavy: {summary['heavy_rain_laps']}")
    print(f"   Temperature range: {summary['min_temp']:.1f}°C - {summary['max_temp']:.1f}°C")
    
    print("\n   Recommended strategy:")
    print(f"   Pit laps: {rain_results['recommended_strategy']['pit_laps']}")
    print(f"   Tires: {rain_results['recommended_strategy']['tires']}")
    
    # Scenario 3: Wet start
    print("\n3. Wet Start (Spa)")
    wet_results = simulate_weather_scenario('Spa', 44, 'heavy_rain', 0.0)
    print(f"   State changes: {wet_results['summary']['state_changes']}")
    print(f"   Wet laps: {wet_results['summary']['heavy_rain_laps']}")
    
    print("\n" + "=" * 60)
    print("Weather system tests completed!")
