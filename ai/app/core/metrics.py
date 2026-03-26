from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from threading import Lock
from time import perf_counter

from fastapi import Response

from app.core.config import settings

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )
    from prometheus_client import multiprocess
except ImportError:  # pragma: no cover - fallback for environments without the package installed yet.
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    CollectorRegistry = None
    Counter = None
    Gauge = None
    Histogram = None
    generate_latest = None
    multiprocess = None


_PROMETHEUS_ENABLED = settings.prometheus_metrics_enabled and all(
    dependency is not None
    for dependency in (CollectorRegistry, Counter, Gauge, Histogram, generate_latest)
)

if _PROMETHEUS_ENABLED:
    _STAGE_SECONDS = Histogram(
        "cafe_crawling_stage_seconds",
        "Stage duration for cafe crawling requests.",
        labelnames=("stage",),
    )
    _INFLIGHT = Gauge(
        "cafe_crawling_inflight",
        "In-flight cafe crawling work.",
        labelnames=("scope",),
    )
    # Multiprocess Prometheus mode is intentionally disabled for the current
    # single-process uvicorn deployment.
    # _INFLIGHT = Gauge(
    #     "cafe_crawling_inflight",
    #     "In-flight cafe crawling work.",
    #     labelnames=("scope",),
    #     multiprocess_mode="livesum",
    # )
    _RESULTS_TOTAL = Counter(
        "cafe_crawling_results_total",
        "Count of crawl outcomes by scope and status.",
        labelnames=("scope", "status"),
    )
else:
    _LOCK = Lock()
    _COUNTERS: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
    _GAUGES: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
    _HISTOGRAM_SUMS: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
    _HISTOGRAM_COUNTS: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)


def _metrics_registry() -> CollectorRegistry | None:
    if not _PROMETHEUS_ENABLED:
        return None

    # Multiprocess Prometheus collection is intentionally disabled for the
    # current single-process uvicorn deployment.
    # if settings.prometheus_multiproc_dir and multiprocess is not None:
    #     registry = CollectorRegistry()
    #     multiprocess.MultiProcessCollector(registry)
    #     return registry
    return None


def _label_key(**labels: str) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(labels.items()))


@contextmanager
def track_stage(stage: str):
    started_at = perf_counter()
    try:
        yield
    finally:
        elapsed = perf_counter() - started_at
        if _PROMETHEUS_ENABLED:
            _STAGE_SECONDS.labels(stage=stage).observe(elapsed)
        else:
            key = ("cafe_crawling_stage_seconds", _label_key(stage=stage))
            with _LOCK:
                _HISTOGRAM_SUMS[key] += elapsed
                _HISTOGRAM_COUNTS[key] += 1


@asynccontextmanager
async def track_inflight(scope: str):
    if _PROMETHEUS_ENABLED:
        gauge = _INFLIGHT.labels(scope=scope)
        gauge.inc()
        try:
            yield
        finally:
            gauge.dec()
        return

    key = ("cafe_crawling_inflight", _label_key(scope=scope))
    with _LOCK:
        _GAUGES[key] += 1
    try:
        yield
    finally:
        with _LOCK:
            _GAUGES[key] -= 1


def record_result(*, scope: str, status: str) -> None:
    if _PROMETHEUS_ENABLED:
        _RESULTS_TOTAL.labels(scope=scope, status=status).inc()
        return

    key = ("cafe_crawling_results_total", _label_key(scope=scope, status=status))
    with _LOCK:
        _COUNTERS[key] += 1


def _render_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    body = ",".join(f'{key}="{value}"' for key, value in labels)
    return f"{{{body}}}"


def _render_fallback_metrics() -> Response:
    lines = [
        "# HELP cafe_crawling_stage_seconds Stage duration for cafe crawling requests.",
        "# TYPE cafe_crawling_stage_seconds histogram",
    ]

    with _LOCK:
        histogram_sums = list(_HISTOGRAM_SUMS.items())
        histogram_counts = dict(_HISTOGRAM_COUNTS)
        gauges = list(_GAUGES.items())
        counters = list(_COUNTERS.items())

    for (metric_name, labels), value in histogram_sums:
        label_text = _render_labels(labels)
        lines.append(f"{metric_name}_sum{label_text} {value}")
        lines.append(f"{metric_name}_count{label_text} {histogram_counts[(metric_name, labels)]}")

    lines.extend(
        [
            "# HELP cafe_crawling_inflight In-flight cafe crawling work.",
            "# TYPE cafe_crawling_inflight gauge",
        ]
    )
    for (metric_name, labels), value in gauges:
        lines.append(f"{metric_name}{_render_labels(labels)} {value}")

    lines.extend(
        [
            "# HELP cafe_crawling_results_total Count of crawl outcomes by scope and status.",
            "# TYPE cafe_crawling_results_total counter",
        ]
    )
    for (metric_name, labels), value in counters:
        lines.append(f"{metric_name}{_render_labels(labels)} {value}")

    payload = "\n".join(lines) + "\n"
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


def render_metrics() -> Response:
    if not _PROMETHEUS_ENABLED:
        return _render_fallback_metrics()

    registry = _metrics_registry()
    payload = generate_latest(registry) if registry is not None else generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
