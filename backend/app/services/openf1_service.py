"""
OpenF1 Service — F1 Strategy Platform v6.5
==========================================
Safe, cached, rate-limited client for the OpenF1 REST API.

Design principles:
  - NEVER spam the OpenF1 API (max 2 req/s, 25 req/min internally)
  - Aggressive in-memory TTL cache (60s live, 300s historical)
  - Retry with exponential backoff (3 attempts)
  - Graceful degradation — always returns data or None, never raises
  - Normalized schemas compatible with existing frontend types
  - Non-blocking: all methods are async

Rate limits (free tier): 3 req/sec, 30 req/min
We operate at 2 req/sec, 25 req/min to stay comfortably within limits.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

OPENF1_BASE = "https://api.openf1.org/v1"

# Cache TTLs (seconds)
CACHE_TTL_LIVE = 60        # Live session data — refresh every minute
CACHE_TTL_HISTORICAL = 300  # Historical data — refresh every 5 minutes
CACHE_TTL_SESSION = 120     # Session info — refresh every 2 minutes

# Rate limiting
MAX_RPS = 2          # requests per second
MAX_RPM = 25         # requests per minute
REQUEST_TIMEOUT = 8  # seconds per request
MAX_RETRIES = 3      # retry attempts
BACKOFF_BASE = 1.5   # exponential backoff multiplier

# Team colors mapping (fallback when not provided by API)
TEAM_COLORS: Dict[str, str] = {
    "Mercedes":         "#00D2BE",
    "Red Bull Racing":  "#1E41FF",
    "Ferrari":          "#E8002D",
    "McLaren":          "#FF8000",
    "Aston Martin":     "#006F62",
    "Alpine":           "#0090FF",
    "Williams":         "#005AFF",
    "Haas F1 Team":     "#B6BABD",
    "RB":               "#2B4562",
    "Kick Sauber":      "#52E252",
    "Alfa Romeo":       "#900000",
}

COMPOUND_COLORS: Dict[str, str] = {
    "SOFT":         "#FF3333",
    "MEDIUM":       "#FFD700",
    "HARD":         "#FFFFFF",
    "INTERMEDIATE": "#39B54A",
    "WET":          "#0067FF",
}


# ─── Cache Entry ──────────────────────────────────────────────────────────────

class CacheEntry:
    """Simple TTL-based cache entry."""
    __slots__ = ("data", "expires_at")

    def __init__(self, data: Any, ttl: float) -> None:
        self.data = data
        self.expires_at = time.monotonic() + ttl

    @property
    def is_fresh(self) -> bool:
        return time.monotonic() < self.expires_at


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, max_rps: float = MAX_RPS) -> None:
        self._max_rps = max_rps
        self._min_interval = 1.0 / max_rps
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


# ─── OpenF1 Client ────────────────────────────────────────────────────────────

class OpenF1Service:
    """
    Async client for the OpenF1 REST API.

    Usage:
        service = OpenF1Service()
        session = await service.get_latest_session()
        positions = await service.get_positions(session_key)
    """

    def __init__(self) -> None:
        self._cache: Dict[str, CacheEntry] = {}
        self._rate_limiter = RateLimiter()
        self._session = None  # aiohttp.ClientSession — lazy init
        self._lock = asyncio.Lock()
        self._available = True  # flipped to False on repeated failures
        self._fail_count = 0
        self._max_fails = 5

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def _get_session(self):
        """Lazily create aiohttp session."""
        if self._session is None or self._session.closed:
            try:
                import aiohttp
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "F1StrategyPlatform/6.5",
                    }
                )
            except ImportError:
                logger.error("[OpenF1] aiohttp not installed — OpenF1 integration disabled")
                self._available = False
        return self._session

    async def close(self) -> None:
        """Cleanly close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Core Fetch ────────────────────────────────────────────────────────────

    async def _fetch(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        ttl: float = CACHE_TTL_LIVE,
    ) -> Optional[List[Dict]]:
        """
        Fetch from OpenF1 API with caching, rate limiting, and retries.
        Returns None on any failure — never raises.
        """
        if not self._available:
            return None

        # Build cache key
        param_str = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
        cache_key = f"{endpoint}?{param_str}"

        # Return cached data if fresh
        entry = self._cache.get(cache_key)
        if entry and entry.is_fresh:
            return entry.data

        # Rate limit
        await self._rate_limiter.acquire()

        # Fetch with retries
        session = await self._get_session()
        if session is None:
            return None

        url = f"{OPENF1_BASE}/{endpoint.lstrip('/')}"
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 429:
                        # Rate limited by server — back off longer
                        wait = BACKOFF_BASE ** (attempt + 2)
                        logger.warning(f"[OpenF1] Rate limited, backing off {wait:.1f}s")
                        await asyncio.sleep(wait)
                        continue

                    if resp.status == 200:
                        data = await resp.json()
                        self._cache[cache_key] = CacheEntry(data, ttl)
                        self._fail_count = 0
                        self._available = True
                        return data

                    if resp.status in (404, 422):
                        # No data for these params — cache empty result
                        self._cache[cache_key] = CacheEntry([], ttl)
                        return []

                    logger.warning(f"[OpenF1] HTTP {resp.status} for {endpoint}")
                    last_error = f"HTTP {resp.status}"

            except asyncio.TimeoutError:
                last_error = "Timeout"
                logger.warning(f"[OpenF1] Timeout on {endpoint} (attempt {attempt + 1})")
            except Exception as exc:
                last_error = str(exc)
                logger.warning(f"[OpenF1] Error on {endpoint}: {exc} (attempt {attempt + 1})")

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(BACKOFF_BASE ** attempt)

        # All attempts failed
        self._fail_count += 1
        if self._fail_count >= self._max_fails:
            logger.error("[OpenF1] Too many failures — temporarily disabling")
            self._available = False
            # Re-enable after 5 minutes
            asyncio.get_event_loop().call_later(300, self._reset_availability)

        logger.error(f"[OpenF1] Failed to fetch {endpoint} after {MAX_RETRIES} attempts: {last_error}")
        # Return stale cached data if available
        if entry:
            return entry.data
        return None

    def _reset_availability(self) -> None:
        """Re-enable after cooldown."""
        self._available = True
        self._fail_count = 0
        logger.info("[OpenF1] Service re-enabled after cooldown")

    # ── Session ───────────────────────────────────────────────────────────────

    async def get_latest_session(self) -> Optional[Dict]:
        """Get the latest/current F1 session."""
        data = await self._fetch("sessions", ttl=CACHE_TTL_SESSION)
        if not data:
            return None
        # Return the most recent session
        try:
            return sorted(data, key=lambda s: s.get("date_start", ""), reverse=True)[0]
        except (IndexError, KeyError):
            return None

    async def get_session_by_key(self, session_key: int) -> Optional[Dict]:
        """Get a specific session by key."""
        data = await self._fetch(
            "sessions",
            params={"session_key": session_key},
            ttl=CACHE_TTL_HISTORICAL,
        )
        return data[0] if data else None

    # ── Drivers ───────────────────────────────────────────────────────────────

    async def get_drivers(self, session_key: Optional[int] = None) -> List[Dict]:
        """Get driver info for a session."""
        params = {}
        if session_key:
            params["session_key"] = session_key
        data = await self._fetch("drivers", params=params, ttl=CACHE_TTL_HISTORICAL)
        return data or []

    # ── Positions ─────────────────────────────────────────────────────────────

    async def get_positions(
        self,
        session_key: Optional[int] = None,
        latest_only: bool = True,
    ) -> List[Dict]:
        """Get driver positions. With latest_only, returns current standings."""
        params: Dict[str, Any] = {}
        if session_key:
            params["session_key"] = session_key
        data = await self._fetch("position", params=params)
        if not data:
            return []

        if latest_only:
            # Get the most recent position entry per driver
            latest: Dict[int, Dict] = {}
            for entry in data:
                dn = entry.get("driver_number")
                if dn is None:
                    continue
                existing = latest.get(dn)
                if existing is None or entry.get("date", "") > existing.get("date", ""):
                    latest[dn] = entry
            return sorted(latest.values(), key=lambda x: x.get("position", 99))
        return data

    # ── Laps ──────────────────────────────────────────────────────────────────

    async def get_laps(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None,
    ) -> List[Dict]:
        """Get lap data with optional filters."""
        params: Dict[str, Any] = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        if lap_number:
            params["lap_number"] = lap_number
        data = await self._fetch("laps", params=params, ttl=CACHE_TTL_LIVE)
        return data or []

    # ── Intervals ─────────────────────────────────────────────────────────────

    async def get_intervals(self, session_key: Optional[int] = None) -> List[Dict]:
        """Get live timing intervals between drivers."""
        params: Dict[str, Any] = {}
        if session_key:
            params["session_key"] = session_key
        data = await self._fetch("intervals", params=params)
        return data or []

    # ── Pit Stops ─────────────────────────────────────────────────────────────

    async def get_pit_stops(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
    ) -> List[Dict]:
        """Get pit stop data."""
        params: Dict[str, Any] = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        data = await self._fetch("pit", params=params, ttl=CACHE_TTL_LIVE)
        return data or []

    # ── Car Telemetry ─────────────────────────────────────────────────────────

    async def get_car_data(
        self,
        driver_number: int,
        session_key: Optional[int] = None,
        latest_only: bool = True,
    ) -> Optional[Dict]:
        """Get car telemetry (speed, throttle, brake, DRS, RPM)."""
        params: Dict[str, Any] = {"driver_number": driver_number}
        if session_key:
            params["session_key"] = session_key
        data = await self._fetch("car_data", params=params)
        if not data:
            return None
        if latest_only:
            return sorted(data, key=lambda x: x.get("date", ""), reverse=True)[0]
        return data

    # ── Location (GPS) ────────────────────────────────────────────────────────

    async def get_location(
        self,
        driver_number: int,
        session_key: Optional[int] = None,
        latest_only: bool = True,
    ) -> Optional[Dict]:
        """Get driver GPS location on track."""
        params: Dict[str, Any] = {"driver_number": driver_number}
        if session_key:
            params["session_key"] = session_key
        data = await self._fetch("location", params=params)
        if not data:
            return None
        if latest_only:
            return sorted(data, key=lambda x: x.get("date", ""), reverse=True)[0]
        return data

    # ── Race Control ──────────────────────────────────────────────────────────

    async def get_race_control(self, session_key: Optional[int] = None) -> List[Dict]:
        """Get race control messages (flags, SC, VSC, incidents)."""
        params: Dict[str, Any] = {}
        if session_key:
            params["session_key"] = session_key
        data = await self._fetch("race_control", params=params)
        return data or []

    # ── Weather ───────────────────────────────────────────────────────────────

    async def get_weather(self, session_key: Optional[int] = None) -> Optional[Dict]:
        """Get latest weather data."""
        params: Dict[str, Any] = {}
        if session_key:
            params["session_key"] = session_key
        data = await self._fetch("weather", params=params)
        if not data:
            return None
        return sorted(data, key=lambda x: x.get("date", ""), reverse=True)[0]

    # ── Stints (Tire compounds) ───────────────────────────────────────────────

    async def get_stints(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
    ) -> List[Dict]:
        """Get tire stint data including compounds."""
        params: Dict[str, Any] = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        data = await self._fetch("stints", params=params, ttl=CACHE_TTL_LIVE)
        return data or []

    # ── Normalized Composite Data ─────────────────────────────────────────────

    async def get_normalized_timing_tower(
        self,
        session_key: Optional[int] = None,
    ) -> List[Dict]:
        """
        Returns a normalized timing tower compatible with frontend CompetitorPanel format.
        Merges: positions + intervals + stints + laps.
        """
        positions, intervals, stints, drivers = await asyncio.gather(
            self.get_positions(session_key),
            self.get_intervals(session_key),
            self.get_stints(session_key),
            self.get_drivers(session_key),
        )

        # Index by driver_number
        interval_map: Dict[int, Dict] = {
            e.get("driver_number"): e for e in intervals if e.get("driver_number")
        }
        driver_map: Dict[int, Dict] = {
            d.get("driver_number"): d for d in drivers if d.get("driver_number")
        }

        # Latest stint per driver
        stint_map: Dict[int, Dict] = {}
        for stint in stints:
            dn = stint.get("driver_number")
            if dn is None:
                continue
            existing = stint_map.get(dn)
            if existing is None or stint.get("stint_number", 0) > existing.get("stint_number", 0):
                stint_map[dn] = stint

        result = []
        for pos_entry in positions:
            dn = pos_entry.get("driver_number")
            drv = driver_map.get(dn, {})
            interval_entry = interval_map.get(dn, {})
            stint_entry = stint_map.get(dn, {})

            team = drv.get("team_name", "")
            compound = stint_entry.get("compound", "").upper()
            tire_age = stint_entry.get("tyre_age_at_start", 0) or 0

            result.append({
                "id": dn,
                "driver": drv.get("full_name", f"Driver {dn}"),
                "driver_code": drv.get("name_acronym", "???"),
                "team": team,
                "team_color": drv.get("team_colour") or TEAM_COLORS.get(team, "#888888"),
                "position": pos_entry.get("position", 99),
                "gap_to_leader": _parse_gap(interval_entry.get("gap_to_leader")),
                "interval": _parse_gap(interval_entry.get("interval")),
                "tire_compound": compound.lower() if compound else "medium",
                "tire_age": tire_age,
                "drs_active": False,  # Requires car_data; omit for tower
                "in_pit": False,
                "source": "openf1",
            })

        return sorted(result, key=lambda x: x["position"])

    async def get_normalized_race_control(
        self,
        session_key: Optional[int] = None,
    ) -> List[Dict]:
        """
        Returns race control messages normalized to frontend RaceDirectorFeed format.
        """
        messages = await self.get_race_control(session_key)
        result = []
        for msg in messages:
            category = msg.get("category", "").lower()
            flag = msg.get("flag", "").lower()
            msg_text = msg.get("message", "")
            date_str = msg.get("date", "")

            # Map to frontend message types
            msg_type = "race_control"
            if flag in ("yellow", "double yellow"):
                msg_type = "incident"
            elif flag in ("red",):
                msg_type = "flag"
            elif "safety car" in msg_text.lower():
                msg_type = "safety_car"
            elif "virtual" in msg_text.lower():
                msg_type = "vsc"
            elif category == "weather":
                msg_type = "weather"

            result.append({
                "id": f"openf1-{date_str}",
                "type": msg_type,
                "text": msg_text,
                "details": f"Category: {category}" if category else None,
                "time": _format_time(date_str),
                "lap": msg.get("lap_number"),
                "priority": "high" if flag in ("red", "yellow", "double yellow") else "normal",
                "source": "openf1",
                "flag": flag,
                "driver_number": msg.get("driver_number"),
                "scope": msg.get("scope", "Track"),
                "sector": msg.get("sector"),
            })

        return sorted(result, key=lambda x: x.get("time", ""), reverse=True)

    async def get_normalized_weather(
        self,
        session_key: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Returns weather data normalized to frontend WeatherForecastPanel format.
        """
        weather = await self.get_weather(session_key)
        if not weather:
            return None

        rainfall = weather.get("rainfall", 0)
        track_temp = weather.get("track_temperature", 0)
        air_temp = weather.get("air_temperature", 0)
        humidity = weather.get("humidity", 0)
        wind_speed = weather.get("wind_speed", 0)
        wind_dir = weather.get("wind_direction", 0)

        weather_state = "dry"
        if rainfall and float(rainfall) > 0:
            weather_state = "wet" if float(rainfall) > 1.0 else "mixed"

        return {
            "state": weather_state,
            "track_temp": round(float(track_temp), 1) if track_temp else 0,
            "air_temp": round(float(air_temp), 1) if air_temp else 0,
            "humidity": round(float(humidity), 1) if humidity else 0,
            "wind_speed": round(float(wind_speed), 1) if wind_speed else 0,
            "wind_direction": int(wind_dir) if wind_dir else 0,
            "rainfall": round(float(rainfall), 2) if rainfall else 0,
            "source": "openf1",
            "timestamp": weather.get("date"),
        }

    async def get_session_info(self) -> Dict:
        """
        Returns session availability information for the frontend mode selector.
        """
        session = await self.get_latest_session()
        if not session:
            return {
                "available": False,
                "session_key": None,
                "session_name": "No session",
                "circuit": "Unknown",
                "status": "offline",
                "is_live": False,
            }

        session_name = session.get("session_name", "Unknown")
        circuit = session.get("circuit_short_name", session.get("location", "Unknown"))
        date_start = session.get("date_start", "")
        date_end = session.get("date_end", "")

        # Determine if live
        now = datetime.now(timezone.utc).isoformat()
        is_live = bool(date_start and date_end and date_start <= now <= date_end)

        return {
            "available": True,
            "session_key": session.get("session_key"),
            "session_name": session_name,
            "circuit": circuit,
            "status": "live" if is_live else "historical",
            "is_live": is_live,
            "date_start": date_start,
            "date_end": date_end,
            "year": session.get("year"),
            "country": session.get("country_name", ""),
        }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_gap(value: Any) -> float:
    """Parse a gap string like '+1.234' or an int/float."""
    if value is None:
        return 0.0
    try:
        s = str(value).replace("+", "").strip()
        if s.upper() == "LAP" or s.upper() == "LAPS":
            return 999.0
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _format_time(date_str: str) -> str:
    """Format ISO datetime to HH:MM:SS."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return date_str[:8] if date_str else ""


# ─── Singleton ────────────────────────────────────────────────────────────────

# Module-level singleton — shared across all requests
_openf1_service: Optional[OpenF1Service] = None


def get_openf1_service() -> OpenF1Service:
    """Get or create the singleton OpenF1Service."""
    global _openf1_service
    if _openf1_service is None:
        _openf1_service = OpenF1Service()
    return _openf1_service
