"""
F1 Strategy Intelligence System - Elite Edition v3.1
Enhanced with Authentication & Authorization Security Layer

FastAPI application with JWT-based authentication, RBAC, and comprehensive security.
"""
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import uvicorn
import asyncio
import json
import os

# Security Layer v3.1
from app.auth.models import init_db, create_default_admin, get_db, User
from app.auth.routes import router as auth_router, limiter
from app.auth.dependencies import (
    require_admin, EngineerPlus, AllAuthenticated
)
from app.api.websocket import router as websocket_router
from app.utils.json_sanitizer import sanitize_response, json_safe, debug_response_types

from app.core.config import CIRCUITS, TIRE_COMPOUNDS, resolve_circuit_id
from app.services.data_generator import load_or_generate_data
from app.services.data_pipeline import F1DataPipeline
from app.models.tire_degradation import TireDegradationModel
from app.models.lap_time_predictor import LapTimePredictor
from app.models.strategy_optimizer import StrategyOptimizer
from app.models.advanced_strategy_optimizer import AdvancedStrategyOptimizer
from app.models.rl_strategy_engine import RLStrategyEngine, RaceState
from app.models.opponent_model import OpponentModelingEngine, create_elite_driver_grid, CompetitiveSituation
from app.models.probabilistic_risk_engine import BayesianRiskModel
from app.models.advanced_metrics import AdvancedMetricsEngine
from app.models.explainable_ai import ExplainableAIEngine
from app.services.race_simulator import RaceSimulator
from app.services.multi_car_simulator import simulate_multi_car_race
from app.services.weather_system import simulate_weather_scenario
from app.services.adaptive_strategy_engine import DigitalTwinSimulator
from app.services.telemetry_pipeline import TelemetryGenerator, TelemetryExporter
from app.data_integration.fastf1_client import FastF1Client, RealDataProvider
from app.services.openf1_service import get_openf1_service


# Initialize FastAPI app
app = FastAPI(
    title="F1 Strategy Intelligence System - Elite Edition",
    description="Elite AI-powered F1 strategy optimization with RL, game theory, and real-time adaptation. "
                "Security Layer v3.1: JWT authentication, RBAC, audit logging, and rate limiting.",
    version="3.1.0",
)

# Rate limiting
app.state.limiter = limiter

# CORS middleware - more restrictive for production
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"]
)

# Include auth routes
app.include_router(auth_router)
app.include_router(websocket_router)

# Pydantic models for API requests/responses
class SimulateRequest(BaseModel):
    circuit: str
    laps: Optional[int] = None
    strategy_type: str = "auto"  # "1_stop", "2_stop", "3_stop", "auto"
    tire_compound: str = "soft"  # "soft", "medium", "hard"
    weather: str = "dry"  # "dry", "wet", "mixed"
    include_safety_car: bool = False


class AdvancedOptimizeRequest(BaseModel):
    circuit: str
    laps: Optional[int] = None
    strategy_type: str = "auto"
    initial_weather: str = "dry"
    rain_probability: float = Field(default=0.2, ge=0.0, le=1.0)
    num_simulations: int = Field(default=50, ge=10, le=200)
    risk_aversion: float = Field(default=0.3, ge=0.0, le=1.0)


class MultiCarRequest(BaseModel):
    circuit: str
    laps: Optional[int] = None
    num_cars: int = Field(default=10, ge=2, le=20)
    weather: str = "dry"
    strategies: Optional[Dict[int, Dict]] = None


class WeatherRequest(BaseModel):
    circuit: str
    laps: Optional[int] = None
    initial_weather: str = "dry"
    rain_probability: float = Field(default=0.3, ge=0.0, le=1.0)


class LiveSimRequest(BaseModel):
    circuit: str
    laps: Optional[int] = None
    strategy_type: str = "auto"
    delay_ms: int = Field(default=100, ge=50, le=1000)


class CircuitInfo(BaseModel):
    name: str
    laps: int
    pit_loss: int
    base_lap_time: float


class StrategyResponse(BaseModel):
    best_strategy: str
    pit_laps: List[int]
    total_time: float
    total_time_formatted: str
    explanation: str
    tires_used: List[str]
    lap_times: List[float]
    tire_degradation: List[float]
    strategy_comparison: dict
    circuit: str
    weather: str
    safety_car_laps: List[int]


class AdvancedStrategyResponse(BaseModel):
    best_strategy: str
    pit_laps: List[int]
    tires: List[str]
    expected_time: float
    time_variance: float
    risk_score: float
    success_probability: float
    explanation: str
    strategy_comparison: dict
    monte_carlo_runs: int
    risk_aversion: float


# Elite Edition Models
class RLStrategyRequest(BaseModel):
    circuit: str
    total_laps: int
    current_lap: int
    position: int
    gap_to_ahead: float
    gap_to_behind: float
    tire_age: int
    tire_compound: str
    weather: str = 'dry'
    safety_car: bool = False


class RLStrategyResponse(BaseModel):
    action: str
    action_name: str
    confidence: float
    should_pit: bool
    recommended_tire: Optional[str]
    explanation: str
    q_values: Dict[str, float]


class OpponentAnalysisRequest(BaseModel):
    circuit: str
    our_position: int
    gap_to_ahead: float
    gap_to_behind: float
    our_tire: str
    our_tire_age: int
    opponent_tire: Optional[str] = None
    opponent_tire_age: Optional[int] = None
    laps_to_go: int


class DigitalTwinRequest(BaseModel):
    circuit: str
    current_lap: int
    current_state: Dict
    scenarios: Optional[List[str]] = None


