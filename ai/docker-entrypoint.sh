#!/bin/sh
set -eu

# PROM_DIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/prometheus}"
# rm -rf "$PROM_DIR"
# mkdir -p "$PROM_DIR"
# exec gunicorn -c /app/gunicorn.conf.py app.main:app

exec uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}"
