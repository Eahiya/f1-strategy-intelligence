import json
import asyncio
import random
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.multi_car_simulator import MultiCarSimulator
from app.services.weather_system import DynamicWeatherSystem, WeatherState
from app.services.driver_manager import driver_manager
from app.models.rl_strategy_engine import RLStrategyEngine, RaceState as RLState
from app.core.config import CIRCUITS, resolve_circuit_id

router = APIRouter()


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _heuristic_action(player, weather_state: str, safety_car_active: bool, current_lap: int, total_laps: int) -> int:
    laps_remaining = max(1, total_laps - current_lap)
    tire_age = getattr(player, "tire_age", 0)
    current_tire = getattr(player, "current_tire", "medium")
    gap_ahead = getattr(player, "gap_to_ahead", 2.0)

    pit_urgency = 0.0
    pit_urgency += _clamp((tire_age - 18) / 14.0, 0.0, 1.0) * 0.55
    pit_urgency += _clamp((2.2 - gap_ahead) / 2.2, 0.0, 1.0) * 0.20
    pit_urgency += 0.20 if safety_car_active else 0.0
    pit_urgency += 0.12 if weather_state in {"light_rain", "heavy_rain"} else 0.0
    pit_urgency += _clamp((laps_remaining - 8) / total_laps, 0.0, 1.0) * 0.08

    if pit_urgency < 0.50:
        return 0
    if weather_state in {"light_rain", "heavy_rain"}:
        return 2
    if current_tire == "soft":
        return 3 if laps_remaining > 18 else 2
    if current_tire == "medium":
        return 3 if laps_remaining > 14 else 1
    return 2


def _build_dynamic_confidence(
    recommendation: Dict,
    player,
    weather_state: str,
    weather_stability: float,
    safety_car_active: bool,
    current_lap: int,
    total_laps: int
) -> Dict:
    rl_confidence = float(recommendation.get("confidence", 0.5))
    heuristic_action = _heuristic_action(player, weather_state, safety_car_active, current_lap, total_laps)
    action_match = 1.0 if int(recommendation.get("action", 0)) == heuristic_action else 0.45

    tire_age = getattr(player, "tire_age", 0)
    tire_certainty = _clamp(1.0 - (tire_age / 42.0), 0.20, 0.98)
    weather_certainty = _clamp(weather_stability, 0.20, 0.98)
    laps_remaining = max(1, total_laps - current_lap)
    late_race_uncertainty = _clamp(laps_remaining / total_laps, 0.15, 1.0)
    model_variance_proxy = _clamp(1.0 - abs(rl_confidence - 0.5) * 1.35, 0.10, 1.0)
    variance_confidence = _clamp(1.0 - model_variance_proxy, 0.10, 0.95)

    overall = (
        rl_confidence * 0.40 +
        tire_certainty * 0.22 +
        weather_certainty * 0.18 +
        action_match * 0.12 +
        late_race_uncertainty * 0.08
    )

    return {
        "overall": round(_clamp(overall, 0.05, 0.99), 3),
        "breakdown": {
            "model_confidence": round(_clamp(rl_confidence, 0.01, 0.99), 3),
            "tire_certainty": round(tire_certainty, 3),
            "weather_stability": round(weather_certainty, 3),
            "model_agreement": round(action_match, 3),
            "variance_confidence": round(variance_confidence, 3),
        }
    }


def _compute_risk_score(player, weather_snapshot, safety_car_active: bool, total_laps: int, current_lap: int) -> Dict:
    tire_age = getattr(player, "tire_age", 0)
    degradation_risk = _clamp(tire_age / 38.0, 0.0, 1.0)
    visibility = float(getattr(weather_snapshot, "visibility", 10.0))
    weather_risk = _clamp((7.5 - visibility) / 6.5, 0.0, 1.0)
    traffic_risk = _clamp((2.0 - getattr(player, "gap_to_ahead", 2.0)) / 2.0, 0.0, 1.0)
    window_pressure = _clamp((current_lap / total_laps) * 1.2, 0.0, 1.0)
    safety_car_risk = 0.18 if safety_car_active else 0.0

    overall = (
        degradation_risk * 0.36 +
        weather_risk * 0.24 +
        traffic_risk * 0.22 +
        window_pressure * 0.12 +
        safety_car_risk * 0.06
    )
    return {
        "overall": round(_clamp(overall, 0.0, 1.0), 3),
        "breakdown": {
            "tire_wear_risk": round(degradation_risk, 3),
            "weather_risk": round(weather_risk, 3),
            "traffic_risk": round(traffic_risk, 3),
            "pit_window_risk": round(window_pressure, 3),
            "safety_car_risk": round(safety_car_risk, 3),
        }
    }


