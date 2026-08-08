# unlock_xs_t1 — build brief

Prepared 2026-08-08. The gate for this experiment was frozen on 2026-07-30 in
`data/rebuild/gates.json` and **must not be edited** — the pre-registration is
already spent. What remains is execution only.

Sibling experiment `value_xs_t1` ran the same day and closed dev-gate NEGATIVE
0/4 (see `docs/…/2026-07-30-value-unlock-xs-design.md` and commit `d093681`).
This half was never started: zero ledger rows, no script, no data namespace.

## Hypothesis (frozen)

Coins facing large near-term scheduled supply unlocks underperform those facing
none. Weekly, dollar-neutral, long low-burden / short high-burden.

`unlock_burden(t, N) = tokens_unlocking(t, t+N] / circulating_supply(t)`

## Why this is not a repeat of value_xs_t1

Different data source, different economic channel, near-disjoint universe (129
DefiLlama emission names vs 132 CoinMetrics names). The value factor asked
whether the market misprices *network activity*; this asks whether it
misprices a *mechanical, publicly scheduled supply shock*. The prior is
better: the unlock date is knowable in advance and the literature on equity
lockup expiries finds real drift.

## What must be built

| Piece | Notes |
|---|---|
| `scripts/unlock_xs_universe.py` | DefiLlama emissions ∩ 799-symbol perp store, liquidity floor = prior-month median quote-volume rank ≤ 150. Mirror `value_xs_universe.py`. |
| Emissions snapshot + vintage stamp | `defillama-datasets.llama.fi/emissions/{protocol}`, ~1.8 MB each. Stamp the fetch per [[reference-data-source-audit-jul30]] — DefiLlama serves the *current* schedule and amends silently. |
| PIT reconstruction | Replay `metadata.events` in timestamp order, applying only events with `timestamp <= t`. Yields the forward unlock curve **as known at t**, not today's amended one. Linear unlocks stay in scope. This is the load-bearing correctness component — get it reviewed. |
| `scripts/unlock_xs_dev.py` | Probes first, STOP contract with exit 2 + `probes.json` written on failure (the bug class that cost `value_xs_t1` two review rounds), then the grid. |

Reuse verbatim, do not re-derive: `run_ls_portfolio` + `RF_DAILY` from
`tradingagents/xsect/carry_xs.py` (the frozen §46 engine), `maxdd` and
`rank_placebo_pvalue` from `tradingagents/xsect/portfolio.py`, DSR helpers from
`tradingagents/strategies/v3/backtest/dsr.py`, `log_trial` from
`tradingagents/rebuild/ledger.py`.

## Probes — all STOP-on-fail, run to completion before the grid

- **P0 — silent restatement.** Reconstructed circulating supply vs an
  independent series (CoinMetrics `SplyCur` where covered, CoinGecko
  otherwise). Divergence *growing toward the present* means DefiLlama has been
  rewriting history without emitting timestamped events, which would make the
  whole PIT reconstruction a fiction. This is the confound-discriminating probe
  and it runs first.
- **P1 — breadth.** Median ≥ 20 names, reported per year. If the first two dev
  years fall below the floor, the dev window is truncated forward and the
  truncation is logged *before* the grid runs.
- **P2 — event study.** Mean forward return t+1..t+14 around cliff unlocks
  releasing ≥ 1% of circulating supply must carry the expected negative sign.

## Grid (frozen — 2 cells only)

`lookahead_days ∈ {14, 30}` × `breadth = decile`. Weekly Monday rebalance,
10 bps/side, rf 4.5% on full capital, dev window 2021-01-01 → 2025-03-31.

Controls, both gating: **C1** trailing-30d realized vol alone; **C2** log market
cap alone, using as-of-t circulating supply from the same reconstruction (not
CoinMetrics — the two universes barely overlap).

## Pass bar

net SR ≥ 1.0 **and** ΔSR vs C1 > 0 **and** ΔSR vs C2 > 0 **and** dual-family
placebo worse-p ≤ 0.05 (500 draws each, costs and rf re-applied inside every
draw) **and** DSR ≥ 0.9 at the registered `n_trials=2`. Ledger-cumulative DSR
is reported but not gated — that amendment was declared before any data was
touched. Tiebreak: highest DSR, then lowest placebo p.

## Expectation and stop discipline

Base rates say negative: eleven consecutive pre-registered leads have failed,
and `value_xs_t1` cleared its placebo and both controls yet still missed the SR
floor by more than half. Two cells is a narrow grid by design. A dev-gate
failure ends the lead this cycle; revival needs a new registered cycle on fresh
data. The holdout (2025-04-01 → 2026-07-01) stays sealed either way — it is
spent only on a champion that has already cleared dev.

## Two rails to honor that this experiment's twin broke

1. **Commit the producing code before logging trials.** The four `value_xs_t1`
   ledger rows cite a commit that does not contain the grid function. The
   ledger's `git_commit` field is only as honest as the working tree was clean.
2. **Never re-run a logged config.** `log_trial()` does not deduplicate on
   `config_hash`; a re-run silently inflates the multiplicity denominator.

## Cost

Roughly a day. No paid data, no GPU, no LLM spend. The thesis does not need
this result — it is a marginal-value addition to the negative map, and skipping
it costs nothing.
