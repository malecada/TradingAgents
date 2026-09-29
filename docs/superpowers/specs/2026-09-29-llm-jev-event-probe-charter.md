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

## 3. Ground truth
Ground truth is rebuilt from committed files by `scripts/llm_event_xs_truth.py`:
- adjudicated rows (154) follow the human verdict;
- unaudited rows (246) keep the gpt-5.4-mini labels.

The runner refuses to call Jev unless the rebuild reproduces C1's published
per-class tp/fp/fn exactly. After E1, a blind sheet (seed 20260929) presents:
- class disputes on unaudited rows (A/B/NO EVENTS/NEITHER);
- 20 agreement spot-checks (BOTH/NO EVENTS/NEITHER);
- same-entity questions on correctly classified events whose names fail the
  automatic rule.

A and B show unique event classes only (no assets, no repeated classes), so
neither side can be recognized by format. Entity names appear on separate
`ENTITY` lines beside each `SAME` question. All rendered text is
whitespace-flattened. The reviewer does not open anything under
`research_runs/llm-jev-p0-label-20260929/outputs/` before the review is committed.

The human verdict is final. A Jev asset of `none` counts as an asset mismatch
and is not reviewed. The spot-check error rate counts a check verdict as an
error only when it is not BOTH and it changes the stored label (C1 semantics).

## 4. Protocol (frozen code; hashes in `gates.json`)
- Question wording SHA-256 `5204286177c37570653da49d476129533474db67143e8d7c613986cf01c784a0` (`scripts/llm_jev_questions.py`).
- Each call asks six Noul class questions plus an asset Choice over up to 30
  deterministic candidates and `none`.
- Two calls are made per article, with candidates forward then reversed. A
  class is an event when the mean probability is at least 0.5. The asset is
  the argmax of the mean.
- The anonymization subsets (50 + 50, C1's) ask the class questions only, on
  text masked by C1's `anonymize()`.
- Retries: at most 5 attempts per call on HTTP 408/429/500/502/503/504/524/529
  or network errors, waiting `retry-after` when given, else 10, 20, 40, 80 s.
  Any model/provider drift, malformed or out-of-range answer (non-finite or
  outside [0, 1]), exhausted retry, HTTP 402 or spend over the cap fails the run.
- Before the run claim, a live preflight on invented text only sends the
  worst-case request shapes (30-candidate choice, 4,000-character non-ASCII
  content, class-only anonymized call). A preflight failure exits before any
  claim and consumes no attempt.
- Model resolution evidence (smoke test 2026-09-29, invented headlines only,
  16 calls, USD 0.00098): alias `typesafe/jev-1.13` resolves to
  `typesafe/jev-1.13-20260917` from provider `TypeSafe`; the dated ID is
  accepted and echoed. Expected E1 spend is about USD 0.05 for 1,000 calls.
- Candidate spans are 1–3 tokens (the design said 1–4; 4 added no measured
  coverage and raises 30-cap pressure) and dictionary matches follow
  dictionary order.

## 5. Gates (union of 400 articles; two verdicts)
| Gate | Floor |
|---|---|
| Per-class precision (classes with < 10 final true events pooled) | >= 0.8 |
| Per-class recall (same pooling) | >= 0.6 |
| Asset-link accuracy on TP pairs | >= 0.9 |
| Anonymization class-set agreement (100 rows) | >= 0.8 |
C1's prefilter-recall gate is not applicable.
Primary verdict — class extraction: precision, recall and anonymization gates all
pass. Secondary verdict — full C1 P0 equivalence: all four gates pass. The split
was decided 2026-09-29, after a truth-only candidate-coverage profile (83/96 truth
assets reachable) and before any Jev output (design spec §5.2 amendment).

## 6. Diagnostics (never gated or used for selection)
- Wilson 95% intervals.
- gpt-5.4-mini head-to-head on the same final truth. Unaudited truth rows
  originate from gpt-5.4-mini, so this comparison is biased toward it.
- Pre-review metrics, and v1/v2 separately.
- Asset candidate coverage.
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
- E2 is registered in `gates_e2.json` after the filled sheet is committed;
  its rules are those of this charter.

## 9. Limitations
- There is no evidence span. Anonymization agreement is the only memorization
  check.
- Jev's training cutoff, determinism and retention are undisclosed.
- The reviewer judges classes without seeing assets in A/B; assets are judged
  only on the ENTITY/SAME lines.
- Entity-name style can differ by source (Jev names are verbatim spans or
  tickers; stored names were normalized by an LLM), a residual blindness limit.
- Per-class counts are small (about 10–35).
- Jev was trained on synthetic data, and its calibration claims are
  unverified.
