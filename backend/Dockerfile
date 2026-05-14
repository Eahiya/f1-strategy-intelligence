# F1 Strategy Platform v4.0 - Production Infrastructure Edition
# Backend Dockerfile - FastAPI + ML Stack

FROM python:3.11-slim as builder

# Build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r f1user && useradd -r -g f1user f1user

# Copy Python packages from builder
COPY --from=builder /root/.local /home/f1user/.local
ENV PATH=/home/f1user/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=f1user:f1user app/ ./app/
COPY --chown=f1user:f1user data/ ./data/

# Create logs directory
RUN mkdir -p /app/logs && chown -R f1user:f1user /app

# Switch to non-root user
USER f1user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV PORT=8000

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
