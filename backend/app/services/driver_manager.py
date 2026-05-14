"""
Driver Management System - Loads and manages F1 driver data
Provides realistic driver profiles and race grid generation
"""
import json
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class DriverProfile:
    """Complete driver profile with performance characteristics."""
    id: int
    driver_code: str
    name: str
    team: str
    team_color: str
    number: int
    country: str
    flag: str
    
    # Performance metrics (0-1 scale)
    skill: float
    race_pace: int
    tire_management: int
    aggression: int
    wet_weather_skill: int
    consistency: int
    qualifying_pace: int
    defending: int
    overtaking: int
    
    @property
    def consistency_factor(self) -> float:
        """Convert consistency to lap time variance factor."""
        return 0.3 * (1.5 - (self.consistency / 100))
    
    @property
    def base_skill(self) -> float:
        """Overall skill rating."""
        return self.skill
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'driver_code': self.driver_code,
            'name': self.name,
            'team': self.team,
            'team_color': self.team_color,
            'number': self.number,
            'country': self.country,
            'skill': self.skill,
            'race_pace': self.race_pace,
            'tire_management': self.tire_management,
            'aggression': self.aggression,
            'wet_weather_skill': self.wet_weather_skill,
            'consistency': self.consistency,
            'qualifying_pace': self.qualifying_pace,
            'defending': self.defending,
            'overtaking': self.overtaking,
        }