async def _process_ai_pit_stops(race_sim: MultiCarSimulator, current_lap: int, weather_state: str, safety_car_active: bool, manager, session_id):
    """Handle pit stop logic for AI drivers."""
    if not race_sim or len(race_sim.drivers) <= 1:
        return

    for d in race_sim.drivers[1:]:  # Skip player (drivers[0])
        should_pit = False
        new_compound = "medium"
        
        # 1. Weather based pit stops
        is_wet = weather_state in ["light_rain", "heavy_rain"]
        is_slick = d.current_tire in ["soft", "medium", "hard"]
        
        if is_wet and is_slick:
            should_pit = True
            new_compound = "intermediate" if weather_state == "light_rain" else "wet"
        elif not is_wet and not is_slick:
            should_pit = True
            new_compound = "medium"
            
        # 2. Tire age based pit stops
        if not should_pit:
            # Drivers have different thresholds based on tire management skill (if available, else 0.5)
            tire_mgmt = getattr(d, 'tire_management', 0.5)
            base_threshold = 18 + (tire_mgmt * 10) # 18-28 range
            threshold = base_threshold + random.randint(-2, 2)
            
            if d.tire_age >= threshold:
                should_pit = True
                laps_left = race_sim.total_laps - current_lap
                if laps_left < 12:
                    new_compound = "soft"
                elif laps_left < 25:
                    new_compound = "medium"
                else:
                    new_compound = "hard"
        
        # 3. Safety car bonus
        if not should_pit and safety_car_active and d.tire_age > 10:
            if random.random() < 0.7:
                should_pit = True
                new_compound = "soft" if (race_sim.total_laps - current_lap) < 15 else "medium"

        if should_pit:
            race_sim.simulate_pit_stop(d, new_compound)
            pit_time = round(random.uniform(22.5, 25.0), 3)
            
            driver_info = driver_manager.get_driver_by_name(d.name)
            driver_code = driver_info.driver_code if driver_info else d.name[:3].upper()
            
            await manager.send_personal_message({
                "type": "pit_stop",
                "data": {
                    "driver": d.name,
                    "driver_code": driver_code,
                    "compound": new_compound,
                    "lap": current_lap,
                    "pit_time": pit_time,
                    "rejoined_position": d.position,
                }
            }, session_id)


def _compute_predicted_gain(action: str, player, risk_score: float, safety_car_active: bool) -> float:
    if not action.upper().startswith("PIT_"):
        return 0.0

    tire_age = getattr(player, "tire_age", 0)
    age_gain = _clamp((tire_age - 10) * 0.12, 0.0, 2.6)
    traffic_gain = _clamp((2.0 - getattr(player, "gap_to_ahead", 2.0)) * 0.35, 0.0, 0.7)
    safety_car_bonus = 0.8 if safety_car_active else 0.0
    risk_penalty = risk_score * 0.9
    return round(_clamp(age_gain + traffic_gain + safety_car_bonus - risk_penalty, -0.5, 3.5), 3)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].close()
            except:
                pass
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

manager = ConnectionManager()


class RaceLifecycle:
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PITTING = "PITTING"
    SAFETY_CAR = "SAFETY_CAR"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"

rl_engine = RLStrategyEngine(use_dqn=True)
try:
    rl_engine.load('models/rl_strategy/final_model.pt')
except:
    print("WS: RL model not found, using untrained engine")

