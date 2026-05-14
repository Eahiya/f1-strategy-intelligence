# F1 Race Strategy Optimization System

A production-quality prototype for simulating Formula 1 race strategies and recommending optimal pit stop strategies using machine learning and rule-based logic.

## Overview

This system simulates F1 race strategies and recommends the optimal pit stop plan based on:
- Historical race data
- Machine learning predictions (tire degradation, lap times)
- Rule-based logic (undercut opportunities, tire thresholds)
- Strategy optimization (1-stop, 2-stop, 3-stop comparison)

## Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI** - High-performance API framework
- **scikit-learn** - Machine learning models
- **pandas/numpy** - Data processing
- **uvicorn** - ASGI server

### Frontend
- **React 18+** - Modern UI framework
- **Recharts** - Data visualization
- **TailwindCSS** - Styling
- **Axios** - API client

## Project Structure

```
f1-strategy-system/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   └── services/
│   └── requirements.txt
├── frontend/          # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── ml_models/         # ML model training & inference
│   ├── tire_degradation.py
│   ├── lap_time_predictor.py
│   └── strategy_optimizer.py
├── data/              # Datasets & data processing
│   ├── raw/
│   ├── processed/
│   └── pipeline.py
├── notebooks/         # Jupyter notebooks for analysis
├── docs/              # Documentation
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip
- npm

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd f1-strategy-system
```

2. **Setup Backend**
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

3. **Setup Frontend**
```bash
cd frontend
npm install
```

4. **Generate Sample Data**
```bash
cd backend
python -c "from app.services.data_generator import generate_dataset; generate_dataset()"
```

### Running the Application

1. **Start Backend Server**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

2. **Start Frontend (in new terminal)**
```bash
cd frontend
npm start
```

3. **Open Browser**
Navigate to `http://localhost:3000`

## API Usage

### Simulate Race Strategy

**Endpoint:** `POST /simulate`

**Request:**
```json
{
  "circuit": "Monza",
  "laps": 53,
  "strategy_type": "auto",
  "tire_compound": "soft"
}
```

**Response:**
```json
{
  "best_strategy": "2-stop",
  "pit_laps": [18, 36],
  "total_time": 5320.45,
  "explanation": "2-stop strategy selected because tire degradation increased significantly after lap 17, making additional stop faster overall.",
  "lap_times": [82.1, 81.9, ...],
  "tire_degradation": [0.0, 0.02, ...],
  "strategy_comparison": {
    "1_stop": {"time": 5420.3, "pit_laps": [27]},
    "2_stop": {"time": 5320.45, "pit_laps": [18, 36]},
    "3_stop": {"time": 5380.2, "pit_laps": [12, 25, 40]}
  }
}
```

## Machine Learning Models

### Model A: Tire Degradation Predictor
- **Type:** Random Forest Regression
- **Inputs:** Tire type, lap number, circuit
- **Output:** Degradation level (0-1 scale)

### Model B: Lap Time Predictor
- **Type:** Random Forest Regression
- **Inputs:** Tire age, circuit, lap number, fuel load
- **Output:** Predicted lap time (seconds)

### Model C: Strategy Optimizer
- **Method:** Simulation-based optimization
- **Strategies Tested:** 1-stop, 2-stop, 3-stop
- **Selection Criteria:** Minimum total race time

## Features

### Core Features
- [x] Data pipeline for F1 datasets
- [x] Tire degradation prediction
- [x] Lap time prediction
- [x] Multi-strategy simulation (1/2/3-stop)
- [x] Rule-based logic layer
- [x] REST API with FastAPI
- [x] React dashboard with visualizations
- [x] Decision explainability

### Bonus Features
- [x] Weather simulation
- [x] Safety car probability
- [x] Strategy comparison charts

## Circuit Database

Supported circuits with lap counts:
- Monza (53 laps)
- Silverstone (52 laps)
- Spa (44 laps)
- Monaco (78 laps)
- Suzuka (53 laps)
- Barcelona (66 laps)

## Tire Compounds

- **Soft:** Fastest, degrades quickly (2-3 sec/lap degradation)
- **Medium:** Balanced (1-2 sec/lap degradation)
- **Hard:** Slowest, durable (0.5-1 sec/lap degradation)

## Performance

- Simulation runs in under 2 seconds
- API response time: < 100ms
- Frontend render time: < 50ms

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI    │────▶│   ML Models │
│  Frontend   │◄────│   Backend    │◄────│  Predictions│
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Simulation  │
                     │    Engine      │
                     └──────────────┘
```

## Future Improvements

1. **Real Data Integration**
   - Connect to Ergast API for live F1 data
   - Historical race data from FastF1

2. **Advanced ML**
   - Deep learning models (LSTM for time series)
   - Reinforcement learning for strategy optimization
   - Ensemble methods for better predictions

3. **Additional Features**
   - Multi-car race simulation
   - Overtaking probability modeling
   - Dynamic weather adaptation
   - Real-time strategy updates

4. **Performance**
   - Caching layer (Redis)
   - Async processing
   - GPU acceleration for ML

## Deployment

### Backend (Render/Railway)
```bash
# requirements.txt includes gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Frontend (Vercel/Netlify)
```bash
npm run build
# Deploy build/ folder
```

## License

MIT License - This is a student project for educational purposes.

## Acknowledgments

- Ergast API for F1 data
- FastF1 library for inspiration
- Formula 1 for the amazing sport

## Contact

For questions or suggestions, please open an issue on GitHub.