class DriverManager:
    """Centralized driver data management."""
    
    _instance = None
    _drivers = None
    _teams = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DriverManager, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance
    
    def _load_data(self):
        """Load driver data from JSON file."""
        try:
            data_path = Path(__file__).parent.parent.parent / 'data' / 'drivers.json'
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._drivers = {}
            for driver_data in data.get('drivers', []):
                profile = DriverProfile(**driver_data)
                self._drivers[profile.driver_code] = profile
                self._drivers[profile.id] = profile
                self._drivers[profile.name] = profile
            
            self._teams = data.get('teams', {})
            
        except Exception as e:
            print(f"Error loading driver data: {e}")
            self._create_fallback_data()
    
    def _create_fallback_data(self):
        """Create minimal fallback driver data if JSON fails."""
        self._drivers = {}
        self._teams = {
            "Red Bull Racing": {"color": "#1E41FF"},
            "Mercedes": {"color": "#00D2BE"},
            "Ferrari": {"color": "#FF0000"},
            "McLaren": {"color": "#FF8000"},
            "Aston Martin": {"color": "#006F62"},
        }
    
    def get_driver(self, identifier) -> Optional[DriverProfile]:
        """Get driver by code, id, or name."""
        if isinstance(identifier, int):
            return self._drivers.get(identifier)
        return self._drivers.get(identifier)
    
    def get_driver_by_code(self, code: str) -> Optional[DriverProfile]:
        """Get driver by their 3-letter code."""
        return self._drivers.get(code.upper())
    
    def get_driver_by_name(self, name: str) -> Optional[DriverProfile]:
        """Get driver by full name."""
        return self._drivers.get(name)
    
    def get_all_drivers(self) -> List[DriverProfile]:
        """Get list of all unique drivers."""
        seen = set()
        drivers = []
        for driver in self._drivers.values():
            if driver.id not in seen:
                seen.add(driver.id)
                drivers.append(driver)
        return sorted(drivers, key=lambda d: d.id)
    
    def get_team_drivers(self, team_name: str) -> List[DriverProfile]:
        """Get both drivers for a team."""
        return [d for d in self.get_all_drivers() if d.team == team_name]
    
    def get_team_color(self, team_name: str) -> str:
        """Get team color hex code."""
        team = self._teams.get(team_name, {})
        return team.get('color', '#888888')
    
    def get_driver_color(self, driver_code: str) -> str:
        """Get color for a specific driver."""
        driver = self.get_driver_by_code(driver_code)
        if driver:
            return driver.team_color
        return '#888888'
    
    def generate_race_grid(self, num_cars: int = 20, randomize: bool = True) -> List[Dict]:
        """
        Generate a realistic race grid with qualifying results.
        
        Args:
            num_cars: Number of cars in the race
            randomize: Add randomness to qualifying results
            
        Returns:
            List of driver dicts with grid positions
        """
        all_drivers = self.get_all_drivers()
        
        if num_cars > len(all_drivers):
            num_cars = len(all_drivers)
        
        # Select drivers for this race
        if randomize:
            selected = random.sample(all_drivers, num_cars)
        else:
            selected = all_drivers[:num_cars]
        
        # Group by team
        team_groups = {}
        for driver in selected:
            if driver.team not in team_groups:
                team_groups[driver.team] = []
            team_groups[driver.team].append(driver)
        
        # Sort teams by max qualifying pace
        sorted_teams = sorted(
            team_groups.items(),
            key=lambda x: max(d.qualifying_pace for d in x[1]),
            reverse=True
        )
        
        grid = []
        position = 1
        
        for team_name, team_drivers in sorted_teams:
            # Sort teammates by qualifying pace
            team_drivers.sort(key=lambda d: d.qualifying_pace, reverse=True)
            
            for driver in team_drivers:
                # Add qualifying variance
                if randomize:
                    variance = random.uniform(-2, 2)
                    grid_pos = max(1, min(num_cars, position + variance))
                else:
                    grid_pos = position
                
                grid.append({
                    **driver.to_dict(),
                    'grid_position': round(grid_pos),
                    'position': round(grid_pos),
                    'gap_to_leader': 0.0 if round(grid_pos) == 1 else round(random.uniform(0.1, 0.8), 3)
                })
                position += 1
        
        # Sort by grid position
        grid.sort(key=lambda x: x['grid_position'])
        
        # Reassign positions after sorting
        for i, driver in enumerate(grid):
            driver['position'] = i + 1
            driver['gap_to_leader'] = 0.0 if i == 0 else round(i * 0.3 + random.uniform(-0.1, 0.1), 3)
        
        return grid
    
    def generate_driver_configs(self, num_cars: int = 20) -> List[Dict]:
        """
        Generate driver configs for the multi-car simulator.
        
        Returns:
            List of driver configuration dicts
        """
        grid = self.generate_race_grid(num_cars)
        
        configs = []
        for driver in grid:
            configs.append({
                'driver_id': driver['id'],
                'name': driver['name'],
                'team': driver['team'],
                'skill': driver['skill'],
                'consistency': driver['consistency'] / 100,
                'aggression': driver['aggression'] / 100,
                'tire_management': driver['tire_management'] / 100,
                'position': driver['position'],
                'gap_to_leader': driver['gap_to_leader'],
                'current_tire': 'soft',
                'tire_age': 0
            })
        
        return configs
    
    def format_driver_name(self, identifier, include_team: bool = False) -> str:
        """Format driver name for display."""
        driver = self.get_driver(identifier)
        if not driver:
            return str(identifier)
        
        if include_team:
            return f"{driver.name} ({driver.team})"
        return driver.name
    
    def format_overtake_message(self, attacker_code: str, defender_code: str, 
                                 location: str = None) -> str:
        """Generate realistic overtake commentary."""
        attacker = self.get_driver_by_code(attacker_code)
        defender = self.get_driver_by_code(defender_code)
        
        if not attacker or not defender:
            return f"{attacker_code} overtook {defender_code}"
        
        locations = {
            'DRS_1': 'into Turn 1',
            'DRS_2': 'on the back straight',
            'turn_1': 'into Turn 1',
            'turn_4': 'at Turn 4',
            'turn_6': 'through Turn 6',
            'turn_10': 'at Turn 10',
            'turn_15': 'through Turn 15',
            'les_combes': 'at Les Combes',
            'bus_stop': 'into the Bus Stop',
            'DRS_zone': 'in the DRS zone'
        }
        
        location_str = locations.get(location, 'on track')
        
        # Use driver last names for commentary
        attacker_last = attacker.name.split()[-1]
        defender_last = defender.name.split()[-1]
        
        return f"{attacker_last} overtook {defender_last} {location_str}"


# Singleton instance
driver_manager = DriverManager()

# Convenience functions
def get_driver(identifier):
    return driver_manager.get_driver(identifier)

def get_driver_by_code(code: str):
    return driver_manager.get_driver_by_code(code)

def get_driver_by_name(name: str):
    return driver_manager.get_driver_by_name(name)

def get_team_color(team_name: str) -> str:
    return driver_manager.get_team_color(team_name)

def get_driver_color(driver_code: str) -> str:
    return driver_manager.get_driver_color(driver_code)

def generate_race_grid(num_cars: int = 20, randomize: bool = True) -> List[Dict]:
    return driver_manager.generate_race_grid(num_cars, randomize)

def generate_driver_configs(num_cars: int = 20) -> List[Dict]:
    return driver_manager.generate_driver_configs(num_cars)

def format_driver_name(identifier, include_team: bool = False) -> str:
    return driver_manager.format_driver_name(identifier, include_team)

def format_overtake_message(attacker: str, defender: str, location: str = None) -> str:
    return driver_manager.format_overtake_message(attacker, defender, location)
