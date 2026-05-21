# V5 MIX — 8-Coin Expansion Design

**Date:** 2026-05-21
**Status:** Approved (design)
**Branch (target):** feature/v5-8coin-expansion (created at implementation time)

## Goal

Expand the canonical V5 MIX strategy from 4 coins (BTC/ETH/BNB/SOL) to 8
(adding XRP, DOGE, ADA, TRX) without regressing risk-adjusted performance.
Acceptance gate: 8-coin walk-forward portfolio Sharpe ≥ ~3.0 **and** max
drawdown below the 4-coin V5 baseline.

Stablecoins (USDT/USDC) are excluded — the 8 coins are the full non-stablecoin
top-10 by market cap.

## Non-goals

- No LLM / hybrid modulator. This is the pure-quant V5 path only.
- No regime overlay (§16: regime is a DD-reducer, not an alpha source; NH-HMM
  bundle is degenerate).
- No live-deployment changes. Hetzner / Binance testnet deployment is untouched
  until the 8-coin backtest passes the acceptance gate.
- No weight sweep and no routing sweep — §19 found equal-weight beats weight
  optimization out-of-sample; pre-register one choice per decision instead.

## Background / current state

- `scripts/baseline_v5_mix.py` is the canonical V5 MIX strategy: V2 signal +
  sizing core, per-coin LGB predictions, equal-weight 4-coin portfolio, no
  regime overlay, no LLM. Current published portfolio SR is 3.18 (drifted from
  3.25 after a data refresh).
- `DEFAULT_ROUTING` in `baseline_v5_mix.py` maps each coin to a prediction
  directory. Current 4 coins: BTC/BNB on the 78-feature canonical pool,
  ETH/SOL on the 193-feature extended pool (+ Coinglass derivatives + PIT
  on-chain). Routing was chosen per coin by standalone WF Sharpe (§20).
- `scripts/evaluate_models_multi.py` already has a 10-coin `DEFAULT_UNIVERSE`
  including ripple, cardano — the pooled prediction pipeline supports the new
  coins with no code change.
- `tradingagents/dataflows/coingecko_binance.py` `_KNOWN_SYMBOLS` already maps
  XRPUSDT/ADAUSDT/DOGEUSDT; TRXUSDT must be added (one line).
- Derivatives data (`data/derivatives/`) currently covers only BTC/ETH/BNB/SOL.
  Microstructure covers only BTC/ETH. On-chain store is pooled by year/month.
- `COSTS` dict in `baseline_v5_mix.py` is currently a single global tier.

## Architecture

The V5 MIX engine is reused unchanged. Only four things change:
coin set, `DEFAULT_ROUTING` dict, portfolio weight scheme, and `COSTS` tiers.
`baseline_v5_mix.py` is extended, not rewritten.

Backtest window: same 4.5-year walk-forward as V5, start 2021-11-07. All four
new coins (XRP, DOGE, ADA, TRX) have price + perp history back to 2021 — no
window truncation.

## Phased plan (staged-gate, approach B)

### Phase P1 — 78f predictions for new 4

Generate walk-forward LGB prediction CSVs for XRP/DOGE/ADA/TRX on the
78-feature canonical pool via `evaluate_models_multi.py`. No data ingestion
needed — the pipeline already supports these coins. Add TRXUSDT to
`_KNOWN_SYMBOLS` first.

Output: `preds_lgb_h7.csv` / `preds_lgb_h14.csv` for the new coins in a 78f
prediction directory.

### Phase P2 — sanity gate

Run a quick 8-coin all-78f portfolio backtest (existing 4 forced onto 78f for
this check only, new 4 on 78f).

**Gate:** if any new coin produces a degenerate signal (dead/flat prediction)
or blown fills, stop and diagnose before spending effort on P3 ingestion. A
non-catastrophic result (no coin individually destroying the portfolio) is
enough to proceed — this is a smoke gate, not the acceptance gate.

### Phase P3 — data ingestion + 193f predictions for new 4

Extend existing ingestion scripts to XRP/DOGE/ADA/TRX:

