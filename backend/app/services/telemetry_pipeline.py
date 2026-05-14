"""
F1 Strategy Intelligence System - Elite Edition v3.0
Telemetry-Style Data Pipeline

Generates high-frequency telemetry data including sector times,
speed traces, and per-corner tire wear approximation.
"""
import numpy as np
import pandas as pd
from typing import List, Dict
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime

from app.core.config import CIRCUITS, TIRE_COMPOUNDS


@dataclass
class SectorTime:
    """Sector time breakdown for a lap."""
    sector_1: float
    sector_2: float
    sector_3: float
    speed_trap: float  # km/h at fastest point
    
    @property
    def total(self) -> float:
        return self.sector_1 + self.sector_2 + self.sector_3


@dataclass
class CornerTelemetry:
    """Per-corner telemetry data."""
    corner_number: int
    entry_speed: float  # km/h
    apex_speed: float
    exit_speed: float
    lateral_g: float
    braking_g: float
    throttle_percent: float
    tire_temp_front_left: float
    tire_temp_front_right: float
    tire_temp_rear_left: float
    tire_temp_rear_right: float


@dataclass
class LapTelemetry:
    """Complete telemetry for a single lap."""
    lap_number: int
    driver_id: int
    race_id: str
    timestamp: str
    
    # Timing
    lap_time: float
    sector_times: SectorTime
    
    # Performance
    top_speed: float
    avg_speed: float
    min_speed: float
    
    # Tire data
    tire_compound: str
    tire_age: int
    tire_wear_percent: float  # 0-100
    estimated_grip: float  # 0-1
    
    # Engine/ERS
    ers_deploy: float  # kJ used
    ers_harvest: float  # kJ recovered
    fuel_flow_rate: float  # kg/h
    
    # Aerodynamics
    drs_active: bool
    drs_zones_used: int
    downforce_level: str  # 'high', 'medium', 'low'
    
    # Conditions
    track_temp: float
    air_temp: float
    wind_speed: float
    wind_direction: str
    
    # Corner data (key corners only)
    corners: List[CornerTelemetry]
    
    # Strategy indicators
    gap_to_ahead: float
    gap_to_behind: float
    position: int


