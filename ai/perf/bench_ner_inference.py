from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.query_preprocess_service import (  # noqa: E402
    _load_menu_ner_components,
    run_menu_ner_inference,
)

DEFAULT_CONCURRENCY_LEVELS = (1, 2, 4, 8, 16)
DEFAULT_WARMUP_REQUESTS = 30
DEFAULT_MEASURED_REQUESTS = 300
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "query-preprocess-corpus.json"
RESULTS_ROOT = Path(__file__).resolve().parent / "results"


@dataclass(slots=True)
class InvocationSample:
    query: str
    queue_delay_ms: float
    service_time_ms: float
    total_latency_ms: float


def _load_corpus(path: Path) -> list[str]:
    corpus = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(corpus, list) or not corpus:
        raise ValueError(f"Corpus at '{path}' must be a non-empty JSON array.")
    normalized_queries = [str(query).strip() for query in corpus if str(query).strip()]
    if not normalized_queries:
        raise ValueError(f"Corpus at '{path}' does not contain any non-blank query.")
    return normalized_queries


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    rank = (len(sorted_values) - 1) * percentile
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    weight = rank - lower_index
    return lower_value + (upper_value - lower_value) * weight


def _summarize_latency(values: list[float]) -> dict[str, float]:
    if not values:
        return {
            "count": 0,
            "min_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
        }
    return {
        "count": len(values),
        "min_ms": round(min(values), 3),
        "p50_ms": round(_percentile(values, 0.50), 3),
        "p95_ms": round(_percentile(values, 0.95), 3),
        "p99_ms": round(_percentile(values, 0.99), 3),
        "max_ms": round(max(values), 3),
    }


def _read_proc_status(pid: int) -> dict[str, int] | None:
    status_path = Path(f"/proc/{pid}/status")
    if not status_path.is_file():
        return None

    snapshot: dict[str, int] = {}
    for line in status_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            snapshot["rss_kb"] = int(line.split()[1])
        elif line.startswith("Threads:"):
            snapshot["threads"] = int(line.split()[1])
    return snapshot or None


async def _run_burst(queries: list[str]) -> tuple[list[InvocationSample], list[str]]:
    if not queries:
        return [], []

    release_event = asyncio.Event()
    release_time = {"value": 0.0}

    async def worker(query: str) -> InvocationSample:
        await release_event.wait()
        released_at = release_time["value"]
        started_at = perf_counter()
        run_menu_ner_inference(query)
        finished_at = perf_counter()
        return InvocationSample(
            query=query,
            queue_delay_ms=(started_at - released_at) * 1000,
            service_time_ms=(finished_at - started_at) * 1000,
            total_latency_ms=(finished_at - released_at) * 1000,
        )

    tasks = [asyncio.create_task(worker(query)) for query in queries]
    await asyncio.sleep(0)
    release_time["value"] = perf_counter()
    release_event.set()

    samples: list[InvocationSample] = []
    errors: list[str] = []
    for result in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(result, Exception):
            errors.append(repr(result))
            continue
        samples.append(result)
    return samples, errors


async def _run_phase(
    *,
    corpus: list[str],
    total_requests: int,
    concurrency: int,
) -> tuple[list[InvocationSample], list[str]]:
    samples: list[InvocationSample] = []
    errors: list[str] = []
    query_index = 0

    while len(samples) + len(errors) < total_requests:
        burst_size = min(concurrency, total_requests - len(samples) - len(errors))
        burst_queries = [
            corpus[(query_index + offset) % len(corpus)]
            for offset in range(burst_size)
        ]
        query_index += burst_size
        burst_samples, burst_errors = await _run_burst(burst_queries)
        samples.extend(burst_samples)
        errors.extend(burst_errors)

    return samples, errors


