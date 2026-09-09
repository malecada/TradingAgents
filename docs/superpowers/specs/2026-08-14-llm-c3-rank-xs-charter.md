# Charter C3 — LLM cross-sectional ranking from numeric PIT cards (`llm_c3_rank_xs`)

**Registered:** 2026-08-14 (gates file `data/llm_event_xs/../llm_rank_xs/gates.json`,
frozen pre-result). **Parent proposal:** `master_thesis/LLM_INTEGRATION_PROPOSAL_2026-08.md` §7.
**Prior charters:** C2 dead at P1 (§62), C1 dead at P0 (§63) → cards carry NO
event-digest section (numeric + categorical only, as the proposal's fallback).
**Discipline:** probe ladder, STOP-on-fail; any STOP = dead this cycle.

## 1. Hypothesis

An LLM given anonymized, structured numeric cards per asset produces an
ordinal ranking of the universe whose residual — after neutralizing to
vol-rank, momentum, and size — has positive IC vs forward returns. Null:
residual IC ≈ 0. The gate is incremental-only AND comparative: the LLM must
beat a GBDT twin trained on identical inputs, else it adds nothing.

## 2. Data and cards (frozen)

Universe: top-200 by trailing 30d median dollar volume, monthly PIT
refresh, from the 799-sym survivorship-safe store (`data/xsect/klines`).
Weekly cadence: cards built each Friday from data through that Friday
(t-1 discipline inside features); ranks predict the following week(s).

Card fields (all PIT, all numeric/categorical, no names in primary runs):
- returns: 4w and 12w log return; distance from 26w high
- risk: 20d EWMA vol; vol-of-vol 20d
- liquidity/size: 30d median dollar volume rank; CM CapMrktCurUSD (where
  covered; missing → null field, disclosed on card)
- funding: last 3d mean and 30d mean funding rate
- activity (where covered): 30d change in AdrActCnt and TxCnt
- unlocks: next-30d scheduled unlock as % of supply; trailing-30d unlocked
  % (unlock_xs machinery + slug map; missing → null)
- age: weeks since first kline; category label (DefiLlama protocolCategory)
Anonymization: asset identity replaced by a per-week random tag
(ASSET_001..); field values rounded to 3 significant digits. A named-card
variant exists ONLY for the P1 memorization probe.

## 3. Ranking construction (frozen)

Model `gpt-5.4-mini`, temperature 0, JSON output, replay-cached.
Partition-rank-average scheme: each week the universe is split into
batches of 25 cards (seeded partition); the LLM returns a full ordering
of each batch ("rank by expected 5-day forward return, best first");
per-asset score = mean normalized in-batch rank across R=2 rounds with
independent partitions. Deciles from scores. Spend cap $80 total.

## 4. Windows

Dev: 2021-01-01 → 2025-03-31. Holdout: 2025-04-01 → 2026-07-01, sealed,
virgin for this family (predlab book claims = separate family, disclosed),
one-shot only if P3 passes. No gate reads holdout.

## 5. Probe ladder (STOP-on-fail, in order)

- **P0 Determinism/stability (~$5):** 8 registered dev weeks (seeded
  draw); rerun with identical inputs → Spearman ≥0.9 per week; batch-order
  shuffle (same partition, shuffled presentation) → Spearman ≥0.8. STOP if
  ranking is a presentation artifact.
- **P1 Anonymization kill-probe (~$10):** 52-week seeded subset ranked
  with named cards. If named IC exceeds anonymous IC by >50% relative,
  the edge is memorization → STOP. Primary evaluation is ALWAYS anonymous.
- **P2 Incremental IC + GBDT twin (compute + ~$40):** full anonymous dev
  run. Weekly cross-sectional residualization of scores on {vol rank, 4w
  momentum, size rank}; residual IC vs 5d forward returns (primary; 10d,
  21d reported). Gates: (a) mean residual IC > 0 with Newey-West t ≥ 2.0;
  (b) LightGBM twin trained walk-forward on identical card features with
  identical targets — LLM residual IC must be ≥ GBDT residual IC. STOP on
  either.
- **P3 Decile LS dev gates (compute):** §43 XS harness verbatim, 5bp +
  funding: decile LS net SR ≥ 0.8; dual-family placebo p < 0.05; DSR > 0.5
  at declared n (≤10 configs this charter + honest cumulative family
  count); ≥3/4 sub-periods non-negative.

## 6. Multiplicity, ledger, stop rules

Ledger `data/llm_rank_xs/trial_ledger.jsonl`, append-only, ≤10 configs
(P0 2, P1 2, P2 3 incl. GBDT twin, P3 ≤3). No prompt changes after P0
runs; no post-hoc field additions/removals; no frequency changes; no
holdout reads before a registered one-shot. Any STOP = dead this cycle.
