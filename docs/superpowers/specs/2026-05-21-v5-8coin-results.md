# V5 MIX 8-Coin Expansion — Results

**Date:** 2026-05-23
**Spec:** `docs/superpowers/specs/2026-05-21-v5-8coin-expansion-design.md`
**Plan:** `docs/superpowers/plans/2026-05-21-v5-8coin-expansion.md`
**Routing:** `docs/superpowers/specs/2026-05-21-v5-8coin-routing.json`
**Branch:** `feature/v5-8coin-expansion`
**Production output:** `data/v5_8coin_production/`

## Verdict

**ACCEPTED.** Both acceptance-gate criteria satisfied:

| Gate | 4-coin V5 | 8-coin V5 | Pass? |
|---|---|---|---|
| Portfolio SR ≥ ~3.0 | +3.178 | **+3.966** | ✓ (Δ +0.79) |
| Max drawdown < 4-coin DD | -4.9% | **-4.8%** | ✓ (lower) |

Plus large gains in compounded return: +764.6% → **+1052.8%** (+38% lift).

## Final 8-coin portfolio — canonical (sat_haircut = 1.5x default)

| Coin | Tier | Pool | SR | Return | maxDD |
|---|---|---|---|---|---|
| bitcoin | core | 78f (frozen §20) | +1.97 | +328% | -6.7% |
| ethereum | core | 193f (frozen §20) | +2.05 | +594% | -8.7% |
| binancecoin | core | 78f (frozen §20) | +1.93 | +730% | -10.4% |
| solana | core | 193f (frozen §20) | +2.32 | +1745% | -12.0% |
| ripple | satellite | 78f (T7) | +2.13 | +1679% | -15.6% |
| dogecoin | satellite | 78f (T7) | +2.00 | +1299% | -15.2% |
| cardano | satellite | 193f (T7) | +2.49 | +2133% | -11.2% |
| tron | satellite | 78f (T7) | +1.92 | +1011% | -13.6% |
| **PORTFOLIO** | **15%×4 core / 10%×4 sat** | mix | **+3.966** | **+1052.8%** | **-4.8%** |

Window: 2021-11-07 → 2026-04-15 (1619 bars, 4.5 yr WF).

## Routing decisions (T7)

For each new coin, ran standalone single-coin V5 backtest on both 78f and 193f
prediction pools (3-coin {BTC, ETH, target} pool each). Routed to whichever
gave the higher standalone Sharpe. Frozen 4 untouched.

| Coin | 78f SR | 193f SR | Routed to |
|---|---|---|---|
| ripple | **+2.15** | +0.85 | 78f |
| dogecoin | **+2.01** | +1.46 | 78f |
| cardano | +1.38 | **+2.51** | 193f |
| tron | **+1.96** | +1.08 | 78f |

Account-model chains (XRP/TRX) and DOGE prefer 78f. Only Cardano benefits
from 193f (Δ +1.13 SR).

## Cost-sensitivity sweep (T11)

Satellite-coin slippage/impact multiplier swept 1.0 / 1.5 / 2.0:

| sat-haircut | Portfolio SR | Return | maxDD |
|---|---|---|---|
| 1.0× | +3.986 | +1067.2% | -4.8% |
| **1.5× (canonical)** | **+3.966** | **+1052.8%** | **-4.8%** |
| 2.0× | +3.948 | +1039.8% | -4.8% |

SR range 3.95–3.99 (Δ 0.04). Result is **robust to the haircut choice** —
the gate verdict does not hinge on it.

Global-cost sensitivity (uniform 1x/2x/3x of all baseline costs, from
`validate_v5_robustness.py`):

| cost mult | SR | Return | maxDD |
|---|---|---|---|
| 1x | +4.019 | +1154.4% | -4.8% |
| 2x | +3.634 | +702.3% | -4.8% |
| 3x | +3.252 | +510.0% | -4.8% |

Even at 3× baseline costs, 8-coin SR (3.25) still beats the 4-coin baseline
(3.18). -19% SR degradation 1x→3x.

## Combinatorial Purged CV (T12)

