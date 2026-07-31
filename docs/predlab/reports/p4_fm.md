# Phase-4 report — zero-shot foundation models (2026-07-31)

Registered `predlab_p4_fm`. Dev-feasible roster after leakage classing:
Chronos-Bolt-small (Class B, window 2024-12→2025-03), TTM-r2 (Class B,
2024-11→2025-03); TabPFN-TS dropped by declared amendment (interactive
license required — revivable via TABPFN_TOKEN); Chronos-2 / TimesFM-2.5 /
Moirai-2 / Toto-2 deferred (released after dev end — no leakage-safe dev
window exists); TimeGPT excluded (unauditable corpus). Matched-window
comparisons vs each cell's CHAMPION by subsetting stored forecasts to
identical origins. n = 121–151 per run — the price of leakage honesty is
statistical power; read everything below with that in mind.

## Results (24 runs; DM one-sided FM-better vs champion)

| Family | Outcome |
|---|---|
| T1 returns ×6 | FMs never beat RW (impr −0.2% to −9.5%) — the null now spans naive, classical, ML, and foundation tiers |
| T3 vol, ETH | **TTM beats the GARCH champion on BOTH grids: 24h +14.0% (p 0.0125), 1h +18.0% (p 0.087)** |
| T3 vol, BTC | mixed: Chronos +10.7% daily (p 0.24); both FMs slightly worse at 1h |
| T4 volume ×8 | vs LGB champion: +2.9–5.2% ns at 1h, negative daily |

## Verdict

- **ETH-vol TTM is SUGGESTIVE, not confirmed**: p 0.0125 at 24 registered
  runs does not clear BH-FDR (rank-1 threshold 0.0042). It is exactly the
  profile the RV-TSFM literature predicted (TTM ≈/> Log-HAR, ensemble value)
  and is coherent across grids. **Action: TTM enters the ETH T3 Phase-5 MCS
  set** — where the surviving-set procedure, not a post-hoc p, decides.
- Returns: unpredictable under a fourth model class. The strongest
  cross-tier negative in the map.
- No FM claim anywhere else; windows too short for small effects.

## Method notes

- TTM daily checkpoints are frequency-aware (`freq_token` required) —
  handled; per-series standardization applied and inverted.
- Variance floor (1e-12) applied to FM vol forecasts for QLIKE validity.
- Chronos-Bolt CPU throughput 5.9 ms/forecast batched — zero-shot batteries
  are compute-trivial; the binding constraint is leakage-safe data, not FLOPs.
