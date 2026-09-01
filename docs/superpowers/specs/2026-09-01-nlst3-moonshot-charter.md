# nlst3 — DEX future-performance ranking (smart-money + deployer history)

Drafted 2026-09-01 BEFORE any new feature-outcome statistic; **user-approved
2026-09-01**; gates `predlab_nlst3` registered at approval, pre-result. Third and final
pre-registered bite at the new-pool panel; contamination handled by
fresh-sample-only evaluation (below). Context: §73 unconditional NEGATIVE,
§74 legitimacy classifier inverted (AUC 0.65 but legit half −48% vs −23%);
post-verdict forensics (ledgered): moonshot base rate P(ret7>+100%) = 3.2%,
no existing feature reaches IC_moon 0.1, top-decile foresight mean +353%.

## Goal (falsifiable)

Can PIT wallet-intelligence features rank new Uniswap v2 pools by future
net return well enough that the top quintile has POSITIVE mean net 7d
return at $1k? (Economic bar stated up front: requires roughly 2.5-3x
moonshot enrichment in the selected quintile; if smart-money signal is not
strong, this dies at P0 — by design.)

## Contamination control (key design)

- BLIND sample extension 120 → 180 pools/quarter (same screening, seed=7
  continuation): ~1,020 new pools, ~400 new entered events.
- ALL P0 statistics evaluated ONLY on the fresh extension ("eval set").
  Pools from nlst/nlst2 (outcomes observed twice) serve solely as PIT
  conditioning history for track-record features — never as eval events.
- Old features may enter the composite with signs fixed to the previously
  observed direction (disclosed as in-sample-derived); the composite claim
  is therefore out-of-sample sign transfer onto virgin events.

## Features (frozen here; G = new/blind, C = carried controls)

| # | Feature | Sign | Source |
|---|---------|------|--------|
| G1 | smart_money_volshare: share of first-24h buy volume from wallets in the top quintile of PIT track record (mean net ret7 of pools they bought in h24, ≥3 prior completed pools, outcomes completed before this pool's creation) | + | full swap-history refetch |
| G2 | smart_money_breadth: count of distinct such wallets buying in h24 | + | same |
| G3 | serial_deployer_perf: deployer's mean ret7 across prior completed pools (≥1 prior; NaN if fresh) | + | deployer index across sample |
| G4 | serial_deployer_count: number of prior pools by deployer | − | same |
| G5 | early_net_inflow: net WETH inflow h0-24 / initial depth | + | on disk |
| G6 | buy_acceleration: swaps h12-24 / swaps h0-12 | + | on disk |
| G7 | ownership_renounced by h24 (OwnershipTransferred → 0x0) | − | token logs refetch (sign: §74 tail lives in non-renounced/scammy bucket) |
| C1 | deployer_supply_share | + | nlst2 cache (sign = observed IC_moon direction, disclosed) |
| C2 | deployer_age | − | nlst2 cache (disclosed) |
| C3 | depth_growth | + | nlst2 cache (disclosed) |

Composite: equal-weight mean of signed per-quarter z-scores, ≥6 available
features required. NO fitting, NO weight tuning, NO threshold search.
Track-record definitions frozen: buyer = swap recipient of WETH-in swap in
first 24h; wallet outcome for a pool = that pool's net ret7 at $1k (own
event table); expanding, strictly PIT (prior pool's entry+7d exit must
precede current pool's creation).

## P0 (one-shot, on the ~400-event eval set only; both must pass)

- T1 existence: Spearman IC(composite, ret7) > 0 with quarter-block
  bootstrap (≥1000) 5th-pct > 0. Report IC_moon alongside.
- T2 economics: top-quintile by composite: mean net ret7 > 0, NW t
  one-sided p < 0.05, AND ex-top-event mean > 0, AND top-1 |contrib| ≤ 50%.
FAIL either ⇒ family CLOSED — no re-weighting, no new features, no target
changes. Per-feature eval-set ICs reported descriptively either way.

## P1 (only on P0 PASS; ONE frozen config)

Buy top-quintile at h24, $1k each, hold 7d, nlst cost model, 1/50 position
cap. House gates (dev net SR ≥ 1, shift placebo p < 0.10, 2× cost-stress,
concentration ≤50%, convention swap). STOP-AND-DECIDE with user before any
holdout; holdout untouched.

## Fetch plan (resumable, hardened dRPC lib; revised at approval)

Track records need only hour-24 buyer data, which nlst2_raw already caches
for previously entered pools. Steps:
1. Extension screening + windows (~1,020 pools, ~2-3h).
2. Re-run nlst2 feature fetch — covers the new entered pools' h24 topic'd
   swaps, transfers, deployer, balances (~400 × 6 calls).
3. Token OwnershipTransferred logs h0-24 for all entered pools (1 call each).
4. Wallet ledger + deployer index built offline from caches; eval-set P0.

## Mechanics

Gates key `predlab_nlst3` (registered on approval, pre-result); ledger
experiment `predlab_nlst3_moonshot`; scripts `predlab_nlst3_{fetch,features,p0}.py`
+ unit tests; outputs `data/predlab/nlst/nlst3_*`. Descriptive per-quarter
tables regardless of verdict (THESIS §75).
