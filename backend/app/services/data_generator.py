"""
Advanced F1 Race Data Generator
Generates realistic, high-quality synthetic F1 race data with weather, temperature,
track evolution, and driver variability.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

from app.core.config import CIRCUITS, TIRE_COMPOUNDS


class WeatherCondition(Enum):
    DRY = "dry"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"


@dataclass
class RaceConditions:
    """Race conditions for a session."""
    weather: WeatherCondition
    track_temp: float  # Celsius
    air_temp: float    # Celsius
    humidity: float    # 0-1
    wind_speed: float  # km/h
    

@dataclass
class DriverProfile:
    """Driver characteristics affecting performance."""
    driver_id: int
    consistency: float  # 0-1, higher = less variance
    pace_skill: float   # 0-1, base pace modifier
    tire_management: float  # 0-1, degradation modifier
    overtaking_skill: float  # 0-1


class AdvancedDataGenerator:
    """
    Professional-grade F1 data generator with realistic physics and variability.
    """
    
    # Weather impact multipliers
    WEATHER_IMPACT = {
        WeatherCondition.DRY: {
            'lap_time_multiplier': 1.0,
            'tire_degradation_multiplier': 1.0,
            'grip_level': 1.0
        },
        WeatherCondition.LIGHT_RAIN: {
            'lap_time_multiplier': 1.08,
            'tire_degradation_multiplier': 0.85,
            'grip_level': 0.85
        },
        WeatherCondition.HEAVY_RAIN: {
            'lap_time_multiplier': 1.20,
            'tire_degradation_multiplier': 0.70,
            'grip_level': 0.65
        }
    }
    
    # Track temperature effects
    TEMP_OPTIMAL = 35.0  # Optimal track temp in Celsius
    TEMP_EFFECT = 0.02   # Seconds per degree deviation
    
    def __init__(self, random_seed: int = 42):
        self.rng = np.random.RandomState(random_seed)
        self.driver_profiles = self._generate_driver_profiles(20)
        
    def _generate_driver_profiles(self, num_drivers: int) -> List[DriverProfile]:
        """Generate diverse driver profiles."""
        profiles = []
        for i in range(num_drivers):
            profiles.append(DriverProfile(
                driver_id=i,
                consistency=self.rng.beta(3, 2),  # Most drivers consistent
                pace_skill=self.rng.normal(0.5, 0.15),  # Centered around 0.5
                tire_management=self.rng.beta(2.5, 2.5),
                overtaking_skill=self.rng.beta(2, 2)
            ))
        return profiles
    
    def generate_race_conditions(self) -> RaceConditions:
        """Generate realistic race conditions."""
        # Weather distribution: 70% dry, 20% light rain, 10% heavy rain
        weather_probs = [0.7, 0.2, 0.1]
        weather = self.rng.choice(
            [WeatherCondition.DRY, WeatherCondition.LIGHT_RAIN, WeatherCondition.HEAVY_RAIN],
            p=weather_probs
        )
        
        # Temperature based on weather
        if weather == WeatherCondition.DRY:
            track_temp = self.rng.normal(45, 8)  # 30-60C typical
            air_temp = self.rng.normal(28, 5)
        elif weather == WeatherCondition.LIGHT_RAIN:
            track_temp = self.rng.normal(32, 5)
            air_temp = self.rng.normal(22, 4)
        else:  # Heavy rain
            track_temp = self.rng.normal(25, 4)
            air_temp = self.rng.normal(18, 3)
        
        return RaceConditions(
            weather=weather,
            track_temp=np.clip(track_temp, 15, 60),
            air_temp=np.clip(air_temp, 10, 40),
            humidity=self.rng.uniform(0.3, 0.9),
            wind_speed=self.rng.exponential(10)  # Mostly low wind
        )
    
    def calculate_base_lap_time(
        self,
        circuit: str,
        tire: str,
        conditions: RaceConditions,
        driver: DriverProfile
    ) -> float:
        """Calculate base lap time with all factors."""
        circuit_config = CIRCUITS[circuit]
        tire_config = TIRE_COMPOUNDS[tire]
        
        # Base circuit time
        base_time = circuit_config["base_lap_time"]
        
        # Tire compound effect
        tire_pace = tire_config["base_pace"]
        
        # Driver pace skill (±0.5s range)
        driver_pace = (driver.pace_skill - 0.5) * 1.0
        
        # Weather impact
        weather_mult = self.WEATHER_IMPACT[conditions.weather]['lap_time_multiplier']
        
        # Temperature effect (slower if too hot or too cold)
        temp_deviation = abs(conditions.track_temp - self.TEMP_OPTIMAL)
        temp_effect = temp_deviation * self.TEMP_EFFECT
        
        return (base_time + tire_pace + driver_pace + temp_effect) * weather_mult
    
    def calculate_tire_degradation(
        self,
        tire: str,
        tire_age: int,
        conditions: RaceConditions,
        driver: DriverProfile
    ) -> float:
        """Calculate tire degradation with environmental factors."""
        tire_config = TIRE_COMPOUNDS[tire]
        base_deg_rate = tire_config["degradation_rate"]
        
        # Driver tire management skill
        driver_factor = 1.0 - (driver.tire_management - 0.5) * 0.3
        
        # Weather effect on degradation
        weather_factor = self.WEATHER_IMPACT[conditions.weather]['tire_degradation_multiplier']
        
        # Temperature effect (higher temp = faster degradation)
        temp_factor = 1.0 + (conditions.track_temp - 35) * 0.01
        
        # Non-linear degradation curve
        adjusted_rate = base_deg_rate * driver_factor * weather_factor * temp_factor
        degradation = adjusted_rate * (tire_age ** 1.5)
        
        return degradation
    
    def generate_lap_noise(self, driver: DriverProfile, lap_num: int) -> float:
        """Generate realistic lap-to-lap variation."""
        # Consistency affects variance
        base_variance = 0.3 * (1.5 - driver.consistency)
        
        # Track evolution (track gets faster, then stabilizes)
        track_evol = -0.05 * np.exp(-lap_num / 10)
        
        # Small random errors (outliers)
        if self.rng.random() < 0.02:  # 2% chance of error
            error = self.rng.exponential(0.5)
        else:
            error = 0
        
        noise = self.rng.normal(0, base_variance) + track_evol + error
        return noise
    
    def generate_race_stint(
        self,
        race_id: int,
        circuit: str,
        tire: str,
        driver: DriverProfile,
        conditions: RaceConditions,
        start_lap: int,
        stint_length: int,
        initial_fuel: float,
        total_laps: int
    ) -> List[Dict]:
        """Generate a complete race stint with all features."""
        records = []
        base_time = self.calculate_base_lap_time(circuit, tire, conditions, driver)
        
        for i in range(stint_length):
            lap_num = start_lap + i
            tire_age = i + 1
            
            # Fuel effect (linear decrease)
            fuel_load = initial_fuel * (1 - (lap_num - 1) / total_laps)
            fuel_effect = fuel_load * 0.08
            
            # Tire degradation
            degradation = self.calculate_tire_degradation(
                tire, tire_age, conditions, driver
            )
            
            # Base lap time
            lap_time = base_time + fuel_effect + degradation
            
            # Add noise
            noise = self.generate_lap_noise(driver, lap_num)
            lap_time += noise
            
            # Pit stop decision (random for training data variety)
            pit_stop = (i == stint_length - 1 and lap_num < total_laps)
            
            record = {
                'race_id': race_id,
                'driver_id': driver.driver_id,
                'lap_number': lap_num,
                'circuit': circuit,
                'tire_compound': tire,
                'tire_age': tire_age,
                'lap_time': round(lap_time, 3),
                'fuel_load': round(fuel_load, 3),
                'fuel_effect': round(fuel_effect, 3),
                'tire_degradation': round(degradation, 3),
                'track_temperature': round(conditions.track_temp, 1),
                'air_temperature': round(conditions.air_temp, 1),
                'weather_condition': conditions.weather.value,
                'humidity': round(conditions.humidity, 2),
                'wind_speed': round(conditions.wind_speed, 1),
                'pit_stop': pit_stop,
                'total_laps': total_laps,
                'stint_number': 0,  # Will be updated
                'grip_level': round(self.WEATHER_IMPACT[conditions.weather]['grip_level'], 2),
                'driver_consistency': round(driver.consistency, 3),
                'driver_pace_skill': round(driver.pace_skill, 3),
                'driver_tire_management': round(driver.tire_management, 3)
            }
            records.append(record)
        
        return records
    
    def generate_full_race(
        self,
        race_id: int,
        circuit: str,
        num_drivers: int = 10,
        strategy_type: str = 'auto'
    ) -> List[Dict]:
        """Generate a complete race with multiple drivers and strategies."""
        total_laps = CIRCUITS[circuit]['laps']
        conditions = self.generate_race_conditions()
        
        # Select random drivers
        drivers = self.rng.choice(self.driver_profiles, num_drivers, replace=False)
        
        all_records = []
        
        for driver in drivers:
            # Determine strategy for this driver
            if strategy_type == 'auto':
                strat = self.rng.choice(['1_stop', '2_stop', '3_stop'])
            else:
                strat = strategy_type
            
            # Generate pit stops based on strategy
            if strat == '1_stop':
                pit_lap = self.rng.randint(int(total_laps * 0.35), int(total_laps * 0.55))
                pit_stops = [pit_lap]
                tires = ['soft', 'hard']
            elif strat == '2_stop':
                pit1 = self.rng.randint(int(total_laps * 0.22), int(total_laps * 0.32))
                pit2 = self.rng.randint(int(total_laps * 0.55), int(total_laps * 0.70))
                pit_stops = [pit1, pit2]
                tires = ['soft', 'medium', 'hard']
            else:  # 3_stop
                pit1 = self.rng.randint(10, int(total_laps * 0.25))
                pit2 = self.rng.randint(int(total_laps * 0.35), int(total_laps * 0.50))
                pit3 = self.rng.randint(int(total_laps * 0.60), int(total_laps * 0.75))
                pit_stops = [pit1, pit2, pit3]
                tires = ['soft', 'medium', 'soft', 'medium']
            
            # Generate stints
            prev_pit = 0
            for stint_idx, pit_lap in enumerate(pit_stops + [total_laps]):
                stint_length = pit_lap - prev_pit
                if stint_length <= 0:
                    continue
                
                tire = tires[min(stint_idx, len(tires) - 1)]
                
                stint_records = self.generate_race_stint(
                    race_id=race_id,
                    circuit=circuit,
                    tire=tire,
                    driver=driver,
                    conditions=conditions,
                    start_lap=prev_pit + 1,
                    stint_length=stint_length,
                    initial_fuel=1.0,
                    total_laps=total_laps
                )
                
                # Update stint number
                for record in stint_records:
                    record['stint_number'] = stint_idx
                
                all_records.extend(stint_records)
                prev_pit = pit_lap
        
        return all_records
    
    def generate_large_dataset(
        self,
        num_races: int = 100,
        output_path: str = None
    ) -> pd.DataFrame:
        """
        Generate a large-scale dataset with multiple races.
        
        Args:
            num_races: Number of races to simulate (default 100 races ~20-50k records)
            output_path: Where to save CSV
            
        Returns:
            DataFrame with all records
        """
        circuits = list(CIRCUITS.keys())
        all_records = []
        
        print(f"Generating {num_races} races...")
        
        for race_id in range(num_races):
            circuit = self.rng.choice(circuits)
            num_drivers = self.rng.randint(8, 15)
            
            race_records = self.generate_full_race(
                race_id=race_id,
                circuit=circuit,
                num_drivers=num_drivers
            )
            
            all_records.extend(race_records)
            
            if (race_id + 1) % 10 == 0:
                print(f"  Completed {race_id + 1}/{num_races} races ({len(all_records)} records)")
        
        df = pd.DataFrame(all_records)
        
        # Add derived features
        df['tire_age_squared'] = df['tire_age'] ** 2
        df['stint_progress'] = df['tire_age'] / df.groupby(['race_id', 'driver_id', 'stint_number'])['tire_age'].transform('max')
        df['race_progress'] = df['lap_number'] / df['total_laps']
        
        # Add weather encoding
        weather_map = {'dry': 0, 'light_rain': 1, 'heavy_rain': 2}
        df['weather_encoded'] = df['weather_condition'].map(weather_map)
        
        # Safety car probability (random events)
        df['safety_car_active'] = False
        for race_id in df['race_id'].unique():
            if self.rng.random() < 0.3:  # 30% chance of SC
                race_df = df[df['race_id'] == race_id]
                sc_start = self.rng.randint(5, race_df['total_laps'].iloc[0] - 5)
                sc_duration = self.rng.randint(3, 8)
                sc_laps = range(sc_start, sc_start + sc_duration)
                
                mask = (df['race_id'] == race_id) & (df['lap_number'].isin(sc_laps))
                df.loc[mask, 'safety_car_active'] = True
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"\nDataset saved: {output_path}")
            print(f"Total records: {len(df):,}")
            print(f"File size: {Path(output_path).stat().st_size / (1024*1024):.2f} MB")
        
        return df


# Backward compatibility
def generate_dataset(num_samples: int = 5000, output_path: str = None) -> pd.DataFrame:
    """Legacy function - now generates by race count for better quality."""
    generator = AdvancedDataGenerator()
    # Approximately 300-500 laps per race
    num_races = max(10, num_samples // 400)
    return generator.generate_large_dataset(num_races, output_path)


def load_or_generate_data(data_dir: str = "data", large: bool = True) -> pd.DataFrame:
    """Load existing data or generate new dataset."""
    if large:
        data_path = Path(data_dir) / "f1_race_data_large.csv"
    else:
        data_path = Path(data_dir) / "f1_race_data.csv"
    
    if data_path.exists():
        print(f"Loading existing dataset: {data_path}")
        return pd.read_csv(data_path)
    
    print("Generating new dataset...")
    generator = AdvancedDataGenerator()
    return generator.generate_large_dataset(
        num_races=100,
        output_path=str(data_path)
    )


if __name__ == "__main__":
    # Generate large dataset
    generator = AdvancedDataGenerator(random_seed=42)
    df = generator.generate_large_dataset(
        num_races=100,
        output_path="data/f1_race_data_large.csv"
    )
    
    print("\n" + "="*60)
    print("Dataset Statistics")
    print("="*60)
    print(f"Total records: {len(df):,}")
    print(f"Unique races: {df['race_id'].nunique()}")
    print(f"Unique drivers: {df['driver_id'].nunique()}")
    print("\nCircuit distribution:")
    print(df['circuit'].value_counts())
    print("\nWeather distribution:")
    print(df['weather_condition'].value_counts())
    print("\nTire compound distribution:")
    print(df['tire_compound'].value_counts())
    print("\nLap time statistics:")
    print(df['lap_time'].describe())
