# Perpetual Funding-Carry Sleeve — Backtest Spec

**Status:** Design / not yet implemented
**Author:** research workflow + design session, 2026-05-30
**Goal:** Add a market-neutral funding-harvest sleeve as an *uncorrelated* return stream to the V5 MIX directional book, and measure whether it lifts blended portfolio Sharpe above the 3.18 baseline.

---

## 0. Origin & rationale

Deep-research survey (5 angles, 26 peer-reviewed sources, adversarially verified) flagged the perpetual-futures
carry trade as the one genuinely **additive, data-ready, orthogonal** idea for this system. Every other surveyed
technique was either redundant with the existing GBDT core (CTREND, momentum β=0.79), a robustness/DD overlay
(vol-target, HRP), or refuted.

**Mechanism (verified, CMU working paper + BIS WP 1087):** A delta-neutral position (short perp + long spot)
harvests the funding rate. Funding median ≈ 0.01%/8h ≈ **11%/yr**, and is **serially correlated** (predictable).
Profitability is driven by the **funding rate, not the basis** (basis median ≈ 0, basis-change ≈ i.i.d.).

**Honest caveats baked into this spec:**
- The headline in-sample Sharpe 7–10 (BTC 7.0–12.8) is **gross / in-sample 2020-08…2022-06**. Realized net
  Sharpe is far lower after costs, liquidation, and funding sign-flips. Expect standalone net SR **0.5–1.5**.
- "Carry is decoupled from BTC trend across bull/bear" was **REFUTED 0-3** → do **not** assume regime-independence;
  funding flips negative in stress.

---

## 1. Locked design decisions

| Fork | Decision | Rationale |
|------|----------|-----------|
| Sign handling | **Trailing-sign gated** (hold only when recent funding > cost hurdle); build *always-on* as ablation | Funding serially correlated → trailing sign predicts next period; avoids paying negative funding |
| Universe | **BTC/ETH first**, expand after mechanism proven | Deepest perp liquidity, cleanest funding history, lowest liquidation risk |
| Capital | **Separate allocation, swept** (carve X% for carry, rest = V5 MIX) | Clean attribution + correlation analysis; X swept to find blended-SR max |

---

## 2. Feasibility note — REAL basis is available (spec corrected 2026-05-30)

**Original assumption (FALSIFIED):** "the repo has only spot OHLCV, no perp/mark price, so basis ≈ 0 and we
inject synthetic noise in P5." During P1 this was disproven.

**Reality:** Binance Futures `fapi` serves **public daily perp price history** on the same API already used for
funding — both `/fapi/v1/klines` (perp last price) and `/fapi/v1/markPriceKlines` (mark price). So the
delta-neutral price-leg PnL can be measured from **real** data, no σ-guessing:

```
spot leg PnL:  + N · spot_ret                       (spot close, coingecko_binance.py)
perp leg PnL:  − N · perp_ret                        (perp MARK close, fapi markPriceKlines)
price PnL_t:   N · (spot_ret_t − perp_ret_t)         # telescopes to −N·Δbasis over the hold
─────────────────────────────────────────────────────────────
sleeve_daily_return_t = funding_collected_t + price_PnL_t − rebalance_costs_t
```

**Why this matters (P1 finding):** with a *perfect* hedge (price PnL ≡ 0) the always-on sleeve prints
SR ≈ 15 (BTC) / 11 (ETH) — the in-sample carry illusion. A synthetic basis-σ sweep shows SR is entirely
governed by basis vol (σ=0.1%/day → SR ~3.3; σ=0.5%/day → SR ~0.5). The realized number depends on the **true**
basis, which we can now measure instead of assume. **Basis modeling moves from P5-stress to P1.5-core.**

