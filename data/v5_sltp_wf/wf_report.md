# V5 MIX TP/SL Walk-Forward Parameter Split Report

Train window: 2021-11-07 → 2024-12-31
Test window:  2025-01-01 → 2026-04-15

Baseline cell: SL=0.03, EE=0.015, TP=0.0

## Close-only engine

- Train-best: SL=0.1, EE=1, TP=0
  - IS SR  = +3.419
  - OOS SR = +3.046
  - OOS DD = 4.5%
  - OOS Calmar = +6.69
- Baseline OOS SR = +3.318
- **Verdict: FAIL** (train-best OOS > baseline OOS? +3.046 vs +3.318)

## Intrabar engine

- Train-best: SL=0, EE=0.005, TP=0.12
  - IS SR  = +3.427
  - OOS SR = +2.994
  - OOS DD = 3.9%
  - OOS Calmar = +8.55
- Baseline OOS SR = +3.192
- **Verdict: FAIL** (train-best OOS > baseline OOS? +2.994 vs +3.192)

## Joint outcome

- Close-only: fail
- Intrabar:   fail

git SHA: 45ab012d79bdbb9dfcfe12e995329b143748739b
wall clock: 36.7 s

