"""
F1 Strategy Platform v5.0 - FastF1 Integration
Client for retrieving real F1 race data using the FastF1 library.
"""
import logging
import threading
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

import os

try:
    import fastf1
    CACHE_DIR = "./f1_cache"
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        fastf1.Cache.enable_cache(CACHE_DIR)
        logger.info(f"FastF1 cache successfully initialized at: {CACHE_DIR}")
        FASTF1_AVAILABLE = True
    except Exception as e:
        logger.error(f"Failed to initialize FastF1 cache directory: {e}. Real data disabled.")
        FASTF1_AVAILABLE = False
except ImportError:
    FASTF1_AVAILABLE = False
    logger.warning("FastF1 not installed. Real data features will be unavailable.")


CIRCUIT_MAPPING = {
    'monza': 'Italy', 'spa': 'Belgium', 'silverstone': 'Great Britain',
    'red_bull_ring': 'Austria', 'spielberg': 'Austria',
    'interlagos': 'Brazil', 'suzuka': 'Japan',
    'bahrain': 'Bahrain', 'jeddah': 'Saudi Arabia', 'miami': 'Miami',
    'barcelona': 'Spain', 'catalunya': 'Spain',
    'monaco': 'Monaco', 'hungaroring': 'Hungary',
    'villeneuve': 'Canada', 'montreal': 'Canada',
    'zandvoort': 'Netherlands', 'marina_bay': 'Singapore', 'singapore': 'Singapore',
    'americas': 'United States', 'austin': 'United States',
    'rodriguez': 'Mexico', 'mexico_city': 'Mexico',
    'yas_marina': 'Abu Dhabi', 'abu_dhabi': 'Abu Dhabi',
    'losail': 'Qatar', 'qatar': 'Qatar',
    'baku': 'Azerbaijan',
    'ricard': 'France', 'paul_ricard': 'France',
    'imola': 'Emilia Romagna',
    'nurburgring': 'Eifel',
    'mugello': 'Tuscany',
    'portimao': 'Portugal',
    'istanbul': 'Turkey',
    'melbourne': 'Australia',
    'shanghai': 'China',
    'las_vegas': 'Las Vegas',
}


@dataclass
class RaceSession:
    year: int
    round_num: int
    circuit: str
    session_type: str
    laps: Optional[pd.DataFrame] = None
    weather: Optional[pd.DataFrame] = None
    results: Optional[pd.DataFrame] = None


@dataclass
class DriverTelemetry:
    driver: str
    team: str
    lap_times: List[float]
    sector_times: Dict[str, List[float]]
    tire_data: Dict[str, Any]
    positions: List[int]

    def get_average_pace(self) -> float:
        return float(np.mean(self.lap_times)) if self.lap_times else 0.0

    def get_pace_consistency(self) -> float:
        return float(np.std(self.lap_times)) if len(self.lap_times) >= 2 else 0.0


