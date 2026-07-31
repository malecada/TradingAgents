# Phase-2 Tier-2 report — ML on returns (T1) and direction (T2) (2026-07-31)

Registered battery `predlab_p2_ml`, cells {BTC,ETH} × {1h,24h} × {T1,T2},
frozen T1T2 feature set (19 features: ret/RV/flow lags, OI/positioning,
funding, calendar), enet + LGB (T2 via the registered ProbClip sign-target
convention), logit champion in-cell.

## T1 returns — ML never beats RW; LGB is actively harmful (4/4)

| Cell | RW | enet | lgb | lgb penalty |
|---|---:|---:|---:|---:|
| BTC 1h | 4.524e-5 | 4.540e-5 (p .99) | 4.799e-5 (p 1) | +6.1% |
| ETH 1h | 5.424e-5 | 5.425e-5 (p .71) | 5.653e-5 (p 1) | +4.2% |
| BTC 24h | 1.038e-3 | 1.077e-3 (p .97) | 1.224e-3 (p 1) | +17.9% |
| ETH 24h | 1.305e-3 | 1.317e-3 (p 1.0) | 1.548e-3 (p 1) | +18.6% |

## T2 direction — the simple logit champion holds everywhere

| Cell | base_rate | logit (champion) | lgb | Notes |
|---|---:|---:|---:|---|
| BTC 1h | 0.24999 | **0.24816** (p 9e-16, PT 2.6e-41) | 0.25178 (p 1.0, PT **2.3e-44**) | ML sign-signal stronger, calibration worse |
| ETH 1h | 0.25006 | **0.24822** (p 4.1e-14, PT 2.5e-31) | 0.25168 (p 1.0, PT 1.7e-31) | replicates |
| BTC 24h | 0.25140 | 0.25178 (ns) | 0.28697 (p 1) | all null |
| ETH 24h | 0.25146 | 0.25081 (ns) | 0.28359 (p 1) | all null |

The striking detail: LGB's SIGN association at 1h is the strongest measured in
the program (PT p 2.3e-44 BTC / 1.7e-31 ETH) — the features contain real
directional information — but its probability calibration is bad enough to
LOSE on Brier to both the base rate and the 5-lag logit. enet is worse still
(miscalibrated linear probabilities, Brier 0.31-0.33). **Registered Phase-5
candidate: LGB sign-score + explicit calibration layer (isotonic/Platt) as a
combination entry — declared here, not run.**

## §40 reconciliation (explicit, per backlog requirement)

§40 (honest rebuild) retired LGB for return-based trading: ΔSR −0.255 vs
factor floor, p_pos 0.354, DSR 0.077. The forecast-space Tier-2 battery
reproduces and sharpens that verdict on independent ground: with a richer,
PIT-clean feature set (incl. OI/positioning unavailable to the V2/V3-era
models) and a pure forecast objective, LGB is 4-19% WORSE than the zero
forecast on return levels in all four cells. The retirement was not an
artifact of the trading harness, sizing, or the old feature set — daily/hourly
return LEVELS are not learnable by GBDT on this feature space, full stop.
The only ML wins anywhere in the map are on volume (P2-02) and, latently,
sign-information without calibration (above).

## Verdict roll-in

- T1 cells: NO-SKILL confirmed at Tier 2 (map unchanged).
- T2 1h champions: logit_lags5 unchanged (Tier-2 challengers lose the
  registered loss); LGB PT signal recorded for Phase-5 combination.
- T2 24h: null at every tier.
