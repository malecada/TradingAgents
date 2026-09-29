# Charter — Jev P0 extraction-quality probe (`llm-jev-event-2026-09-29`)

**Frozen:** 2026-09-29, before any Jev call on sample text. **Design:**
`docs/superpowers/specs/2026-09-29-llm-jev-event-probe-design.md`.
**Parent mechanism:** `llm_c1_event_xs` (charter 2026-08-11; P0 v1 FAIL, v2 STOP).
**Authority:** user instruction of 2026-09-29 (probe only; OpenRouter key supplied;
paid spend capped at USD 5). No production, order or account action follows.

## 1. Question
Does Jev (`typesafe/jev-1.13-20260917`, OpenRouter Decisions API, provider locked to
TypeSafe, alpha endpoint), as sole class extractor with no keyword prefilter,
meet the C1 P0 extraction floors on the 400 adjudicated C1 P0 articles?

## 2. Inputs and exposure
The 12 committed C1 P0 artifacts are registered by hash in `gates.json`:
- samples, gpt-5.4-mini labels, adjudication sheets and keys;
- anonymization subsets and published results, for v1 and v2.

All 400 articles were inspected in August 2026. The stage is development and
reuse is exploratory; no fresh-data claim is made.

## 3. Ground truth and blind review
Ground truth is rebuilt from committed files by `scripts/llm_event_xs_truth.py`:
- adjudicated rows (154) follow the human verdict;
- unaudited rows (246) keep the gpt-5.4-mini labels.

The runner refuses to call Jev unless the rebuild reproduces C1's published
per-class tp/fp/fn exactly. After E1, a blind sheet (seed 20260929) presents:
- class disputes on unaudited rows (A/B/NO EVENTS/NEITHER);
- 20 agreement spot-checks (BOTH/NO EVENTS/NEITHER);
- same-entity questions (Y/N) on correctly classified events whose names fail
  the automatic rule.

Blindness:
- A and B show unique event classes only, with no assets and no repeated classes.
- On class rows, entity names appear on `ENTITY (class): X = … | Y = …` lines in
  an order drawn independently of the A/B letters. On entity rows, A and B are
  the two names.
- All rendered text is whitespace-flattened.
- The sheet header carries the frozen general rules, class definitions and v2
  rules (which apply to every row), plus the verdict instructions: A or B only
  when that class set is exactly right, otherwise `NEITHER: class/asset; …`.
- The reviewer consults nothing under
  `research_runs/llm-jev-p0-label-20260929/outputs/` or `data/llm_event_xs/`,
  and no git or GitHub view of those files, before the filled sheet is
  committed. The E1 outputs are pushed for backup before the review.

The human verdict is final. A Jev asset of `none` counts as an asset mismatch
and is not reviewed.

The spot-check error rate counts a check verdict as an error only when it is
not BOTH and it changes the stored label. This is the committed v1 C1 scorer's
rule. C1's published v2 figure (4/30) counted every non-BOTH verdict; under
this rule it would be 1/30. A NEITHER verdict always counts as an error.

## 4. Protocol (frozen code; hashes in `gates.json`)
- Question wording SHA-256 `5204286177c37570653da49d476129533474db67143e8d7c613986cf01c784a0` (`scripts/llm_jev_questions.py`).
- Each call asks six Noul class questions plus an asset Choice over up to 30
  deterministic candidates and `none`.
- Articles with no candidate get no asset question; their asset is `none`
  (5 articles, none with a truth event).
- Two calls are made per article, with candidates forward then reversed. A
  class is an event when the mean probability is at least 0.5.
- The asset is the argmax of the mean. Ties go to the lowest key, meaning the
  earliest candidate; Jev reports probabilities to two decimals, so ties can
  occur.