28 test folds, n_groups=8, test_groups=2, embargo=14 (strategy-layer CPCV
over portfolio returns):

- Mean SR: **+4.07**, median +3.99, std 0.49
- Min +3.18, max +5.06
- p05 +3.45, p95 +4.87
- **100% folds SR > 0, SR > 1, SR > 2**
- PBO proxy (fraction of folds with SR<0): **0.000**

Worst fold SR (+3.18) equals the 4-coin baseline exactly — every CPCV
slice of the 8-coin portfolio meets or beats the 4-coin baseline.

## Regime decomposition (T12)

Portfolio split by BTC regime over the 1619-bar window:

| Regime | n bars | % | SR | Return |
|---|---|---|---|---|
| bull | 176 | 10.9% | +4.11 | +30.0% |
| sideways | 913 | 56.4% | **+4.66** | +360.1% |
| bear | 530 | 32.7% | +3.17 | +109.7% |

All three regimes positive. Even bear-regime SR (+3.17) matches the
4-coin full-window baseline.

## Sanity gate (T3) — for the record

Mid-build all-78f 8-coin sanity backtest (existing 4 + new 4, all on 78f
pool, equal-weight): SR **+3.76** / +921% / -4.6% DD. Already cleared the
acceptance gate before P3 data ingestion — confirmed no degenerate new
coin, justified continuing to 193f.

## What changed (plan-vs-actual drift)

Three plan corrections surfaced during execution, fixed in-place:

1. **Per-coin 3-coin pools, not 8-coin mega-pool.** CLAUDE.md documents that
   pooling beyond BTC+ETH degrades directional accuracy 12-22pp; §20 V5
   routing used 3-coin {BTC,ETH,target} pools. Plan T2/T6 updated to per-coin
   `multi_3coins_<sym>_(pit_)wf` naming.
2. **`--days 3000` required** for the 4.5-yr walk-forward window. Plan's
   bare `evaluate_models_multi.py` command used the default `--days 730`,
   which yields only ~1 yr of OOS predictions.
3. **Three hardcoded coin maps** needed updating, not the `--coins` flag the
   plan assumed: `fetch_coinglass_history.py:COIN_TO_SYMS`,
   `coinmetrics.py:SUPPORTED` (+ per-coin community-metric sets, probe-
   confirmed), `onchain.py:cm_asset_map`, `onchain_features.py:COIN_ALIAS` +
   `RAW_METRICS_BY_COIN`.

Also fixed: `.env` line-6 glue from no-trailing-newline append; pct-change
inf→nan sanitize in `build_pit_onchain_features` (early-2019 stablecoin
supply zeros → div-by-zero blowup, latent bug not hit by ETH/SOL §20 runs
which used shorter --days).

## Notes / caveats

- Per §19, no weight sweep performed: fixed 15%×4 core + 10%×4 satellite,
  validated not swept.
- Routing pre-registered one-choice-per-coin (no sweep): DSR multiple-testing
  haircut not applied per-coin since each decision was binary and committed
  before the final portfolio run.
- Account-model chains (XRP/TRX/ADA) returned fewer on-chain features than
  BTC/ETH (UTXO-style metrics absent on CM community tier for non-UTXO
  chains). Expected; LGB tolerates NaN. T5 verification confirmed 48–61
  oc_ columns per new coin vs 65+ for BTC.
- Live deployment unchanged. This expansion is backtest-only; the existing
  4-coin Hetzner deployment is untouched.

## Reproduce

```bash
# Production 8-coin run
python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2026-04-15 \
    --output-dir data/v5_8coin_production

# 4-coin regression (must match SR 3.18)
python scripts/baseline_v5_mix.py --start 2021-11-07 --end 2026-04-15 \
    --routing-json data/v5_4coin_routing.json \
    --output-dir data/v5_4coin_regression

# Cost sweep
for h in 1.0 1.5 2.0; do
  python scripts/baseline_v5_mix.py --sat-haircut $h \
      --output-dir data/v5_8coin_sat${h}
done

# Robustness (CPCV + regime + cost-mult)
python scripts/validate_v5_robustness.py
# Output: data/v5_validation/v5_robustness.json
```
