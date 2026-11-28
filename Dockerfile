# ==========================================
# Build stage with Python 3.11 slim
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies if required for C/C++ compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in an isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# Final runtime stage
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime curl for healthcheck validation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Environment defaults (Render overrides PORT at runtime)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Copy application code, static assets, and data files
COPY engine ./engine
COPY data ./data
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create non-root user for security best practices
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Document default port
EXPOSE 8000

# Docker/Render local healthcheck probe (reads dynamically assigned $PORT)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD sh -c "curl -f http://127.0.0.1:${PORT:-8000}/healthz || exit 1"

# Launch Uvicorn on the port Render assigns ($PORT).
#  - exec: uvicorn becomes PID 1 so Render's SIGTERM triggers a clean shutdown
#  - --proxy-headers / --forwarded-allow-ips: trust Render's proxy so redirects
#    (e.g. /app -> /app/) keep https instead of downgrading to http
#  - --timeout-keep-alive 75: stay above the proxy's idle timeout to avoid sporadic 502s
CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --timeout-keep-alive 75"]
