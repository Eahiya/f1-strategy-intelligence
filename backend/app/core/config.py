"""Configuration settings for the F1 Strategy System."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Circuit configurations (2025/2026 calendar)
# base_lap_time: approximate clean-air lap time in seconds
# pit_loss: typical time lost during a pit stop (entry + stop + exit vs flying lap)
# laps: official race distance
# tire_factor: how much the circuit degrades tires (higher = more wear)
CIRCUITS = {
    # European Rounds
    "Monza": {"laps": 53, "pit_loss": 22, "base_lap_time": 82.0, "tire_factor": 0.8, "overtaking": 0.9, "country": "Italy"},
    "Silverstone": {"laps": 52, "pit_loss": 24, "base_lap_time": 90.0, "tire_factor": 1.0, "overtaking": 0.7, "country": "UK"},
    "Spa": {"laps": 44, "pit_loss": 23, "base_lap_time": 105.0, "tire_factor": 1.1, "overtaking": 0.8, "country": "Belgium"},
    "Monaco": {"laps": 78, "pit_loss": 18, "base_lap_time": 72.0, "tire_factor": 0.6, "overtaking": 0.1, "country": "Monaco"},
    "Suzuka": {"laps": 53, "pit_loss": 25, "base_lap_time": 88.0, "tire_factor": 1.05, "overtaking": 0.5, "country": "Japan"},
    "Barcelona": {"laps": 66, "pit_loss": 24, "base_lap_time": 78.0, "tire_factor": 1.2, "overtaking": 0.5, "country": "Spain"},
    "Red Bull Ring": {"laps": 71, "pit_loss": 20, "base_lap_time": 66.0, "tire_factor": 1.3, "overtaking": 0.85, "country": "Austria"},
    "Hungaroring": {"laps": 70, "pit_loss": 22, "base_lap_time": 77.0, "tire_factor": 1.4, "overtaking": 0.3, "country": "Hungary"},
    "Zandvoort": {"laps": 72, "pit_loss": 22, "base_lap_time": 72.0, "tire_factor": 1.1, "overtaking": 0.6, "country": "Netherlands"},
    "Imola": {"laps": 63, "pit_loss": 24, "base_lap_time": 82.0, "tire_factor": 0.9, "overtaking": 0.4, "country": "Italy"},
    "Spielberg": {"laps": 71, "pit_loss": 20, "base_lap_time": 66.0, "tire_factor": 1.3, "overtaking": 0.85, "country": "Austria"},
    
    # Middle East Rounds
    "Bahrain": {"laps": 57, "pit_loss": 23, "base_lap_time": 93.0, "tire_factor": 1.3, "overtaking": 0.75, "country": "Bahrain"},
    "Jeddah": {"laps": 50, "pit_loss": 24, "base_lap_time": 72.0, "tire_factor": 0.7, "overtaking": 0.7, "country": "Saudi Arabia"},
    "Abu Dhabi": {"laps": 58, "pit_loss": 23, "base_lap_time": 88.0, "tire_factor": 0.9, "overtaking": 0.6, "country": "UAE"},
    "Qatar": {"laps": 57, "pit_loss": 24, "base_lap_time": 84.0, "tire_factor": 1.0, "overtaking": 0.55, "country": "Qatar"},
    
    # Americas Rounds
    "Miami": {"laps": 57, "pit_loss": 22, "base_lap_time": 82.0, "tire_factor": 0.8, "overtaking": 0.65, "country": "USA"},
    "Austin": {"laps": 56, "pit_loss": 24, "base_lap_time": 96.0, "tire_factor": 1.1, "overtaking": 0.7, "country": "USA"},
    "Montreal": {"laps": 70, "pit_loss": 21, "base_lap_time": 76.0, "tire_factor": 0.7, "overtaking": 0.75, "country": "Canada"},
    "Mexico City": {"laps": 71, "pit_loss": 19, "base_lap_time": 78.0, "tire_factor": 0.6, "overtaking": 0.7, "country": "Mexico"},
    "Interlagos": {"laps": 71, "pit_loss": 22, "base_lap_time": 72.0, "tire_factor": 0.9, "overtaking": 0.8, "country": "Brazil"},
    "Las Vegas": {"laps": 50, "pit_loss": 23, "base_lap_time": 92.0, "tire_factor": 0.5, "overtaking": 0.6, "country": "USA"},
    
    # Asia-Pacific Rounds
    "Melbourne": {"laps": 58, "pit_loss": 23, "base_lap_time": 80.0, "tire_factor": 0.8, "overtaking": 0.65, "country": "Australia"},
    "Shanghai": {"laps": 56, "pit_loss": 24, "base_lap_time": 92.0, "tire_factor": 0.9, "overtaking": 0.6, "country": "China"},
    "Singapore": {"laps": 62, "pit_loss": 26, "base_lap_time": 100.0, "tire_factor": 1.1, "overtaking": 0.4, "country": "Singapore"},
    
    # Additional historic/backup circuits
    "Baku": {"laps": 51, "pit_loss": 21, "base_lap_time": 84.0, "tire_factor": 0.5, "overtaking": 0.9, "country": "Azerbaijan"},
    "Paul Ricard": {"laps": 53, "pit_loss": 23, "base_lap_time": 85.0, "tire_factor": 0.85, "overtaking": 0.5, "country": "France"},
    "Portimao": {"laps": 66, "pit_loss": 24, "base_lap_time": 82.0, "tire_factor": 1.0, "overtaking": 0.55, "country": "Portugal"},
    "Istanbul": {"laps": 58, "pit_loss": 23, "base_lap_time": 88.0, "tire_factor": 1.5, "overtaking": 0.6, "country": "Turkey"},
}

# Tire compound configurations
TIRE_COMPOUNDS = {
    "soft": {
        "base_pace": -1.5,  # seconds faster than medium
        "degradation_rate": 0.12,
        "optimal_laps": 20,
        "color": "#FF3333"
    },
    "medium": {
        "base_pace": 0.0,
        "degradation_rate": 0.07,
        "optimal_laps": 35,
        "color": "#FFE119"
    },
    "hard": {
        "base_pace": 1.2,  # seconds slower than medium
        "degradation_rate": 0.04,
        "optimal_laps": 50,
        "color": "#FFFFFF"
    }
}

# Strategy parameters
STRATEGY_CONFIG = {
    "degradation_threshold": 3.0,  # seconds - when tire degradation triggers pit
    "undercut_advantage": 2.5,  # seconds gained by undercutting
    "safety_car_pit_gain": 8.0,  # seconds saved during safety car
    "fuel_effect_per_lap": 0.03,  # seconds faster per lap as fuel burns
    "max_stint_length": 40,  # maximum laps on any tire
}

# Circuit ID mapping (frontend snake_case -> backend proper name)
CIRCUIT_ID_MAP = {
    'monza': 'Monza',
    'silverstone': 'Silverstone',
    'spa': 'Spa',
    'monaco': 'Monaco',
    'suzuka': 'Suzuka',
    'red_bull_ring': 'Red Bull Ring',
    'hungaroring': 'Hungaroring',
    'catalunya': 'Barcelona',
    'barcelona': 'Barcelona',
    'zandvoort': 'Zandvoort',
    'imola': 'Imola',
    'spielberg': 'Spielberg',
    'bahrain': 'Bahrain',
    'jeddah': 'Jeddah',
    'abu_dhabi': 'Abu Dhabi',
    'qatar': 'Qatar',
    'miami': 'Miami',
    'austin': 'Austin',
    'montreal': 'Montreal',
    'mexico_city': 'Mexico City',
    'interlagos': 'Interlagos',
    'las_vegas': 'Las Vegas',
    'melbourne': 'Melbourne',
    'shanghai': 'Shanghai',
    'singapore': 'Singapore',
    'baku': 'Baku',
    'paul_ricard': 'Paul Ricard',
    'portimao': 'Portimao',
    'istanbul': 'Istanbul',
    'yas marina': 'Abu Dhabi',
    'yas_marina': 'Abu Dhabi',
    'yas marina circuit': 'Abu Dhabi',
    'abu dhabi': 'Abu Dhabi',
}

def resolve_circuit_id(circuit_id: str) -> str:
    """Resolve a frontend circuit ID to a backend circuit name."""
    # Try direct match first
    if circuit_id in CIRCUITS:
        return circuit_id
    # Try ID mapping
    if circuit_id in CIRCUIT_ID_MAP:
        return CIRCUIT_ID_MAP[circuit_id]
    # Try title case
    title = circuit_id.title()
    if title in CIRCUITS:
        return title
    # Try replacing underscores with spaces and title case
    spaced = circuit_id.replace('_', ' ').title()
    if spaced in CIRCUITS:
        return spaced
    return None


# API settings
API_PREFIX = "/api/v1"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
