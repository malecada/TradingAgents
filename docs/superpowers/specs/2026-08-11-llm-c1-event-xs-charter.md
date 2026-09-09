# Charter C1 — Structured event extraction as cross-sectional features (`llm_c1_event_xs`)

**Registered:** 2026-08-11 (gates file `data/llm_event_xs/gates.json`, frozen
pre-result). **Parent proposal:** `master_thesis/LLM_INTEGRATION_PROPOSAL_2026-08.md` §5.
**Prior charter:** C2 veto — NEGATIVE at P1 (THESIS §62); its corpus assets
(Alpaca 2021-2023 BTC/ETH backfill, GDELT 2021) are inherited and extended here.
**Discipline:** probe ladder, STOP-on-fail; any STOP = charter dead this cycle.

## 1. Hypothesis

Typed, asset-linked, dated event features extracted from PIT news — classes:
*exploit/hack*, *regulatory action*, *exchange listing/delisting*, *token
unlock/emission announcement*, *protocol upgrade/partnership*,
*insolvency/withdrawal-halt* — carry cross-sectional predictive content for
1–10 day forward returns on the wide perp universe, beyond price/volume/funding
features. Null: fewer than 2 event classes show a significant event-study CAR
with the pre-registered sign.

Internal prior: §51 unlock forensics (median −3.05% post-cliff, large cliffs
−5.41%) — one class has demonstrated conditional drift. The falsified designs
(§48, §23.12, §33, §42) all emitted scalar opinions; C1 emits dated facts.

## 2. Corpus (frozen at extraction time; declared here)

- Alpaca News PIT store `data/sentiment/alpaca/` (bitemporal): original
  BTC/ETH build + C2 backfill + **wide backfill** (797 perp-base symbols,
  2021-01 → 2025-03, launched 2026-08-11 pre-registration).
- GDELT DOC 2.0 store `data/sentiment/gdelt/`: 2021-01 → 2025-03 (C2's 2021
  fetch + wide fetch launched 2026-08-11). Frozen default query; 250/day cap
  disclosed (day truncation biases toward high-coverage stories).
- Corpus is frozen when both backfills complete, before P0 sampling. Failed
  fetch days are disclosed in the extraction manifest.
- Timestamp convention: provider event_ts + 60s synthetic ingest lag
  (store-wide, disclosed). All joins to returns use entry at first daily bar
  open ≥ event day + 1 (t+1-open discipline).

## 3. Model, cost controls, and cutoff mitigations (frozen)

- Extractor: `gpt-5.4-mini`, temperature 0, Batch API where available,
  replay-cached. **Spend cap: $60** for the full charter (measured; sweep
  aborts if projected cost exceeds cap — abort = infra event, not a result).
- **Keyword prefilter** (frozen list, case-insensitive, on
  headline+summary+content): hack, hacked, exploit, exploited, breach, stolen,
  drained, vulnerability, insolven, bankrupt, withdraw, halt, suspend,
  frozen, depeg, collaps, liquidat, SEC, CFTC, lawsuit, charge, settle,
  ban, regulat, delist, listing, lists, launch, unlock, vesting, emission,
  airdrop, upgrade, hard fork, mainnet, partnership, acqui, merge.
  Non-matching articles are not sent to the LLM. Prefilter recall is
  measured in P0 (sample drawn from the FULL corpus, not the filtered set).
- **Dedup**: near-duplicate collapse before extraction — same day + same
  first-8-token headline prefix, plus exact-headline cross-source dedup.
- **Two-stage input**: headline+summary only; full content appended only
  when the first pass returns `ambiguous=true` (single retry, counted).
- **Cutoff mitigations** (dev window inside model pretraining window):
  1. Evidence-span requirement — every extracted event must include a
     verbatim quote from the article supporting the class and severity;
     rows with non-matching spans are dropped (counted, disclosed).
  2. Severity rubric is fact-based (see §4), not model judgment.
  3. P0 includes an anonymization spot-check: 50 of the sample articles
     re-extracted with entity names masked; class-label agreement ≥0.8
     with unmasked extraction, else memorization suspected → STOP.

