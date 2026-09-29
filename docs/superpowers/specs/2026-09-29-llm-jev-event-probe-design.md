# Design — Jev extraction-quality probe on the C1 P0 sample (`llm_jev_event`)

**Date:** 2026-09-29. **Status:** design approved in conversation; this file is
the written spec. The frozen experiment contract is a separate charter
(`docs/superpowers/specs/2026-09-29-llm-jev-event-probe-charter.md`) written
from this design and committed with the registration before any Jev call on
sample data.

**Scope (user decision, 2026-09-29):** probe only. P1 breadth, P2 event study,
P3 portfolio, C2 crisis veto, severity and any full-corpus sweep are out of
scope. A PASS triggers nothing automatically.

**Parent family:** `llm_c1_event_xs` (charter
`docs/superpowers/specs/2026-08-11-llm-c1-event-xs-charter.md`, gates
`data/llm_event_xs/gates.json`, ledger `data/llm_event_xs/trial_ledger.jsonl`).
C1 remains dead; this is a new registration of the same mechanism, not a C1
amendment.

## 1. Question

Does TypeSafe's Jev (System One model; typed answers with probabilities, no
text generation), used as the sole class extractor with no keyword prefilter,
meet the C1 P0 extraction floors on the same 400 adjudicated articles on which
`gpt-5.4-mini` failed?

C1 P0 failures being tested:

| Round | Failure |
|---|---|
| v1 (300 articles) | precision regulatory 0.73, upgrade_partnership 0.79; recall pooled small classes 0.36; prefilter recall 0.53 |
| v2 (100 fresh articles, v2 prompt) | pooled precision 0.75; prefilter recall 0.70 |

The prefilter existed because running an LLM on every corpus article exceeded
the C1 spend cap. At Jev's price (USD 0.042 per million input tokens, output
free) the full 378k-article corpus costs roughly USD 10, so the prefilter is
removed rather than repaired.

## 2. Inputs (all committed, read-only)

- `data/llm_event_xs/p0_sample.parquet` (300 rows), `p0_sample_v2.parquet` (100).
- `data/llm_event_xs/p0_extractor_labels.json`, `p0v2_extractor_labels.json`
  (gpt-5.4-mini labels).
- `data/llm_event_xs/p0_adjudication.md` + `p0_adjudication_key.json` (115
  rows: 55 disagreements, 60 agreement checks); `p0v2_adjudication.md` +
  `p0v2_adjudication_key.json` (39 rows: 9 + 30).
- `data/llm_event_xs/p0_result.json`, `p0v2_result.json` (published C1
  metrics, used only for the reproduction check).
- `data/llm_event_xs/p0_extractor_labels_anon.json`,
  `p0v2_extractor_labels_anon.json` define the 50+50 anonymization subsets
  (seeds 20260813, 20260814).

Sample exposure: all 400 articles were inspected in August 2026. Stage
`development`, reuse `exploratory`; no fresh-data claim.

## 3. Ground truth

### 3.1 Rebuild from committed artifacts

The C1 scorer read the `claude-haiku-4-5` pre-labels from a session scratchpad
that no longer exists. The adjudication sheets carry both label sets as
`class/asset/sevN` lines (multiple events separated by `;`), so ground truth is
rebuilt from committed files only:

- Adjudicated rows (154): verdict `A`/`B` selects that label set (parsed from
  the sheet line); `BOTH` = the shared set; `NO EVENTS` = empty; `NEITHER` =
  the adjudicator's correction (all C1 NEITHER rows resolved to empty).