class TelemetryGenerator:
    """
    High-frequency telemetry data generator.
    Creates realistic telemetry traces for detailed analysis.
    """
    
    # Sector distribution (approximate)
    SECTOR_DISTRIBUTION = {
        'Monza': [0.28, 0.42, 0.30],  # Sectors 1, 2, 3 as % of lap
        'Silverstone': [0.30, 0.35, 0.35],
        'Spa': [0.32, 0.38, 0.30],
        'Monaco': [0.35, 0.35, 0.30],
        'Suzuka': [0.33, 0.34, 0.33],
        'Barcelona': [0.31, 0.36, 0.33]
    }
    
    # Key corners per circuit
    KEY_CORNERS = {
        'Monza': [
            {'num': 1, 'name': 'Rettifilo', 'speed': 'high'},
            {'num': 4, 'name': 'Lesmo 1', 'speed': 'medium'},
            {'num': 6, 'name': 'Lesmo 2', 'speed': 'medium'},
            {'num': 8, 'name': 'Ascari', 'speed': 'high'},
            {'num': 11, 'name': 'Parabolica', 'speed': 'medium'}
        ],
        'Silverstone': [
            {'num': 1, 'name': 'Abbey', 'speed': 'high'},
            {'num': 3, 'name': 'Village', 'speed': 'medium'},
            {'num': 6, 'name': 'Brooklands', 'speed': 'medium'},
            {'num': 9, 'name': 'Copse', 'speed': 'high'},
            {'num': 15, 'name': 'Stowe', 'speed': 'high'}
        ],
        'Spa': [
            {'num': 1, 'name': 'La Source', 'speed': 'slow'},
            {'num': 7, 'name': 'Les Combes', 'speed': 'medium'},
            {'num': 11, 'name': 'Pouhon', 'speed': 'high'},
            {'num': 15, 'name': 'Bus Stop', 'speed': 'slow'}
        ]
    }
    
    def __init__(self, circuit: str, race_id: str = None):
        self.circuit = circuit
        self.race_id = race_id or f"RACE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.circuit_config = CIRCUITS[circuit]
        self.base_lap_time = self.circuit_config['base_lap_time']
        
    def generate_sector_times(self, 
                            lap_time: float,
                            tire_age: int,
                            tire_compound: str,
                            drs_active: bool = False) -> SectorTime:
        """
        Generate realistic sector time breakdown.
        
        Args:
            lap_time: Total lap time
            tire_age: Current tire age
            tire_compound: Tire compound
            drs_active: Whether DRS was used
            
        Returns:
            SectorTime with sector breakdowns
        """
        # Get sector distribution
        dist = self.SECTOR_DISTRIBUTION.get(self.circuit, [0.33, 0.33, 0.34])
        
        # Base sector times
        s1_base = lap_time * dist[0]
        s2_base = lap_time * dist[1]
        s3_base = lap_time * dist[2]
        
        # Add variation
        s1_var = np.random.normal(0, 0.2)
        s2_var = np.random.normal(0, 0.3)
        s3_var = np.random.normal(0, 0.2)
        
        # Tire degradation affects later sectors more
        tire_penalty = tire_age * 0.03
        s2_base += tire_penalty * 0.6  # Sector 2 is longest
        s3_base += tire_penalty * 0.4
        
        # DRS benefit (mostly in sectors 1 and 3)
        if drs_active:
            s1_drs = np.random.uniform(0.3, 0.8)
            s3_drs = np.random.uniform(0.2, 0.6)
        else:
            s1_drs = 0
            s3_drs = 0
        
        sector_1 = max(s1_base + s1_var - s1_drs, s1_base * 0.95)
        sector_2 = max(s2_base + s2_var, s2_base * 0.95)
        sector_3 = max(s3_base + s3_var - s3_drs, s3_base * 0.95)
        
        # Speed trap (typically end of longest straight)
        base_speed = 320 if self.circuit == 'Monza' else 300
        if self.circuit == 'Monaco':
            base_speed = 280
        
        speed_var = np.random.normal(0, 5)
        speed_trap = base_speed + speed_var
        
        return SectorTime(
            sector_1=round(sector_1, 3),
            sector_2=round(sector_2, 3),
            sector_3=round(sector_3, 3),
            speed_trap=round(speed_trap, 1)
        )
    
    def generate_corner_telemetry(self,
                                 corner_info: Dict,
                                 tire_age: int,
                                 tire_compound: str) -> CornerTelemetry:
        """Generate telemetry for a specific corner."""
        speed_type = corner_info.get('speed', 'medium')
        
        # Base speeds by corner type
        if speed_type == 'high':
            entry_base = 240
            apex_base = 180
            exit_base = 220
            lateral_g = 3.5
        elif speed_type == 'medium':
            entry_base = 180
            apex_base = 100
            exit_base = 160
            lateral_g = 4.0
        else:  # slow
            entry_base = 120
            apex_base = 60
            exit_base = 100
            lateral_g = 4.5
        
        # Tire degradation affects cornering
        grip_loss = min(0.3, tire_age / 60)
        speed_factor = 1 - grip_loss * 0.1
        lateral_g_factor = 1 - grip_loss * 0.15
        
        # Variation
        entry_speed = entry_base * speed_factor + np.random.normal(0, 5)
        apex_speed = apex_base * speed_factor + np.random.normal(0, 3)
        exit_speed = exit_base * speed_factor + np.random.normal(0, 5)
        
        lateral_g = lateral_g * lateral_g_factor + np.random.normal(0, 0.2)
        braking_g = min(5.0, lateral_g * 1.2)
        
        # Throttle application
        if speed_type == 'high':
            throttle = 85 + np.random.normal(0, 5)
        elif speed_type == 'medium':
            throttle = 70 + np.random.normal(0, 10)
        else:
            throttle = 60 + np.random.normal(0, 15)
        
        throttle_percent = np.clip(throttle, 0, 100)
        
        # Tire temperatures (increase with tire age)
        base_temp = 90 + tire_age * 0.5
        temps = [
            base_temp + np.random.normal(0, 5),
            base_temp + np.random.normal(0, 5),
            base_temp + np.random.normal(0, 3),
            base_temp + np.random.normal(0, 3)
        ]
        
        return CornerTelemetry(
            corner_number=corner_info['num'],
            entry_speed=round(entry_speed, 1),
            apex_speed=round(apex_speed, 1),
            exit_speed=round(exit_speed, 1),
            lateral_g=round(lateral_g, 2),
            braking_g=round(braking_g, 2),
            throttle_percent=round(throttle_percent, 1),
            tire_temp_front_left=round(temps[0], 1),
            tire_temp_front_right=round(temps[1], 1),
            tire_temp_rear_left=round(temps[2], 1),
            tire_temp_rear_right=round(temps[3], 1)
        )
    
    def generate_lap_telemetry(self,
                              lap_number: int,
                              driver_id: int,
                              lap_time: float,
                              tire_compound: str,
                              tire_age: int,
                              position: int,
                              gap_to_ahead: float,
                              gap_to_behind: float,
                              weather: str = 'dry',
                              track_temp: float = 35.0) -> LapTelemetry:
        """Generate complete telemetry for a lap."""
        
        # Sector times
        drs_active = lap_number > 1 and np.random.random() < 0.7  # 70% chance DRS used
        sector_times = self.generate_sector_times(
            lap_time, tire_age, tire_compound, drs_active
        )
        
        # Speed statistics
        # base_speed = self.circuit_config['base_lap_time']
        top_speed = sector_times.speed_trap
        avg_speed = (self.circuit_config.get('length', 5000) / lap_time) * 3.6  # km/h
        min_speed = avg_speed * 0.4 + np.random.normal(0, 5)
        
        # Tire wear calculation
        tire_config = TIRE_COMPOUNDS[tire_compound]
        wear_rate = 100 / tire_config['optimal_laps']
        tire_wear = min(100, tire_age * wear_rate + np.random.normal(0, 2))
        estimated_grip = max(0.4, 1 - tire_wear / 150)
        
        # ERS simulation
        ers_deploy = np.random.uniform(100, 200)  # kJ per lap
        ers_harvest = np.random.uniform(80, 150)  # kJ recovered
        fuel_flow = np.random.uniform(80, 100)  # kg/h
        
        # Conditions
        air_temp = track_temp - np.random.uniform(5, 15)
        wind_speed = np.random.exponential(8)
        wind_dir = np.random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        
        # Corner telemetry (key corners only)
        corner_data = []
        key_corners = self.KEY_CORNERS.get(self.circuit, [])
        for corner in key_corners:
            corner_telem = self.generate_corner_telemetry(
                corner, tire_age, tire_compound
            )
            corner_data.append(corner_telem)
        
        return LapTelemetry(
            lap_number=lap_number,
            driver_id=driver_id,
            race_id=self.race_id,
            timestamp=datetime.now().isoformat(),
            lap_time=lap_time,
            sector_times=sector_times,
            top_speed=round(top_speed, 1),
            avg_speed=round(avg_speed, 1),
            min_speed=round(max(0, min_speed), 1),
            tire_compound=tire_compound,
            tire_age=tire_age,
            tire_wear_percent=round(tire_wear, 1),
            estimated_grip=round(estimated_grip, 3),
            ers_deploy=round(ers_deploy, 1),
            ers_harvest=round(ers_harvest, 1),
            fuel_flow_rate=round(fuel_flow, 2),
            drs_active=drs_active,
            drs_zones_used=int(drs_active) * np.random.randint(1, 3),
            downforce_level='low' if self.circuit in ['Monza', 'Spa'] else 'medium',
            track_temp=round(track_temp, 1),
            air_temp=round(air_temp, 1),
            wind_speed=round(wind_speed, 1),
            wind_direction=wind_dir,
            corners=corner_data,
            gap_to_ahead=round(gap_to_ahead, 3),
            gap_to_behind=round(gap_to_behind, 3),
            position=position
        )
    
    def generate_race_telemetry(self,
                              driver_id: int,
                              total_laps: int,
                              pit_laps: List[int],
                              tire_strategy: List[str],
                              base_position: int = 5) -> List[LapTelemetry]:
        """
        Generate complete race telemetry.
        
        Returns:
            List of LapTelemetry for entire race
        """
        telemetry_laps = []
        current_tire_idx = 0
        
        for lap in range(1, total_laps + 1):
            # Determine tire
            while (current_tire_idx < len(pit_laps) and 
                   lap > pit_laps[current_tire_idx]):
                current_tire_idx += 1
            
            current_tire = tire_strategy[min(current_tire_idx, len(tire_strategy) - 1)]
            
            # Calculate tire age
            if current_tire_idx == 0:
                tire_age = lap
            else:
                tire_age = lap - pit_laps[current_tire_idx - 1]
            
            # Simulate lap time
            tire_config = TIRE_COMPOUNDS[current_tire]
            base_time = self.base_lap_time + tire_config['base_pace']
            degradation = tire_config['degradation_rate'] * (tire_age ** 1.5)
            lap_time = base_time + degradation + np.random.normal(0, 0.3)
            
            # Position and gaps (simplified)
            position = base_position + np.random.randint(-1, 2)
            position = max(1, min(20, position))
            gap_ahead = np.random.uniform(0.5, 3.0)
            gap_behind = np.random.uniform(0.5, 5.0)
            
            # Generate telemetry
            telem = self.generate_lap_telemetry(
                lap, driver_id, lap_time, current_tire, tire_age,
                position, gap_ahead, gap_behind
            )
            
            telemetry_laps.append(telem)
        
        return telemetry_laps