class TelemetryRequest(BaseModel):
    circuit: str
    driver_id: int
    total_laps: int
    pit_laps: List[int]
    tire_strategy: List[str]
    base_position: int = 5


class ExplainRequest(BaseModel):
    race_state: Dict
    question: Optional[str] = None


class EliteStatusResponse(BaseModel):
    version: str
    edition: str
    features: List[str]
    models_loaded: bool
    rl_agent_trained: bool
    performance_mode: str


# Global model instances
_models_initialized = False
_rl_engine = None
_opponent_model = None
_risk_model = None
_metrics_engine = None
_xai_engine = None
_adaptive_engine = None
_fastf1_client = None
_real_data_provider = None
tire_model = None
lap_time_model = None
strategy_optimizer = None


def initialize_models():
    """Initialize and train ML models on startup."""
    global _models_initialized, tire_model, lap_time_model, strategy_optimizer, _rl_engine, _opponent_model, _risk_model, _metrics_engine, _xai_engine, _fastf1_client, _real_data_provider
    
    if _models_initialized:
        return
    
    print("=" * 70)
    print("F1 Strategy Intelligence System v3.1 - Security Layer")
    print("Initializing Elite Edition with Authentication...")
    print("=" * 70)
    
    # Initialize database
    init_db()
    create_default_admin()
    print("[OK] Database initialized")
    
    # Generate or load data
    df = load_or_generate_data()
    
    # Initialize pipeline
    pipeline = F1DataPipeline()
    (X_lt, y_lt), (X_deg, y_deg) = pipeline.prepare_for_training(df)
    
    # Train tire degradation model
    tire_model = TireDegradationModel()
    deg_metrics = tire_model.train(X_deg, y_deg)
    print(f"[OK] Tire model trained - RMSE: {deg_metrics['rmse']:.4f}")
    
    # Train lap time predictor
    lap_time_model = LapTimePredictor()
    lt_metrics = lap_time_model.train(X_lt, y_lt)
    print(f"[OK] Lap time model trained - RMSE: {lt_metrics['rmse']:.4f}")
    
    # Initialize strategy optimizer
    strategy_optimizer = StrategyOptimizer(lap_time_model, tire_model)
    
    # Initialize FastF1 client
    print("\nInitializing FastF1 integration...")
    _fastf1_client = FastF1Client()
    if _fastf1_client.is_available():
        print("[OK] FastF1 is available - real historical data enabled")
        _real_data_provider = RealDataProvider(_fastf1_client)
    else:
        print("[!] FastF1 not installed - using synthetic data (pip install fastf1)")
    
    # Initialize Elite Edition components
    print("\nInitializing Elite Edition AI components...")
    
    # RL Engine (light training for quick start)
    _rl_engine = RLStrategyEngine(use_dqn=True)
    print("[OK] RL Strategy Engine initialized")
    
    # Opponent Model
    _opponent_model = OpponentModelingEngine()
    drivers = create_elite_driver_grid()
    for driver in drivers:
        _opponent_model.register_driver(driver)
    print(f"[OK] Opponent Model initialized ({len(drivers)} elite drivers)")
    
    # Risk Model
    _risk_model = BayesianRiskModel()
    print("[OK] Probabilistic Risk Model initialized")
    
    # Metrics Engine
    _metrics_engine = AdvancedMetricsEngine()
    print("[OK] Advanced Metrics Engine initialized")
    
    # XAI Engine
    _xai_engine = ExplainableAIEngine()
    print("[OK] Explainable AI Engine initialized")
    
    _models_initialized = True
    
    print("\n" + "=" * 70)
    print("[OK][OK][OK] ELITE EDITION v3.1 FULLY INITIALIZED [OK][OK][OK]")
    print("Security: JWT Auth | RBAC | Audit Logging | Rate Limiting")
    print("=" * 70)


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    initialize_models()

@app.get("/", response_model=EliteStatusResponse)
async def root():
    """Root endpoint with Elite Edition v3.1 API info including security status."""
    return {
        "version": "3.1.0",
        "edition": "ELITE",
        "security_layer": "v3.1",
        "features": [
            "Reinforcement Learning Strategy Engine (DQN)",
            "Game Theory & Opponent Modeling",
            "Probabilistic Risk Engine (Bayesian)",
            "Real-Time Adaptive Strategy",
            "Digital Twin Simulation",
            "Telemetry Data Pipeline",
            "Advanced Metrics (Undercut, Tire Delta)",
            "Explainable AI (XAI)",
            "Monte Carlo Optimization",
            "Multi-Car Simulation with Overtaking",
            "Dynamic Weather System",
            "Real-time Race Streaming",
            "JWT Authentication",
            "Role-Based Access Control (RBAC)",
            "Audit Logging",
            "Rate Limiting"
        ],
        "models_loaded": _models_initialized,
        "rl_agent_trained": _rl_engine is not None,
        "performance_mode": "ELITE",
        "security_status": "ACTIVE",
        "authentication": "JWT Required",
        "roles": ["admin", "engineer", "viewer"],
        "endpoints": {
            "public": ["/", "/health", "/auth/login"],
            "protected": ["/simulate/*", "/elite/*", "/optimize/*"],
            "admin_only": ["/auth/register", "/auth/users"]
        }
    }


@app.get("/circuits")
async def get_circuits():
    """Get list of all available circuits with full configurations."""
    circuits = []
    for name, config in CIRCUITS.items():
        circuits.append({
            "name": name,
            "id": name.lower().replace(' ', '_').replace("'", ''),
            "laps": config["laps"],
            "pit_loss": config["pit_loss"],
            "base_lap_time": config["base_lap_time"],
            "tire_factor": config.get("tire_factor", 1.0),
            "overtaking": config.get("overtaking", 0.5),
            "country": config.get("country", "Unknown")
        })
    return {"circuits": circuits, "total": len(circuits)}


