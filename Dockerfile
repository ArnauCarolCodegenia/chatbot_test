# =============================================================================
# Google ADK Project — Dockerfile
# =============================================================================
# Multi-stage build: keeps the final image lean (~200 MB vs ~600 MB).
# The ADK web server listens on PORT (default 8080).
# =============================================================================

# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Expose ADK web port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Default: run ADK web server
# Override CMD in docker-compose or k8s for other modes (e.g. "python main.py")
ENV PORT=8080
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]
