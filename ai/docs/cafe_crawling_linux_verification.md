# Cafe Crawling Linux Verification

Use these commands on the Linux server before, during, and after a large crawl batch to verify that browser workers are being recycled cleanly and that process or file descriptor growth returns to baseline.

## Commands

```bash
docker exec ai-container sh -lc "ps -eo pid,ppid,stat,rss,cmd | egrep 'uvicorn|chrome-headless|playwright|node'"
docker exec ai-container sh -lc "ps -eo stat,pid,ppid,cmd | awk '\$1 ~ /^Z/'"
docker exec ai-container sh -lc "PID=\$(pgrep -fo 'uvicorn app.main:app'); ls /proc/\$PID/fd | wc -l"
docker exec ai-container sh -lc "PID=\$(pgrep -fo 'uvicorn app.main:app'); egrep 'VmRSS|Threads|FDSize' /proc/\$PID/status"
docker exec ai-container sh -lc "PID=\$(pgrep -fo 'uvicorn app.main:app'); grep 'open files' /proc/\$PID/limits"
```

## What To Look For

- Child `chrome-headless` and Playwright `node` processes should rise during the batch and return near baseline within 30 seconds after the batch finishes.
- `ps` output should not accumulate zombie (`Z`) children across repeated batches.
- The Uvicorn process file descriptor count should not increase monotonically across repeated `50` item batches.
- `VmRSS`, `Threads`, and `FDSize` should stabilize after each batch instead of stepping upward forever.

## Log Signals

- `Cafe crawling batch worker setup` confirms the queue worker count and recycle threshold applied for the batch.
- `Cafe crawling resource state: event=browser_launch` confirms worker browser launches.
- `Cafe crawling resource state: event=browser_recycle` confirms a worker browser was recycled after the configured threshold or a failure.
- `Cafe crawling batch complete ... resource_counters=...` provides the in-process counter snapshot to compare with Linux process and FD observations.

## Interpretation Guide

- If `empty_result` starts repeating while Linux process count and FD count stay stable, focus on shared browser state corruption or anti-bot behavior rather than cleanup leaks.
- If process count, RSS, or FD count grows after every batch and does not return near baseline, treat it as effective resource leakage even if `close()` calls are present in code.
- If `browser_recycle` logs appear before the failure pattern stops spreading, the worker browser recycling is containing the issue to a single worker generation instead of poisoning the entire batch.