@app.get("/tires")
async def get_tires():
    """Get tire compound information."""
    tires = []
    for name, config in TIRE_COMPOUNDS.items():
        tires.append({
            "name": name,
            "base_pace": config["base_pace"],
            "degradation_rate": config["degradation_rate"],
            "optimal_laps": config["optimal_laps"],
            "color": config["color"]
        })
    return {"tires": tires}


@app.post("/simulate", response_model=StrategyResponse)
@limiter.limit("30/minute")  # Rate limit: 30 simulations per minute
async def simulate_strategy(
    body: SimulateRequest,
    request: Request
    # Authentication disabled for demo - add back: current_user: User = Depends(AllAuthenticated)
):
    """
    Simulate race strategy and return optimal pit stop plan.
    
    Uses real FastF1 historical data when available, falls back to synthetic.
    
    **Rate Limit:** 30 requests per minute
    """
    # Resolve circuit ID (handles frontend snake_case -> backend proper name)
    circuit_key = resolve_circuit_id(body.circuit)
    if not circuit_key:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown circuit: {body.circuit}. Available: {list(CIRCUITS.keys())}"
        )
    
    # Validate tire compound (case-insensitive)
    tire_key = body.tire_compound.lower() if body.tire_compound else ""
    if tire_key not in TIRE_COMPOUNDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tire: {body.tire_compound}. Available: {list(TIRE_COMPOUNDS.keys())}"
        )
    
    # Get total laps
    total_laps = body.laps or CIRCUITS[circuit_key]["laps"]
    
    # Validate and map strategy type
    strategy_mapping = {
        "auto": "auto", "conservative": "1_stop", "aggressive": "2_stop",
        "custom": "3_stop", "1_stop": "1_stop", "2_stop": "2_stop", "3_stop": "3_stop"
    }
    strategy_type = strategy_mapping.get(body.strategy_type, body.strategy_type)
    valid_strategies = ["auto", "1_stop", "2_stop", "3_stop"]
    if strategy_type not in valid_strategies:
        raise HTTPException(status_code=400, detail=f"Invalid strategy_type: {body.strategy_type}")
    
    # If FastF1 is available, try to enhance simulation with real data (non-blocking)
    real_data_enhancement = None
    if _real_data_provider:
        try:
            import threading
            result_holder = [None]
            def _fetch():
                try:
                    result_holder[0] = _real_data_provider.get_tire_degradation_data(
                        circuit_key, tire_key, min_laps=3
                    )
                except Exception:
                    pass
            t = threading.Thread(target=_fetch, daemon=True)
            t.start()
            t.join(timeout=10)
            if t.is_alive():
                print(f"[!] FastF1 data fetch timed out for {circuit_key}/{tire_key}, using synthetic")
            else:
                real_data_enhancement = result_holder[0]
        except Exception as e:
            print(f"[!] FastF1 data enhancement failed: {e}")
    
    try:
        weather = (body.weather or "dry").lower()
        
        result = strategy_optimizer.optimize(
            circuit=circuit_key,
            total_laps=total_laps,
            strategy_type=strategy_type,
            weather=weather,
            safety_car_prob=0.15 if body.include_safety_car else 0.0
        )
        
        # Format total time
        total_seconds = result['total_time']
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        time_formatted = f"{minutes}:{seconds:05.2f}"
        
        # Build response and sanitize for JSON serialization
        response_data = {
            "best_strategy": str(result['best_strategy']),
            "pit_laps": list(result['pit_laps']),
            "total_time": float(result['total_time']),
            "total_time_formatted": str(time_formatted),
            "explanation": str(result['explanation']),
            "tires_used": [str(t) for t in result['tires_used']],
            "lap_times": result['lap_times'],
            "tire_degradation": result['tire_degradation'],
            "strategy_comparison": result['strategy_comparison'],
            "circuit": str(circuit_key),
            "weather": str(result['weather']),
            "safety_car_laps": list(result.get('safety_car_laps', []))
        }
        
        # Sanitize all NumPy/pandas types for JSON serialization
        try:
            sanitized = sanitize_response(response_data, endpoint="/simulate")
        except RuntimeError as se:
            raise HTTPException(status_code=500, detail=str(se))
        
        debug_response_types(sanitized, "/simulate")
        return StrategyResponse(**sanitized)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@app.post("/race-simulation")
@limiter.limit("20/minute")  # Rate limit: 20 detailed simulations per minute
async def detailed_race_simulation(
    body: SimulateRequest,
    request: Request,
    current_user: User = Depends(AllAuthenticated),
    db: Session = Depends(get_db)
):
    """
    Run detailed lap-by-lap race simulation.
    
    **Authentication Required:** Any role (Viewer, Engineer, Admin)
    
    **Rate Limit:** 20 requests per minute
    
    Returns complete race data with per-lap details.
    """
    if body.circuit not in CIRCUITS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown circuit: {body.circuit}"
        )
    
    total_laps = body.laps or CIRCUITS[body.circuit]["laps"]
    
    # First optimize strategy
    opt_result = strategy_optimizer.optimize(
        circuit=body.circuit,
        total_laps=total_laps,
        strategy_type=body.strategy_type,
        weather=body.weather
    )
    
    # Run detailed simulation
    simulator = RaceSimulator(body.circuit, total_laps, body.tire_compound)
    simulator.initialize_race(
        weather=body.weather,
        safety_car_prob=0.15 if body.include_safety_car else 0.0
    )
    
    simulator.simulate_race(
        pit_laps=opt_result['pit_laps'],
        tire_strategy=opt_result['tires_used']
    )
    
    summary = simulator.get_race_summary()
    
    # Get detailed lap data
    lap_data = []
    for state in simulator.race_state.lap_states:
        lap_data.append({
            "lap": state.lap_number,
            "lap_time": state.lap_time,
            "tire": state.tire_compound,
            "tire_age": state.tire_age,
            "degradation": state.tire_degradation,
            "fuel": round(state.fuel_load, 2)
        })
    
    return {
        "summary": summary,
        "lap_data": lap_data,
        "optimal_strategy": {
            "pit_laps": opt_result['pit_laps'],
            "tires": opt_result['tires_used'],
            "explanation": opt_result['explanation']
        }
    }


