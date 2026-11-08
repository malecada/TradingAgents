# Charter 0 — DeepSeek V4-Pro extraction-quality probe (`llm-v2-charter0-2026-11-09`)

**Frozen:** 2026-11-08, before any model call on sample text. **Parent plan:**
`docs/superpowers/specs/2026-11-08-multiagent-v2-analysis-and-plan.md` (Phase 0, week 1).
**Parent mechanism:** `llm_c1_event_xs` (charter 2026-08-11; P0 v1 FAIL, v2 STOP, THESIS §63).
**Protocol lineage:** the Jev probe charter of 2026-09-29 (registered, never run); its truth
rebuild, blind review and gate scoring are reused unchanged.
**Authority:** user decisions of 2026-11-08 (DeepSeek via OpenRouter; Charter 0 is the first
executable step; paid spend for this charter capped at USD 5). No production, order or
account action follows from any verdict.

## 1. Question
Does DeepSeek V4-Pro (`deepseek/deepseek-v4-pro` on OpenRouter, provider Baidu, fp8), as sole
extractor with C1's v2 prompt, structured output and **no keyword prefilter**, in a **single
full-text pass**, meet the C1 P0 extraction floors on the 400 adjudicated C1 P0 articles on
which `gpt-5.4-mini` failed?

C1 P0 failures being tested:

| Round | Failure |
|---|---|
| v1 (300 articles) | precision regulatory 0.73, upgrade_partnership 0.79; recall pooled small classes 0.36; prefilter recall 0.53 |
| v2 (100 fresh articles, v2 prompt) | pooled precision 0.75; prefilter recall 0.70 |

The prefilter existed because running the LLM on every corpus article exceeded C1's cap. At
the smoke-test cost (about USD 0.0005–0.0016 per article) the 378K-article corpus costs
roughly USD 200–600, so the prefilter is removed rather than repaired.

## 2. Inputs and exposure
The 12 committed C1 P0 artifacts are registered by hash in `gates.json`: samples (300 + 100),
gpt-5.4-mini labels, adjudication sheets and keys, anonymization subsets and published
results, for v1 and v2. All 400 articles were inspected in August 2026. Stage is
development, reuse exploratory; no fresh-data claim is made.

## 3. Ground truth and blind review
Ground truth is rebuilt from committed files by `scripts/llm_event_xs_truth.py`: adjudicated
rows (154) follow the human verdict; unaudited rows (246) keep the gpt-5.4-mini labels. The
runner refuses to call the model unless the rebuild reproduces C1's published per-class
tp/fp/fn exactly.

After E1, one blind sheet (seed 20261109, `scripts/llm_v2c0_review.py`, construction and
parsing from `scripts/llm_jev_review.py`) presents, in shuffled order with A/B assignment
randomized per row:
- class disputes on unaudited rows where the model's class set differs from the stored one
  (verdicts `A`, `B`, `NO EVENTS`, `NEITHER: class/asset; …`);
- 20 agreement spot-checks on unaudited rows where class sets agree (`BOTH`, `NO EVENTS`,
  `NEITHER: …`);
- same-entity questions (`Y`/`N`) for correctly classified events whose asset names fail the
  automatic match rule.

Blindness: A and B show class sets only, no assets, no repeated classes; entity names appear on
`ENTITY` lines in an order drawn independently of the A/B letters; text is
whitespace-flattened; the header carries the frozen general rules, class definitions and v2
rules. The reviewer consults nothing under `research_runs/llm-v2c0-p0-label-20261109/outputs/`
or `data/llm_event_xs/` before the filled sheet is committed. The E1 outputs are pushed for
backup before the review. The human verdict is final.

The spot-check error rate counts a check verdict as an error only when it is not `BOTH` and it
changes the stored label (the committed v1 C1 scorer's rule). A `NEITHER` verdict always counts
as an error.

## 4. Protocol (frozen code; hashes in `gates.json`)
- **Model and route.** `deepseek/deepseek-v4-pro` via `POST https://openrouter.ai/api/v1/chat/completions`,
  body `provider: {order: ["Baidu"], allow_fallbacks: false, quantizations: ["fp8"]}`. The
  response must echo `model == deepseek/deepseek-v4-pro` and `provider == Baidu`; a mismatch
  fails the run. Baidu does not accept `seed`; determinism is measured, not assumed (§6).
- **Prompt.** C1's `PROMPT_V2` imported verbatim from `scripts/llm_event_xs_extract.py`
  (class definitions, general rules, v2 additional rules, severity rubric, evidence rule).
  Contract SHA-256 `4bf1e5ef146a4c85a55ae1ae674b1012baab4009be06ea235f73a3fd3c5df1c1` (`scripts/llm_v2c0_prompt.py::prompt_sha256`,
  covering prompt, JSON schema, class list, 4,000-character content cap and field order).
- **Structured output.** `response_format = json_schema, strict: true` with the schema
  `{events: [{asset: str, class: enum(6), severity: 1|2|3, evidence: str}], ambiguous: bool}`.
  Answers are validated structurally; a schema violation, a non-`stop` finish reason, empty
  content or non-numeric `usage.cost` fails the run.
- **Sampling.** `temperature: 0`, `max_tokens: 4000`, `reasoning: {effort: "medium"}`
  (reasoning is on by provider default; the effort is pinned so it cannot drift).
- **Text.** One call per article on headline, summary (when non-empty) and content (first
  4,000 characters, when non-empty), joined by newlines, built by `build_state` from
  `scripts/llm_jev_questions.py` (NaN-safe). C1's two-stage headline-then-content design is
  replaced by this single full-text pass.
- **Evidence spans.** C1 rule: an event whose `evidence` is not a loose substring of the
  supplied text is dropped and counted (`spans_dropped`).
- **Anonymized subsets.** C1's 50 + 50 rows (seeds 20260813, 20260814, identities read from the
  committed anon label files) re-labeled on text masked by C1's `anonymize()` (entity and date
  masks). Class-set agreement with the named labels is the anonymization gate.