class FastF1Client:
    def __init__(self, cache_dir: str = "./f1_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._session_cache: Dict[str, Any] = {}

    def is_available(self) -> bool:
        return FASTF1_AVAILABLE

    def _resolve_circuit(self, circuit: str, year: int = 2023) -> str:
        key = circuit.lower().replace(' ', '_')
        if key in CIRCUIT_MAPPING:
            return CIRCUIT_MAPPING[key]
        return circuit

    def load_session(self, year: int, circuit: str, session_type: str = 'R', timeout: int = 30) -> Optional[RaceSession]:
        cache_key = f"{year}_{circuit}_{session_type}"
        if cache_key in self._session_cache:
            return self._session_cache[cache_key]

        if not FASTF1_AVAILABLE:
            return None

        ff1_event = self._resolve_circuit(circuit, year)
        result = [None]

        def _load():
            try:
                session = fastf1.get_session(year, ff1_event, session_type)
                session.load(laps=True, telemetry=False, weather=False, messages=False)
                laps_copy = session.laps.copy() if hasattr(session, 'laps') and session.laps is not None else None
                results_copy = session.results.copy() if hasattr(session, 'results') else None
                result[0] = RaceSession(
                    year=year,
                    round_num=int(session.event.get('RoundNumber', 0)),
                    circuit=str(session.event.get('EventName', ff1_event)),
                    session_type=session_type,
                    laps=laps_copy,
                    results=results_copy,
                )
            except Exception as e:
                logger.error(f"FastF1 session load failed: {e}")

        thread = threading.Thread(target=_load, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            logger.warning(f"FastF1 load timeout for {year} {circuit} ({ff1_event})")
            return None

        if result[0]:
            self._session_cache[cache_key] = result[0]
        return result[0]

    def get_driver_telemetry(self, session: RaceSession, driver: str) -> Optional[DriverTelemetry]:
        if not session or session.laps is None:
            return None
        try:
            driver_laps = session.laps.pick_driver(driver)
            if driver_laps.empty:
                return None

            def _to_seconds(series):
                if series is None or series.empty:
                    return []
                if hasattr(series.dt, 'total_seconds'):
                    return series.dt.total_seconds().tolist()
                return series.tolist()

            return DriverTelemetry(
                driver=driver,
                team=str(driver_laps['Team'].iloc[0]) if 'Team' in driver_laps.columns else 'Unknown',
                lap_times=_to_seconds(driver_laps['LapTime']) if 'LapTime' in driver_laps.columns else [],
                sector_times={
                    'S1': _to_seconds(driver_laps['Sector1Time']),
                    'S2': _to_seconds(driver_laps['Sector2Time']),
                    'S3': _to_seconds(driver_laps['Sector3Time']),
                },
                tire_data={
                    'compounds': driver_laps['Compound'].unique().tolist() if 'Compound' in driver_laps.columns else [],
                    'stints': self._calculate_stints(driver_laps),
                },
                positions=driver_laps['Position'].dropna().astype(int).tolist() if 'Position' in driver_laps.columns else [],
            )
        except Exception as e:
            logger.error(f"Driver telemetry failed: {e}")
            return None

    def _calculate_stints(self, laps: pd.DataFrame) -> List[Dict]:
        if 'Compound' not in laps.columns or 'Stint' not in laps.columns:
            return []
        stints = []
        for stint_num in laps['Stint'].unique():
            stint_laps = laps[laps['Stint'] == stint_num]
            if not stint_laps.empty:
                stints.append({
                    'number': int(stint_num),
                    'compound': stint_laps['Compound'].iloc[0],
                    'laps': len(stint_laps),
                    'start_lap': int(stint_laps['LapNumber'].iloc[0]) if 'LapNumber' in stint_laps.columns else 0,
                    'end_lap': int(stint_laps['LapNumber'].iloc[-1]) if 'LapNumber' in stint_laps.columns else 0,
                })
        return stints

    def get_circuit_info(self, circuit: str, year: int = 2023) -> Dict:
        if not FASTF1_AVAILABLE:
            return {"name": circuit, "round": 0, "country": "Unknown", "location": "Unknown"}
        try:
            ff1_event = self._resolve_circuit(circuit, year)
            schedule = fastf1.get_event_schedule(year)
            match = schedule[schedule['EventName'].str.contains(ff1_event, case=False, na=False)]
            if not match.empty:
                return {
                    "name": str(match.iloc[0]['EventName']),
                    "round": int(match.iloc[0]['RoundNumber']),
                    "country": str(match.iloc[0]['Country']),
                    "location": str(match.iloc[0]['Location']),
                }
        except Exception as e:
            logger.warning(f"Circuit info failed: {e}")
        return {"name": circuit, "round": 0, "country": "Unknown", "location": "Unknown"}

    def get_historical_strategies(self, circuit: str, years: List[int] = None) -> List[Dict]:
        if years is None:
            years = [2023, 2022]
        strategies = []
        for year in years:
            try:
                session = self.load_session(year, circuit, 'R', timeout=25)
                if session and session.laps is not None:
                    winner = self._get_race_winner(session)
                    if winner:
                        telemetry = self.get_driver_telemetry(session, winner)
                        if telemetry:
                            strategies.append({
                                "year": year,
                                "winner": winner,
                                "stints": telemetry.tire_data.get('stints', []),
                                "compounds": telemetry.tire_data.get('compounds', []),
                                "avg_pace": round(telemetry.get_average_pace(), 3),
                                "num_pit_stops": max(0, len(telemetry.tire_data.get('stints', [])) - 1),
                            })
            except Exception as e:
                logger.warning(f"Historical strategy failed for {year} {circuit}: {e}")
        return strategies

    def _get_race_winner(self, session: RaceSession) -> Optional[str]:
        if session.results is not None and not session.results.empty:
            winner = session.results[session.results['Position'] == 1]
            if not winner.empty:
                return str(winner.iloc[0]['Abbreviation'])
        if session.laps is not None and not session.laps.empty:
            last_lap = session.laps['LapNumber'].max()
            final = session.laps[session.laps['LapNumber'] == last_lap]
            if not final.empty:
                p1 = final[final['Position'] == 1]
                if not p1.empty:
                    return str(p1.iloc[0]['Driver'])
        return None


class RealDataProvider:
    def __init__(self, client: FastF1Client = None):
        self.client = client or FastF1Client()
        self._deg_cache: Dict[str, Optional[pd.DataFrame]] = {}

    def get_tire_degradation_data(self, circuit: str, compound: str, min_laps: int = 5) -> Optional[pd.DataFrame]:
        cache_key = f"{circuit}_{compound}"
        if cache_key in self._deg_cache:
            return self._deg_cache[cache_key]

        if not self.client.is_available():
            return None

        try:
            session = self.client.load_session(2023, circuit, 'R', timeout=15)
            if not session or session.laps is None:
                self._deg_cache[cache_key] = None
                return None

            compound_laps = session.laps[session.laps['Compound'] == compound]
            if compound_laps.empty or len(compound_laps) < min_laps:
                self._deg_cache[cache_key] = None
                return None

            rows = []
            for driver in compound_laps['Driver'].unique():
                dlaps = compound_laps[compound_laps['Driver'] == driver].copy()
                dlaps['TireAge'] = dlaps.groupby('Stint').cumcount() + 1
                rows.append(dlaps[['LapNumber', 'LapTime', 'TireAge', 'Driver']])

            if rows:
                combined = pd.concat(rows, ignore_index=True)
                if pd.api.types.is_timedelta64_dtype(combined['LapTime']):
                    combined['LapTimeSeconds'] = combined['LapTime'].dt.total_seconds()
                else:
                    combined['LapTimeSeconds'] = combined['LapTime']
                self._deg_cache[cache_key] = combined
                return combined
        except Exception as e:
            logger.error(f"Degradation data failed: {e}")

        self._deg_cache[cache_key] = None
        return None

    def validate_prediction_against_real(self, predicted_time: float, circuit: str, year: int = 2023) -> Dict:
        try:
            session = self.client.load_session(year, circuit, 'R', timeout=20)
            if not session or session.results is None:
                return {"status": "no_data", "message": "Real data unavailable"}
            winner = self.client._get_race_winner(session)
            if not winner:
                return {"status": "no_winner"}
            winner_laps = session.laps[session.laps['Driver'] == winner] if session.laps is not None else None
            if winner_laps is None or winner_laps.empty:
                return {"status": "no_laps"}
            actual_time = winner_laps['LapTime'].dt.total_seconds().sum()
            diff = predicted_time - actual_time
            pct = (diff / actual_time) * 100
            return {
                "status": "validated", "predicted_time": predicted_time,
                "actual_time": round(actual_time, 2), "difference_seconds": round(diff, 2),
                "percentage_error": round(pct, 2), "winner": winner,
                "accuracy": "good" if abs(pct) < 5 else "fair" if abs(pct) < 10 else "poor",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
