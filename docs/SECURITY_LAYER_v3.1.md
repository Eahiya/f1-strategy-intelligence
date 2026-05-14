# F1 Strategy Intelligence System - Security Layer v3.1

## 🔐 Authentication & Authorization System

---

## 📋 OVERVIEW

**Version:** 3.1.0  
**Edition:** ELITE + Security  
**Status:** PRODUCTION-READY

The Security Layer v3.1 adds comprehensive authentication and authorization to the F1 Strategy Intelligence System, making it suitable for enterprise deployment.

---

## 🛡️ SECURITY FEATURES

### 1. JWT Authentication
- **Algorithm:** HS256
- **Access Token Expiry:** 30 minutes
- **Refresh Token Expiry:** 7 days
- **Library:** python-jose[cryptography]

### 2. Password Security
- **Hashing:** bcrypt with 12 rounds
- **Requirements:**
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

### 3. Role-Based Access Control (RBAC)

#### Roles:
| Role | Level | Permissions |
|------|-------|-------------|
| **ADMIN** | 3 | Full system access, user management, all simulations |
| **ENGINEER** | 2 | Elite AI tools, digital twin, optimization, simulations |
| **VIEWER** | 1 | Read-only access, view simulations, basic analysis |

### 4. Rate Limiting
| Endpoint Type | Rate Limit |
|---------------|------------|
| Basic Simulation | 30/minute |
| Detailed Simulation | 20/minute |
| Monte Carlo Optimize | 10/minute |
| Multi-Car Simulation | 15/minute |
| Weather Simulation | 20/minute |
| Live Streaming | 5/minute |
| RL Strategy | 30/minute |
| Digital Twin | 5/minute |
| Telemetry (Admin) | 10/minute |
| Auth Login | 10/minute |
| Auth Register | 5/minute |

### 5. Audit Logging
- **Database:** SQLite/PostgreSQL
- **File Logs:** `backend/logs/audit.log`
- **Tracked Data:**
  - User ID and username
  - Endpoint accessed
  - HTTP method
  - Request parameters
  - Timestamp
  - IP address
  - Response status

### 6. CORS Protection
- **Allowed Origins:** Configurable via environment variable
- **Default:** `http://localhost:3000`
- **Allowed Methods:** GET, POST, PUT, DELETE
- **Credentials:** Enabled

---

## 📁 FILE STRUCTURE

```
backend/
├── app/
│   └── auth/
│       ├── __init__.py          # Auth module exports
│       ├── models.py            # User & AuditLog models, database
│       ├── password_utils.py    # bcrypt hashing & validation
│       ├── auth_handler.py      # JWT token operations
│       ├── dependencies.py      # RBAC dependencies & permission checkers
│       ├── routes.py            # Auth API endpoints (/auth/*)
│       └── logging.py           # Audit logging system
├── logs/
│   └── audit.log                # Audit log file
└── f1_strategy.db             # SQLite database (default)

frontend/
└── src/
    ├── context/
    │   └── AuthContext.js       # React auth context & JWT management
    └── components/
        ├── LoginPage.js         # Secure login UI
        └── ProtectedRoute.js    # Route guard for role-based access
```

---

## 🔌 API ENDPOINTS

### Public Endpoints (No Auth Required)
```
GET  /              - System status
GET  /health        - Health check
POST /auth/login    - Authenticate & get JWT
```

### Authentication Endpoints
```
POST /auth/register       - Register new user (Admin only)
POST /auth/login          - Authenticate user
GET  /auth/me             - Get current user profile
PUT  /auth/me             - Update profile
POST /auth/refresh        - Refresh access token
POST /auth/change-password - Change password
GET  /auth/users          - List all users (Admin)
PUT  /auth/users/{id}     - Update user role (Admin)
DELETE /auth/users/{id}   - Deactivate user (Admin)
```

### Protected Simulation Endpoints
```
POST /simulate              - Basic strategy (All roles)
POST /race-simulation       - Detailed simulation (All roles)
POST /optimize/advanced     - Monte Carlo (Engineer+)
POST /simulate/multi-car    - Multi-car race (All roles)
POST /simulate/weather      - Weather sim (All roles)
POST /simulate/live         - Live streaming (All roles)
```

### Protected Elite Endpoints
```
POST /elite/rl-strategy        - RL decisions (Engineer+)
POST /elite/opponent-analysis  - Game theory (Engineer+)
POST /elite/digital-twin       - Scenario sim (Engineer+)
POST /elite/telemetry          - Telemetry data (Admin only)
POST /elite/explain            - XAI explanations (All roles)
POST /elite/advanced-metrics   - Metrics (All roles)
```

---

## 🔑 USAGE GUIDE

### 1. First-Time Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set environment variables (optional)
export JWT_SECRET_KEY="your-super-secret-key"
export DATABASE_URL="postgresql://user:pass@localhost/f1strategy"
export ALLOWED_ORIGINS="http://localhost:3000"

# Run the application
uvicorn app.main:app --reload --port 8000
```

**Default Admin Account:**
- Username: `admin`
- Password: `admin123`
- **⚠️ Change this password after first login!**

### 2. Authentication Flow

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "engineer1",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "user_id": 2,
    "username": "engineer1",
    "email": "engineer@f1.com",
    "role": "engineer"
  }
}
```

