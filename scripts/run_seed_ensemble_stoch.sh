#!/bin/bash
# Stochastic-bagging seed ensemble: subsample=0.8, colsample=0.8, freq=1.
# NOW seeds differ -> averaging can reduce variance. 5 seeds parallel.
set -u
cd /home/malecada/master_thesis/TradingAgents-research
for SEED in 42 7 123 2024 777; do
  OUT=data/seed_ens_stoch/seed_${SEED}
  [ -f "$OUT/preds_lgb_h14.csv" ] && { echo "seed $SEED done, skip"; continue; }
  mkdir -p "$OUT"
  ( echo "=== stoch seed $SEED start $(date) ===" ;
    LGB_SEED=$SEED LGB_BAGGING=0.8 LGB_FEATURE=0.8 uv run python scripts/evaluate_models_multi.py \
      --coins bitcoin ethereum --days 2200 --min-train 365 \
      --models lgb --horizons 7 14 --trade-date 2026-04-15 \
      --output-dir "$OUT" > logs/leads/stoch_seed_${SEED}.log 2>&1 \
      && echo "=== stoch seed $SEED OK $(date) ===" \
      || echo "=== stoch seed $SEED FAILED $(date) ===" ) &
done
wait
echo "ALL STOCH SEEDS DONE $(date)"
