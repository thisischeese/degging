from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class MetricSpec:
    metric_type: str
    description: str
    labelnames: tuple[str, ...]


_METRIC_SPECS = {
    "cafe_crawling_stage_seconds": MetricSpec(
        metric_type="histogram",
        description="Stage duration for cafe crawling requests.",
        labelnames=("stage",),
    ),
    "cafe_crawling_inflight": MetricSpec(
        metric_type="gauge",
        description="In-flight cafe crawling work.",
        labelnames=("scope",),
    ),
    "cafe_crawling_results_total": MetricSpec(
        metric_type="counter",
        description="Count of crawl outcomes by scope and status.",
        labelnames=("scope", "status"),
    ),
    "query_preprocess_stage_seconds": MetricSpec(
        metric_type="histogram",
        description="Stage duration for query preprocessing work.",
        labelnames=("stage",),
    ),
    "query_preprocess_inflight": MetricSpec(
        metric_type="gauge",
        description="In-flight query preprocessing work.",
        labelnames=("stage",),
    ),
    "map_search_stage_seconds": MetricSpec(
        metric_type="histogram",
        description="Stage duration for map search requests.",
        labelnames=("stage",),
    ),
}

_PROMETHEUS_ENABLED = settings.prometheus_metrics_enabled and all(
    dependency is not None
    for dependency in (CollectorRegistry, Counter, Gauge, Histogram, generate_latest)
)

if _PROMETHEUS_ENABLED:
    _PROMETHEUS_METRICS: dict[str, object] = {}
    for metric_name, spec in _METRIC_SPECS.items():
        if spec.metric_type == "histogram":
            _PROMETHEUS_METRICS[metric_name] = Histogram(
                metric_name,
                spec.description,
                labelnames=spec.labelnames,
            )
        elif spec.metric_type == "gauge":
            _PROMETHEUS_METRICS[metric_name] = Gauge(
                metric_name,
                spec.description,
                labelnames=spec.labelnames,
            )
        elif spec.metric_type == "counter":
            _PROMETHEUS_METRICS[metric_name] = Counter(
                metric_name,
                spec.description,
                labelnames=spec.labelnames,
            )
        else:  # pragma: no cover - defensive branch for future edits.
            raise ValueError(f"Unsupported metric type: {spec.metric_type}")
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


def _metric_spec(metric_name: str) -> MetricSpec:
    try:
        return _METRIC_SPECS[metric_name]
    except KeyError as exc:  # pragma: no cover - defensive branch for future edits.
        raise ValueError(f"Unknown metric: {metric_name}") from exc


def _normalize_labels(metric_name: str, **labels: str) -> dict[str, str]:
    spec = _metric_spec(metric_name)
    provided_label_names = tuple(sorted(labels))
    expected_label_names = tuple(sorted(spec.labelnames))
    if provided_label_names != expected_label_names:
        raise ValueError(
            f"Metric '{metric_name}' labels must be {expected_label_names}, got {provided_label_names}."
        )
    return {label_name: str(labels[label_name]) for label_name in spec.labelnames}


def _label_key(**labels: str) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(labels.items()))


def _observe_histogram(metric_name: str, value: float, **labels: str) -> None:
    normalized_labels = _normalize_labels(metric_name, **labels)
    if _PROMETHEUS_ENABLED:
        histogram = _PROMETHEUS_METRICS[metric_name]
        histogram.labels(**normalized_labels).observe(value)
        return

    key = (metric_name, _label_key(**normalized_labels))
    with _LOCK:
        _HISTOGRAM_SUMS[key] += value
        _HISTOGRAM_COUNTS[key] += 1


def _change_gauge(metric_name: str, delta: float, **labels: str) -> None:
    normalized_labels = _normalize_labels(metric_name, **labels)
    if _PROMETHEUS_ENABLED:
        gauge = _PROMETHEUS_METRICS[metric_name]
        if delta >= 0:
            gauge.labels(**normalized_labels).inc(delta)
        else:
            gauge.labels(**normalized_labels).dec(-delta)
        return

    key = (metric_name, _label_key(**normalized_labels))
    with _LOCK:
        _GAUGES[key] += delta


def _increment_counter(metric_name: str, amount: float = 1.0, **labels: str) -> None:
    normalized_labels = _normalize_labels(metric_name, **labels)
    if _PROMETHEUS_ENABLED:
        counter = _PROMETHEUS_METRICS[metric_name]
        counter.labels(**normalized_labels).inc(amount)
        return

    key = (metric_name, _label_key(**normalized_labels))
    with _LOCK:
        _COUNTERS[key] += amount


@contextmanager
def _track_histogram(metric_name: str, **labels: str):
    started_at = perf_counter()
    try:
        yield
    finally:
        _observe_histogram(metric_name, perf_counter() - started_at, **labels)


@contextmanager
def _track_gauge(metric_name: str, **labels: str):
    _change_gauge(metric_name, 1.0, **labels)
    try:
        yield
    finally:
        _change_gauge(metric_name, -1.0, **labels)


@contextmanager
def track_stage(stage: str):
    with _track_histogram("cafe_crawling_stage_seconds", stage=stage):
        yield


@asynccontextmanager
async def track_inflight(scope: str):
    with _track_gauge("cafe_crawling_inflight", scope=scope):
        yield


def record_result(*, scope: str, status: str) -> None:
    _increment_counter("cafe_crawling_results_total", scope=scope, status=status)


@contextmanager
def track_query_preprocess_stage(stage: str):
    with _track_histogram("query_preprocess_stage_seconds", stage=stage):
        yield


@contextmanager
def track_query_preprocess_inflight(stage: str):
    with _track_gauge("query_preprocess_inflight", stage=stage):
        yield


@contextmanager
def track_map_search_stage(stage: str):
    with _track_histogram("map_search_stage_seconds", stage=stage):
        yield


def _render_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    body = ",".join(f'{key}="{value}"' for key, value in labels)
    return f"{{{body}}}"


def _render_fallback_metrics() -> Response:
    with _LOCK:
        histogram_sums = list(_HISTOGRAM_SUMS.items())
        histogram_counts = dict(_HISTOGRAM_COUNTS)
        gauges = list(_GAUGES.items())
        counters = list(_COUNTERS.items())

    lines: list[str] = []
    for metric_name, spec in _METRIC_SPECS.items():
        lines.append(f"# HELP {metric_name} {spec.description}")
        lines.append(f"# TYPE {metric_name} {spec.metric_type}")

        if spec.metric_type == "histogram":
            for (current_metric_name, labels), value in histogram_sums:
                if current_metric_name != metric_name:
                    continue
                label_text = _render_labels(labels)
                lines.append(f"{metric_name}_sum{label_text} {value}")
                lines.append(
                    f"{metric_name}_count{label_text} {histogram_counts[(metric_name, labels)]}"
                )
        elif spec.metric_type == "gauge":
            for (current_metric_name, labels), value in gauges:
                if current_metric_name != metric_name:
                    continue
                lines.append(f"{metric_name}{_render_labels(labels)} {value}")
        elif spec.metric_type == "counter":
            for (current_metric_name, labels), value in counters:
                if current_metric_name != metric_name:
                    continue
                lines.append(f"{metric_name}{_render_labels(labels)} {value}")

    payload = "\n".join(lines) + "\n"
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


def render_metrics() -> Response:
    if not _PROMETHEUS_ENABLED:
        return _render_fallback_metrics()

    registry = _metrics_registry()
    payload = generate_latest(registry) if registry is not None else generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