class TelemetryExporter:
    """Export telemetry data to various formats."""
    
    @staticmethod
    def to_dataframe(telemetry_laps: List[LapTelemetry]) -> pd.DataFrame:
        """Convert telemetry to DataFrame."""
        records = []
        for lap in telemetry_laps:
            record = {
                'lap_number': lap.lap_number,
                'driver_id': lap.driver_id,
                'race_id': lap.race_id,
                'lap_time': lap.lap_time,
                'sector_1': lap.sector_times.sector_1,
                'sector_2': lap.sector_times.sector_2,
                'sector_3': lap.sector_times.sector_3,
                'speed_trap': lap.sector_times.speed_trap,
                'top_speed': lap.top_speed,
                'tire_compound': lap.tire_compound,
                'tire_age': lap.tire_age,
                'tire_wear_percent': lap.tire_wear_percent,
                'estimated_grip': lap.estimated_grip,
                'drs_active': lap.drs_active,
                'track_temp': lap.track_temp,
                'position': lap.position,
                'gap_to_ahead': lap.gap_to_ahead
            }
            
            # Add corner data
            for corner in lap.corners:
                prefix = f"corner_{corner.corner_number}_"
                record[f'{prefix}entry_speed'] = corner.entry_speed
                record[f'{prefix}apex_speed'] = corner.apex_speed
                record[f'{prefix}lateral_g'] = corner.lateral_g
            
            records.append(record)
        
        return pd.DataFrame(records)
    
    @staticmethod
    def save_to_csv(telemetry_laps: List[LapTelemetry], filepath: str):
        """Save telemetry to CSV."""
        df = TelemetryExporter.to_dataframe(telemetry_laps)
        
        # Create directory if needed
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(filepath, index=False)
        print(f"Telemetry saved to {filepath}")
    
    @staticmethod
    def to_json(telemetry_laps: List[LapTelemetry]) -> str:
        """Convert telemetry to JSON string."""
        data = []
        for lap in telemetry_laps:
            record = {
                'lap_number': lap.lap_number,
                'lap_time': lap.lap_time,
                'sector_times': {
                    's1': lap.sector_times.sector_1,
                    's2': lap.sector_times.sector_2,
                    's3': lap.sector_times.sector_3,
                    'total': lap.sector_times.total
                },
                'tire': {
                    'compound': lap.tire_compound,
                    'age': lap.tire_age,
                    'wear_percent': lap.tire_wear_percent,
                    'grip': lap.estimated_grip
                },
                'performance': {
                    'top_speed': lap.top_speed,
                    'drs_active': lap.drs_active
                },
                'race_context': {
                    'position': lap.position,
                    'gap_to_ahead': lap.gap_to_ahead
                }
            }
            data.append(record)
        
        return json.dumps(data, indent=2)


