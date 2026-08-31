# nlst2 — DEX legitimacy-classifier entry

Drafted 2026-08-31 BEFORE any feature-outcome statistic was computed;
**user-approved 2026-08-31**. Gates key `predlab_nlst2` registered at
approval, pre-result. No feature/outcome relationship examined yet.

## Motivation (user hypothesis + feasibility bound)

User hypothesis: discover new coins, classify legit vs scam from on-chain
(+news/social) data, buy only legit. Not tested by nlst (§73 —
unconditional). Feasibility bound from the closed nlst DEX panel
(exploratory forensics, 2026-08-31, ledgered as descriptive):

- Perfect-foresight no-rug subsets have POSITIVE means (+73%…+224% at
  7/14d; mean_ex_top +22%…+43%) despite negative medians (−30%) and
  pos-share only ~30% — a lottery with positive EV under rug foresight.
- Break-even bought-set rug rate at 7d: 42% vs 54% base — a classifier only
  needs moderate discrimination to flip EV sign AT THE MEAN.
- CEX variant OUT OF SCOPE: exchange listing is already a legitimacy filter
  and §73 shows mean ≈ 0/negative there; classifier would need XS skill,
  a different mechanism.
- News/social OUT OF SCOPE v1: PIT history for day-old microcaps not freely
  recoverable (Twitter paid, Telegram no archive) — recorded as infeasible.

Known risks stated upfront: payoff is moonshot-carried (top-1 |contrib|
35-67% even in foresight subsets) — the ≤50% concentration gate may bind;
capacity trivial ($1k/pool scale); MEV/sandwich unmodeled (disclosed).

## Sample

Existing 1,020 screened-KEEP pools (60/quarter, seed=7) + a BLIND extension
to 120/quarter (same screening protocol, same filters, fetched before any
feature-outcome stat is computed) ⇒ ~2,040 pools, ~800-850 entered events.
Same dev window 2021-01-01→2025-03-31; holdout untouched; entry/exit/cost
model IDENTICAL to nlst_dex (charter 2026-08-26).

## Pre-named features (8, all PIT at the hour-24 entry; frozen here)

| # | Feature | Source | Status |
|---|---------|--------|--------|
| F1 | lp_secured: share of LP tokens burned (0x0/0xdead) or in lockers (Unicrypt/Team.Finance/Pinklock list frozen in script) by h24 | pair-token Transfer logs | refetch |
| F2 | deployer_age: deployer nonce at pool-creation block | archive getTransactionCount | refetch |
| F3 | deployer_supply_share: deployer balance share of token at h24 | token Transfer logs | refetch |
| F4 | pool_supply_share: balanceOf(pair)/totalSupply of token at h24 (higher = less overhang) | archive eth_call | refetch |
| F5 | buyer_breadth: unique buyer addresses in first 24h | pair Swap logs w/ topics | refetch |
| F6 | sell_ratio: n_sell24 / n_swap24 | on disk | ready |
| F7 | sell_tax_proxy: median shortfall of realized sell output vs constant-product expectation | Swap+Sync on disk | ready |
| F8 | depth_growth: WETH reserve at h24 / first-Sync reserve | on disk | ready |

Composite legit-score: equal-weight mean of the 8 feature z-scores
(pre-signed by the hypothesized legit direction stated in the run script
header before computation; per-quarter z). NO fitting, NO weights tuning,
NO threshold search.

## P0 (one-shot, 2 tests, both must pass)

- T1 discrimination: AUC of legit-score for rug-within-14d, pooled dev.
  Gate: AUC ≥ 0.65 AND quarter-block bootstrap (≥1000 draws) 5th-pct ≥ 0.55.
- T2 economic transfer: top-half by legit-score (median split, fixed):
  mean net ret7 > 0, NW t (events by date, lag 5), one-sided p < 0.05,
  AND mean_ex_top-event still > 0 (lottery honesty).
FAIL either ⇒ cycle CLOSED (no re-weighting, no threshold moves, no new
features). Per-feature univariate rank-ICs reported descriptively either way.

## P1 (only if P0 passes; ONE frozen config)

Buy top-half legit-score pools at h24, $1k each, hold 7d, nlst cost model,
position cap 1/50 of book equity. House gates: dev net SR ≥ 1.0, shift
placebo p < 0.10, 2× cost-stress sign, top-1 event share ≤ 50%,
convention-swap no flip. Then STOP-AND-DECIDE with user; holdout one-shot
needs explicit user approval.

## Mechanics

Gates key `predlab_nlst2`; ledger experiment `predlab_nlst2_dexlegit`;
scripts `predlab_nlst2_features.py` (fetch+build, resumable) +
`predlab_nlst2_p0.py`; new feature code unit-tested before first use;
outputs `data/predlab/nlst/nlst2_*`. Fetch reuses the hardened dRPC lib.

## Amendments at registration (2026-08-31, pre-computation)

- F4 changed from draft's top-10 holder share to pool_supply_share
  (balanceOf(pair)/totalSupply at h24): full holder-set reconstruction needs
  token Transfer history from token genesis — infeasible at free tier.
  Recorded BEFORE any feature was computed.
- Deployer (F2/F3) defined precisely as: recipient of the first LP mint
  (first pair-token Transfer from 0x0) — the de-facto pool operator;
  creation-tx sender is unrecoverable from cached enumeration (no txhash).
- Approved defaults: sample extension to 120/quarter fetched blind; P0
  one-shot as specified; holdout stop-and-decide.