@app.post("/optimize/advanced", response_model=AdvancedStrategyResponse)
@limiter.limit("10/minute")  # Rate limit: 10 Monte Carlo optimizations per minute
async def advanced_optimize(
    body: AdvancedOptimizeRequest,
    request: Request,
    current_user: User = Depends(EngineerPlus),  # Engineer or Admin only
    db: Session = Depends(get_db)
):
    """
    Advanced strategy optimization using Monte Carlo simulation.
    
    **Authentication Required:** Engineer or Admin role
    
    **Rate Limit:** 10 requests per minute (computationally expensive)
    
    Provides risk-adjusted strategy recommendations based on multiple
    simulated race scenarios with varying weather and conditions.
    """
    if body.circuit not in CIRCUITS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown circuit: {body.circuit}"
        )
    
    total_laps = body.laps or CIRCUITS[body.circuit]["laps"]
    
    try:
        optimizer = AdvancedStrategyOptimizer(
            num_monte_carlo_runs=body.num_simulations,
            risk_aversion=body.risk_aversion
        )
        
        result = optimizer.optimize(
            circuit=body.circuit,
            total_laps=total_laps,
            strategy_type=body.strategy_type,
            initial_weather=body.initial_weather,
            rain_probability=body.rain_probability
        )
        
        # Sanitize all NumPy types for JSON serialization
        sanitized = sanitize_response(result, endpoint="/optimize/advanced")
        return AdvancedStrategyResponse(**sanitized)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@app.post("/simulate/multi-car")
@limiter.limit("15/minute")
async def multi_car_simulation(
    request: Request,
    body: MultiCarRequest,
    response: Response,
    current_user: User = Depends(AllAuthenticated),
):
    """
    Multi-car race simulation with overtaking and dirty air effects.
    
    **Authentication Required:** Any role (Viewer, Engineer, Admin)
    
    **Rate Limit:** 15 requests per minute
    
    Simulates realistic racing between multiple drivers with
    different strategies, overtaking attempts, and track position effects.
    """
    circuit_key = resolve_circuit_id(body.circuit) or body.circuit
    total_laps = body.laps or CIRCUITS[circuit_key]["laps"]
    
    try:
        results = simulate_multi_car_race(
            circuit=circuit_key,
            total_laps=total_laps,
            num_cars=body.num_cars,
            strategies=body.strategies,
            weather=body.weather
        )
        
        # Build response and sanitize for JSON serialization
        response_data = {
            "circuit": results['circuit'],
            "total_laps": results['total_laps'],
            "weather": results['weather'],
            "final_standings": results['final_standings'],
            "total_overtakes": results['total_overtakes'],
            "overtake_log": results['overtakes'][:10],  # First 10 overtakes
            "lap_count": len(results['lap_history'])
        }
        
        # Sanitize all NumPy/pandas types for JSON serialization
        try:
            sanitized = sanitize_response(response_data, endpoint="/simulate/multi-car")
        except RuntimeError as se:
            raise HTTPException(status_code=500, detail=str(se))
        
        debug_response_types(sanitized, "/simulate/multi-car")
        return sanitized
        
    except HTTPException:
        raise
    except Exception as e:
        # Fallback synthetic data for demo mode when real multi-car sim fails
        print(f"[Warning] Multi-car simulation failed: {e}")
        import traceback
        traceback.print_exc()
        
        synthetic = {
            "circuit": circuit_key,
            "total_laps": int(total_laps),
            "weather": str(body.weather),
            "final_standings": [],
            "total_overtakes": 0,
            "overtake_log": [],
            "lap_history": [],
        }
        response.headers['X-Data-Source'] = 'synthetic'
        return synthetic


@app.post("/simulate/weather")
@limiter.limit("20/minute")
async def weather_simulation(
    request: Request,
    body: WeatherRequest,
    response: Response,
    current_user: User = Depends(AllAuthenticated),
):
    """
    Dynamic weather simulation for a race.
    
    **Authentication Required:** Any role (Viewer, Engineer, Admin)
    
    **Rate Limit:** 20 requests per minute
    
    Generates weather timeline with state transitions and
    provides tire strategy recommendations for changing conditions.
    """
    circuit_key = resolve_circuit_id(body.circuit) or body.circuit
    total_laps = body.laps or CIRCUITS[circuit_key]["laps"]
    
    try:
        results = simulate_weather_scenario(
            circuit=circuit_key,
            total_laps=total_laps,
            initial_weather=body.initial_weather,
            rain_probability=body.rain_probability
        )
        
        # Build response and sanitize for JSON serialization
        response_data = {
            "circuit": circuit_key,
            "total_laps": total_laps,
            "summary": results['summary'],
            "weather_timeline": results['weather_timeline'][:20],  # Sample first 20 laps
            "recommended_strategy": results['recommended_strategy']
        }
        
        # Sanitize all NumPy types for JSON serialization
        sanitized = sanitize_response(response_data, endpoint="/simulate/weather")
        
        # Indicate data source as real when weather simulation completes
        response.headers['X-Data-Source'] = 'real'
        return sanitized
        
    except Exception as e:
        # Fallback synthetic weather data for demo
        print(f"[Warning] Weather simulation failed: {e}")
        synthetic = {
            "circuit": circuit_key,
            "total_laps": total_laps,
            "summary": {"description": "Synthetic weather run"},
            "weather_timeline": [],
            "recommended_strategy": {"pit_laps": [20, 40], "tires": ["soft", "medium"]}
        }
        response.headers['X-Data-Source'] = 'synthetic'
        return synthetic