class RaceEventTracker:
    def __init__(self):
        self.prev_positions: Dict[str, int] = {}
        self.prev_weather_state: Optional[str] = None
        self.prev_safety_car = False
        self.events: List[dict] = []

    def check_events(self, lap: int, drivers, weather_state, safety_car: bool) -> List[dict]:
        events = []
        for d in drivers:
            prev = self.prev_positions.get(d.driver_id)
            if prev is not None and prev != d.position:
                direction = "gained" if prev > d.position else "lost"
                change = abs(prev - d.position)
                if change >= 2:
                    events.append({
                        "type": "position_change",
                        "lap": lap,
                        "driver": d.name,
                        "message": f"{d.name} {direction} {change} positions! Now P{d.position}"
                    })
                self.prev_positions[d.driver_id] = d.position

        if self.prev_weather_state and self.prev_weather_state != weather_state:
            events.append({
                "type": "weather_change",
                "lap": lap,
                "message": f"Track conditions changed from {self.prev_weather_state} to {weather_state}"
            })
        self.prev_weather_state = weather_state

        if safety_car != self.prev_safety_car:
            if safety_car:
                events.append({
                    "type": "safety_car",
                    "lap": lap,
                    "message": "Safety Car deployed! Field bunching up."
                })
            else:
                events.append({
                    "type": "safety_car_end",
                    "lap": lap,
                    "message": "Safety Car coming in. Racing resumes next lap."
                })
            self.prev_safety_car = safety_car

        self.events.extend(events)
        return events

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)

    race_sim: Optional[MultiCarSimulator] = None
    weather_sys: Optional[DynamicWeatherSystem] = None
    is_running = False
    lifecycle_status = RaceLifecycle.IDLE
    race_task = None
    pause_event = asyncio.Event()
    pause_event.set()
    pit_lock = asyncio.Lock()

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            msg_data = data.get("data", {})

            if msg_type == "init":
                circuit = msg_data.get("circuit", "Monza").capitalize()
                laps = msg_data.get("total_laps", 53)
                weather_init = msg_data.get("weather", "dry")

                if isinstance(weather_init, dict):
                    weather_str = weather_init.get("state", "dry")
                else:
                    weather_str = weather_init

                race_sim = MultiCarSimulator(circuit, laps, num_cars=10)
                race_sim.initialize_race(weather=weather_str)

                weather_sys = DynamicWeatherSystem()
                weather_sys.initialize(
                    initial_state=WeatherState(weather_str),
                    total_laps=laps
                )

                # Build competitors list with driver codes
                init_competitors = []
                for d in race_sim.drivers:
                    driver_info = driver_manager.get_driver_by_name(d.name)
                    init_competitors.append({
                        "id": d.driver_id,
                        "driver": d.name,
                        "driver_code": driver_info.driver_code if driver_info else d.name[:3].upper(),
                        "team": d.team,
                        "team_color": driver_info.team_color if driver_info else None
                    })
                
                await manager.send_personal_message({
                    "type": "race_init",
                    "data": {
                        "circuit": circuit,
                        "total_laps": laps,
                        "weather": weather_init,
                        "scenario": msg_data.get("scenario", "normal"),
                        "competitors": init_competitors
                    }
                }, session_id)

            elif msg_type == "start_race":
                is_running = True
                lifecycle_status = RaceLifecycle.RUNNING
                pause_event.set()
                if race_sim and weather_sys:
                    if race_task and not race_task.done():
                        race_task.cancel()
                    race_task = asyncio.create_task(
                        run_race_loop(session_id, race_sim, weather_sys, pause_event, pit_lock)
                    )
                    await manager.send_personal_message({
                        "type": "race_status",
                        "data": {"status": lifecycle_status}
                    }, session_id)

            elif msg_type == "pause_race":
                lifecycle_status = RaceLifecycle.PAUSED
                pause_event.clear()
                await manager.send_personal_message({
                    "type": "race_status",
                    "data": {"status": lifecycle_status}
                }, session_id)

            elif msg_type == "resume_race":
                lifecycle_status = RaceLifecycle.RUNNING
                pause_event.set()
                await manager.send_personal_message({
                    "type": "race_status",
                    "data": {"status": lifecycle_status}
                }, session_id)

            elif msg_type == "stop_race":
                is_running = False
                lifecycle_status = RaceLifecycle.IDLE
                pause_event.set()
                if race_task:
                    race_task.cancel()

            elif msg_type == "action":
                action = msg_data.get("action") or ""
                pit_success = False
                predicted_gain = 0.0

                if race_sim and action.upper().startswith("PIT_"):
                    parts = action.split("_", 1)
                    compound = parts[1].lower() if len(parts) > 1 else "medium"
                    if compound not in {"soft", "medium", "hard"}:
                        compound = "medium"

                    try:
                        async with pit_lock:
                            lifecycle_status = RaceLifecycle.PITTING
                            await manager.send_personal_message({
                                "type": "race_status",
                                "data": {"status": lifecycle_status}
                            }, session_id)

                            player_driver = race_sim.drivers[0]
                            current_lap = race_sim.current_lap
                            if weather_sys and weather_sys.history:
                                weather_for_risk = weather_sys.history[-1]
                            elif weather_sys:
                                weather_for_risk = weather_sys.get_initial_weather()
                            else:
                                weather_for_risk = None

                            risk_score = 0.0
                            if weather_for_risk is not None:
                                risk_score = _compute_risk_score(
                                    player_driver,
                                    weather_for_risk,
                                    False,
                                    race_sim.total_laps,
                                    current_lap
                                )["overall"]
                            predicted_gain = _compute_predicted_gain(action, player_driver, risk_score, False)

                            # Execute pit stop
                            race_sim.simulate_pit_stop(player_driver, compound)
                            pit_time = round(random.uniform(22, 26), 3)

                            # Ensure lifecycle returns to RUNNING
                            lifecycle_status = RaceLifecycle.RUNNING

                            # Send pit stop completion message
                            await manager.send_personal_message({
                                "type": "pit_stop",
                                "data": {
                                    "driver": player_driver.name,
                                    "compound": compound,
                                    "lap": current_lap,
                                    "pit_time": pit_time,
                                    "rejoined_position": player_driver.position,
                                    "status": lifecycle_status,
                                }
                            }, session_id)

                            # Send race status update
                            await manager.send_personal_message({
                                "type": "race_status",
                                "data": {"status": lifecycle_status}
                            }, session_id)

                            pit_success = True
                            print(f"[Pit Stop] Completed for {player_driver.name}: {compound} tires, lap {current_lap}, P{player_driver.position}")

                    except Exception as pit_error:
                        # CRITICAL: Always ensure we return to RUNNING state
                        lifecycle_status = RaceLifecycle.RUNNING
                        print(f"[Pit Stop] Error during pit execution: {pit_error}")

                        # Notify client of error but race continues
                        await manager.send_personal_message({
                            "type": "race_status",
                            "data": {"status": lifecycle_status}
                        }, session_id)

                # Always send action received confirmation
                try:
                    await manager.send_personal_message({
                        "type": "action_received",
                        "data": {
                            "action": action,
                            "lap": race_sim.current_lap if race_sim else 0,
                            "predicted_gain": predicted_gain,
                            "decision_id": f"dec_{random.randint(1000, 9999)}",
                            "success": pit_success if action.upper().startswith("PIT_") else True
                        }
                    }, session_id)
                except Exception as send_error:
                    print(f"[Action Handler] Failed to send confirmation: {send_error}")

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(session_id)

