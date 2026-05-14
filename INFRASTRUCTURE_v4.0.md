# F1 Strategy Platform v4.0 - Production Infrastructure Edition

## 🏗️ Infrastructure Architecture

---

## 📋 SYSTEM OVERVIEW

**Version:** 4.0.0  
**Edition:** Production Infrastructure  
**Status:** PRODUCTION-READY

The F1 Strategy Platform has been transformed from a development system to a production-grade infrastructure with Docker orchestration, monitoring, caching, and CI/CD automation.

---

## 🏛️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NGINX (Reverse Proxy)                       │
│  • SSL Termination                                              │
│  • Load Balancing                                               │
│  • Rate Limiting                                                │
│  • Security Headers                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────┐           ┌─────────────────────┐
│     Frontend        │           │      Backend       │
│   (React + NGINX)   │           │   (FastAPI + ML)   │
│   Port: 80          │           │   Port: 8000       │
└─────────────────────┘           └─────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────┐
              │                           │                   │
              ▼                           ▼                   ▼
┌─────────────────┐           ┌─────────────────┐   ┌─────────────────┐
│   PostgreSQL    │           │     Redis       │   │   Prometheus    │
│   (Database)    │           │   (Cache/Rate)  │   │   (Metrics)     │
│   Port: 5432    │           │   Port: 6379    │   │   Port: 9090    │
└─────────────────┘           └─────────────────┘   └─────────────────┘
                                                            │
                                                            ▼
                                                  ┌─────────────────┐
                                                  │     Grafana     │
                                                  │  (Dashboards)   │
                                                  │   Port: 3001    │
                                                  └─────────────────┘
```

---

## 🐳 DOCKER SERVICES

### Core Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **nginx** | nginx:alpine | 80, 443 | Reverse proxy, SSL |
| **backend** | f1-backend:latest | 8000 | FastAPI API server |
| **frontend** | f1-frontend:latest | 80 | React SPA |
| **postgres** | postgres:15-alpine | 5432 | Primary database |
| **redis** | redis:7-alpine | 6379 | Cache & rate limiting |

### Monitoring Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **prometheus** | prom/prometheus | 9090 | Metrics collection |
| **grafana** | grafana/grafana | 3001 | Visualization |

---

## 🚀 QUICK START

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 2 CPU cores minimum

### 1. Clone and Configure

```bash
git clone <your-repo>
cd f1-strategy

# Copy environment template
cp .env.example .env

# Edit .env with your production values
nano .env
```

### 2. Start Production Stack

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### 3. Verify Deployment

```bash
# Health check
curl http://localhost/health

# Check backend
curl http://localhost/api/health