- **Repeat subset (diagnostic).** 50 v1 articles (seed 20261109) labeled a second time with
  identical requests; class-set and asset flip rates are reported, never gated.
- **Concurrency.** Four worker threads; results keyed by sample index, order-independent.
- **Retries.** At most 5 attempts per call on HTTP 408/429/500/502/503/504/520/521/522/523/524/529,
  network errors, or a 200 body carrying only a retryable provider error; waits are
  `retry-after` capped at 120 s when given, otherwise 10, 20, 40 and 80 s. HTTP 402, exhausted
  retries, drift, or spend over the cap fail the run.
- **Spend cap.** USD 5.00 for E1, summed from each response's `usage.cost`; the run aborts
  before a call when the cap could be exceeded. Preflight (invented text, worst-case shapes)
  is capped at USD 0.05 and runs before any run claim.
- **Smoke evidence (2026-11-08, invented headlines only, 5 calls, USD 0.0046):**
  `research/llm-v2-charter0-2026-11-09/smoke/smoke-20261108.txt`. Model and provider echoed as
  pinned; schema-valid answers; reasoning tokens 94–998 per call; latency 2.8–16.8 s.
  Expected E1 spend about USD 0.3–0.8 for 500 calls.

## 5. Gates (union of 400 articles; two verdicts; floors are C1's, unchanged)
| Gate | Floor |
|---|---|
| Per-class precision (classes with < 10 final true events pooled) | >= 0.8 |
| Per-class recall (same pooling) | >= 0.6 |
| Asset-link accuracy on verified TP pairs | >= 0.9 |
| Anonymization class-set agreement (100 rows) | >= 0.8 |

C1's prefilter-recall gate is not applicable (no prefilter).

Asset match rule: a pair matches when the names are equal after C1's `norm_asset`, when one is a
contiguous whole-token run of the other, or when the reviewer answered `SAME = Y`. Where the
reviewer adopted the model's class set, the pair counts only on an explicit `SAME` answer;
pairs without one are unverified and excluded from the gated denominator (a lenient value
counting them as hits is reported).

Verdicts:
- **Primary — class extraction:** precision, recall and anonymization gates all pass.
- **Secondary — full C1 P0 equivalence:** all four gates pass.

Consequence for the parent plan (decided here, before the result): primary PASS puts typed
events into the dossier (plan §6.2 step 4); primary FAIL routes the dossier to article
summaries plus numeric cards and records a second extraction negative at a frontier-class
tier. Neither verdict authorizes anything else; P1–P3 work requires a new charter on data
after 2026-09-15 only.

## 6. Diagnostics (never gated or used for selection)
Wilson 95% intervals; gpt-5.4-mini head-to-head on the same final truth (biased toward
gpt-5.4-mini because unaudited truth rows originate from it); pre-review metrics and v1/v2
separately; C1-exact asset-link value; severity distribution per class; evidence spans dropped
and ambiguous rate; repeat-subset flip rates; per-class anonymization agreement; recall on
prefilter-negative rows; cost, latency, reasoning tokens and projected full-corpus cost.

## 7. Stop rules and attribution
- One shot. No prompt, schema, provider, sampling or threshold change after the first call on
  sample text, and no resampling.
- FAIL ends this design for this cycle.
- An E1 infrastructure failure consumes an attempt; any retry requires a recorded review
  decision and a new experiment ID.
- Budget: family `llm-news-event-extraction`, attempt budget 12, 2 prior attempts (C1 v1, v2;
  the Jev E1 registration was never started). E1 `llm-v2c0-p0-label-20261109` and E2
  `llm-v2c0-p0-score-20261109` (child of E1) consume 2 attempts.
- E2 is registered in `gates_e2.json` after the filled sheet has been validated by the parser
  and committed. Its rules are those of this charter, and its source and runtime hashes must
  equal E1's.
- After E2, an independent recomputation of the counts, asset link and anonymization
  agreement from the raw E1 outputs, the filled sheet and the key, without importing the
  scorer, must match `p0_verdict.json`.

## 8. Limitations
- Truth on the 246 unaudited rows is gpt-5.4-mini's label set; disputes are resolved by the
  blind review, agreements are not re-examined beyond the 20 spot-checks.
- No `seed` on the pinned provider; run-to-run variation is measured on 50 articles only.
- The anonymization check masks a fixed entity and date list; famous-episode leakage beyond
  that list is not measured here (it is addressed by the parent plan's probes).
- DeepSeek publishes no knowledge cutoff; the release date (2026-04-24) is the bound used by
  the parent plan. All 400 articles (2021–2025) predate it, so recall of outcomes is possible
  in principle; extraction of contemporaneous facts is the least exposed task, and the
  anonymization gate is the only in-charter control.
- Per-class counts are small (about 10–35); intervals are wide and the frozen floors decide.
- Entity-name style differs by source (model names are verbatim spans or tickers; stored
  names were normalized by an LLM); the `SAME` lines are the residual blindness limit.