| Data | Script(s) | Notes |
|---|---|---|
| OHLCV | `coingecko_binance.py` | Add TRXUSDT to `_KNOWN_SYMBOLS` (done in P1) |
| Derivatives (OI, funding, liquidations, long-short, taker) | `fetch_coinglass_history.py` → `build_derivatives_features.py` | All 4 covered by Coinglass Hobbyist tier |
| On-chain | `refetch_coinmetrics_full.py` → `backfill_onchain.py` | CoinMetrics community covers all 4 |
| DefiLlama TVL | `fetch_defillama_extensions.py` | Only TRX has real DeFi TVL |

**Account-model vs UTXO:** XRP, TRX, ADA are account-model chains. UTXO-style
features (UTXO age bands, etc.) will be null for them. This is expected — LGB
tolerates null columns; affected coins simply have fewer than 193 usable
features. DefiLlama TVL features are mostly null for XRP/DOGE/ADA (no real
DeFi). Neither is a blocker.

**PIT discipline:** every ingest writes the as-of / observation timestamp,
matching the existing PIT store. No look-ahead.

Then generate 193f-pool walk-forward predictions for the new 4. Outcome of P3:
both 78f and 193f prediction sets exist for every new coin, so P4 can route.

### Phase P4 — routing, portfolio assembly, validation

**Routing:** for each new coin, run a standalone single-coin V5 WF backtest
twice — once with 78f predictions, once with 193f — and pick the higher
Sharpe. Extend `DEFAULT_ROUTING` with the 4 winners' prediction directories.
Existing 4 routes are frozen. One pre-registered choice per coin, no sweep.

**Weights — core/satellite, fixed:**
- Core (BTC, ETH, BNB, SOL): 15% each = 60%
- Satellite (XRP, DOGE, ADA, TRX): 10% each = 40%

Single fixed scheme; validated, not swept.

**Costs — split `COSTS` into two tiers:**
- Core tier: unchanged (slippage 0.0005, price_impact 0.00005, spread 0.0001).
- Satellite tier: conservative haircut — 1.5× slippage and 1.5× price_impact
  for the new 4. All four are liquid Binance perps, so this is a
  margin-of-safety, not a true microstructure model.
- P4 includes a 1× / 1.5× / 2× cost-sensitivity check so the gate result is
  not fragile to the haircut choice.

**Validation:**
- 4.5-year walk-forward, 8-coin core/satellite portfolio.
- Per-coin attribution (SR / return / DD contribution).
- CPCV + Deflated Sharpe Ratio — 8 coins means more routing decisions, so the
  DSR multiple-testing haircut matters.
- Bootstrap CI on portfolio Sharpe.
- Side-by-side vs the 4-coin V5 baseline (SR 3.18).

**Acceptance gate:** 8-coin portfolio walk-forward SR ≥ ~3.0 **and** max
drawdown below the 4-coin V5 max drawdown.

## Expected outcome / risks

- Crypto alts correlate ~0.7–0.9 with BTC; the BTC/BNB ~-0.007 pairing that
  drove 4-coin diversification is not expected to repeat. Realistic outcome:
  Sharpe roughly flat vs 4-coin, max drawdown lower (breadth as a DD-reducer,
  consistent with the V4 regime finding). New coins carrying net alpha would be
  an upside surprise, not the base case.
- **Risk — 193f portability:** account-model chains lose UTXO features; the
  193f pool may not beat 78f for XRP/TRX/ADA. Mitigated by data-driven routing
  (P4) — a coin simply routes to 78f if 193f does not win.
- **Risk — routing overfit:** 8 coins = 8 routing decisions. Mitigated by DSR
  haircut and pre-registered single choice per coin (no sweep).
- **Risk — slippage realism on satellites.** Mitigated by the 1.5× haircut +
  1×/1.5×/2× sensitivity check.
- **Risk — P2 reveals a dead coin.** That is the gate working as designed —
  stop and diagnose before P3.

## Testing

- Unit: extend `tests/strategies/` coverage for the 2-tier `COSTS` and the
  core/satellite weight scheme; existing 4-coin V5 results must be unchanged
  when run with the 4-coin config (regression guard).
- Smoke: P2 8-coin all-78f backtest doubles as an integration smoke test.
- Full suite (`tests/strategies/`) must stay green.