# Access application
open http://localhost
```

### 4. Access Monitoring

- **Grafana Dashboards:** http://localhost:3001
  - Username: `admin`
  - Password: (from .env GRAFANA_PASSWORD)
  
- **Prometheus:** http://localhost:9090

---

## 📊 SERVICE DETAILS

### NGINX (Reverse Proxy)

**Configuration:** `nginx/nginx.conf`

**Features:**
- SSL/TLS termination (HTTPS ready)
- Gzip compression
- Security headers (CSP, XSS, CSRF)
- Rate limiting (10r/s default)
- JSON structured access logs
- WebSocket support (for live streaming)

**Routes:**
- `/api/*` → Backend
- `/*` → Frontend
- `/health` → Health check
- `/metrics` → Prometheus metrics (internal)

### Backend (FastAPI)

**Configuration:** `backend/Dockerfile`

**Features:**
- Multi-stage build (reduces image size)
- Non-root user (security)
- Health checks
- 2 worker processes (Uvicorn)
- JSON structured logging
- Prometheus metrics endpoint

**Endpoints:**
- `/health` - Health check
- `/metrics` - Prometheus metrics
- `/simulate` - Strategy simulation
- `/elite/*` - Elite AI features
- `/auth/*` - Authentication

### Frontend (React)

**Configuration:** `frontend/Dockerfile`

**Features:**
- Production-optimized build
- NGINX serving static files
- Gzip compression
- Security headers
- SPA routing support

### PostgreSQL

**Features:**
- Persistent volume storage
- Health checks
- Automated backups (configurable)

### Redis

**Features:**
- LRU cache eviction
- Persistent storage (AOF)
- 256MB memory limit
- Rate limiting backend

---

## 🔧 CONFIGURATION

### Environment Variables

Required in `.env`:

```bash
# Database
DB_USER=f1user
DB_PASSWORD=secure_random_password
DB_NAME=f1strategy

# JWT
JWT_SECRET_KEY=openssl_rand_hex_32

# Monitoring
GRAFANA_PASSWORD=admin_password

# CORS
ALLOWED_ORIGINS=https://yourdomain.com
```

See `.env.example` for all options.

### Resource Limits

Backend container (from docker-compose.yml):
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

---

## 📈 MONITORING

### Grafana Dashboards

**Dashboard URL:** http://localhost:3001

**Pre-built Dashboards:**

1. **System Overview**
   - Service health status
   - Request rate
   - Response times
   - Error rates

2. **Simulation Metrics**
   - Simulation duration by circuit
   - Strategy type distribution
   - Success/failure rates

### Prometheus Metrics

**Available Metrics:**

```
# HTTP request metrics
http_requests_total{method, endpoint, status}
http_request_duration_seconds_bucket{endpoint, le}

# Simulation metrics
simulation_duration_seconds{circuit, strategy_type}
simulation_requests_total{circuit, strategy_type}

# Cache metrics
cache_hits_total{cache_type}
cache_misses_total{cache_type}

# System metrics
process_resident_memory_bytes
cpu_usage_percent
```

### Alerting (Optional)

Add alert rules to `monitoring/prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

---

## 🧪 LOAD TESTING

### Using Locust

```bash
# Install locust
pip install locust

# Run load test
cd tests
locust -f locustfile.py --host=http://localhost

# Or headless mode
locust -f locustfile.py --host=http://localhost \
  --headless -u 100 -r 10 --run-time 5m
```

### Load Test Scenarios

| Scenario | Users | Spawn Rate | Duration |
|----------|-------|------------|----------|
| Light | 50 | 5/s | 10m |
| Medium | 100 | 10/s | 15m |
| Heavy | 200 | 20/s | 30m |
| Spike | 500 | 50/s | 5m |

### Performance Targets

| Metric | Target |
|--------|--------|
| Response Time (p95) | < 500ms |
| Response Time (p99) | < 1000ms |
| Error Rate | < 1% |
| Throughput | > 100 req/s |

---

## 🔒 SECURITY

### Production Checklist

- [ ] Change default admin password
- [ ] Generate strong JWT_SECRET_KEY
- [ ] Enable HTTPS (SSL certificates)
- [ ] Configure CORS for specific origins
- [ ] Set up firewall rules
- [ ] Enable fail2ban (optional)
- [ ] Regular security updates

### Security Headers

NGINX adds these headers:

```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
```

### HTTPS Setup

1. Obtain SSL certificates (Let's Encrypt)
2. Uncomment HTTPS server block in `nginx/nginx.conf`
3. Mount certificates in docker-compose:

```yaml
volumes:
  - ./ssl/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
  - ./ssl/privkey.pem:/etc/nginx/ssl/privkey.pem:ro
```

---

## 🔄 CI/CD PIPELINE

### GitHub Actions Workflow

**File:** `.github/workflows/ci-cd.yml`

**Stages:**

1. **Test**
   - Backend unit tests (pytest)
   - Frontend tests
   - Code coverage
   - Linting (flake8, black)

2. **Security**
   - Trivy vulnerability scan
   - Dependency check

3. **Build**
   - Docker image build
   - Push to GitHub Container Registry
   - Multi-platform support

4. **Integration Test**
   - Docker-compose stack test
   - Health checks

5. **Deploy**
   - Staging deployment
   - Production deployment (manual approval)

### Container Registry

Images are published to:
- `ghcr.io/{owner}/f1-strategy/backend:latest`
- `ghcr.io/{owner}/f1-strategy/frontend:latest`

---

## 📦 DEPLOYMENT OPTIONS

### Option 1: Docker Compose (Recommended for single server)

```bash
docker-compose up -d
```

### Option 2: Kubernetes (For high availability)

```bash
kubectl apply -f k8s/
```

### Option 3: Cloud Providers

**AWS:**
- ECS (Elastic Container Service)
- EKS (Elastic Kubernetes Service)

**Azure:**
- AKS (Azure Kubernetes Service)
- Container Instances

**GCP:**
- GKE (Google Kubernetes Engine)
- Cloud Run

---

## 🛠️ TROUBLESHOOTING

### Services Not Starting

```bash
# Check logs
docker-compose logs [service_name]

# Restart specific service
docker-compose restart backend

# Check resource usage
docker stats
```

### Database Issues

```bash
# Reset database (WARNING: loses data)
docker-compose down -v
rm -rf postgres_data

# Restore from backup
docker-compose exec -T postgres pg_restore < backup.sql
```

### Performance Issues

```bash
# Check container resources
docker stats

# View slow queries (if enabled)
docker-compose logs postgres | grep "duration:"

# Check cache hit rate
redis-cli -h localhost info stats | grep keyspace
```

---

## 📊 MONITORING QUERIES

### Prometheus Query Examples

**Request Rate:**
```promql
rate(http_requests_total[5m])
```

**95th Percentile Latency:**
```promql
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)
```

**Error Rate:**
```promql
rate(http_requests_total{status=~"5.."}[5m]) 
/ 
rate(http_requests_total[5m])
```

**Cache Hit Rate:**
```promql
rate(cache_hits_total[5m]) 
/ 
(rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

---

## 🔧 MAINTENANCE

### Backup Database

```bash
# Automated backup script
#!/bin/bash
docker-compose exec -T postgres pg_dump -U f1user f1strategy > backup_$(date +%Y%m%d).sql
```

### Update Images

```bash
# Pull latest images
docker-compose pull

# Rolling update
docker-compose up -d --no-deps --build backend
```

### Clean Up

```bash
# Remove unused containers and images
docker system prune -a

# Clear logs
docker-compose logs --tail 100
```

---

## 📈 SCALING GUIDE

### Vertical Scaling

Increase resources in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

### Horizontal Scaling

Add multiple backend instances with load balancer:

```yaml
services:
  backend-1:
    ...
  backend-2:
    ...
  nginx:
    upstream backend {
      server backend-1:8000;
      server backend-2:8000;
    }
```

### Database Scaling

- Read replicas for analytics queries
- Connection pooling (PgBouncer)
- Partitioning for large tables

---

## 📦 FILE STRUCTURE

```
f1-strategy/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
├── nginx/
│   └── nginx.conf
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/
├── tests/
│   └── locustfile.py
├── docker-compose.yml
├── .env.example
├── .github/workflows/ci-cd.yml
└── INFRASTRUCTURE_v4.0.md (this file)
```

---

## ✅ PRODUCTION READINESS CHECKLIST

- [x] Docker containers configured
- [x] NGINX reverse proxy with SSL
- [x] Database persistence
- [x] Redis caching
- [x] Structured JSON logging
- [x] Prometheus metrics
- [x] Grafana dashboards
- [x] Health checks
- [x] Rate limiting
- [x] Security headers
- [x] CI/CD pipeline
- [x] Load testing suite
- [x] Environment configuration
- [x] Backup strategy
- [x] Documentation

---

## 🚀 DEPLOYMENT SUMMARY

```
╔══════════════════════════════════════════════════════════════════╗
║  F1 Strategy Platform v4.0 - Production Infrastructure            ║
║                                                                   ║
║  Status: PRODUCTION-READY                                          ║
║                                                                   ║
║  Start Command: docker-compose up -d                             ║
║  Access URL: http://localhost (or your domain)                  ║
║  Monitoring: http://localhost:3001 (Grafana)                     ║
║                                                                   ║
║  Features:                                                        ║
║  • 6 Container Services                                           ║
║  • NGINX Reverse Proxy + SSL                                      ║
║  • PostgreSQL Database                                            ║
║  • Redis Caching                                                  ║
║  • Prometheus Metrics                                             ║
║  • Grafana Dashboards                                              ║
║  • CI/CD Pipeline (GitHub Actions)                               ║
║  • Load Testing (Locust)                                          ║
║                                                                   ║
║  Total Infrastructure Code: ~2,000 lines                         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

**Ready for championship-level deployment! 🏎️🏆**
