#!/usr/bin/env bash
# Invoke generate_agent_signals.py in a loop, restarting on any non-zero exit
# (transient OpenAI outage, connection drop, crash, anything). The runner is
# idempotent — resumes from partial CSVs and refills ERROR rows. Safe to run
# for hours unattended.
#
# Usage:
#   scripts/run_until_done.sh --coins bitcoin ethereum --start 2026-01-16 \
#       --end 2026-04-15 --analysts market onchain prediction crypto_sentiment \
#       --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
#       --sentiment-mode pit --output-dir data/agent_signals_pit_p3
#
# Every arg after the script name is forwarded verbatim to the underlying
# generate_agent_signals.py.

set -u

PYBIN="${PYBIN:-/usr/bin/python3}"
MAX_RESTARTS="${MAX_RESTARTS:-50}"
RESTART_SLEEP="${RESTART_SLEEP:-15}"

cd "$(dirname "$0")/.."
LOG_DIR="${LOG_DIR:-/tmp/agent_signals_gen}"
mkdir -p "$LOG_DIR"

attempt=0
while [ "$attempt" -lt "$MAX_RESTARTS" ]; do
    attempt=$((attempt + 1))
    ts=$(date -u +"%Y%m%dT%H%M%SZ")
    log="$LOG_DIR/run_${ts}_attempt${attempt}.log"
    echo "[run_until_done] attempt=${attempt} log=${log}"
    $PYBIN scripts/generate_agent_signals.py "$@" >"$log" 2>&1
    rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "[run_until_done] generate_agent_signals exited 0 — done"
        exit 0
    fi
    echo "[run_until_done] exit code ${rc} — sleeping ${RESTART_SLEEP}s before retry"
    sleep "$RESTART_SLEEP"
done
echo "[run_until_done] gave up after ${MAX_RESTARTS} attempts"
exit 1
