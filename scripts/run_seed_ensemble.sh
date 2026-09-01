#!/bin/bash
# Multi-seed LGB walk-forward: 5 seeds, canonical 78f 2-coin pool, BT8 protocol.
set -u
cd /home/malecada/master_thesis/TradingAgents-research
for SEED in 42 7 123 2024 777; do
  OUT=data/seed_ens/seed_${SEED}
  if [ -f "$OUT/preds_lgb_h14.csv" ]; then echo "seed $SEED done, skip"; continue; fi
  mkdir -p "$OUT"
  echo "=== seed $SEED start $(date) ==="
  LGB_SEED=$SEED uv run python scripts/evaluate_models_multi.py \
    --coins bitcoin ethereum --days 2200 --min-train 365 \
    --models lgb --horizons 7 14 --trade-date 2026-04-15 \
    --output-dir "$OUT" || echo "SEED $SEED FAILED"
  echo "=== seed $SEED end $(date) ==="
done
echo "ALL SEEDS DONE $(date)"