async def _benchmark_concurrency(
    *,
    corpus: list[str],
    concurrency: int,
    warmup_requests: int,
    measured_requests: int,
) -> dict[str, Any]:
    if warmup_requests > 0:
        await _run_phase(
            corpus=corpus,
            total_requests=warmup_requests,
            concurrency=concurrency,
        )

    process_snapshot_before = _read_proc_status(os.getpid())
    measured_started_at = perf_counter()
    samples, errors = await _run_phase(
        corpus=corpus,
        total_requests=measured_requests,
        concurrency=concurrency,
    )
    measured_elapsed = perf_counter() - measured_started_at
    process_snapshot_after = _read_proc_status(os.getpid())

    queue_delays = [sample.queue_delay_ms for sample in samples]
    service_times = [sample.service_time_ms for sample in samples]
    total_latencies = [sample.total_latency_ms for sample in samples]

    return {
        "concurrency": concurrency,
        "warmup_requests": warmup_requests,
        "measured_requests": measured_requests,
        "completed_requests": len(samples),
        "error_count": len(errors),
        "errors": errors[:10],
        "throughput_rps": round(len(samples) / measured_elapsed, 3) if measured_elapsed > 0 else 0.0,
        "queue_delay": _summarize_latency(queue_delays),
        "service_time": _summarize_latency(service_times),
        "total_latency": _summarize_latency(total_latencies),
        "process_snapshot_before": process_snapshot_before,
        "process_snapshot_after": process_snapshot_after,
    }


async def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark isolated menu NER inference under burst concurrency.",
    )
    parser.add_argument(
        "--profile-name",
        default="production-like",
        help="Label written into the results payload.",
    )
    parser.add_argument(
        "--warmup-requests",
        type=int,
        default=DEFAULT_WARMUP_REQUESTS,
        help="Warmup requests per concurrency level.",
    )
    parser.add_argument(
        "--measured-requests",
        type=int,
        default=DEFAULT_MEASURED_REQUESTS,
        help="Measured requests per concurrency level.",
    )
    parser.add_argument(
        "--concurrency",
        nargs="*",
        type=int,
        default=list(DEFAULT_CONCURRENCY_LEVELS),
        help="Concurrency burst sizes to benchmark.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional results directory. Defaults to perf/results/ner-benchmark-<timestamp>.",
    )
    args = parser.parse_args()

    if args.warmup_requests < 0 or args.measured_requests <= 0:
        raise ValueError("Warmup requests must be >= 0 and measured requests must be > 0.")
    if not args.concurrency or any(level <= 0 for level in args.concurrency):
        raise ValueError("Concurrency levels must contain positive integers.")

    corpus = _load_corpus(FIXTURE_PATH)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_dir or RESULTS_ROOT / f"ner-benchmark-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    _load_menu_ner_components.cache_clear()
    cold_load_snapshot_before = _read_proc_status(os.getpid())
    cold_load_started_at = perf_counter()
    _load_menu_ner_components()
    cold_load_elapsed = perf_counter() - cold_load_started_at
    cold_load_snapshot_after = _read_proc_status(os.getpid())

    results = []
    for concurrency in args.concurrency:
        benchmark = await _benchmark_concurrency(
            corpus=corpus,
            concurrency=concurrency,
            warmup_requests=args.warmup_requests,
            measured_requests=args.measured_requests,
        )
        results.append(benchmark)

    payload = {
        "profile_name": args.profile_name,
        "environment": {
            "TOKENIZERS_PARALLELISM": os.getenv("TOKENIZERS_PARALLELISM"),
            "OMP_NUM_THREADS": os.getenv("OMP_NUM_THREADS"),
            "MKL_NUM_THREADS": os.getenv("MKL_NUM_THREADS"),
        },
        "corpus_path": str(FIXTURE_PATH),
        "corpus_size": len(corpus),
        "cold_load": {
            "load_seconds": round(cold_load_elapsed, 3),
            "process_snapshot_before": cold_load_snapshot_before,
            "process_snapshot_after": cold_load_snapshot_after,
        },
        "benchmarks": results,
    }

    output_path = output_dir / "summary.json"
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"NER benchmark summary written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
