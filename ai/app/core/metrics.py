from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from threading import Lock
from time import perf_counter

from fastapi import Response


CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
_LOCK = Lock()
_COUNTERS: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_GAUGES: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_HISTOGRAM_SUMS: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_HISTOGRAM_COUNTS: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)


def _label_key(**labels: str) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(labels.items()))


@contextmanager
def track_stage(stage: str):
    started_at = perf_counter()
    try:
        yield
    finally:
        key = ("cafe_crawling_stage_seconds", _label_key(stage=stage))
        elapsed = perf_counter() - started_at
        with _LOCK:
            _HISTOGRAM_SUMS[key] += elapsed
            _HISTOGRAM_COUNTS[key] += 1


@asynccontextmanager
async def track_inflight(scope: str):
    key = ("cafe_crawling_inflight", _label_key(scope=scope))
    with _LOCK:
        _GAUGES[key] += 1
    try:
        yield
    finally:
        with _LOCK:
            _GAUGES[key] -= 1


def record_result(*, scope: str, status: str) -> None:
    key = ("cafe_crawling_results_total", _label_key(scope=scope, status=status))
    with _LOCK:
        _COUNTERS[key] += 1


def _render_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    body = ",".join(f'{key}="{value}"' for key, value in labels)
    return f"{{{body}}}"


def render_metrics() -> Response:
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
