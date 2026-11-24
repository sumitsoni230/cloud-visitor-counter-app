# ==============================================================================
# Cost-Optimized Multi-Stage Lightweight Dockerfile
# Base Image: Python 3.11-slim (Drastically reduces size from ~1020MB to ~135MB)
# Security: Runs as a non-privileged user (appuser)
# ==============================================================================

# Stage 1: Build stage (Installs wheels)
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal Runtime stage
FROM python:3.11-slim AS runner

# Set metadata and labels
LABEL maintainer="Cloud Computing Project Student"
LABEL description="Visitor Counter Web App with Flask and Redis"

# Create a non-root system user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /app

# Copy installed python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000 \
    REDIS_HOST=localhost \
    REDIS_PORT=6379

# Copy application source code
COPY app.py .

# Adjust ownership
RUN chown -R appuser:appgroup /app /home/appuser

# Switch to non-root user for security
USER 10001:10001

EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/healthz')" || exit 1

# Launch with production Gunicorn WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--access-logfile", "-", "app:app"]
