# nlst4 — DEX smart-money ranking at scale (registered 2026-09-04)

Status: **REGISTERED pre-result.** Gates key `predlab_nlst4` in
`data/predlab/gates.json` is written in the same commit as this file, before
any pool beyond the closed nlst3 sample is screened. Source:
`master_thesis/LEADS_SCOPE_2026-09-02.md` Lead 3; parents §73–§75 (nlst,
nlst2, nlst3 — all CLOSED; nlst3 T1 PASS IC +0.136, T2 FAIL economics,
one-event-carried top quintile). Decisions under the user's afk autonomy grant
(2026-09-04): (a) quota 600 KEEP per quarter in the seeded order (quarters whose
candidate list exhausts first end ragged — declared, not a search); (b) the
C-LLM cell is **dropped at registration**: it needs an Etherscan API key and
none exists in the repo (coverage probe cannot be run); revivable only by a new
registered cell; (c) the 2025-04-01 → 2026-06-30 pool enumeration (H2 holdout)
is fetched after the dev screening completes and is NOT evaluated this cycle.

## Goal (falsifiable)

The frozen nlst3 composite (ten features, signs, per-quarter equal-weight z,
≥ 6 features) evaluated on a much larger set of virgin Uniswap-v2 pools either
powers the economic claim — top-quintile positive mean net 7-day return at
$1k that is not one-event-carried — or falsifies it with adequate power.
Null: the composite ranks (T1) but the top quintile's mean is carried by a
handful of moonshots (T2 FAIL), as in nlst3.

## Contamination control

All P0 statistics on the **new** virgin pools only (KEEP #181 onward per
quarter in `screened.jsonl` file order). The 3,060 prior pools (outcomes
observed by nlst/nlst2/nlst3) serve solely as PIT wallet track-record and
deployer history. Composite frozen; no re-weighting, no threshold search, no
new features.

## Sample and power

Screening continues from the nlst3 state (63,052 screened, 3,060 KEEP, 180
per quarter) in the seed-7 permutation until 600 KEEP per quarter or
exhaustion of the quarter's F1/F4 candidate list (four quarters — 2021Q4,
2022Q3, 2022Q4, 2023Q1 — are expected to exhaust at ≈ 500–550). Expected
≈ 7,000 new KEEP pools, ≈ 40 % entered at h24 ⇒ ≈ 2,800 entered events, ≈ 560
top-quintile selections; at the observed ex-top mean (+30 %) and SD ≈ 250 %,
SE ≈ 10 pp ⇒ t ≈ 3. The screening state before this cycle is snapshotted to
`dex_raw/screened_nlst3_snapshot.jsonl` (sha256 recorded) so the closed
family's eval set stays reproducible.

## Cells and gates (one-shot on the new pools)

- **T1 existence (replication):** Spearman IC(composite, net ret7) > 0 with
  quarter-block bootstrap (1,000 draws, seed 7) 5th percentile > 0.
- **T2 economics:** top-quintile mean net ret7 > 0 with NW one-sided p < 0.05
  AND ex-top-event mean > 0 AND top-1 share ≤ 25 % AND $5k cost-stress keeps
  the sign; median disclosed.
- Both required. FAIL ⇒ family CLOSED (final; no fourth bite).

## P1 (only on T1+T2 PASS; one config)

Buy the top quintile at h24, $1k each, hold 7 d, nlst cost model (exact
constant-product round trip with 0.3 % LP fee per side + two swaps' gas), 1/50
position cap; house gates (net SR ≥ 1, shift placebo p < 0.10, 2× cost-stress,
concentration ≤ 25 %, convention swap). Then STOP-AND-DECIDE (holdout H2
enumeration 2025-04 → 2026-06, one-shot, user decision).

## Data and mechanics

dRPC free endpoint (`https://eth.drpc.org`, 10k-block getLogs cap, 0.22 s
throttle; observed 3,300–3,700 screens/h, ≈ 480 pools/h phase C, ≈ 6 calls
per pool features). Scripts: `predlab_nlst4_screen.py` (imports the closed
family's `phase_a/phase_b/phase_c` with the quota raised to 600 — the closed
script is not edited), then `predlab_nlst4_features.py` (nlst2 + nlst3 feature
caches for the new pools, same functions) and `predlab_nlst4_p0.py` (one-shot;
refuses if verdicts exist). Logs/pids beside the data
(`data/predlab/nlst/nlst4_*.log/.pid`); every phase is append-only and
resumable. Ledger experiment `predlab_nlst4`. THESIS §79.

**Effort:** ≈ 35–48 h screening + ≈ 15 h phase C + ≈ 12 h features
(background) + 1 day analysis. **Cost:** $0.
