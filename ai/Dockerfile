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
RUN uv sync --frozen --no-dev --no-install-project

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

# Install Chromium and its OS dependencies into the runtime image
RUN playwright install --with-deps chromium

# Copy the application source after dependency installation for better caching
COPY . .

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
