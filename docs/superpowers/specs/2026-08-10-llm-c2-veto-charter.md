# Charter C2 — LLM asymmetric risk veto on the champion book (`llm_c2_veto_ovl`)

**Registered:** 2026-08-10 (gates key `llm_c2_veto_ovl`, frozen pre-result).
**Parent proposal:** `master_thesis/LLM_INTEGRATION_PROPOSAL_2026-08.md` §6.
**Status discipline:** probe ladder with STOP-on-fail; any STOP = charter dead
this cycle; revival requires a new registered cycle on fresh data.

## 1. Hypothesis

Rare, high-severity market-level stress events (exchange insolvency, major
hack, systemic depeg, systemic regulatory/macro shock) are identifiable in
PIT news within 24h, and a *reduce-only* overlay (exposure multiplier
m ∈ {0, 0.5}, capped at ≤10 veto-days per calendar year) on the Phase-O
champion low-vol LS book reduces MaxDD / tail CVaR without degrading SR.

Null: no DD-quantile improvement over the un-vetoed book at SR
non-inferiority.

Priors priced in: symmetric daily LLM modulation is falsified (§48); V4
(§16) showed regime-class information at best buys drawdown, not alpha —
therefore the gate IS DD reduction at SR-neutrality, never SR gain. A veto
that never fires reproduces the champion exactly; asymmetry + rarity bound
the damage an unskilled classifier can do.

## 2. Book and engine (frozen)

- Book: Phase-O final champion — `ewma_20` low-vol rank LS, eq-quintile,
  monthly top-200 PIT, daily rebalance, `vt15_naive20_b100` overlay (O4
  formula), 5bp + funding costs. Engine: `opt.build_signal` +
  `opt.run_ls` + O4 overlay verbatim from
  `scripts/predlab_champion_backtest.py` (report-only rerun of frozen
  configs; no new trials on the book itself).
- Veto actuation: multiplier `m_t` applied to the overlay scale on day t:
  `s_veto_t = s_t * m_t`; overlay net recomputed with the O4 cost formula
  on `s_veto` (transition costs of de-risking and re-risking are charged).
- Timing: causal veto decisions for day t may use news with ingest
  timestamp ≤ end of day t−1 UTC (engine convention: row-t weights trade
  the day-t return, info through t−1). The oracle (P0 only) is exempt —
  it is a ceiling, not a strategy.

## 3. Windows

- **Dev D:** 2021-01-01 → 2025-03-31 (the champion's design window). All
  probes P0–P3 run here.
- **V (2025-04-01 → 2026-07-01):** NON-VIRGIN; disclosure-only reporting,
  no gate reads it.
- **Forward F (2026-07-02 → open):** sealed. If dev PASS, the veto overlay
  registers a forward one-shot alongside the champion's F spend (earliest
  2027-01-02, separate verdicts file `data/predlab/llm_veto/f_verdicts.json`;
  spend script refuses if file exists).

## 4. Veto budget (frozen)

≤10 veto-days (m<1) per calendar year, enforced deterministically in
calendar order: once a year's budget is exhausted, further signals map to
m=1. Severity→multiplier mapping frozen: severity 2 → m=0.0, severity 1 →
m=0.5, severity 0 → m=1.0.

## 5. Probe ladder (STOP-on-fail, in order)

### P0 — Oracle ceiling (zero LLM cost)
Perfect-foresight veto: for each calendar year in D, select the k=10 days
with the worst overlaid-book net returns; set m=0 on those days; recompute
with transition costs. Report relative MaxDD reduction, ΔSR, CVaR5.
**STOP if relative MaxDD reduction < 20% or ΔSR < −0.05.** The ceiling is
also the yardstick that prices P3: a classifier can only capture part of it.

### P1 — News recall audit (zero LLM cost bar pennies)
Admissible corpus (declared): Alpaca News PIT store
(`TradingAgents/data/sentiment/alpaca/`, bitemporal, ingest-timestamped)
**including a declared backfill of currently missing months over D**
(provider fixed archive; backfill rows carry backfill-time `as_of_ts` and
are disclosed as such — same precedent as the original store build), plus
GDELT DOC 2.0 backfill (`scripts/backfill_gdelt.py`) where run. Corpus is
frozen before P2 prompts execute.
For each oracle veto day: does the corpus contain ≥1 same-day-or-earlier
(≤24h lookback) market-level crisis-class headline (hack / insolvency /
withdrawal-halt / depeg / regulatory shock / liquidation cascade / macro
shock)? Audited per day (LLM-assisted screen + hand check).
**STOP if coverage < 60% of oracle veto days.** If tail days are
news-silent, the information channel does not exist in the admissible
corpus.

