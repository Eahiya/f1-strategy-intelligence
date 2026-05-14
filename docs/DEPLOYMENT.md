# Deployment Guide

## Overview

This guide covers deploying the F1 Strategy Optimization System to production.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React App     │────▶│   FastAPI       │────▶│   ML Models     │
│   (Frontend)    │◄────│   (Backend)     │◄────│   & Data        │
│   Vercel        │     │   Render/       │     │   In-Memory     │
│                 │     │   Railway         │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Backend Deployment

### Option 1: Render (Recommended)

1. **Create `render.yaml`**
```yaml
services:
  - type: web
    name: f1-strategy-api
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python -c "from app.services.data_generator import generate_dataset; generate_dataset()"
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
```

2. **Deploy**
```bash
# Push to GitHub
git push origin main

# Connect repository in Render dashboard
# Service will auto-deploy on push
```

### Option 2: Railway

1. **Create `railway.json`**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt && python -c 'from app.services.data_generator import generate_dataset; generate_dataset()'"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

2. **Deploy**
```bash
railway login
railway init
railway up
```

### Option 3: Heroku

1. **Create `Procfile`**
```
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

2. **Create `runtime.txt`**
```
python-3.10.13
```

3. **Deploy**
```bash
heroku create f1-strategy-api
heroku config:set PYTHONPATH=backend
git push heroku main
```

---

## Frontend Deployment

### Option 1: Vercel (Recommended)

1. **Create `vercel.json`**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "framework": "create-react-app",
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-api-url.com/$1"
    }
  ]
}
```

2. **Set API URL**
```bash
# Create .env.production
REACT_APP_API_URL=https://your-api-url.com
```

3. **Deploy**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Option 2: Netlify

1. **Create `netlify.toml`**
```toml
[build]
  command = "npm run build"
  publish = "build"

[[redirects]]
  from = "/api/*"
  to = "https://your-api-url.com/:splat"
  status = 200
```

2. **Deploy**
```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --prod
```

### Option 3: GitHub Pages

1. **Update `package.json`**
```json
{
  "homepage": "https://yourusername.github.io/f1-strategy",
  "scripts": {
    "predeploy": "npm run build",
    "deploy": "gh-pages -d build"
  }
}
```

2. **Install gh-pages**
```bash
npm install --save-dev gh-pages
```

3. **Deploy**
```bash
npm run deploy
```

---

## Environment Variables

### Backend (.env)
```bash
# API Settings
DEBUG=false
PORT=8000

# CORS
CORS_ORIGINS=https://your-frontend-url.com,https://your-frontend-url.vercel.app

# Data
DATA_DIR=./data

# Optional: External APIs
ERGAST_API_URL=https://ergast.com/api/f1
```

### Frontend (.env.production)
```bash
REACT_APP_API_URL=https://your-api-url.com
REACT_APP_API_TIMEOUT=10000
```

---

## Docker Deployment

### Backend Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate data on build
RUN python -c "from app.services.data_generator import generate_dataset; generate_dataset()"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run
```bash
cd backend
docker build -t f1-strategy-api .
docker run -p 8000:8000 f1-strategy-api
```

---

## Database (Optional)

For storing race history and analytics:

### PostgreSQL on Render
```yaml
services:
  - type: psql
    name: f1-strategy-db
    plan: starter
```

### Connection
```python
# backend/app/core/database.py
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
```

---

## Monitoring & Logging

### Backend Logging
```python
# app/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Performance Monitoring

#### Option 1: New Relic
```bash
pip install newrelic
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uvicorn app.main:app
```

#### Option 2: Datadog
```bash
pip install datadog
ddtrace-run uvicorn app.main:app
```

---

## Security Checklist

- [ ] Enable HTTPS only
- [ ] Set up CORS properly
- [ ] Add rate limiting
- [ ] Validate all inputs
- [ ] No hardcoded secrets
- [ ] Environment variables for config
- [ ] Security headers (CSP, HSTS)

### Security Headers
```python
# app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["your-domain.com", "*.vercel.app"]
)
```

---

## Scaling

### Horizontal Scaling

#### With Docker Compose
```yaml
version: '3'
services:
  api:
    build: ./backend
    ports:
      - "8000"
    deploy:
      replicas: 3
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

#### With Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: f1-strategy-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: f1-strategy-api
  template:
    metadata:
      labels:
        app: f1-strategy-api
    spec:
      containers:
      - name: api
        image: f1-strategy-api:latest
        ports:
        - containerPort: 8000
```

---

## CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
  
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install & Build
        run: |
          cd frontend
          npm ci
          npm run build
      
      - name: Deploy to Vercel
        run: |
          npm i -g vercel
          vercel --token ${{ secrets.VERCEL_TOKEN }} --prod
```

---

## Cost Estimates

### Free Tier Options
| Service | Provider | Limit |
|---------|----------|-------|
| Backend | Render | 750 hours/month |
| Frontend | Vercel | 100GB bandwidth |
| Database | Supabase | 500MB |

### Paid Tier (Estimated)
| Service | Monthly Cost |
|---------|-------------|
| Render (Standard) | $7 |
| Vercel Pro | $20 |
| Database | $15 |
| **Total** | **~$42/month** |

---

## Troubleshooting

### Common Issues

#### CORS Errors
```python
# Add specific origins
origins = [
    "https://your-frontend.vercel.app",
    "https://your-frontend.netlify.app"
]
```

#### Cold Start Latency
- Use Render's "Keep Alive" feature
- Or Railway (faster cold starts)

#### Memory Issues
- Reduce dataset size for training
- Use model quantization
- Implement caching

---

## Maintenance

### Regular Tasks

#### Weekly
- Check error logs
- Monitor API latency
- Review usage metrics

#### Monthly
- Retrain models if needed
- Update dependencies
- Security patches

#### Quarterly
- Performance optimization
- Feature updates
- Cost review

---

## Support

For deployment issues:
- Check logs in dashboard
- Review environment variables
- Test locally first
- Contact platform support
