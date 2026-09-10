# Fixed factor-floor accounting correction — 2026-09-10

## Purpose and authority

The user authorized reevaluation of the remaining eighteen BTC/ETH factor/V2 configurations. This is a bounded historical measurement correction of the closed factor-floor program. No new strategy, selection, adoption test, model fit, holdout, external data request, operational change or deployment is authorized by this charter. The 22 settlement-blocked accounting cases remain parked.

The July broad charter calls for a benchmark ranking, not a standalone factor adoption gate. Its exact18 enumeration and clean executed-source identity are not proven before July outcomes. The correction separately registers the preserved eighteen identities now. Historical artifacts and criteria remain immutable. Saved July scalar results and the sole saved BEST daily stream are comparison references, not valid contemporary evidence.

## Frozen inputs, grid and clock

Only the two locally saved original-worktree caches, with hashes in the accompanying provenance manifest and gates entry, may supply prices. A byte-preserving, date-filtered snapshot includes ALL available history through2025-03-31. Prices after that date are not parsed or loaded; no network or replacement source is permitted. These are unverified saved spot/mixed-provider proxy caches, without contemporaneous raw receipts or July input hashes. No actual perpetual price/funding history is claimed.

Development valuation dates are2021-11-07..2025-03-31 inclusive (1241); first return is2021-11-08 (1240 daily returns). Prior available history supplies signal warmup/state. Sizing resets inside development exactly as before. Full source/snapshot and development clocks must be sorted, unique, midnight UTC, contiguous and have finite positive coherent OHLC. Require at least200 prior days. For the XS cell only, use the common contiguous prior-history span from the later source start (2019-04-15), matching the original prior-history join; explicitly account for BTC2019-04-14 being outside that span. Both development calendars must match exactly, with no development join loss. Missing or malformed required data makes the affected cell unavailable, never filled/dropped/shortened. No rows after cutoff are admitted.

Grid, in preserved source order: TSMOM LS k7/14/30/90; TSMOM LO k7/14/30/90; TSMOM LS k180; MA LS10/50,20/100,50/200; MA LO10/50,20/100,50/200; Donchian LS20/55; XS BTC/ETH30d. All eighteen are reported without ranking-based selection or overwriting BEST.

Signal builders and V2 sizing remain the preserved July implementation: prior-close signals, prior-close sizing inputs, target_vol=.10, Kelly=.5, leverage cap3, hold7, early-exit .015, lookback20, vol cap.95. Sizing volatility retains sqrt252 because it sets quantities; reporting alone changes to sqrt365. Stateful Donchian receives all available pre-window history.

## Book and benchmark conventions

The repaired shared V2 engine uses simple price returns, pretrade NAV targets, actual signed marked-notional turnover, one-way fees, signed assumed daily funding+.0003 (long pays, short receives), and quadratic turnover impact. Fee=.0004, slippage=.0005, spread=.0001, impact=.00005. Keep3% intrabar price stop, trade-equity stop1.0, takeprofit0 and permanent15% per-coin drawdown halt. Full post-halt cash tails and initial NAV are retained. Stops use the assumed threshold fill even across gaps; funding is the daily opening-exposure approximation even on stop days. No gap-aware fill, realized funding, liquidation or stop-reentry policy is introduced.

The primary aggregate remains the daily arithmetic mean of two separately simulated sleeve returns. This is a 50/50 benchmark return index, not a pooled executable account: transfers, changing sleeve capital, cross-sleeve rebalancing costs, netting and margin are not modeled. Report each sleeve separately, exact halt dates, fees/funding/impact/turnover, price stops and threshold fills outside the day's envelope.

Primary index metrics: full-clock Sharpe sqrt365*mean/std(ddof1), zero cash hurdle; compounded total return; drawdown including initial NAV; n1240. Also report sqrt252 Sharpe for historical metric comparison. Active-only Sharpe is diagnostic; never replace the full clock. No DSR or bootstrap adoption verdict is inferred because there is no original standalone factor gate. The eighteen related configurations and every sensitivity remain disclosed.

## Fixed measurement and forensic comparisons

For every configuration, before any selection:

1. Primary repaired engine with original assumptions.
2. Zero execution cost (fee/slippage/spread/impact zero, funding unchanged).
3. Twice execution cost (all four execution terms doubled, funding unchanged).
4. Zero assumed funding (original execution costs).
5. Preserved July engine, AST-extracted without invoking its CLI/import side effects, on exactly the same inputs/signals/targets.

All four repaired runs independently apply the same stop rule; changed NAV may change halt dates. Preserve all90 two-sleeve book/index evaluations, nested under18 configuration ledger records, not90 distinct hypotheses. Also save18 invalid-log shadow diagnostics. These replace primary gross exposure*simple return with exposure*log1p(simple return) on the frozen primary exposure/stop schedule and retain the identical primary funding and execution-charge fractions. They are not executable counterfactuals, do not recompute stops, and cannot support promotion. Any invalid arithmetic is explicitly unavailable.

Compare old-engine replay against all eighteen archived scalar metrics using original sqrt252/no-initial-NAV-DD definitions (absolute tolerance1e-10), and against the archived selected daily stream (rtol0, atol1e-10). A mismatch preserves all results but prohibits exact historical reproduction/attribution claims. A match supports numerical parity on saved references; it does not prove unavailable July data lineage. Old versus repaired on the same current snapshot separately isolates the declared accounting change from source differences.

Before real results, synthetic hand checks must cover fees/funding signs and flat, stop/exit attribution, initial-loss drawdown, full cash tail, planted positive-return book, frozen-log distortion, zero-cost/funding controls and unavailable calendar/data. Existing signal causality and sizing golden tests must pass. No empirical parameter search, resampling-based winner selection or new pass threshold is added.

## Execution and evidence

Commit this charter, exact gate, source/input/archive hashes before empirical outcomes. Commit reviewed runner/trace source before execution; registry preflight must prove clean executable inputs and unchanged gate/policy. Exclusively create one output directory, refuse repeats and preserve incomplete starts. Save per-config target signals, all book returns, primary traces, all scalar outcomes, runtime/source provenance and hashes. Recheck input/source/gate hashes at completion. Append exactly18 primary records with nested diagnostics to the central financial ledger, preserving its original730-row/428150-byte prefix. Original gates and evidence remain unchanged. Any unavailable case remains in the denominator. Completion updates the correction ledger, findings and report; no revised historical file is overwritten.

Implementation sequence: input/source provenance and committed registration; tested trace-only engine extension and isolated wrapper; independent review and source commit; full fixed run; independent result/negative-forensic review; preservation checks and complete evidence report; commit and push. Any substantive methodological amendment must be committed before affected outcomes exist. A completed run cannot be repeated under this key.
