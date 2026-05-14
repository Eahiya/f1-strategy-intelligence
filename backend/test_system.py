"""Test script for the F1 Strategy System."""
import sys
sys.path.insert(0, '.')

from app.services.data_generator import generate_dataset
from app.services.data_pipeline import F1DataPipeline
from app.models.tire_degradation import TireDegradationModel
from app.models.lap_time_predictor import LapTimePredictor
from app.models.strategy_optimizer import StrategyOptimizer
from app.services.race_simulator import RaceSimulator

print("=" * 60)
print("F1 Strategy System Test")
print("=" * 60)

# Test 1: Data Generation
print("\n[1/5] Testing Data Generation...")
df = generate_dataset(num_samples=500, output_path='data/f1_race_data.csv')
print(f"  Generated {len(df)} lap records")
print(f"  Circuits: {df['circuit'].nunique()}")
print(f"  Tire compounds: {df['tire_compound'].nunique()}")

# Test 2: Data Pipeline
print("\n[2/5] Testing Data Pipeline...")
pipeline = F1DataPipeline()
(X_lt, y_lt), (X_deg, y_deg) = pipeline.prepare_for_training(df)
print(f"  Lap time features: {X_lt.shape}")
print(f"  Degradation features: {X_deg.shape}")

# Test 3: Tire Degradation Model
print("\n[3/5] Testing Tire Degradation Model...")
tire_model = TireDegradationModel()
tire_metrics = tire_model.train(X_deg, y_deg)
print(f"  RMSE: {tire_metrics['rmse']:.4f}s")
print(f"  R2: {tire_metrics['r2']:.4f}")

# Test 4: Lap Time Predictor
print("\n[4/5] Testing Lap Time Predictor...")
lap_model = LapTimePredictor()
lap_metrics = lap_model.train(X_lt, y_lt)
print(f"  RMSE: {lap_metrics['rmse']:.4f}s")
print(f"  MAE: {lap_metrics['mae']:.4f}s")
print(f"  R2: {lap_metrics['r2']:.4f}")

# Test 5: Strategy Optimizer
print("\n[5/5] Testing Strategy Optimizer...")
optimizer = StrategyOptimizer()
result = optimizer.optimize('Monza', 53, 'auto', 'dry', 0.0)
print(f"  Best Strategy: {result['best_strategy']}")
print(f"  Pit Laps: {result['pit_laps']}")
print(f"  Total Time: {result['total_time']:.2f}s")
print(f"  Tires Used: {result['tires_used']}")

# Test 6: Race Simulator
print("\n[BONUS] Testing Race Simulator...")
simulator = RaceSimulator('Monza', 53, 'soft')
simulator.initialize_race('dry', 0.0)
simulator.simulate_race(
    pit_laps=result['pit_laps'],
    tire_strategy=result['tires_used']
)
summary = simulator.get_race_summary()
print(f"  Total Time: {summary['total_time']:.2f}s")
print(f"  Avg Lap: {summary['avg_lap_time']:.2f}s")
print(f"  Best Lap: {summary['best_lap']:.2f}s")

print("\n" + "=" * 60)
print("All Tests Passed!")
print("=" * 60)
