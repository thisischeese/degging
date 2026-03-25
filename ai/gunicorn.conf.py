from __future__ import annotations

import os

try:
    from prometheus_client import multiprocess
except ImportError:  # pragma: no cover - local environments may not have the package installed yet.
    multiprocess = None


bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "4"))
worker_class = "uvicorn_worker.UvicornWorker"
threads = 1
preload_app = False
timeout = int(os.getenv("GUNICORN_TIMEOUT", "300"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "60"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "200"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "20"))
accesslog = "-"
errorlog = "-"
capture_output = True
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")


def child_exit(server, worker) -> None:
    if multiprocess is not None:
        multiprocess.mark_process_dead(worker.pid)