async def run_race_loop(
    session_id: str,
    race_sim: MultiCarSimulator,
    weather_sys: DynamicWeatherSystem,
    pause_event: asyncio.Event,
    pit_lock: asyncio.Lock
):
    if not race_sim or not weather_sys:
        return

    event_tracker = RaceEventTracker()
    prev_player_pos = race_sim.drivers[0].position if race_sim.drivers else 1
    weather_change_counter = 0

    consecutive_errors = 0
    max_consecutive_errors = 3

    try:
        while race_sim.current_lap < race_sim.total_laps:
            if session_id not in manager.active_connections:
                break
            # CRITICAL FIX: Acquire lock BEFORE checking pause event
            # This ensures pit actions properly block the race loop
            async with pit_lock:
                await pause_event.wait()

                # Simulate lap with error recovery
                try:
                    weather_snapshot = weather_sys.evolve_weather(race_sim.current_lap + 1)
                    race_sim.weather = weather_snapshot.state.value
                    
                    # Calculate safety car status for this lap
                    safety_car_active = any(
                        getattr(d, 'safety_car', False) for d in race_sim.drivers
                    ) or (random.random() < (0.006 + (0.01 if weather_snapshot.state != WeatherState.DRY else 0.0)) and race_sim.current_lap > 5)

                    # Process AI pit stops BEFORE simulating the lap
                    await _process_ai_pit_stops(
                        race_sim, 
                        race_sim.current_lap, 
                        race_sim.weather, 
                        safety_car_active, 
                        manager, 
                        session_id
                    )
                    
                    lap_result = race_sim.simulate_lap()
                    consecutive_errors = 0  # Reset error count on success
                except Exception as lap_error:
                    consecutive_errors += 1
                    print(f"[Race Loop] Lap simulation error (consecutive: {consecutive_errors}): {lap_error}")
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"[Race Loop] Too many consecutive errors, stopping race loop")
                        break
                    # Skip this lap iteration but continue the race
                    await asyncio.sleep(0.5)
                    continue


            # Generate enhanced events for new components
            enhanced_events = []
            
            # Track status evolution
            if race_sim.current_lap % 10 == 0:
                enhanced_events.append({
                    "type": "track_evolution",
                    "lap": race_sim.current_lap,
                    "message": f"Track grip improving: {min(95, 60 + race_sim.current_lap)}% optimal",
                    "details": "Temperature and rubber build-up increasing grip levels"
                })

            # Dynamic incidents tied to weather and tire stress
            field_avg_tire_age = sum(d.tire_age for d in race_sim.drivers) / max(1, len(race_sim.drivers))
            incident_probability = _clamp(
                0.01 +
                (0.02 if weather_snapshot.state != WeatherState.DRY else 0.0) +
                _clamp((field_avg_tire_age - 14) / 30.0, 0.0, 0.03),
                0.01,
                0.08
            )
            if random.random() < incident_probability and race_sim.current_lap > 3:
                incident_types = ["spin", "off_track", "mechanical"]
                incident = random.choice(incident_types)
                incident_driver = random.choice(race_sim.drivers[1:])  # Not player
                enhanced_events.append({
                    "type": "incident",
                    "lap": race_sim.current_lap,
                    "message": f"Incident: {incident_driver.name} {incident.replace('_', ' ')}",
                    "details": f"Driver {incident_driver.name} reported {incident} at turn {random.randint(1, 15)}",
                    "driver": incident_driver.name,
                    "location": f"Turn {random.randint(1, 15)}",
                    "severity": "medium" if incident in ["spin", "off_track"] else "high"
                })

            # Driver behavior events using live profile traits
            if race_sim.current_lap % 4 == 0:
                personality_driver = max(
                    race_sim.drivers[1:],
                    key=lambda d: (d.aggression * 0.55 + (1.0 - d.consistency) * 0.45)
                )
                personality = "aggressive" if personality_driver.aggression > 0.72 else "measured"
                enhanced_events.append({
                    "type": "driver_behavior",
                    "lap": race_sim.current_lap,
                    "message": f"{personality_driver.name} showing {personality} racing style",
                    "details": f"Driver adapting strategy based on {personality} approach",
                    "driver": personality_driver.name,
                    "personality": personality
                })

            events = event_tracker.check_events(
                race_sim.current_lap, race_sim.drivers,
                weather_snapshot.state.value, safety_car_active
            )
            weather_change_counter += sum(1 for event in events if event.get("type") == "weather_change")
            
            # Merge enhanced events with existing events
            events.extend(enhanced_events)

            player = race_sim.drivers[0]
            ahead = next((d for d in race_sim.drivers if d.position == player.position - 1), None)
            behind = next((d for d in race_sim.drivers if d.position == player.position + 1), None)

            rl_state = RLState(
                lap_number=race_sim.current_lap,
                total_laps=race_sim.total_laps,
                tire_age=player.tire_age,
                tire_compound={'soft': 0, 'medium': 1, 'hard': 2}.get(player.current_tire, 0),
                current_position=player.position,
                gap_to_ahead=player.gap_to_ahead,
                gap_to_behind=behind.gap_to_ahead if behind else 5.0,
                gap_to_leader=player.gap_to_leader,
                weather_condition=0 if weather_snapshot.state == WeatherState.DRY else 1,
                track_temperature=weather_snapshot.track_temp,
                safety_car_active=safety_car_active,
                fuel_load=50.0 * (1 - race_sim.current_lap / race_sim.total_laps),
                tire_degradation=player.tire_age * 0.05,
                track_evolution=race_sim.current_lap * 0.001
            )

            recommendation = rl_engine.predict(rl_state)

            lap_results_by_id = {r['driver'].driver_id: r for r in lap_result['results']}

            competitors = []
            for d in race_sim.drivers:
                # Get driver code from driver_manager
                driver_info = driver_manager.get_driver_by_name(d.name)
                driver_code = driver_info.driver_code if driver_info else d.name[:3].upper()
                team_color = driver_info.team_color if driver_info else None
                
                competitors.append({
                    "id": d.driver_id,
                    "driver": d.name,
                    "driver_code": driver_code,
                    "team": d.team,
                    "team_color": team_color,
                    "position": d.position,
                    "gap_to_leader": round(d.gap_to_leader, 3),
                    "tire_compound": d.current_tire,
                    "tire_age": d.tire_age,
                    "lap_time": round(lap_results_by_id.get(d.driver_id, {}).get('lap_time', 90.0), 3)
                })

            player_result = lap_results_by_id.get(player.driver_id, {})

            risk_data = _compute_risk_score(
                player=player,
                weather_snapshot=weather_snapshot,
                safety_car_active=safety_car_active,
                total_laps=race_sim.total_laps,
                current_lap=race_sim.current_lap
            )
            confidence_data = _build_dynamic_confidence(
                recommendation=recommendation,
                player=player,
                weather_state=weather_snapshot.state.value,
                weather_stability=1.0 - _clamp(weather_change_counter / max(1, race_sim.current_lap), 0.0, 0.9),
                safety_car_active=safety_car_active,
                current_lap=race_sim.current_lap,
                total_laps=race_sim.total_laps
            )

            decision_outcome = None
            if prev_player_pos != player.position:
                position_change = prev_player_pos - player.position
                expected_gain = _clamp(confidence_data["overall"] * 1.8 - risk_data["overall"] * 1.2, -2.0, 2.0)
                realized_gain = float(position_change)
                decision_outcome = {
                    "lap": race_sim.current_lap,
                    "position_change": position_change,
                    "regret": round(expected_gain - realized_gain, 3)
                }
                prev_player_pos = player.position

            try:
                await manager.send_personal_message({
                    "type": "lap_update",
                    "data": {
                        "lap": race_sim.current_lap,
                        "player": {
                            "position": player.position,
                            "gap_to_leader": round(player.gap_to_leader, 3),
                            "tire_compound": player.current_tire,
                            "tire_age": player.tire_age,
                            "lap_time": round(player_result.get('lap_time', 90.0), 3),
                            "tire_degradation": player.tire_age * 0.05,
                            "tire_uncertainty": round(_clamp(player.tire_age / 45.0, 0.02, 0.45), 3)
                        },
                        "competitors": competitors,
                        "weather": {
                            "state": weather_snapshot.state.value,
                            "temp": weather_snapshot.track_temp
                        },
                        "safety_car_active": safety_car_active,
                        "events": events if events else None,
                        "recommendation": recommendation,
                        "decision_outcome": decision_outcome,
                        "metrics": {
                            "tire_deg": player.tire_age * 0.05,
                            "fuel": round(50.0 * (1 - race_sim.current_lap / race_sim.total_laps), 1),
                            "track_temp": weather_snapshot.track_temp,
                            "risk_score": risk_data["overall"],
                            "risk_breakdown": risk_data["breakdown"]
                        },
                        "confidence": confidence_data
                    }
                }, session_id)
            except Exception:
                break

            await asyncio.sleep(1.5)

        try:
            await manager.send_personal_message({
                "type": "race_finished",
                "data": {
                    "total_laps": race_sim.total_laps,
                    "final_position": race_sim.drivers[0].position,
                    "analysis": "Elite performance observed. Strategic depth utilized."
                }
            }, session_id)
        except Exception:
            pass
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Race loop error: {e}")
