# Phase 1 Performance Check

## Prerequisites
- Run the app with the new crawler settings enabled.
- Install `k6` on the load generator host.
- Keep `/metrics` reachable from the same network.

## 4-Core Docker Run
```bash
docker build -t cafe-ai-local .
docker run --rm --cpus=4 -p 8000:8000 --env-file .env cafe-ai-local
```

## Baseline / After Commands
```bash
k6 run perf/k6/cafe-crawling.js -e BASE_URL=http://127.0.0.1:8000 -e PAYLOAD=1-cafe -e ITERATIONS=10
k6 run perf/k6/cafe-crawling.js -e BASE_URL=http://127.0.0.1:8000 -e PAYLOAD=3-cafe -e ITERATIONS=10
k6 run perf/k6/cafe-crawling.js -e BASE_URL=http://127.0.0.1:8000 -e PAYLOAD=5-cafe -e ITERATIONS=10
```

## Concurrent Smoke
```bash
k6 run perf/k6/cafe-crawling.js -e BASE_URL=http://127.0.0.1:8000 -e PAYLOAD=3-cafe -e VUS=3 -e ITERATIONS=9
```

## 5-Cafe Baseline / After
```powershell
powershell -ExecutionPolicy Bypass -File .\perf\Compare-5Cafe.ps1 -BaselineUrl http://127.0.0.1:8000 -AfterUrl http://127.0.0.1:8001 -Iterations 10
```

## Metrics To Compare
- `cafe_crawling_stage_seconds`
- `cafe_crawling_inflight`
- `cafe_crawling_results_total`

## Success Targets
- 1-cafe `p50` latency improves by at least 30%.
- 5-cafe batch wall time improves by at least 60%.
- Error-rate regression stays within 1 percentage point.
