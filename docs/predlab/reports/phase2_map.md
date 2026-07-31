# Predictability Map v2 — after Phase 2 (2026-07-31)

Delta over `phase1_map.md`. All Phase-2 results from frozen registrations
(`predlab_p2_ml`, `predlab_p2_t7`); every evaluated config ledgered (ledger
now 250+ unique hashes); holdout sealed, zero spends. All new candidate
p-values (≤ 6.7e-5, most ≪ 1e-10) jointly survive BH-FDR q=0.10 with the
Phase-1 battery by direct inspection (they are smaller than Phase-1's
smallest passing threshold).

## Champion changes

| Cell family | Phase-1 champion | Phase-2 outcome |
|---|---|---|
| T4 volume ×4 | seasonal-AR | **LGB** (Δ5.4–12.1% vs seasonal-AR, pairwise DM p ≤ 6.7e-5; permute-y clean; cumulative 35–42% vs naive) |
| T3 vol ×4 | HARQ (BTC) / GARCH (ETH) | unchanged — ML never beats champions |
| T2 dir 1h ×2 | logit_lags5 | unchanged — ML miscalibrated despite stronger sign signal (PT p 2.3e-44); LGB+calibration declared for Phase 5 |
| T1 return ×4 | RW (baseline-wins) | unchanged — LGB actively harmful (§40 reconciled in forecast space) |

## New cells: T7 cross-sectional (SKILL-CANDIDATE)

- ret-rank 24h: five floor-passing signals (park_5 IC −0.089/t −17.5 dominant;
  momentum = reversal; rev_1; volchg) + passing combos (ridge +0.082/t 19.2,
  lgb +0.077/t 24.1) — none beats park_5 alone; Phase-5 MCS selects.
- Liquidity-slice forensic: effect stronger in top-50 → not microstructure.
- ret-rank 7d: same structure. Vol-rank: trivial persistence (recorded).

## The Phase-2 headline

**Time-series return levels are unpredictable at every horizon and every
tier; cross-sectional return RANKS are richly predictable.** Together with
Phase 1: predictability in crypto (this data, these methods) lives in
(a) volume, (b) realized vol, (c) hourly direction, (d) cross-sectional
ranks — never in time-series return levels.

## Current skill-candidate inventory (pre-holdout)

9 Phase-1 cells + 4 Tier-2 volume champion upgrades + T7 (24h, 7d) =
**11 distinct skilled cells + 1 champion-upgrade family**, all dev-only;
graduation requires Phase-5 MCS + sealed-holdout one-shots (U1–U5).
