#!/bin/bash
# Resilient parallel runner for the 4 hybrid signal-gen experiments.
# Each gen resumes from its CSV (skips cached dates). Retry up to 3x on death.
set -u
cd /home/malecada/master_thesis/TradingAgents-research
START=2025-04-18; END=2026-04-15
EXPECT=365   # ~363 daily bars + header slack

run_one() {
  local name=$1 coin=$2 preset=$3 outdir=$4; shift 4
  local analysts="$*"
  local csv="data/$outdir/${coin}_${START}_${END}.csv"
  for attempt in 1 2 3 4; do
    local have=0; [ -f "$csv" ] && have=$(wc -l < "$csv")
    if [ "$have" -ge "$EXPECT" ]; then echo "[$name] complete ($have rows)"; return 0; fi
    echo "[$name] attempt $attempt, have=$have rows, $(date)"
    uv run python scripts/generate_hybrid_signals.py \
      --coins "$coin" --start "$START" --end "$END" \
      --analysts $analysts --quant-version v5 --quant-pool-preset "$preset" \
      --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
      --output-dir "data/$outdir" >> "logs/leads/${name}.log" 2>&1
    sleep 5
  done
  echo "[$name] EXHAUSTED retries, $(date)"
}

run_one bnb_1y      binancecoin v5_4coin hybrid_signals_v5_bnbsol_1y      market onchain prediction &
run_one sol_1y      solana      v5_4coin hybrid_signals_v5_bnbsol_1y      market onchain prediction &
run_one eth_prod3   ethereum    v5_2coin hybrid_signals_v5_eth_prod3_1y   market onchain prediction &
run_one eth_dropmkt ethereum    v5_2coin hybrid_signals_v5_eth_dropmkt_1y onchain prediction &
wait
echo "ALL HYBRID GENS DONE $(date)"
