# 1. Build Stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Build dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for better layer caching
COPY pyproject.toml uv.lock ./

# Install runtime dependencies into the virtual environment
RUN uv sync --no-dev --no-install-project

# 2. Run Stage
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy the prebuilt virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Make the virtualenv and Playwright browser bundle available at runtime
ENV PATH="/app/.venv/bin:$PATH"
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Runtime environment settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Seoul
# Keep WEB_CONCURRENCY unset so uvicorn stays single-process.
# ENV WEB_CONCURRENCY=4
# ENV GUNICORN_TIMEOUT=300
# ENV GUNICORN_GRACEFUL_TIMEOUT=60
# ENV GUNICORN_KEEPALIVE=5
# ENV GUNICORN_MAX_REQUESTS=200
# ENV GUNICORN_MAX_REQUESTS_JITTER=20
# Single-process uvicorn does not need Prometheus multiprocess mode.
# ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
ENV POSTGRES_POOL_MIN_SIZE=1
ENV POSTGRES_POOL_MAX_SIZE=5
ENV MONGO_MAX_POOL_SIZE=20
# 베어메탈 방식으로 구현 시, 주석 해제할 것 
# ENV CAFE_BATCH_CONCURRENCY=2
ENV CAFE_BATCH_CONCURRENCY=3

# Install Chromium and its OS dependencies into the runtime image
RUN playwright install --with-deps chromium

# Copy the application source after dependency installation for better caching
COPY . .

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
# 베어메탈 방식으로 구현 시, 주석 해제할 것 
# RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000
# 베어메탈 방식으로 구현 시, 주석 해제할 것 
# ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
