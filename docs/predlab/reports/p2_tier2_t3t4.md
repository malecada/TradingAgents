# Phase-2 Tier-2 report — ML on vol (T3) and volume (T4) cells (2026-07-31)

Registered battery `predlab_p2_ml` (frozen pre-result; per-symbol eval windows:
BTC 2021-01-01+, ETH 2021-12-01+ per the OI coverage gate). Models: elastic
net + LGB on the frozen ≤25-feature sets (RV/flow/calendar + OI/positioning +
funding); Phase-1 champions run in-cell at their registered cadences.

## T4 volume — LGB beats the Phase-1 champion in ALL FOUR cells

| Cell | Champion (seasonal-AR) | LGB | Δ vs champion | DM p (pairwise) |
|---|---:|---:|---:|---:|
| BTC 1h | 0.6723 | **0.6358** | +5.4% | 1.6e-90 |
| BTC 24h | 0.7549 | **0.7036** | +6.8% | 6.7e-5 |
| ETH 1h | 0.7143 | **0.6689** | +6.4% | 2.4e-96 |
| ETH 24h | 0.6048 | **0.5316** | +12.1% | 1.6e-10 |

All four ≥ the 5% registered floor, cross-symbol × cross-grid replication,
against the STRONGEST prior model (not just the registered baseline).
Forensics: n_features leak-guard with a bite test (unguarded model exploits a
planted target column at p<1e-10; guarded does not); permute-y null (features
held, target permuted) kills LGB's skill at p ≈ 1.0. **Tier-2 SKILL-CANDIDATE
(vs-champion) in all four volume cells — the first cells where ML adds genuine
increment over the best classical model.**

Elastic net is catastrophic on volume (MASE 1.49–4.17): linear-on-standardized
features cannot track the trending log-volume level. Recorded; GBDT's
advantage here is level-adaptivity, consistent with the tabular-SOTA prior.

## T3 realized vol — ML NEVER beats the champion (4/4)

| Cell | Champion | ML best | Verdict |
|---|---|---|---|
| BTC 1h | harq 0.5370 | lgb 0.9201 | champion wins by 42% |
| BTC 24h | harq 0.3520 | enet 0.7996 | champion wins by 56% |
| ETH 1h | gjr11 0.5936 | lgb 0.6031 | champion wins (close, +1.6%) |
| ETH 24h | gjr11 0.3987 | enet 0.5052 | champion wins by 21% |

The registered feature set (including OI, positioning, funding, taker flow)
adds NOTHING over structural vol models — HAR/GARCH's parametric persistence
structure dominates generic GBDT/linear regression on this target. Consistent
with the literature prior (HAR-class hard to beat; ML gains marginal) and
with the house's LGB history, now demonstrated in forecast space. ETH 1h is
the only near-miss (lgb within 1.6% of gjr) — an ensemble question for
Phase 5, not a win.

## Map update

- T4 volume: champion lineage is now seasonal-naive → seasonal-AR → **LGB**
  (Δ cumulative vs naive: 35–42% MASE) across all four cells.
- T3 vol champions unchanged (BTC HARQ, ETH GARCH-family).
- Reproducibility spot-checks: seasonal-AR and HARQ reproduce their Phase-1
  losses to 4-6 decimals inside the Tier-2 runs.

Next per backlog: P2-03 (ML on T1/T2 — includes the §40 LGB-retirement
reconciliation), P2-04 (T7 cross-sectional battery), P2-05 (Phase-2 report).
