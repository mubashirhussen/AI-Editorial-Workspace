# Multi-stage / Production-hardened Backend Dockerfile
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build essentials for native wheels if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final Runtime Image
FROM python:3.11-slim AS runner

WORKDIR /app

# Install curl for container HEALTHCHECK and libpq for PostgreSQL support
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Security: Create non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code and configuration
COPY backend /app/backend
COPY backend/alembic.ini /app/backend/alembic.ini
COPY requirements.txt /app/requirements.txt

# Create storage directory for SQLite/backups if needed and grant ownership
RUN mkdir -p /app/backend/data /app/backend/backups && \
    chown -R appuser:appgroup /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production \
    PORT=8000

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check using root liveness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Production startup
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