Funding income itself is backtestable from the funding series alone
([onchain.py:222](../tradingagents/dataflows/onchain.py#L222) `_scrape_funding_rates`, any `SYMBOL`USDT); the
basis leg adds perp-mark klines. P5 retains a **synthetic** basis stress on top of the real basis (for
forward-looking robustness), but the baseline now uses real basis.

### ⚠️ Funding-units bug to fix first
`_scrape_funding_rates` aggregates with `groupby("date")["fundingRate"].mean()`
([onchain.py:247](../tradingagents/dataflows/onchain.py#L247)) — the **mean** of the (up to 3) 8h prints.
Daily *income* = **sum** of the 3×8h periods, not the mean. Re-derive daily income as `Σ(intraday prints)`
(or `mean × n_periods`) or the backtest undercounts carry income ~3×.

---

## 3. PnL model (per coin, per day)

Delta-neutral notional `N`, short perp + long spot:

```
funding_income_t   = funding_daily_t · N            # shorts RECEIVE when funding>0, PAY when <0
price_pnl_t        ≈ 0                                # delta-neutral
entry/exit_cost    = 2 · (fee 0.04% + slippage 0.05%) · N   # both legs, only on rebalance
sleeve_return_t    = funding_daily_t − amortized_costs_t − basis_noise_t
```

Cost constants from V5 MIX (`COSTS`, [baseline_v5_mix.py:62](../scripts/baseline_v5_mix.py#L62)):
`fee_rate=0.0004`, `slippage=0.0005`. Funding is **income** here, not the `funding_rate` cost line already in
`COSTS` — do not double-count.

**Trailing-sign gate:** enter/hold when `EMA_k(funding) > hurdle`, else flat. `hurdle` ≥ amortized round-trip cost.
Sweep `k ∈ {3,7,14}` days and `hurdle`. Each gate transition = one round-trip cost.

---

## 4. Phased implementation (TDD)

### P0 — Data audit & funding-income series
- Confirm funding coverage + history depth for `BTCUSDT`, `ETHUSDT` (extend scraper loop beyond default BTC).
- Build `funding_daily_income(coin, dates)` = Σ intraday 8h prints/day, PIT-aligned (`as_of_ts ≤ trade_date`),
  written to the bitemporal store ([onchain_store.py](../tradingagents/dataflows/onchain_store.py)).
- **Gate:** clean daily funding history for BTC + ETH over the V5 MIX backtest window (2021-11 … 2026-04).

### P1 — Sleeve PnL engine ✅ DONE
- `carry_sleeve_return(funding_income, sign_mode, costs) -> pd.Series` (always_on; gated raises until P2).
- `aggregate_daily_funding_income`, `fetch_funding_raw`, `funding_daily_income` shipped; 7 tests green.
- **Finding:** perfect-hedge always_on SR ≈ 15 (BTC) / 11 (ETH) = in-sample illusion → real basis needed (P1.5).

### P1.5 — Real basis leg (the crux — promoted from P5)
- New: `fetch_perp_mark(symbol, start, end) -> pd.Series` (daily perp mark close, `/fapi/v1/markPriceKlines`).
- `price_pnl_t = spot_ret_t − perp_ret_t` from real spot + perp-mark closes; telescopes to −Δbasis over a hold.
- Extend `carry_sleeve_return` to accept a `price_pnl` series (default zero = P1 perfect-hedge behavior).
- **Tests:** zero price_pnl → P1 unchanged; telescoping identity; sign correctness.
- **Deliverable:** the *real-basis* standalone SR for BTC/ETH — first honest number.

### P2 — Sign gating + cost model
- Implement trailing-EMA gate + cost hurdle; count round-trips; apply entry/exit cost on each transition.
- Implement `sign_mode="always_on"` as ablation baseline.
- **Tests:** turnover accounting, cost applied exactly once per transition, gate hysteresis.

### P3 — Standalone metrics
- Net SR / maxDD via existing `_metrics(r)` ([baseline_v5_mix.py:155](../scripts/baseline_v5_mix.py#L155)).
- **Mandatory sub-period split**: high-funding (2020-22-style) vs compressed (2023+). Report each.
- Worst negative-funding drawdown stretch. Gated-vs-always-on comparison table.

### P4 — Portfolio blend (the actual prize)
- Add sleeve as extra column to `portfolio_return(df, weights)` ([baseline_v5_mix.py:99](../scripts/baseline_v5_mix.py#L99)).
- **Correlation** of sleeve returns vs V5 MIX portfolio returns (target near-zero — this drives the diversification lift).
- Sweep carry allocation `X ∈ {5,10,20%}` (rest renormalized across V5 MIX coins); plot blended SR vs X.
- **Go/no-go:** blended SR > 3.18 at some X.

### P5 — Robustness
- **Synthetic basis stress** *on top of* the real basis (P1.5): add extra `Δbasis ~ N(0, σ)`; sweep σ; report SR sensitivity (forward-looking, since future basis vol may exceed history).
- Cost sensitivity (fee/slippage ×{1, 1.5, 2}).
- Reuse existing CPCV/DSR machinery for sub-period robustness.
- Document short-leg **liquidation-buffer** assumption (cannot fully model without perp price).

---

## 5. Success criteria (pass/fail)

1. Standalone sleeve **net** SR in a sane range (0.5–1.5); if it prints 7+, a unit/cost bug is hiding.
2. Sleeve↔V5 MIX **correlation** near zero (the diversification thesis).
3. **Blended portfolio SR > 3.18** at some allocation X — the go/no-go.

If (2) holds but standalone SR is modest, the blend can *still* win on diversification — that's the whole point;
judge on (3), not on the sleeve's standalone SR.

---

## 6. Validity threats (encoded as tests, not prose)

| Threat | Mitigation in spec |
|--------|--------------------|
| In-sample funding 2020-22 high, 2023+ compressed | P3 mandatory sub-period split |
| No perp price → basis ignored | P5 basis-noise injection |
| Short-perp liquidation on price spikes | Documented margin-buffer assumption; flagged as unmodeled |
| Funding sign-flips | Trailing-sign gate + worst-negative-stretch report |
| Funding-income 3× undercount | §2 units fix in P0 before anything else |

---

## 7. LLM-modulator tie-in (future, not P0–P5)

Your risk-debate agents could gate the sleeve (cut it when a funding-flip / stress regime is detected) and your
quant/LLM could predict funding regime (`sign_mode="predicted"`, the stretch fork). Natural fit for the existing
agent layer — but only after the gated baseline proves out.