- Unaudited rows (185 v1 + 61 v2 = 246): gpt-5.4-mini labels (class-set
  agreement with the pre-label; C1's correct-by-agreement convention).

**Reproduction check (blocking):** scoring the gpt-5.4-mini labels against the
rebuilt truth with the C1 matching rule must reproduce the per-class tp/fp/fn
counts in both `p0_result.json` and `p0v2_result.json` exactly. No registration
proceeds until it does.

### 3.2 Blind human review of Jev disputes

After E1 and before any metric is computed, one blind sheet is produced for
the user (C1 markdown format; A/B randomly assigned between Jev and the stored
label with a fixed seed; key kept in a separate file the reviewer does not
open; human verdict final):

1. **Class disputes:** unaudited rows where Jev's class-set differs from the
   stored class-set. Verdicts `A`, `B`, `BOTH`, `NO EVENTS`,
   `NEITHER: <labels>`.
2. **Agreement spot-checks:** 20 randomly chosen (fixed seed) unaudited rows
   where the class-sets agree, interleaved with the disputes.
3. **Asset disputes:** on every correctly classified event (all 400 rows),
   when the Jev asset and the truth asset fail the automatic match rule
   (§5.3), the sheet asks "same entity? Y/N" with the two names in random
   order.

The 154 previously adjudicated rows keep their human labels for classes and
are not re-reviewed for classes. A class verdict selecting a label set adopts
that set's assets as truth (C1 convention), so asset disputes arise only where
the chosen truth and Jev's events share a class but name different entities.

## 4. Jev call protocol

### 4.1 Client and access

- Plain `requests` (declared dependency); no SDK, no lockfile change.
- Route (user decision, 2026-09-29): OpenRouter Decisions API,
  `POST https://openrouter.ai/api/alpha/decisions`, bearer key from the
  checkout's `.env` (`OPENROUTER_API_KEY`, or `OPENROUTER_API` as the user
  named it). Request body `{model, state, questions, provider}`; the question
  wire format matches TypeSafe's (`type` noul/choice/score, `instructions`,
  `criteria`). The endpoint is labelled alpha by OpenRouter (disclosed).
- `provider = {"only": ["TypeSafe"], "allow_fallbacks": false}` so no other
  provider can answer.
- Credentials are never read or printed by the assistant; the client loads
  them through `dotenv`.
- The model is pinned to a dated immutable ID (form
  `typesafe/jev-1.13-20260917`) taken from the smoke-test response's `model`
  field (§8 step 4) and frozen in the charter. Every response's `id`,
  `model`, `provider` and `usage` are stored. A response naming a different
  model or provider fails the run.
- Retry on HTTP 429/5xx/524/529 with exponential backoff honoring
  `retry-after`, at most 5 attempts per call; exhaustion fails the run (no
  silent unknown rows). HTTP 402 (credits) fails immediately.
- Spend cap USD 5, summed from each response's `usage.cost`; the run aborts
  before a call when the next call's projected cost would exceed it.

### 4.2 State

JSON object `{"headline": ..., "summary": ... (if non-empty),
"content": first 4,000 characters (if non-empty)}`. The anonymized variant
applies C1's `anonymize()` (imported from `scripts/llm_event_xs_extract.py`)
to each field.

### 4.3 Questions (seven per call, answered in one pass)

