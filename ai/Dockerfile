# 1. Build Stage
FROM python:3.11-slim AS builder

WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# AI 관련 라이브러리 컴파일용 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일만 먼저 복사 (캐시 활용)
COPY pyproject.toml uv.lock ./

# 의존성 설치 (운영 환경만, --frozen으로 lock 파일 그대로 사용)
RUN uv sync --frozen --no-dev --no-install-project

# 2. Run Stage
FROM python:3.11-slim

WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 빌드 스테이지에서 설치된 가상환경 복사
COPY --from=builder /app/.venv /app/.venv

# 소스 코드 복사
COPY . .

# 가상환경 PATH 등록
ENV PATH="/app/.venv/bin:$PATH"

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Seoul

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]