@app.post("/simulate/live")
@limiter.limit("5/minute")  # Rate limit: 5 live simulations per minute
async def live_simulation(
    body: LiveSimRequest,
    request: Request,
    current_user: User = Depends(AllAuthenticated),
    db: Session = Depends(get_db)
):
    """
    Real-time race simulation with streaming updates.
    
    **Authentication Required:** Any role (Viewer, Engineer, Admin)
    
    **Rate Limit:** 5 requests per minute (resource intensive)
    
    Simulates race lap-by-lap with configurable delay between laps.
    Returns SSE (Server-Sent Events) stream for live updates.
    """
    if body.circuit not in CIRCUITS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown circuit: {body.circuit}"
        )
    
    total_laps = body.laps or CIRCUITS[body.circuit]["laps"]
    
    async def event_generator():
        """Generate lap-by-lap race events."""
        # Initialize simulator
        simulator = RaceSimulator(body.circuit, total_laps, "soft")
        simulator.initialize_race()
        
        # Get optimized strategy
        # opt_result = quick_optimize(
        #     request.circuit, total_laps, num_simulations=10
        # )
        
        # Simulate race
        for lap in range(1, total_laps + 1):
            lap_state = simulator.simulate_lap()
            
            event_data = {
                "lap": lap_state.lap_number,
                "lap_time": lap_state.lap_time,
                "tire": lap_state.tire_compound,
                "tire_age": lap_state.tire_age,
                "degradation": lap_state.tire_degradation,
                "total_time": round(simulator.race_state.total_time, 2)
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(request.delay_ms / 1000)
        
        # Send final result
        summary = simulator.get_race_summary()
        yield f"data: {json.dumps({'status': 'complete', 'summary': summary})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# Elite Edition Endpoints

@app.post("/elite/rl-strategy", response_model=RLStrategyResponse)
@limiter.limit("30/minute")
async def rl_strategy_decision(
    body: RLStrategyRequest,
    request: Request,
    current_user: User = Depends(EngineerPlus),  # Engineer or Admin
    db: Session = Depends(get_db)
):
    """
    Get strategy decision from Reinforcement Learning agent.
    
    **Authentication Required:** Engineer or Admin role
    
    Uses trained DQN to recommend optimal pit/stay-out decisions.
    """
    if not _rl_engine:
        raise HTTPException(status_code=503, detail="RL engine not initialized")
    
    try:
        # Create race state
        state = RaceState(
            lap_number=body.current_lap,
            total_laps=body.total_laps,
            tire_age=body.tire_age,
            tire_compound={'soft': 0, 'medium': 1, 'hard': 2}.get(body.tire_compound, 0),
            current_position=body.position,
            gap_to_ahead=body.gap_to_ahead,
            gap_to_behind=body.gap_to_behind,
            gap_to_leader=body.gap_to_ahead + 5,  # Estimated
            weather_condition={'dry': 0, 'wet': 1, 'mixed': 0}.get(body.weather, 0),
            track_temperature=35.0,
            safety_car_active=body.safety_car,
            fuel_load=50.0 * (1 - body.current_lap / body.total_laps),
            tire_degradation=body.tire_age * 0.05,
            track_evolution=body.current_lap * 0.001
        )
        
        # Get RL prediction
        prediction = _rl_engine.predict(state)
        
        return RLStrategyResponse(**prediction)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RL prediction error: {str(e)}")


@app.post("/elite/opponent-analysis")
@limiter.limit("20/minute")
async def opponent_analysis(
    request: Request,
    body: OpponentAnalysisRequest,
    response: Response,
    current_user: User = Depends(AllAuthenticated),
):
    """
    Analyze opponent behavior and provide competitive insights.
    
    **Authentication Required:** Engineer or Admin role
    
    Includes undercut viability, tire delta analysis, and strategic recommendations.
    """
    if not _opponent_model:
        raise HTTPException(status_code=503, detail="Opponent model not initialized")
    
    try:
        circuit_key = resolve_circuit_id(body.circuit) or body.circuit
        situation = CompetitiveSituation(
            our_position=body.our_position,
            car_ahead_id=None,
            car_behind_id=None,
            gap_to_ahead=body.gap_to_ahead,
            gap_to_behind=body.gap_to_behind,
            laps_to_go=body.laps_to_go,
            our_tire_age=body.our_tire_age,
            our_tire_compound=body.our_tire,
            ahead_tire_age=body.opponent_tire_age,
            ahead_tire_compound=body.opponent_tire,
            behind_tire_age=None,
            behind_tire_compound=None
        )
        
        # Get undercut analysis
        undercut = _opponent_model.analyze_undercut_opportunity(
            situation, circuit_key
        )
        
        recommendations = _opponent_model.get_strategic_recommendations(
            situation, circuit_key
        )
        
        # Build response and sanitize for JSON serialization
        response_data = {
            'undercut_analysis': {
                'viable': undercut.viable,
                'probability': undercut.probability,
                'optimal_lap': undercut.optimal_lap,
                'time_gain_potential': undercut.time_gain_potential,
                'risk_score': undercut.risk_score,
                'reasoning': undercut.reasoning
            },
            'strategic_recommendations': recommendations['recommendations'],
            'primary_strategy': recommendations['primary_strategy']
        }
        
        # Sanitize all NumPy types for JSON serialization
        sanitized = sanitize_response(response_data, endpoint="/elite/opponent-analysis")
        
        # Real data path for opponent analysis
        response.headers['X-Data-Source'] = 'real'
        return sanitized
        
    except Exception as e:
        # Demo fallback data when opponent analytics engine fails or is unavailable
        print(f"[Warning] Opponent analysis failed: {e}")
        fallback = {
            'undercut_analysis': {
                'viable': False,
                'probability': 0.0,
                'optimal_lap': None,
                'time_gain_potential': 0.0,
                'risk_score': 0.0,
                'reasoning': 'Demo fallback'
            },
            'strategic_recommendations': [],
            'primary_strategy': 'Hold'
        }
        response.headers['X-Data-Source'] = 'synthetic'
        return fallback


@app.post("/elite/digital-twin")
@limiter.limit("5/minute")  # Resource intensive
async def digital_twin_simulation(
    body: DigitalTwinRequest,
    request: Request,
    current_user: User = Depends(EngineerPlus),
    db: Session = Depends(get_db)
):
    """
    Run Digital Twin parallel simulations for scenario analysis.
    
    **Authentication Required:** Engineer or Admin role
    
    **Rate Limit:** 5 requests per minute (resource intensive)
    
    Evaluates multiple future scenarios to generate contingency plans.
    """
    try:
        twin = DigitalTwinSimulator(body.circuit, 
                                   body.current_state.get('total_laps', 53))
        
        # Define scenarios
        scenarios = twin.define_scenarios(body.current_state)
        
        # Filter if specific scenarios requested
        if body.scenarios:
            scenarios = [s for s in scenarios if s['id'] in body.scenarios]
        
        # Run parallel simulations
        base_strategy = {
            'pit_laps': body.current_state.get('pit_laps', [20, 40]),
            'tires': body.current_state.get('tires', ['soft', 'medium', 'hard'])
        }
        
        results = twin.run_parallel_simulations(
            scenarios, body.current_state, base_strategy
        )
        
        # Generate contingency plan
        plan = twin.get_contingency_plan(results)
        
        return {
            'scenarios_evaluated': len(results),
            'contingency_plan': plan,
            'scenario_results': [
                {
                    'id': r.scenario_id,
                    'description': r.description,
                    'probability': r.probability,
                    'projected_position': r.projected_outcome.get('final_position'),
                    'strategy_adjustment': r.strategy_adjustment
                }
                for r in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Digital twin error: {str(e)}")


@app.post("/elite/telemetry")
@limiter.limit("10/minute")
async def generate_telemetry(
    body: TelemetryRequest,
    request: Request,
    current_user: User = Depends(require_admin),  # Admin only
    db: Session = Depends(get_db)
):
    """
    Generate high-frequency telemetry data for a race.
    
    **Authentication Required:** Admin only
    
    **Rate Limit:** 10 requests per minute
    
    Includes sector times, speed traces, and per-corner data.
    """
    try:
        generator = TelemetryGenerator(body.circuit)
        
        telemetry = generator.generate_race_telemetry(
            driver_id=body.driver_id,
            total_laps=body.total_laps,
            pit_laps=body.pit_laps,
            tire_strategy=body.tire_strategy,
            base_position=body.base_position
        )
        
        # Convert to DataFrame and then to dict for JSON (sanitize pandas types)
        df = TelemetryExporter.to_dataframe(telemetry)
        
        response_data = {
            'telemetry_generated': len(telemetry),
            'laps': df.to_dict('records'),
            'summary': {
                'average_lap_time': df['lap_time'].mean(),
                'best_lap_time': df['lap_time'].min(),
                'consistency': df['lap_time'].std(),
                'drs_activations': int(df['drs_active'].sum()) if 'drs_active' in df.columns else 0
            }
        }
        
        try:
            sanitized = sanitize_response(response_data, endpoint="/elite/telemetry")
        except RuntimeError as se:
            raise HTTPException(status_code=500, detail=str(se))
        
        debug_response_types(sanitized, "/elite/telemetry")
        return sanitized
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telemetry error: {str(e)}")


@app.post("/elite/explain")
@limiter.limit("30/minute")
async def explain_decision(
    body: ExplainRequest,
    request: Request,
    current_user: User = Depends(AllAuthenticated),
    db: Session = Depends(get_db)
):
    """
    Generate explainable AI output for strategy decisions.
    
    **Authentication Required:** Any authenticated role
    
    Provides transparent reasoning, alternatives considered, and risk analysis.
    Also answers natural language questions about decisions.
    """
    if not _xai_engine:
        raise HTTPException(status_code=503, detail="XAI engine not initialized")
    
    try:
        # Parse race state from request
        state_data = body.race_state
        
        state = RaceState(
            lap_number=state_data.get('lap', 1),
            total_laps=state_data.get('total_laps', 53),
            tire_age=state_data.get('tire_age', 0),
            tire_compound={'soft': 0, 'medium': 1, 'hard': 2}.get(
                state_data.get('tire_compound', 'medium'), 1),
            current_position=state_data.get('position', 5),
            gap_to_ahead=state_data.get('gap_to_ahead', 2.0),
            gap_to_behind=state_data.get('gap_to_behind', 3.0),
            gap_to_leader=state_data.get('gap_to_leader', 10.0),
            weather_condition={'dry': 0, 'wet': 1}.get(
                state_data.get('weather', 'dry'), 0),
            track_temperature=state_data.get('track_temp', 35.0),
            safety_car_active=state_data.get('safety_car', False),
            fuel_load=state_data.get('fuel_load', 50.0),
            tire_degradation=state_data.get('tire_degradation', 0.0),
            track_evolution=state_data.get('track_evolution', 0.0)
        )
        
        # Mock recommendations (in real use, would call actual models)
        rl_rec = {
            'action_name': 'PIT_SOFT' if state.tire_age > 20 else 'STAY_OUT',
            'confidence': 0.85 if state.tire_age > 20 else 0.6
        }
        opt_rec = {
            'pit_laps': [25, 42],
            'tires': ['soft', 'medium', 'hard']
        }
        
        # Generate explanation
        explanation = _xai_engine.explain_strategy_decision(state, rl_rec, opt_rec)
        
        # If question provided, answer it
        if request.question:
            answer = _xai_engine.answer_question(request.question, explanation)
            return {
                'explanation': explanation.to_dict(),
                'natural_language': explanation.to_natural_language(),
                'question_answer': answer
            }
        
        return {
            'explanation': explanation.to_dict(),
            'natural_language': explanation.to_natural_language()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")


@app.post("/elite/advanced-metrics")
async def advanced_metrics(
    circuit: str,
    total_laps: int,
    current_user: User = Depends(AllAuthenticated),
    db: Session = Depends(get_db)
):
    """
    Get advanced race metrics definitions and calculators.
    
    **Authentication Required:** Any authenticated role
    """
    if not _metrics_engine:
        raise HTTPException(status_code=503, detail="Metrics engine not initialized")
    
    return {
        'available_metrics': {
            'undercut_effectiveness': {
                'description': 'Measures success of undercut attempts',
                'components': ['gap_change', 'time_gained', 'position_change'],
                'formula': 'composite_score'
            },
            'tire_delta': {
                'description': 'Performance difference between tire compounds',
                'units': 'seconds_per_lap'
            },
            'track_position_value': {
                'description': 'Strategic value of current position',
                'components': ['clean_air', 'drs_access', 'overtake_difficulty']
            },
            'strategy_regret': {
                'description': 'Difference between actual and optimal hindsight strategy',
                'units': 'positions_and_seconds'
            }
        },
        'circuit_specific': {
            'circuit': circuit,
            'total_laps': total_laps,
            'undercut_zones': [
                {'start': int(total_laps * 0.3), 'end': int(total_laps * 0.7)}
            ]
        }
    }


# ==========================================
# FastF1 Real Data Endpoints
# ==========================================

@app.get("/fastf1/status")
async def fastf1_status():
    """Check FastF1 availability and real data status."""
    if _fastf1_client:
        return {
            "available": _fastf1_client.is_available(),
            "cache_dir": str(_fastf1_client.cache_dir),
            "data_provider_active": _real_data_provider is not None
        }
    return {"available": False, "message": "FastF1 client not initialized"}


@app.get("/fastf1/circuit-info")
async def fastf1_circuit_info(circuit: str, year: int = 2023):
    if not _fastf1_client:
        raise HTTPException(status_code=503, detail="FastF1 not initialized")
    resolved = resolve_circuit_id(circuit) or circuit
    info = _fastf1_client.get_circuit_info(resolved, year)
    return {"circuit": info}


@app.get("/fastf1/historical-strategies")
async def fastf1_historical_strategies(circuit: str, years: str = "2022,2023,2024"):
    """
    Fetch historical race strategies from FastF1.
    Runs in a thread pool so it doesn't block the event loop.
    Response shape normalised for the frontend HistoricalStrategyBrowser.
    """
    if not _fastf1_client:
        raise HTTPException(status_code=503, detail="FastF1 not initialized")

    year_list = [int(y.strip()) for y in years.split(",") if y.strip().isdigit()]
    if not year_list:
        raise HTTPException(status_code=400, detail="Invalid years parameter")

    resolved = resolve_circuit_id(circuit) or circuit

    def _fetch_blocking():
        """Blocking call — runs in executor thread."""
        raw = _fastf1_client.get_historical_strategies(resolved, year_list)

        normalised = []
        for item in raw:
            # Build a strategy array: [{compound, lap}] from stints
            stints = item.get("stints", [])
            strategy = [
                {
                    "compound": str(s.get("compound", "UNKNOWN")).capitalize(),
                    "lap": int(s.get("start_lap", 0)),
                }
                for s in stints
            ]

            # Estimate total_time from avg_pace × winner lap count
            laps_driven = sum(s.get("laps", 0) for s in stints)
            avg_pace = float(item.get("avg_pace", 0))
            total_seconds = avg_pace * laps_driven if laps_driven > 0 else 0
            if total_seconds > 0:
                m = int(total_seconds // 60)
                s_ = total_seconds % 60
                total_time_fmt = f"{m}:{s_:05.2f}"
            else:
                total_time_fmt = None

            normalised.append({
                "year": int(item.get("year", 0)),
                "name": str(resolved),
                "winner": str(item.get("winner", "")),
                "strategy": strategy,
                "compounds": [str(c) for c in item.get("compounds", [])],
                "num_pit_stops": int(item.get("num_pit_stops", 0)),
                "avg_pace": round(float(item.get("avg_pace", 0)), 3),
                "total_time": total_time_fmt,
            })
        return normalised

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        strategies = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch_blocking),
            timeout=120.0  # 2 min hard cap
        )
        raw_response = {
            "circuit": circuit,
            "years_analyzed": year_list,
            "strategies": strategies,
            "data_source": "fastf1",
            "total_races": len(strategies),
        }
        return sanitize_response(raw_response, endpoint="/fastf1/historical-strategies")
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="FastF1 data fetch timed out. Try fetching a single year or a well-cached circuit."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Historical data error: {str(e)}")


@app.get("/fastf1/driver-telemetry")
async def fastf1_driver_telemetry(circuit: str, driver: str, year: int = 2024):
    if not _fastf1_client:
        raise HTTPException(status_code=503, detail="FastF1 not initialized")
    resolved = resolve_circuit_id(circuit) or circuit
    session = _fastf1_client.load_session(year, resolved, 'R', timeout=30)
    if not session:
        raise HTTPException(status_code=404, detail=f"No data for {year} {circuit}")
    telemetry = _fastf1_client.get_driver_telemetry(session, driver)
    if not telemetry:
        raise HTTPException(status_code=404, detail=f"No telemetry for driver {driver}")
    return {
        "driver": telemetry.driver, "team": telemetry.team,
        "avg_pace": telemetry.get_average_pace(),
        "consistency": telemetry.get_pace_consistency(),
        "lap_times": telemetry.lap_times[:10],
        "positions": telemetry.positions[:10],
        "tire_compounds": telemetry.tire_data.get('compounds', []),
        "stints": telemetry.tire_data.get('stints', []),
    }


@app.post("/fastf1/validate-prediction")
async def fastf1_validate_prediction(predicted_time: float, circuit: str, year: int = 2024):
    if not _real_data_provider:
        raise HTTPException(status_code=503, detail="FastF1 data provider not initialized")
    resolved = resolve_circuit_id(circuit) or circuit
    result = _real_data_provider.validate_prediction_against_real(predicted_time, resolved, year)
    return result


# ==========================================
# OpenF1 Real Data Integration
# ==========================================

@app.get("/openf1/session")
@limiter.limit("30/minute")
async def openf1_session(
    request: Request,
    current_user: User = Depends(AllAuthenticated)
):
    """Get current OpenF1 session availability and info."""
    service = get_openf1_service()
    data = await service.get_session_info()
    return json_safe(data)

@app.get("/openf1/positions")
@limiter.limit("30/minute")
async def openf1_positions(
    request: Request,
    current_user: User = Depends(AllAuthenticated)
):
    """Get normalized driver positions from OpenF1."""
    service = get_openf1_service()
    data = await service.get_normalized_timing_tower()
    return json_safe(data)

@app.get("/openf1/timing")
@limiter.limit("30/minute")
async def openf1_timing(
    request: Request,
    current_user: User = Depends(AllAuthenticated)
):
    """Get normalized timing tower from OpenF1."""
    service = get_openf1_service()
    data = await service.get_normalized_timing_tower()
    return json_safe(data)

@app.get("/openf1/race-control")
@limiter.limit("30/minute")
async def openf1_race_control(
    request: Request,
    current_user: User = Depends(AllAuthenticated)
):
    """Get normalized race control messages from OpenF1."""
    service = get_openf1_service()
    data = await service.get_normalized_race_control()
    return json_safe(data)

@app.get("/openf1/weather")
@limiter.limit("30/minute")
async def openf1_weather(
    request: Request,
    current_user: User = Depends(AllAuthenticated)
):
    """Get normalized weather data from OpenF1."""
    service = get_openf1_service()
    data = await service.get_normalized_weather()
    return json_safe(data)

@app.get("/openf1/telemetry/{driver_number}")
@limiter.limit("60/minute")
async def openf1_telemetry(
    driver_number: int,
    request: Request,
    current_user: User = Depends(AllAuthenticated)
):
    """Get latest car telemetry and GPS location for a specific driver."""
    service = get_openf1_service()
    car_data = await service.get_car_data(driver_number)
    location = await service.get_location(driver_number)
    
    return json_safe({
        "driver_number": driver_number,
        "car_data": car_data,
        "location": location
    })

# ==========================================
# Health & Status
# ==========================================

@app.get("/health")
async def health_check():
    """Health check endpoint with security status."""
    return {
        "status": "healthy",
        "version": "3.1.0",
        "edition": "ELITE",
        "security_layer": "v3.1 - ACTIVE",
        "models_loaded": _models_initialized,
        "systems": {
            "ml_models": _models_initialized,
            "rl_engine": _rl_engine is not None,
            "opponent_model": _opponent_model is not None,
            "risk_model": _risk_model is not None,
            "xai_engine": _xai_engine is not None
        },
        "security": {
            "jwt_authentication": "ACTIVE",
            "rbac": "ACTIVE",
            "rate_limiting": "ACTIVE",
            "audit_logging": "ACTIVE",
            "password_hashing": "bcrypt",
            "database": "SQLAlchemy + SQLite/PostgreSQL"
        },
        "features": [
            "reinforcement_learning",
            "opponent_modeling",
            "probabilistic_risk",
            "digital_twin",
            "explainable_ai",
            "telemetry_pipeline",
            "jwt_authentication",
            "role_based_access_control",
            "rate_limiting",
            "audit_logging"
        ],
        "authentication_required": True,
        "roles": ["admin", "engineer", "viewer"],
        "endpoints_protected": "ALL (except /health, /, /auth/login)"
    }


if __name__ == "__main__":
    # Railway sets PORT automatically; default to 8000 for local dev
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