### 3. Using Protected Endpoints

**With JWT Token:**
```bash
curl -X POST http://localhost:8000/simulate \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "circuit": "Monza",
    "laps": 53,
    "strategy_type": "auto"
  }'
```

### 4. Register New Users (Admin Only)

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@f1.com",
    "password": "SecurePass123!",
    "role": "engineer"
  }'
```

---

## 🎭 ROLE PERMISSIONS MATRIX

| Feature | VIEWER | ENGINEER | ADMIN |
|---------|--------|----------|-------|
| Basic Simulation | ✅ | ✅ | ✅ |
| Race Simulation | ✅ | ✅ | ✅ |
| Multi-Car Sim | ✅ | ✅ | ✅ |
| Weather Sim | ✅ | ✅ | ✅ |
| Live Streaming | ✅ | ✅ | ✅ |
| Monte Carlo Optimize | ❌ | ✅ | ✅ |
| RL Strategy | ❌ | ✅ | ✅ |
| Opponent Analysis | ❌ | ✅ | ✅ |
| Digital Twin | ❌ | ✅ | ✅ |
| XAI Explain | ✅ | ✅ | ✅ |
| Advanced Metrics | ✅ | ✅ | ✅ |
| Telemetry Pipeline | ❌ | ❌ | ✅ |
| Register Users | ❌ | ❌ | ✅ |
| Manage Users | ❌ | ❌ | ✅ |
| View Audit Logs | ❌ | ❌ | ✅ |

---

## 🛡️ SECURITY BEST PRACTICES

### Environment Variables
```bash
# Required for production
JWT_SECRET_KEY="your-256-bit-secret-key-here"
DATABASE_URL="postgresql://..."
ALLOWED_ORIGINS="https://yourdomain.com"
ACCESS_TOKEN_EXPIRE_MINUTES="30"
```

### Production Checklist
- [ ] Change default admin password
- [ ] Set strong JWT_SECRET_KEY
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS only
- [ ] Configure CORS for specific origins only
- [ ] Set up log rotation for audit logs
- [ ] Monitor failed login attempts
- [ ] Regular security updates

---

## 📊 SECURITY METRICS

The system tracks:
- **Authentication attempts** (success/failure)
- **Endpoint access frequency** by user
- **Rate limit violations**
- **Permission denials** (403 errors)

View statistics (Admin only):
```bash
GET /auth/users/{user_id}/activity
GET /admin/usage-statistics  # (to be implemented)
```

---

## 🔧 TROUBLESHOOTING

### "Invalid or expired token"
- Token has expired (30 minutes)
- Solution: Re-login or use refresh token

### "Admin access required"
- Endpoint requires admin role
- Solution: Use admin account or request access

### "Rate limit exceeded"
- Too many requests
- Solution: Wait for rate limit reset

### "Could not validate credentials"
- Invalid JWT format
- Solution: Ensure Bearer prefix: `Authorization: Bearer <token>`

---

## 🚀 DEPLOYMENT

### Docker (Recommended)
```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENV DATABASE_URL=${DATABASE_URL}

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment File (.env)
```
JWT_SECRET_KEY=your-super-secret-256-bit-key
DATABASE_URL=postgresql://f1user:f1pass@db:5432/f1strategy
ALLOWED_ORIGINS=https://f1strategy.yourcompany.com
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 📈 CODE STATISTICS

| Component | Lines | Purpose |
|-----------|-------|---------|
| models.py | 200 | Database & schemas |
| password_utils.py | 80 | bcrypt hashing |
| auth_handler.py | 150 | JWT operations |
| dependencies.py | 180 | RBAC middleware |
| routes.py | 250 | Auth endpoints |
| logging.py | 200 | Audit system |
| AuthContext.js | 180 | React auth |
| LoginPage.js | 350 | Login UI |
| ProtectedRoute.js | 120 | Route guards |
| **TOTAL** | **~1,710** | **Security Layer** |

---

## ✅ SECURITY COMPLIANCE

The Security Layer v3.1 implements:
- ✅ JWT-based stateless authentication
- ✅ Role-Based Access Control (RBAC)
- ✅ Password hashing with bcrypt
- ✅ Rate limiting per endpoint
- ✅ Comprehensive audit logging
- ✅ CORS protection
- ✅ Input validation (Pydantic)
- ✅ SQL injection protection (SQLAlchemy ORM)

---

## 🏆 SYSTEM STATUS

```
╔══════════════════════════════════════════════════════════════════╗
║  F1 Strategy Intelligence System v3.1                            ║
║  ELITE EDITION + SECURITY LAYER                                  ║
║                                                                   ║
║  Status: PRODUCTION-READY                                          ║
║  Authentication: JWT ACTIVE                                       ║
║  Authorization: RBAC ACTIVE                                       ║
║  Rate Limiting: ACTIVE                                           ║
║  Audit Logging: ACTIVE                                           ║
╚══════════════════════════════════════════════════════════════════╝
```

---

*Security Layer v3.1 - Professional Authentication for Championship-Grade Systems*
