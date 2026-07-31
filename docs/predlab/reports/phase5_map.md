# Predictability map v3 — FINAL (post-holdout, 2026-07-31)

Program endpoint: dev map (v2) filtered through per-cell MCS champion
freeze + sealed-holdout one-shots (15 months, zero prior spends).
Cell states: **USABLE** (U1–U4 met on holdout), ATTENUATED (holdout skill
real but under the registered floor), FRAGILE (dev skill did not survive
in the registered loss), NULL (no dev skill — never reached holdout).

| Target | Horizon | BTC | ETH |
|---|---|---|---|
| T1 return level | 1h / 24h / 7d | NULL (4 model classes) | NULL (4 model classes) |
| T2 direction | 1h | FRAGILE (Brier gate; sign edge +2.51pp persists) | FRAGILE (Brier gate; sign edge +1.69pp persists) |
| T2 direction | 24h / 7d | NULL | NULL |
| T3 realized vol | 1h | **USABLE — HARQ +15.1%** | ATTENUATED (egarch +7.4% < 10.7% floor) |
| T3 realized vol | 24h | **USABLE — HARQ +22.6%** | NULL at dev (gjr never beat HAR baseline family cleanly) |
| T4 volume | 1h | **USABLE — LGB +44.8%** | **USABLE — LGB +42.3%** |
| T4 volume | 24h | **USABLE — LGB +26.6%** | **USABLE — LGB +30.1%** |
| T5 range | — | folded into T3 (rv family) | folded into T3 |
| T6 funding | 8h / 24h | NULL (AR(1) baseline wins) | NULL |
| T7 xs low-vol rank | 24h | **USABLE — park_5 IC −0.083, NW-t −11.5** (200-name universe) | ← same cell |

## The final claims (usable prediction models, U1–U4)

1. **Volume, both symbols, both grids** — LGB on 13 registered features
   (lagged log-volume, rv, trade intensity, seasonality, OI deltas,
   funding). Holdout MASE gains +26.6…+44.8% vs seasonal-naive, DM
   p ≤ 8e-12, effects ≥ dev.
2. **BTC realized variance, both grids** — HARQ (HAR + realized
   quarticity). Holdout QLIKE gains +15.1% (1h) / +22.6% (24h) vs HAR,
   DM p ≤ 5.5e-11.
3. **Cross-sectional next-day return rank** — 5-day Parkinson-vol sort on
   the monthly top-200 universe; holdout IC −0.083 (NW-t −11.5),
   replicating dev −0.089. (Low-vol names outperform in rank space —
   the mechanism behind the §43 XS-momentum reversal.)

## What did not survive

- Return LEVELS: null across naive/classical/ML/foundation tiers, every
  horizon, both symbols — the strongest cross-tier negative in the map.
- Direction probabilities: hourly logit edges (the first-ever T2 skill in
  the program) keep their SIGN edge on holdout but fail the registered
  Brier criteria — calibration-fragile, not sign-fragile.
- ETH vol: consistently harder than BTC (dev fragility flags → holdout
  attenuation). The TTM ensemble upgrade (+17.5% dev, dm_p 4.4e-7)
  remains a dev-level result — not holdout-spent, by the champion-only
  contract.
- 7d horizon: nothing at any tier; skill is horizon-local (1h ≫ 24h ≫ 7d).

## Program invariants held

Zero holdout spends before P5-02; every battery pre-registered; every
positive forensically nulled (shuffled-target / permute-y / within-day
shuffle); every negative reported with power context.