### P2 — Classifier dev (bounded LLM spend)
- Model pinned: `gpt-5.4-mini`, temperature 0, replay-cached. One frozen
  prompt (appendix A of this charter, committed before any evaluation
  run). No prompt re-tuning after seeing evaluation output — a failed
  prompt kills the charter this cycle.
- Input per day t: deduplicated market-level headline digest from the
  admissible corpus, ingest ≤ end of day t−1 UTC, 48h window, max 60
  headlines, no prices, no returns.
- Output: market severity ∈ {0,1,2} + one-line rationale.
- Episode list frozen for leave-one-episode-out (LOEO): May-2021 crash;
  Terra/LUNA May-2022; 3AC/Celsius Jun–Jul-2022; FTX Nov-2022; USDC/SVB
  Mar-2023; Aug-2024 carry unwind; Feb–Mar-2025 drawdown.
- Gates: (a) recall ≥0.5 — fraction of oracle veto days receiving m<1
  before budget exhaustion; (b) veto budget respected by construction;
  (c) **anonymization kill-probe**: rerun with entity names and dates
  stripped from headlines; anonymized recall must be ≥0.7× named recall,
  else the signal is memorization → **STOP** (constraint 4.2 of the
  proposal; dev window is inside the model's pretraining window, so this
  probe is load-bearing).

### P3 — Overlay dev gates (compute only)
All on D, transition costs included, vs the un-vetoed champion book:
- G1: relative MaxDD reduction ≥ 10%.
- G2: relative CVaR5 (mean of worst 5% daily returns) improvement ≥ 5%.
- G3: SR non-inferiority — point ΔSR ≥ −0.10 AND stationary block
  bootstrap (mean block 20d, 2000 draws) P(ΔSR ≤ −0.30) < 0.05.
- G4: random-veto placebo — 400 budget-matched random veto-day draws;
  real MaxDD reduction > 95th percentile of placebo distribution.
- G5: attribution breadth — veto days with m<1 intersect ≥2 distinct
  frozen episodes (the claim must not be a single-episode artifact).
Dev PASS = P0–P3 all pass. V window reported for disclosure only.

## 6. Multiplicity and spend (frozen)

- Ledgered configs ≤ 6: P0 oracle (1), P2 classifier named + anonymized
  (2), P3 overlay real + placebo-summary (2), reserve (1). Each row into
  `data/predlab/trial_ledger.jsonl`, experiment `llm_c2_veto_ovl`; DSR
  accounting joins the predlab pool at the honest cumulative count.
- LLM spend cap: $50 (cheap tier, cached). P0 free; P1 ≈ pennies.

## 7. Stop rules

- Any probe STOP → charter dead this cycle; no post-hoc episode
  exclusions; no post-hoc budget changes; no prompt iteration after
  evaluation output exists; no reading V or F for any gate.
- Amendments only pre-result, declared in-file in gates.json.

## Appendix A — frozen classifier prompt (P2)

```
You are a crypto market risk auditor. You are given a digest of news
headlines from the last 48 hours (crypto and macro). Classify the
CURRENT market-level stress severity for a systematic crypto portfolio.

Severity definitions:
- 2 (severe): ongoing or imminent systemic event — major exchange
  insolvency or withdrawal halt, top-20 protocol/stablecoin collapse or
  depeg in progress, exchange hack > $100M at a top-10 venue, forced
  liquidation cascade across venues, or an acute macro shock hitting all
  risk assets.
- 1 (elevated): credible, specific signs that such an event may be
  developing (proof-of-reserves panic, large fund insolvency rumors from
  multiple sources, regulatory emergency action against a systemically
  important venue).
- 0 (normal): everything else, including ordinary bad news, price drops,
  lawsuits, and single-project failures outside the top tier.

Rules: judge only from the given headlines; do not use knowledge of
later events; prefer 0 when uncertain; output exactly:
SEVERITY: <0|1|2>
REASON: <one line>
```

Anonymized variant: identical, with entity names and dates replaced by
placeholders (ENTITY_1, DATE_1, …) in the digest by deterministic
preprocessing.
