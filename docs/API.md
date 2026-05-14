# F1 Strategy Optimization API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Health Check
Check if the API is running and models are loaded.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "circuits_available": 6,
  "version": "1.0.0"
}
```

---

### 2. Get Circuits
Get list of available F1 circuits with configurations.

**Endpoint:** `GET /circuits`

**Response:**
```json
{
  "circuits": [
    {
      "name": "Monza",
      "laps": 53,
      "pit_loss": 22,
      "base_lap_time": 82.0
    }
  ]
}
```

---

### 3. Get Tire Compounds
Get information about available tire compounds.

**Endpoint:** `GET /tires`

**Response:**
```json
{
  "tires": [
    {
      "name": "soft",
      "base_pace": -1.5,
      "degradation_rate": 0.12,
      "optimal_laps": 20,
      "color": "#FF3333"
    }
  ]
}
```

---

### 4. Simulate Strategy (Main Endpoint)
Simulate and optimize race strategy for a given circuit.

**Endpoint:** `POST /simulate`

**Request Body:**
```json
{
  "circuit": "Monza",
  "laps": 53,
  "strategy_type": "auto",
  "tire_compound": "soft",
  "weather": "dry",
  "include_safety_car": false
}
```

**Parameters:**
- `circuit` (required): Circuit name (Monza, Silverstone, Spa, Monaco, Suzuka, Barcelona)
- `laps` (optional): Number of laps. Defaults to circuit's standard lap count.
- `strategy_type` (optional): "auto", "1_stop", "2_stop", "3_stop". Default: "auto"
- `tire_compound` (optional): "soft", "medium", "hard". Default: "soft"
- `weather` (optional): "dry", "wet", "mixed". Default: "dry"
- `include_safety_car` (optional): boolean. Default: false

**Response:**
```json
{
  "best_strategy": "2_stop",
  "pit_laps": [18, 36],
  "total_time": 5320.45,
  "total_time_formatted": "88:40.45",
  "explanation": "2-stop strategy selected because tire degradation increased significantly after lap 17...",
  "tires_used": ["soft", "medium", "hard"],
  "lap_times": [82.1, 81.9, ...],
  "tire_degradation": [0.0, 0.02, ...],
  "strategy_comparison": {
    "1_stop": {
      "time": 5420.3,
      "pit_laps": [27],
      "tires": ["medium", "hard"]
    },
    "2_stop": {
      "time": 5320.45,
      "pit_laps": [18, 36],
      "tires": ["soft", "medium", "hard"]
    }
  },
  "circuit": "Monza",
  "weather": "dry",
  "safety_car_laps": []
}
```

---

### 5. Detailed Race Simulation
Run lap-by-lap simulation with detailed per-lap data.

**Endpoint:** `POST /race-simulation`

**Request Body:** Same as `/simulate`

**Response:**
```json
{
  "summary": {
    "circuit": "Monza",
    "total_laps": 53,
    "total_time": 5320.45,
    "pit_laps": [18, 36],
    "avg_lap_time": 100.4,
    "best_lap": 80.2,
    "worst_lap": 105.8,
    "max_degradation": 4.5,
    "safety_car_laps": [],
    "tire_stints": [
      {"lap": 18, "new_tire": "medium"},
      {"lap": 36, "new_tire": "hard"}
    ]
  },
  "lap_data": [
    {
      "lap": 1,
      "lap_time": 82.1,
      "tire": "soft",
      "tire_age": 1,
      "degradation": 0.0,
      "fuel": 1.0
    }
  ],
  "optimal_strategy": {
    "pit_laps": [18, 36],
    "tires": ["soft", "medium", "hard"],
    "explanation": "..."
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Unknown circuit: InvalidCircuit. Available: ['Monza', 'Silverstone', ...]"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Simulation error: ..."
}
```

---

## Circuit Reference

| Circuit | Laps | Pit Loss | Base Lap Time |
|---------|------|----------|---------------|
| Monza | 53 | 22s | 82.0s |
| Silverstone | 52 | 24s | 90.0s |
| Spa | 44 | 23s | 105.0s |
| Monaco | 78 | 18s | 72.0s |
| Suzuka | 53 | 25s | 88.0s |
| Barcelona | 66 | 24s | 78.0s |

---

## Tire Compound Reference

| Compound | Base Pace | Degradation | Optimal Laps |
|----------|-----------|--------------|--------------|
| Soft | -1.5s | 0.12 s/lap | 20 laps |
| Medium | 0.0s | 0.07 s/lap | 35 laps |
| Hard | +1.2s | 0.04 s/lap | 50 laps |

---

## Example Usage

### cURL
```bash
# Get circuits
curl http://localhost:8000/circuits

# Simulate strategy
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "circuit": "Monza",
    "strategy_type": "auto",
    "tire_compound": "soft",
    "weather": "dry"
  }'
```

### Python
```python
import requests

# Simulate strategy
response = requests.post(
    "http://localhost:8000/simulate",
    json={
        "circuit": "Monza",
        "strategy_type": "auto",
        "weather": "dry"
    }
)
result = response.json()
print(f"Best strategy: {result['best_strategy']}")
print(f"Pit laps: {result['pit_laps']}")
print(f"Total time: {result['total_time_formatted']}")
```

### JavaScript
```javascript
// Simulate strategy
fetch('http://localhost:8000/simulate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    circuit: 'Monza',
    strategy_type: 'auto',
    weather: 'dry'
  })
})
.then(response => response.json())
.then(data => {
  console.log('Best strategy:', data.best_strategy);
  console.log('Pit laps:', data.pit_laps);
});
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider:
- 100 requests per minute per IP
- Caching for identical requests

## CORS

API allows cross-origin requests from all origins in development. For production, update CORS settings in `app/main.py`.
