#!/usr/bin/env bash
# Audit remediation: regenerate all 8 V5 MIX route prediction dirs under
#   (A) purged expanding window        -> data/audit_fix/purged/<route>
#   (B) purged rolling 730d window     -> data/audit_fix/rolling730/<route>
# Protocol otherwise identical to THESIS_FINDINGS §20:
#   --days 2200 --min-train 365 --models lgb --horizons 7 14 --trade-date 2026-04-15
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
BASE="--horizons 7 14 --days 2200 --min-train 365 --models lgb --trade-date 2026-04-15 --purge"
LOGDIR=data/audit_fix/logs
mkdir -p "$LOGDIR"

# route_name|coins|extra
ROUTES=(
  "multi_2coins_walkforward|bitcoin ethereum|"
  "multi_2coins_pit_wf|bitcoin ethereum|--onchain-pit"
  "multi_3coins_bnb_wf|bitcoin ethereum binancecoin|"
  "multi_3coins_sol_pit_wf|bitcoin ethereum solana|--onchain-pit"
  "multi_3coins_xrp_wf|bitcoin ethereum ripple|"
  "multi_3coins_doge_wf|bitcoin ethereum dogecoin|"
  "multi_3coins_ada_pit_wf|bitcoin ethereum cardano|--onchain-pit"
  "multi_3coins_trx_wf|bitcoin ethereum tron|"
)

JOBS=()
for r in "${ROUTES[@]}"; do
  IFS='|' read -r name coins extra <<<"$r"
  JOBS+=("purged/$name|$coins|$extra|")
  JOBS+=("rolling730/$name|$coins|$extra|--train-window-days 730")
done

run_job() {
  local spec="$1"
  IFS='|' read -r out coins extra window <<<"$spec"
  local log="$LOGDIR/$(echo "$out" | tr '/' '_').log"
  if [ -f "data/audit_fix/$out/summary.csv" ]; then
    echo "SKIP $out (summary exists)"
    return 0
  fi
  echo "START $out $(date -u +%H:%M:%S)"
  OMP_NUM_THREADS=2 $PY scripts/evaluate_models_multi.py \
    --coins $coins $BASE $extra $window \
    --output-dir "data/audit_fix/$out" >"$log" 2>&1
  local rc=$?
  echo "DONE  $out rc=$rc $(date -u +%H:%M:%S)"
  return $rc
}
export -f run_job 2>/dev/null || true

FAIL=0
printf '%s\n' "${JOBS[@]}" | while read -r spec; do echo "$spec"; done >"$LOGDIR/queue.txt"
N_PAR="${N_PAR:-3}"
i=0
pids=()
for spec in "${JOBS[@]}"; do
  run_job "$spec" &
  pids+=($!)
  i=$((i + 1))
  if (( i % N_PAR == 0 )); then
    for p in "${pids[@]}"; do wait "$p" || FAIL=1; done
    pids=()
  fi
done
for p in "${pids[@]}"; do wait "$p" || FAIL=1; done
echo "ALL DONE fail=$FAIL $(date -u)"
