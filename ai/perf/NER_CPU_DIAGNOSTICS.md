# NER CPU Diagnostics

This harness separates the diagnosis into three layers:

- `NER-only`: isolated `run_menu_ner_inference()` burst benchmark
- `query-preprocess`: deprecated HTTP surface used as a focused end-to-end probe
- `map-search`: full `/ai/map/search` path with DB and dense-query work included

## Fixed Inputs

- Query corpus: `perf/fixtures/query-preprocess-corpus.json`
- Map search base payload: `perf/fixtures/map-search-base.json`
- Concurrency levels: `1 2 4 8 16`
- Warmup: `30` requests per surface and concurrency
- Measured phase: `300` requests per surface and concurrency

## Profiles

### Production-like

Run with the current environment as-is.

### Controlled CPU

```bash
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

## 1. NER-only Benchmark

```bash
uv run python perf/bench_ner_inference.py --profile-name production-like
```

Controlled CPU:

```bash
TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
uv run python perf/bench_ner_inference.py --profile-name controlled-cpu
```

Results are written to `perf/results/ner-benchmark-<timestamp>/summary.json`.

The summary records:

- cold model load time
- `queue_delay`, `service_time`, and `total_latency`
- `p50`, `p95`, `p99`, `max`
- throughput
- Linux `/proc/<pid>/status` snapshots when available

## 2. Query Preprocess HTTP Load

Warmup:

```bash
k6 run perf/k6/query-preprocess.js -e BASE_URL=http://127.0.0.1:8000 -e VUS=4 -e ITERATIONS=30
```

Measured:

```bash
k6 run perf/k6/query-preprocess.js \
  -e BASE_URL=http://127.0.0.1:8000 \
  -e VUS=4 \
  -e ITERATIONS=300 \
  --summary-export perf/results/query-preprocess-v4-summary.json
```

## 3. Map Search HTTP Load

Warmup:

```bash
k6 run perf/k6/map-search.js -e BASE_URL=http://127.0.0.1:8000 -e VUS=4 -e ITERATIONS=30
```

Measured:

```bash
k6 run perf/k6/map-search.js \
  -e BASE_URL=http://127.0.0.1:8000 \
  -e VUS=4 \
  -e ITERATIONS=300 \
  --summary-export perf/results/map-search-v4-summary.json
```

Repeat the warmup and measured pair for `VUS=1,2,4,8,16`.

## 4. Linux CPU and /proc Capture

Make the helper executable once on the Linux host:

```bash
chmod +x perf/linux/capture_process_stats.sh
```

Observe a running `uvicorn` PID while a load command executes:

```bash
PID=$(pgrep -fo 'uvicorn app.main:app')
perf/linux/capture_process_stats.sh perf/results/map-search-v4 --pid "$PID" -- \
  k6 run perf/k6/map-search.js -e BASE_URL=http://127.0.0.1:8000 -e VUS=4 -e ITERATIONS=300
```

Observe the isolated NER benchmark process directly:

```bash
perf/linux/capture_process_stats.sh perf/results/ner-only -- \
  uv run python perf/bench_ner_inference.py --profile-name production-like
```

Each capture writes:

- `pidstat.txt`
- `proc-status.before.txt`
- `proc-status.after.txt`
- `proc-limits.txt`
- `command.stdout.txt`
- `command.stderr.txt`
- `command.exit-code.txt`

## 5. Interpretation Rules

- Confirm `NER CPU bottleneck` when `NER-only` `total_latency p99` rises sharply with concurrency and `pidstat` shows sustained CPU pressure, while DB-related stages do not rise proportionally.
- Confirm `NER is not the primary bottleneck` when `NER-only` tail latency remains flat but `query-preprocess` or `map-search` tail latency grows.
- Confirm `mixed bottleneck` when `NER-only` degrades and the HTTP layers also show DB or pool-related stage growth.

Use `/metrics` to compare stage histograms across the HTTP surfaces:

- `query_preprocess_stage_seconds{stage="mecab_analysis"}`
- `query_preprocess_stage_seconds{stage="ner_inference"}`
- `query_preprocess_stage_seconds{stage="ner_postprocess"}`
- `query_preprocess_stage_seconds{stage="query_encoding"}`
- `query_preprocess_stage_seconds{stage="preprocess_total"}`
- `map_search_stage_seconds{stage="preprocess_total"}`
- `map_search_stage_seconds{stage="candidate_lookup"}`
- `map_search_stage_seconds{stage="menu_lookup"}`
- `map_search_stage_seconds{stage="map_search_total"}`
