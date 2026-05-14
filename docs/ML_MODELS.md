# Machine Learning Models Documentation

## Overview

The F1 Strategy Optimization System uses three layers of ML models:

1. **Tire Degradation Predictor** - Predicts tire performance decay
2. **Lap Time Predictor** - Forecasts lap times based on conditions
3. **Strategy Optimizer** - Simulates and selects optimal strategies

---

## Model A: Tire Degradation Predictor

### Purpose
Predicts how much a tire will degrade (in seconds) based on tire age, compound, and circuit characteristics.

### Algorithm
- **Type:** Random Forest Regression
- **Library:** scikit-learn

### Hyperparameters
```python
RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
```

### Input Features
| Feature | Type | Description |
|---------|------|-------------|
| circuit_encoded | int | Circuit ID (0-5) |
| tire_compound_encoded | int | Tire type (0=soft, 1=medium, 2=hard) |
| tire_age | int | Laps on current tire |
| tire_age_sq | float | Tire age squared (captures non-linear degradation) |
| stint_progress | float | Progress through stint (0-1) |

### Output
- **tire_degradation:** Predicted lap time increase due to tire wear (seconds)

### Performance
| Metric | Typical Value |
|--------|---------------|
| RMSE | 0.2-0.4 seconds |
| R² | 0.85-0.95 |
| MAE | 0.15-0.25 seconds |

### Training Data
- Generated synthetic data (5000+ samples)
- 80/20 train/test split

---

## Model B: Lap Time Predictor

### Purpose
Predicts lap time based on tire state, fuel load, circuit, and lap number.

### Algorithm
- **Type:** Random Forest Regression
- **Library:** scikit-learn

### Hyperparameters
```python
RandomForestRegressor(
    n_estimators=150,
    max_depth=15,
    min_samples_split=3,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)
```

### Input Features
| Feature | Type | Description |
|---------|------|-------------|
| circuit_encoded | int | Circuit ID |
| tire_compound_encoded | int | Tire type |
| lap_number | int | Current lap number |
| tire_age | int | Laps on tire |
| tire_age_sq | float | Tire age squared |
| fuel_load | float | Fuel remaining (0-1) |
| fuel_effect | float | Fuel impact on pace |
| stint_progress | float | Stint progress |
| total_laps | int | Race length |

### Output
- **lap_time:** Predicted lap time in seconds

### Performance
| Metric | Typical Value |
|--------|---------------|
| RMSE | 0.3-0.6 seconds |
| MAE | 0.2-0.4 seconds |
| R² | 0.90-0.98 |
| Mean % Error | < 0.5% |

### Feature Importance
1. **tire_age** (35%) - Most important factor
2. **circuit_encoded** (25%) - Circuit characteristics
3. **fuel_load** (15%) - Fuel effect
4. **tire_compound** (15%) - Tire type
5. **lap_number** (10%) - Race progress

---

## Model C: Strategy Optimizer

### Purpose
Determines optimal pit stop strategy by simulating multiple scenarios.

### Method
**Simulation-based Optimization**

### Algorithm
1. Generate pit window combinations
2. For each combination:
   - Assign tire compounds
   - Simulate race lap-by-lap
   - Calculate total time
3. Select strategy with minimum total time

### Strategy Types

#### 1-Stop Strategy
- Pit window: 25-65% of race
- Typical split: Soft → Hard or Medium → Hard

#### 2-Stop Strategy
- First pit: 20-35% of race
- Second pit: 55-70% of race
- Common: Soft → Medium → Hard

#### 3-Stop Strategy
- First pit: 15-25% of race
- Second pit: 40-50% of race
- Third pit: 65-75% of race
- Aggressive: Multiple soft stints

### Decision Factors

#### Tire Degradation Thresholds
```python
if degradation > 3.0 seconds:
    pit_triggered = True
    
if tire_age > optimal_laps * 1.2:
    pit_triggered = True
```

#### Safety Car Adjustment
- Reduces pit loss by 70% when safety car is active
- Triggers opportunistic pit stops

#### Weather Impact
- Dry: 1.0x multiplier
- Wet: 1.15x multiplier (slower, more tire wear)
- Mixed: 1.08x multiplier

---

## Data Generation

### Synthetic Data Approach

Since real F1 data has restrictions, the system uses physics-based synthetic data:

```python
lap_time = base_time + tire_pace + degradation + fuel_effect + noise

where:
    base_time = circuit-specific constant
    tire_pace = compound offset (-1.5 to +1.2 seconds)
    degradation = deg_rate * (tire_age ^ 1.5)
    fuel_effect = fuel_load * 0.08 * (1 - lap/total_laps)
    noise = N(0, 0.3)  # Normal distribution
```

### Data Schema
```python
{
    "circuit": str,              # Circuit name
    "tire_compound": str,        # soft/medium/hard
    "lap_number": int,           # Lap in race
    "tire_age": int,             # Laps on tire
    "fuel_load": float,          # 0-1 scale
    "lap_time": float,           # Seconds
    "total_laps": int,           # Race length
    "stint_length": int,         # Planned stint
    "tire_degradation": float    # Delta from first lap
}
```

---

## Model Training Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Generate  │───▶│    Clean    │───▶│   Encode    │
│    Data     │    │    Data     │    │   Features  │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                             ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Predict   │◀───│    Train    │◀───│  Engineer   │
│   & Explain │    │    Models   │    │  Features   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Training Code
```python
# Initialize pipeline
pipeline = F1DataPipeline()

# Load/generate data
df = load_or_generate_data()

# Prepare features
(X_lt, y_lt), (X_deg, y_deg) = pipeline.prepare_for_training(df)

# Train models
tire_model = TireDegradationModel()
tire_model.train(X_deg, y_deg)

lap_time_model = LapTimePredictor()
lap_time_model.train(X_lt, y_lt)
```

---

## Model Persistence

Models are saved/loaded using joblib:

```python
# Save
model.save("models/tire_model.joblib")

# Load
model.load("models/tire_model.joblib")
```

---

## Performance Optimization

### Caching
- Model predictions are deterministic for same inputs
- Consider Redis/memcached for production

### Parallel Processing
- Strategy simulation uses multiple threads
- Random Forests use `n_jobs=-1` for all cores

### Fast Inference
- Predictions complete in < 10ms
- Full strategy simulation in < 2 seconds

---

## Future Improvements

### 1. Real Data Integration
- Connect to FastF1 library
- Use Ergast API historical data
- Feature: Real track evolution patterns

### 2. Advanced Models
- **LSTM Networks:** For time-series lap prediction
- **XGBoost/LightGBM:** Alternative to Random Forest
- **Ensemble Methods:** Combine multiple models

### 3. Transfer Learning
- Pre-train on generic circuits
- Fine-tune on specific tracks

### 4. Online Learning
- Update models with actual race data
- Adapt to current season characteristics

---

## Validation

### Cross-Validation
- 5-fold cross-validation for model selection
- Time-series aware splitting for temporal data

### Testing
```python
# Unit tests for models
pytest backend/tests/test_models.py

# Integration tests
pytest backend/tests/test_api.py
```

---

## Model Monitoring

Track these metrics in production:
- Prediction latency (target: < 50ms)
- Error rates (target: < 5%)
- Model drift (retrain monthly)