- Jev emits at most one event per class per article.
- The anonymization subsets (50 + 50, C1's) ask the class questions only, on
  text masked by C1's `anonymize()`.
- Retries:
  - at most 5 attempts per call, on HTTP 408/429/500/502/503/504/520/521/522/523/524/529
    or network errors;
  - waits are `retry-after` capped at 120 s when given, otherwise 10, 20, 40
    and 80 s.
- The run fails on any of:
  - model or provider drift;
  - a malformed or out-of-range answer (non-finite, or outside [0, 1]);
  - exhausted retries;
  - HTTP 402;
  - spend over the cap.
- Before the run claim, a live preflight sends the worst-case request shapes
  on invented text only: a 30-candidate choice, 4,000-character non-ASCII
  content, and a class-only anonymized call. A preflight failure exits before
  any claim and consumes no attempt.
- Model resolution evidence: a smoke test on 2026-09-29 used invented
  headlines only, 16 calls, USD 0.00098; logs are in
  `research/llm-jev-event-2026-09-29/smoke/`. Alias `typesafe/jev-1.13`
  resolves to `typesafe/jev-1.13-20260917` from provider `TypeSafe`, and the
  dated ID is accepted and echoed. Expected E1 spend is about USD 0.05 for
  1,000 calls.
- Candidate spans are 1–3 tokens and may cross spaced punctuation; dictionary
  matches follow dictionary order. The design said 1–4 tokens; 4 added no
  measured coverage and raises pressure on the 30-candidate cap.

## 5. Gates (union of 400 articles; two verdicts)
| Gate | Floor |
|---|---|
| Per-class precision (classes with < 10 final true events pooled) | >= 0.8 |
| Per-class recall (same pooling) | >= 0.6 |
| Asset-link accuracy on verified TP pairs | >= 0.9 |
| Anonymization class-set agreement (100 rows) | >= 0.8 |

C1's prefilter-recall gate is not applicable.

Asset match rule:
- A pair matches when the names are equal after C1's `norm_asset` (lowercase,
  strip, alias map), when one is a contiguous whole-token run of the other, or
  when the reviewer answered SAME = Y.
- This is looser than C1's exact `norm_asset` equality. Known false positives
  include Bitcoin/Bitcoin Cash and Binance/Binance.US.
- Where the reviewer adopted Jev's class set, the pair counts only on an
  explicit SAME answer. Pairs without one are unverified and excluded from the
  gated denominator.
- On NEITHER rows, the reviewer-typed assets are compared with the automatic
  rule only.

Verdicts:
- Primary — class extraction: the precision, recall and anonymization gates
  all pass.
- Secondary — full C1 P0 equivalence: all four gates pass.

The split was decided on 2026-09-29, after a truth-only candidate-coverage
profile (83/96 truth assets reachable) and before any Jev output (design spec
§5.2 amendment).

## 6. Diagnostics (never gated or used for selection)
- Wilson 95% intervals.
- gpt-5.4-mini head-to-head on the same final truth. Unaudited truth rows
  originate from gpt-5.4-mini, so this comparison is biased toward it.
- Pre-review metrics, and v1/v2 separately.
- Asset figures:
  - candidate coverage;
  - the lenient asset-link value, with unverified pairs counted as hits;
  - the number of unverified pairs;
  - the C1-exact asset-link value (`norm_asset` equality only).
- Reliability bins and threshold sweep 0.3–0.9.
- Stability: flip rate, |Δp|, exact 0/1 counts.
- Recall on prefilter-negative rows.
- Cost, latency and projected full-corpus cost.

## 7. Stop rules and attribution
- One shot. No amendment, wording, threshold, candidate or model change after
  the first sample call, and no resampling.
- FAIL ends this design for this cycle.
- An E1 infrastructure failure consumes an attempt; any retry requires a
  recorded review decision and a new experiment ID.
- An asset-link failure with candidate coverage below 0.9 is recorded as a
  candidate-generator (measurement) defect; the secondary verdict is still FAIL.
- PASS authorizes nothing further. Any P1–P3 work requires a new charter
  using data after 2026-09-15 only.

## 8. Budget and lifecycle
- Family `llm-news-event-extraction`: budget 12, with 2 prior attempts.
- E1 `llm-jev-p0-label-20260929` and E2 `llm-jev-p0-score-20260929` (child)
  consume 2 attempts.
- E2 is registered in `gates_e2.json` after the filled sheet has been
  validated by the parser and committed. Its rules are those of this charter,
  and its source and runtime hashes must equal E1's.
- After E2, an independent reviewer recomputes the counts, asset link and
  anonymization agreement from the raw E1 outputs, the filled sheet and the
  key, without importing the scorer, and must match `p0_verdict.json`.

## 9. Limitations
- There is no evidence span. Anonymization agreement is the only memorization
  check.
- The anonymization check is confounded: anonymized calls also drop the asset
  question, so disagreement mixes masking with the change in question set.
- Jev's training cutoff, determinism and retention are undisclosed.
- The reviewer judges classes without seeing assets in A/B; assets are judged
  only on the ENTITY/SAME lines.
- Entity-name style can differ by source: Jev names are verbatim spans or
  tickers, while stored names were normalized by an LLM. On entity rows this is
  a residual blindness limit.
- Two truth articles hold two regulatory events each, so regulatory recall is
  capped at 33/35.
- Per-class counts are small (about 10–35).
- Jev was trained on synthetic data, and its calibration claims are
  unverified.