- **Six Nouls**, one per class. Each instruction = C1's general rules
  ("Only report events the article itself asserts as fact or formal action
  (not speculation, price commentary, or opinion)"; "No knowledge of later
  events; judge only the given text") + the class definition taken verbatim
  from C1's prompt class list and the v2 additional rules. Exact strings live
  in `scripts/llm_jev_questions.py`; their SHA-256 is pinned by a test and
  frozen in the charter.
- **One asset Choice:** "Which entity is primarily affected by the main event
  the article reports?" Options = code-generated candidates (max 30) plus
  `none` ("the article reports no qualifying event, or no listed entity
  fits").
- Severity is not asked.

### 4.4 Candidate generator (deterministic, frozen)

Union, case-insensitive dedup, ordered by first appearance, capped at 30:

1. Alpaca rows only: `symbols` split on commas, quote suffix stripped
   (`BTCUSD` → `BTC`). GDELT `symbols` reflect the fetch query, not the
   article, and are ignored.
2. Dictionary matches (word-boundary, case-insensitive) in headline+summary
   against a frozen list: C1's `ENTITY_MASK` names plus a fixed list of major
   coin names and tickers.
3. Capitalized spans of 1–4 tokens in headline+summary (tokens starting with
   an uppercase letter or containing a digit), leading articles stripped,
   single tokens in a frozen stoplist dropped.

Content is not scanned for candidates. Truth assets mentioned only in content
are therefore unreachable; the coverage diagnostic (§6) measures this.

### 4.5 Repeats, aggregation, anonymization

- Two calls per article: candidates in forward order, then reversed. Noul
  questions are identical in both.
- Per class, the mean of the two Noul probabilities; event when mean ≥ 0.5.
- Asset = argmax of the mean Choice probability per candidate; `none` = no
  asset. The three multi-event articles share one asset (disclosed).
- Anonymization check: the same 50 v1 and 50 v2 rows as C1, anonymized state,
  same two-call protocol.
- Volume: 400 × 2 + 100 × 2 = 1,000 calls, about 0.6M input tokens
  (≈ USD 0.03).

### 4.6 Frozen before any sample call

Question strings, candidate generator code and lists, threshold 0.5, model
version, seeds. The only permitted pre-registration calls are a smoke test on
invented headlines (not corpus text).

## 5. Scoring and gates

### 5.1 Matching

C1 rule: per article, each Jev event is greedily matched to an unused truth
event of the same class → TP, else FP; unmatched truth events → FN. Classes
with fewer than 10 true events in the final (post-review) truth across the 400
articles are pooled into `pooled_small` for gates.

### 5.2 Gates (all must pass; evaluated on the union of 400 articles)

| Gate | Floor |
|---|---|
| Per-class precision (pooling as above) | ≥ 0.8 |
| Per-class recall (pooling as above) | ≥ 0.6 |
| Asset-link accuracy on TP pairs | ≥ 0.9 |
| Anonymization class-set agreement (100 rows) | ≥ 0.8 |

C1's prefilter-recall gate is not applicable (no prefilter).

### 5.3 Asset match rule

After C1's `norm_asset` (lowercase, strip, alias map), a pair matches when the
strings are equal or one is a contiguous whole-token subsequence of the other.
Remaining mismatches go to the human sheet (§3.2 item 3); a "Y" verdict counts
as a match.

## 6. Diagnostics (reported, never gated or used for selection)

- Wilson 95% intervals per gate class; statement of power (n ≈ 14 per class
  gives roughly [0.55, 0.93] around a 0.8 precision).
- gpt-5.4-mini scored on the same final truth (head-to-head), with the
  disclosure that unaudited truth rows originate from gpt-5.4-mini.
- Pre-review metrics against stored labels only; v1 and v2 separately.
- Asset candidate coverage: share of TP pairs whose truth entity is among the
  candidates.
- Per-class reliability bins and a threshold sweep 0.3–0.9.
- Stability: class-set flip rate between the two calls, |Δp| distribution,
  count of exact 0/1 probabilities.
- Recall on the prefilter-negative stratum (≈ 7 true events; descriptive only).
- Cost, latency, projected full-corpus cost.

## 7. Stop rules, attribution, registration

### 7.1 Stop rules

- One shot. No amendment round, no change to questions, threshold,
  candidates or model after the first sample call, no resampling.
- FAIL = this Jev extraction design is dead for this cycle.
- An E1 infrastructure failure consumes an attempt; any retry needs a
  recorded review decision and a new experiment ID.
- PASS permits nothing further automatically. P1–P3 would require a new
  charter handling Jev's undisclosed training cutoff (the C1 sealed holdout
  2025-04-01 → 2026-07-01 predates Jev's release, so only data after
  2026-09-15 is clean).

### 7.2 Attribution (governance: distinguish failure types)

- Asset-link failure with candidate coverage < 0.9 is recorded as a
  candidate-generator (measurement) defect, not a Jev failure; the verdict is
  still FAIL.
- Label-quality concerns are bounded by the spot-check error rate and
  reported alongside the verdict.

### 7.3 Lifecycle registration

- Program directory `research/llm-jev-event-2026-09-29/`, registration
  `gates.json` (schema v1, `tradingagents.research` run-admission contract).
- Family: mechanism "LLM typed news event extraction"; attempt budget 12
  (C1's declared configuration count), prior attempts 2 (C1 P0 v1 and v2),
  history reference = C1 ledger and charter.
- Dataset: C1 P0 samples, exposure `2021-01-01 → 2025-04-01` state `exposed`.
- **E1 `llm-jev-p0-label-20260929`** (parent null): Jev calls; JSON outputs =
  labels, anonymized labels, raw responses, review sheet data, review key.
  No metrics. A non-lifecycle helper renders the JSON sheet to markdown for
  the reviewer.
- **E2 `llm-jev-p0-score-20260929`** (parent E1): registered in a second file
  `gates_e2.json` committed after the filled sheet is committed; inputs = E1
  outputs, filled sheet, C1 artifacts; outputs = verdict and diagnostics JSON.
  The charter (gates and rules for both steps) is frozen in the design commit
  before E1.
- Attempts consumed: E1 + E2 → 4 of 12.
- Paid-resource authority: the user's instruction of 2026-09-29, capped at
  USD 5, recorded in the charter.

## 8. Implementation outline

### 8.1 Files (new only; C1 files are read, never modified)

| File | Responsibility |
|---|---|
| `scripts/llm_event_xs_truth.py` | Rebuild C1 truth from committed artifacts; C1 matching/scoring helpers |
| `scripts/llm_jev_client.py` | OpenRouter Decisions client: pinning, provider lock, retries, usage and cost cap |
| `scripts/llm_jev_questions.py` | Frozen question strings, candidate generator, request builder |
| `scripts/llm_jev_event_p0.py` | `label` (E1) and `score` (E2) runners via `ResearchRun`; sheet render/parse |
| `research/llm-jev-event-2026-09-29/` | `gates.json`, later `gates_e2.json`, `STATE.md` |
| `tests/research/test_llm_jev_*.py` | Offline tests (no network) |

### 8.2 Tests

- Truth rebuild reproduces C1 v1 and v2 per-class counts exactly (real
  committed artifacts) — blocking.
- Scorer on a synthetic case with hand-computed expected values.
- Candidate generator on fixed headlines; request payload shape; pinned hash
  of question strings.
- Aggregation, threshold, asset argmax, flip rate.
- Blind sheet: seeded A/B assignment, key absent from sheet, parse round-trip
  of a filled sheet.
- Client with mocked HTTP: retry on 429, failure on version change, abort at
  the cost cap.
- Repository named offline target `scripts/verify_offline.py` still passes.

### 8.3 Order

1. Truth rebuild + reproduction test; stop if it does not match.
2. Remaining code and offline tests.
3. User adds the OpenRouter key to this worktree's `.env` (done 2026-09-29).
4. Smoke test on invented headlines; fix client issues; take the dated model ID
   from the response `model` field and freeze it. *(Moved before the design commit
   relative to the conversation outline, because the version pin and client
   source hashes must be final at registration.)*
5. Charter + E1 registration + `tradingagents.research check`; independent
   reviewer subagent checks charter and registration against C1 artifacts;
   commit; push to origin.
6. E1 run → blind sheet.
7. User review (≈ 30–45 min).
8. Commit filled sheet + `gates_e2.json`; E2 run → verdict; independent
   forensic review; findings section and program `STATE.md`.

## 9. Known limitations (disclosed in the charter)

- No evidence span: C1's first cutoff mitigation is lost; anonymization
  agreement is the remaining memorization check.
- Jev's training cutoff, determinism and data retention are undisclosed; the
  sample (2021–2025) predates its release. Class labels describe article text,
  which limits but does not remove hindsight risk.
- Truth on non-disputed unaudited rows originates from gpt-5.4-mini; Jev is
  credited only where it agrees, and disputes are human-reviewed.
- Small per-class counts; a PASS clears a floor on this sample, not a
  population claim.
- Jev was trained on synthetic data; vendor calibration claims are unverified.
  Independent tests report type-specific miscalibration and order
  sensitivity, addressed here by the fixed threshold and two-order averaging.