if __name__ == "__main__":
    # Test telemetry generation
    print("Testing Telemetry Pipeline")
    print("=" * 60)
    
    # Generate telemetry for a race
    generator = TelemetryGenerator('Monza', 'TEST_RACE_001')
    
    telemetry = generator.generate_race_telemetry(
        driver_id=0,
        total_laps=53,
        pit_laps=[18, 36],
        tire_strategy=['soft', 'medium', 'hard'],
        base_position=3
    )
    
    print(f"\nGenerated {len(telemetry)} laps of telemetry")
    
    # Show sample lap
    sample = telemetry[10]
    print(f"\nSample Lap {sample.lap_number}:")
    print(f"  Lap Time: {sample.lap_time:.3f}s")
    print(f"  Sectors: {sample.sector_times.sector_1:.3f} / {sample.sector_times.sector_2:.3f} / {sample.sector_times.sector_3:.3f}")
    print(f"  Speed Trap: {sample.sector_times.speed_trap:.1f} km/h")
    print(f"  Tire: {sample.tire_compound} (age {sample.tire_age}, wear {sample.tire_wear_percent:.1f}%)")
    print(f"  Grip: {sample.estimated_grip:.3f}")
    print(f"  DRS: {'Active' if sample.drs_active else 'Inactive'}")
    print(f"  Position: P{sample.position}, Gap: +{sample.gap_to_ahead:.3f}s")
    
    # Show corner data
    print("\n  Key Corners:")
    for corner in sample.corners[:3]:
        print(f"    T{corner.corner_number}: Entry {corner.entry_speed:.0f} km/h, "
              f"Apex {corner.apex_speed:.0f}, G-force {corner.lateral_g:.2f}")
    
    # Export test
    print("\n--- Export Test ---")
    df = TelemetryExporter.to_dataframe(telemetry[:5])
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)[:10]}...")
    
    print("\n" + "=" * 60)
    print("Telemetry pipeline test complete!")
