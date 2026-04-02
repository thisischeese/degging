#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  capture_process_stats.sh OUTPUT_DIR -- COMMAND [ARGS...]
  capture_process_stats.sh OUTPUT_DIR --pid PID -- COMMAND [ARGS...]

Examples:
  capture_process_stats.sh perf/results/ner-only -- uv run python perf/bench_ner_inference.py
  capture_process_stats.sh perf/results/map-search --pid 1234 -- k6 run perf/k6/map-search.js
EOF
}

if [[ $# -lt 3 ]]; then
  usage
  exit 1
fi

OUTPUT_DIR=$1
shift

TARGET_PID=""
if [[ "${1:-}" == "--pid" ]]; then
  TARGET_PID=${2:-}
  if [[ -z "$TARGET_PID" ]]; then
    echo "Missing PID after --pid" >&2
    exit 1
  fi
  shift 2
fi

if [[ "${1:-}" != "--" ]]; then
  usage
  exit 1
fi
shift

if [[ $# -lt 1 ]]; then
  echo "Missing command to execute" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

COMMAND_STDOUT="$OUTPUT_DIR/command.stdout.txt"
COMMAND_STDERR="$OUTPUT_DIR/command.stderr.txt"
PIDSTAT_OUTPUT="$OUTPUT_DIR/pidstat.txt"
STATUS_BEFORE="$OUTPUT_DIR/proc-status.before.txt"
STATUS_AFTER="$OUTPUT_DIR/proc-status.after.txt"
LIMITS_OUTPUT="$OUTPUT_DIR/proc-limits.txt"
EXIT_CODE_OUTPUT="$OUTPUT_DIR/command.exit-code.txt"

PIDSTAT_PID=""
COMMAND_PID=""

cleanup() {
  if [[ -n "$PIDSTAT_PID" ]]; then
    kill "$PIDSTAT_PID" >/dev/null 2>&1 || true
    wait "$PIDSTAT_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

if [[ -z "$TARGET_PID" ]]; then
  "$@" >"$COMMAND_STDOUT" 2>"$COMMAND_STDERR" &
  COMMAND_PID=$!
  TARGET_PID=$COMMAND_PID
else
  COMMAND_PID=0
fi

if [[ ! -d "/proc/$TARGET_PID" ]]; then
  echo "Target PID '$TARGET_PID' is not available under /proc" >&2
  if [[ "$COMMAND_PID" -ne 0 ]]; then
    wait "$COMMAND_PID" || true
  fi
  exit 1
fi

cat "/proc/$TARGET_PID/status" >"$STATUS_BEFORE"
cat "/proc/$TARGET_PID/limits" >"$LIMITS_OUTPUT"
pidstat -u -t 1 -p "$TARGET_PID" >"$PIDSTAT_OUTPUT" 2>&1 &
PIDSTAT_PID=$!

if [[ "$COMMAND_PID" -ne 0 ]]; then
  set +e
  wait "$COMMAND_PID"
  COMMAND_EXIT_CODE=$?
  set -e
else
  set +e
  "$@" >"$COMMAND_STDOUT" 2>"$COMMAND_STDERR"
  COMMAND_EXIT_CODE=$?
  set -e
fi

echo "$COMMAND_EXIT_CODE" >"$EXIT_CODE_OUTPUT"

if [[ -d "/proc/$TARGET_PID" ]]; then
  cat "/proc/$TARGET_PID/status" >"$STATUS_AFTER"
fi

exit "$COMMAND_EXIT_CODE"