## 4. Extraction output (frozen schema)

Per article → JSON list of events:
`{asset: <symbol-mappable name>, class: <one of 6>, severity: 1|2|3,
evidence: <verbatim span>, ambiguous: <bool>}`
Severity anchors (in-article facts only): 3 = protocol/venue-threatening
(>$100M or >5% supply or top-20 venue/asset); 2 = material (> $10M or
named top-100 asset direct impact); 1 = minor/peripheral mention.
Entity→perp mapping is a declared deliverable with an injectivity assertion
(`map_slugs_to_perps` lesson, §51 cycle). Dedup events by (asset, class, day).

## 5. Probe ladder (STOP-on-fail, in order)

### P0 — Extraction quality (hybrid hand-label, ~$5)
- Sample: 300 articles stratified from the FULL frozen corpus: 200 from
  prefilter-positive, 100 from prefilter-negative (recall check), spread
  across years 2021–2025 and both stores.
- **Hybrid ground truth (registered protocol)**: pre-label by a DIFFERENT
  model family (`claude-haiku-4-5`, temp 0) with the same schema; human
  adjudicates (a) every disagreement between pre-label and extractor,
  (b) a random 60-article agreement subsample (agreement-bias check).
  Human verdict is final; adjudication happens blind to which model
  produced which label.
- Gates: per-class precision ≥0.8, recall ≥0.6 (classes with <10 sample
  events pooled into "other" for the gate), asset-link accuracy ≥0.9,
  prefilter recall ≥0.85 (share of true events in the prefilter-negative
  stratum must be ≤ what this implies), anonymization agreement ≥0.8.
  One amendment round permitted (prompt/prefilter fix + fresh 100-article
  audit); STOP if still unmet.

### P1 — Coverage/breadth (compute only)
After full-corpus extraction: ≥60 distinct mapped symbols with ≥1 event in
the dev window; ≥8 events/month average across classes combined in 2023+;
per-class counts reported. STOP if breadth floor unmet.

### P2 — Event-study (compute only)
Per-class CAR(1–10d, t+1-open entry) vs matched non-event controls
(same-day universe, nearest vol-rank), block bootstrap. Registered signs:
hack −, delisting −, regulatory −, insolvency −, listing +, unlock −,
upgrade/partnership + (reported, weakest prior). PASS requires ≥2 classes
significant (p<0.05) with the registered sign. STOP if <2.

### P3 — Portfolio dev gates (compute only)
Event features (event-day indicators, exp-decayed counts, severity-weighted
sums) added to the §43 XS harness on the 799-sym store; **incremental
gate**: baseline = vol-rank + momentum + size feature set; net SR
improvement ≥ +0.15 at 5bp+funding costs, dual-family placebo p<0.05,
DSR>0.5 at declared n (this charter declares ≤12 ledgered configs), 3/4
sub-periods non-negative. Standalone event-strategy results reported but
cannot pass the charter.

## 6. Windows

Dev = 2021-01-01 → 2025-03-31 (aligned with predlab D; unlock/§43 cycles
used similar). Holdout = 2025-04-01 → 2026-07-01 **sealed** for a one-shot
only if P3 passes (this window is virgin for event-feature claims;
disclosed: it is spent for predlab book-level claims, which are a different
family). No gate reads holdout.

## 7. Multiplicity, ledger, stop rules

- Ledger `data/llm_event_xs/trial_ledger.jsonl`, append-only; ≤12 configs
  (P0 audit 2 rows incl. amendment, P2 seven class rows, P3 ≤3 feature-set
  rows). DSR at honest cumulative count.
- Stop rules: any probe STOP = dead this cycle; no post-hoc class
  exclusions; no prompt changes after P0 gate passes; no re-sampling after
  audit results exist; extraction store retained as a reusable asset
  regardless of verdict.
