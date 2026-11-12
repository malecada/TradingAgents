# Charter 2 — Reader configuration (`llm-v2-charter2`) — DRAFT, NOT FROZEN

**Status:** draft, second revision, 2026-11-12. The decisions on the first draft are recorded in §10. Stage R0
(code, tests, synthetic dry run) is complete. Stage R1 (pilot) has not run. Nothing is registered and no outcome has been
joined under this document. The freeze (R2) needs approval.
**Family:** `llm-multiagent-v2`, attempts used 2 of 6 (Charter 1 interrupted with a failed receipt, Charter 1b
FAIL). This charter is attempt 3.
**Predecessor:** `docs/superpowers/specs/2026-11-11-llm-v2-charter1b-dev-run-charter.md`, run
`llm-v2c1b-dev-run-20261112`, verdict FAIL.

## 1. Why this configuration

Charter 1b tested the assignment-literal order: a quant forecast, then agents that read one anonymised dossier
per asset and state a probability, then a judge, then a blend. On 66 weeks the judge probability carried no
information next to the quant forecast (encompassing t −0.02), its calibration slope was 0.007 and its
dispersion was 0.06. The mean of the three analysts did better than the judge that summarised them (IC 0.030
against 0.012), so the layers lost information. The agents were asked for an absolute probability on a
relative target, one asset at a time, which is a forecasting task the language model has no training signal
for.

The reader configuration removes that task from the language model. Agents read text and record what it
states. A fitted cross-sectional model, trained walk-forward on realised outcomes, decides what those records
are worth and in which direction. The language model never states a probability, a return or a rank.

### Earlier programmes that bear on this (closed-programmes ledger)

| Programme | What was tested | Outcome | Bearing here |
|---|---|---|---|
| `llm_c1_event_xs` (Aug 2026, THESIS §63) | Typed-event extraction as cross-sectional features | Stopped at extraction quality (precision 0.75 < 0.80, keyword prefilter recall 0.70 < 0.85). The forecast value of the features was never tested. | Same idea. The prefilter that failed is gone: every linked article is typed (§3.1). Extraction quality is measured again (§4, R1). |
| Sentiment index as model feature (THESIS §33) | LLM/BERT sentiment index as a feature for BTC and ETH daily | All gates failed | Time-series, two assets, tone only. Here: cross-section of 50, event facts, weekly. A tone-only result here would repeat that negative. |
| `llm_c2_veto_ovl` (§62) | News veto overlay | Stopped at P1 | Not repeated. |
| `llm_c3_rank_xs`, `llm_c3p_pair_xs` (§64, §65) | LLM ranks or compares assets directly on numeric cards | Order artefact; pairwise IC +0.008, t 1.01 on 222 weeks | The "direct comparison" change. Largely tested already, without text. |
| Event-time news trading research | Reaction within minutes to hours | No-go | The "fresher information" change inherits this prior. |
| News → volatility (lead list Aug 2026) | Not run | Open | The "different target" change. Reuses the records of this charter at no extra LLM cost. |

## 2. Question, target, universe

Unchanged from Charter 1b. Universe: the 50 perpetual contracts with the highest trailing 30-day dollar volume
each Friday. Decision time: Saturday 00:00 UTC after the Friday card. Target: the 7-day simple return rank
within the universe. Windows: development 2022-01-07 → 2024-12-27 (156 weeks, of which the first 52 are
training only and the last 104, from 2023-01-06, are the test weeks), Sealed-A 2025-01 → 2026-04, Sealed-B
2026-05 → 2026-12-11. Both sealed windows are untouched and their text is not built.

Question: do facts read from anonymised news and community text by language-model agents carry information
about next-week relative returns beyond the quant forecast, when a fitted model and not the language model
maps them to a forecast?

## 3. Design

```
text store ─► typing (done, cached) ─► reading sets ─► reader A ─┐
                                                      reader B ─┴─► comparison in code ─► agreed records ──────┐
                                                                          │                                    ▼
                                                                          └─► adjudicator (disputed assets) ─► consensus records
                                                                                                               │
numeric card ─► quant features ──────────────────────┐                                                        ▼
                                                      └─► fitted model ◄── asset-week text features (code, no model call)
                                                                │
                                                                ▼
                                                    ranks ─► rule-based book
```

### 3.1 Reading list (built, no cost)

`tradingagents/reader/items.py`, `scripts/reader_items_build.py`. One row per (document, linked asset) for
every row of the text store, joined to the cached typing. Event dates start on 2021-12-01 and capture dates
(`as_of_ts`) on 2022-01-01, so the 30-day windows of the decisions of January 2022 are partly covered. Those
weeks are training weeks only. The dossier of Charter 1b showed at most 25 items per asset-week and that cap
was binding in 26 % of asset-weeks (nearly every week for the largest assets). The reading list has no cap for
news. An item is admissible for a decision when its `as_of_ts` is not later than the decision time.

Facts of the built tables (no outcome involved). A "read" item is a typed event or opinion item that yields a
record for the asset under §3.2. The work-list rows were recomputed with the final reading rule on the
registered universe; the first draft quoted 50,362 documents and 58,958 records, counted before the restriction
to the weekly top 50.

| Quantity | Value |
|---|---|
| Item rows (document × linked asset) | 520,434 over 353,739 documents (news 54,258, community 299,481) |
| Typed documents | 101,099 (event 37,486, opinion 30,554, other types 33,059); name leaks after de-identification: 0 |
| Asset-weeks (7,800) with any linked item in the last 7 days | 78.2 % (median 6 items, 90th percentile 61) |
| Asset-weeks with a read item in the last 7 days | 55.1 % (median 1, mean 6.2, 90th percentile 15); test weeks 52.5 % |
| Asset-weeks with a read item in the last 30 days | 76.7 % (median 5); test weeks 75.6 % |
| Assets per week with a read item in the last 7 days | 16 to 39 of 50, median 28 |
| Reader work list | 48,261 documents (news 26,476, community 21,785; events 25,855, opinions 22,406), 53,330 (document, asset) records |
| Assets per document | one asset in 91.3 % of documents, mean 1.105, at most 9 |
| Records read for the filed asset (summary without an asset token) | 9,953 |
| Consistency with the dossier build | 96,431 of 96,433 community posts selected by the 25-newest rule are typed |

Text is sparse. In 45 % of asset-weeks block B can have nothing from the last 7 days and the asset sits at the
tied rank of zero activity. Records that the readers mark as side mentions or as not about the asset lower the
coverage further. This limits power and is part of the power statement in §5.

### 3.2 Reader agents and consensus

Code: `tradingagents/reader/reading.py`, `schema.py`, `extract.py`, `consensus.py`.

**Unit.** One typed document of type `event` or `analysis_opinion`, in its de-identified summary of at most
two sentences (role tokens, rounded magnitudes, relative dates, no names). Price recaps, promotional and
unrelated items are excluded by their type. An agent sees the item type (event, or opinion or analysis), the
source kind (news or community post), the summary and the asset tokens to record. It sees no price series, no
return, no date, no outlet and no quant forecast. A document is read once, not once per week.

**Reading set.** For the Friday card of a universe week the decision time is that Friday plus one day. The
reading set of an asset holds the store rows linked to the asset with `decision − 30 d ≤ event_ts ≤ decision`
and `as_of_ts ≤ decision`: every news row, and of the community posts only those with the asset as primary
subject, the newest 25 (by `event_ts`, ties by `doc_id`). This is the rule under which the typing was bought,
so every member is typed.

**Records to read.** A row of a reading set yields a record when its document is typed `event` or
`analysis_opinion` and either the summary carries the token of the asset, or the summary carries no asset
token at all and the asset is the single primary link of the document. In the second case the asset is listed
as `Filed_asset` and the agent is told that the summary describes it without a token. The unit of a document
lists every asset with such a row in any reading set, sorted by token.

**Record.**

| Field | Values | Rule |
|---|---|---|
| `relevance` | subject, side_mention, not_about | whether the item is about this asset |
| `event_class` | security_incident, legal_regulatory, exchange_listing, exchange_delisting, token_supply_increase, token_supply_reduction, protocol_upgrade_or_launch, partnership_or_integration, adoption_or_product, distress_or_outage, governance_or_team, funding_or_treasury, market_wide_or_macro, opinion_or_forecast, other | one class |
| `status` | occurred, scheduled, proposed_or_rumoured | from the wording |
| `direction` | favourable, unfavourable, mixed, neutral | for a holder of the asset, from what the item states. For an opinion item: the stance of the author. Never inferred from a price move. |
| `materiality` | 1, 2, 3 | from stated magnitudes only (amounts, shares of supply, number of users, legal severity) |
| `evidence` | verbatim phrase | must occur in the summary; checked by code |

**Roles.** Three roles on one model with one instruction (Appendix A). Reader A is the event analyst and
receives the instruction alone. Reader B is the reviewer: the same instruction plus one paragraph that makes
neutral direction and materiality 1 the default. The adjudicator receives the instruction plus one paragraph
and sees both readings. No role states a probability, a return or a rank.

**Validity.** A record is valid when its asset was requested, its fields are within the schema and its
evidence phrase occurs in the summary after whitespace and case are normalised. A `not_about` record needs no
evidence and is stored with fixed neutral fields. The first record of an asset counts and records for assets
that were not requested are ignored. Assets without a valid record are read once more with one added line
(Appendix A). A second failure leaves the reading missing. The limit of 12 words on the evidence phrase is an
instruction and is not enforced by code.

**Agreement.** Code compares the two readings of every asset. They agree when relevance is equal and either
both are `not_about`, or class, status and direction are equal and materiality differs by at most one. The
agreed record takes the fields of reader A with the lower of the two materiality values. A missing reading is
a disagreement.

**Adjudication.** When a document has disputed assets with at least one valid reading, the adjudicator
receives the summary and, for those assets only, both readings with their evidence, labelled reader 1 and
reader 2. Which reader is shown first is fixed per document by the parity of the SHA-256 of the document id.
The record of the adjudicator is final and is validated like a reading, with one re-read. A disputed asset
with no valid reading at all, or without a valid record of the adjudicator, is `unresolved`: it enters no
feature and is counted.

This is the debate and the consensus of the configuration: two independent readings, an agreement rule in
code and a third agent that decides the disputed records. It is about what the text says, not about what the
price will do.

**Model.** `deepseek/deepseek-v4.1-flash` through OpenRouter, providers Baidu and DeepInfra only,
quantisation fp8, reasoning disabled, temperature 0, at most 1,500 output tokens, strict JSON schema. This is
the route used for the typing. The model was released in September 2026. The role is extraction, so recall of
later prices has a narrow path into the output (§6).

**Cache.** Every call is stored under the hash of model, system prompt and user prompt in an append-only
file (`data/reader/calls.jsonl`). The record table is rebuilt from that file alone, so an interrupted
extraction resumes without paying twice and the registered run can verify the record table against the calls.

### 3.3 Asset-week features (code, no model call)

Code: `tradingagents/reader/features.py`. With `age = decision − event_ts`, "last 7 days" means `age < 7 d`
and "days 8 to 30" means `7 d ≤ age ≤ 30 d`. Block A counts every linked document observable at the decision
(`as_of_ts ≤ decision`), typed or not, with no cap. Block B uses the records of the reading set of §3.2 that
are resolved (agreed or adjudicated) and have relevance `subject`. Event features use items of type `event`
and remove near-duplicates: within an asset-week, records equal on class, status, direction and 7-day age
bucket count once with their highest materiality. The sign of a direction is +1 for favourable, −1 for
unfavourable and 0 for mixed and neutral.

| Block | Feature | Definition |
|---|---|---|
| A (typing only) | `attn_7d` | log(1 + distinct linked documents of the last 7 days) |
| A | `attn_abn` | `attn_7d` minus the mean of the same quantity over the 8 preceding 7-day windows of the asset, all counted from what is observable at this decision. A window counts only when it starts on or after 2022-01-01; with fewer than 4 such windows the value is missing and the asset takes the neutral rank (first available at the decision of 2022-02-05). |
| B (reader) | `tone_7d` | sum of sign × materiality over events of the last 7 days |
| B | `tone_30d` | the same over days 8 to 30 |
| B | `unfav_7d` | sum of materiality over unfavourable events of the last 7 days |
| B | `sched_fwd` | sum of sign × materiality over events with status scheduled, last 30 days |
| B | `stance_7d` | sum of the direction sign over opinion items (type `analysis_opinion`) of the last 7 days, no removal of duplicates |
| B | `supply_30d` | materiality of supply increases minus materiality of supply reductions over records of both types, last 30 days, near-duplicates removed |

Eight features. Each is turned into a within-week percentile rank minus 0.5 over the 50 universe members
(ties share the average rank, a missing value takes 0). An asset without records has zero in every block-B
feature and shares the tied rank of zero activity. The list is fixed here and is not revised after any
outcome is opened.

Class-only variant (descriptive, §5): `tone_7d_c`, `tone_30d_c`, `unfav_7d_c` and `sched_fwd_c` replace the
direction of the reader by a fixed sign per event class, with duplicates removed on class, status and bucket.
`supply_30d` is the same in both variants. Reader judgement enters the variant through relevance, class,
status and materiality only.

| Sign | Classes |
|---|---|
| −1 | security_incident, legal_regulatory, exchange_delisting, token_supply_increase, distress_or_outage |
| +1 | exchange_listing, token_supply_reduction, protocol_upgrade_or_launch, partnership_or_integration, adoption_or_product, funding_or_treasury |
| 0 | governance_or_team, market_wide_or_macro, opinion_or_forecast, other |

Counts reported with the features and used in no model: `n_subject_7d`, `n_subject_30d`, `n_unresolved_30d`.

### 3.4 Forecaster

Code: `tradingagents/reader/model.py`, `charter2.py`. The primary forecaster is the model family of the
existing quant forecast (`tradingagents/dossier/quant_forecast.py`): ridge regression without intercept of the
within-week return rank on the ranked features, penalty 10, refitted every Friday on the earlier Fridays whose
7-day outcome is realised by the decision time, burn-in 52 weeks. Text features start on 2022-01-07, so the
first forecast is for 2023-01-06 and the test window is 104 weeks.

| Score | Model | Features | Role |
|---|---|---|---|
| `s_text` | ridge | the 8 text features | gate score (§5) |
| `s_full` | ridge | 12 quant features and 8 text features | descriptive |
| `s_quant` | ridge | 12 quant features on the same training weeks (the twin) | descriptive |
| `s_block_a`, `s_block_b` | ridge | block A alone, block B alone | descriptive |
| `s_text_class` | ridge | block A and the class-only variant of block B | descriptive |
| `g_text`, `g_full`, `g_quant` | boosted trees | as the ridge scores of the same name | descriptive |
| `cf_text`, `cf_full`, `cf_quant` | ridge, blocked cross-fit | as above | descriptive, all 156 weeks |
| `p_quant` | existing quant forecast | the 12 quant features, walk-forward on the cards from 2021-01-01 (`data/dossier/quant_forecasts.parquet`) | comparison score of the gate |

- `p_quant` is the registered forecast of Charters 1 and 1b and is not refitted. `s_quant` is its twin on the
  panel weeks of this charter, so that `s_full` and `s_quant` differ only by the text features.
- Boosted trees (decision 4 of §10): LightGBM, same walk-forward as the ridge, parameters fixed in advance and
  not tuned on any outcome: 200 rounds, learning rate 0.03, 4 leaves, depth 2, at least 100 rows per leaf,
  feature and row sampling 0.8, L2 penalty 10, fixed seed, one thread, deterministic mode. No gate depends on
  them. Tree ensembles were retired in the honest rebuild of July 2026; the columns show whether that holds
  here and cannot change the verdict.
- Blocked cross-fit: 6 blocks of consecutive weeks, each forecast from the weeks outside it with one week
  left out on both sides. It uses later data and is descriptive only.
- The gate score is fitted without a guard. A failure of any other fit leaves its column empty, is recorded
  in the output and cannot change the verdict.

Why the gate stays on the ridge: the panel is 50 assets by at most 156 weeks, and realistic effects are a rank
correlation of a few hundredths. At that signal level every extra free parameter costs more in estimation
noise than it can return.

### 3.5 Decision

The rule-based long-short book of Charter 1b (`rule_weights`) applied to the within-week ranks of five scores
(`s_full`, `s_quant`, `p_quant`, `g_full`, `s_text`), with the cost and funding accounting of Charter 1b. The
books are descriptive (§5).

## 4. Stages

| Stage | Content | Cost | Opens outcomes |
|---|---|---|---|
| R0 | Reading list, reader, feature, model and evaluation code, tests, synthetic dry run, noise pass rate of the gate | 0 | no |
| R1 | Extraction pilot on 300 units | about $0.04 | no |
| R2 | Freeze of this document (needs approval) | 0 | no |
| R3a | Full extraction into the call cache and the record table | §8 | no |
| R3b | Registration, pre-flight, registered run with the single outcome join and the verdict | 0 | yes, once |

**R0 (complete).** The code of §7 with 102 offline tests, a dry run of the whole registered run on synthetic
inputs, and the pass rate of the gates on noise (Appendix B).

**R1 pilot.** `scripts/reader_extract.py --pilot 300` reads a simple random sample of 300 units of the work
list (seed 20261112: 339 records, 162 news and 138 community documents, 151 events and 149 opinions) with both
readers and the adjudicator. Reported: validity of the readings, evidence grounding, agreement by field,
adjudication rate, providers, latency, cost per unit and the projection for the whole list.
- Stop rule: evidence grounding below 0.95 or agreement on direction below 0.70 sends the instruction back
  once. A second failure stops the charter before the freeze.
- Evidence grounding: of the well-formed first-read records of readers A and B that need an evidence phrase
  (every record except a clean `not_about`), the share whose phrase occurs in the summary.
- Agreement on direction: the share of equal direction over the records for which both readings are valid
  and neither is `not_about`.
- The pilot reads no outcome and its report holds none. A revision of the instruction after a failed pilot
  may use extraction quality only. The calls of a passed pilot stay in the cache and are reused by the full
  extraction.

**R2 freeze.** The draft mark in the title is removed, the status line is changed and the document is
committed. From then on it stays byte-identical: the extraction manifest records its hash and the registered
run requires the same hash. Results of the extraction are recorded in `research/multiagent-v2/STATE.md`.

**R3a extraction.** `scripts/reader_extract.py --cost-cap 10.00`, after the freeze (the script refuses a
draft). The spend limit is cumulative over every call in the cache, the pilot included.
- 16 workers. A unit whose call fails is tried again in up to three passes. 50 failed units in a row stop
  the run.
- A stopped or incomplete run writes no record table and resumes from the cache. Units whose call keeps
  failing are written as unresolved only through an explicit `--accept-missing N`, and they are listed in the
  manifest.
- Outputs: `data/reader/records.parquet` and `data/reader/extraction_manifest.json` (hash of this document,
  prompt hash, model pin, universe, quality report, hashes of the cache, the inputs, the record table and the
  extraction source files, commit).
- The extraction reads no outcome.

**R3b registered run.** `scripts/reader_charter2_register.py` writes the registration
(`research/llm-v2-charter2-<date>/gates.json`, experiment `llm-v2c2-reader-dev-run-<date>`) with the hashes of
this document, of 37 source files and of the inputs: items, typed documents, cards, call cache, record table,
extraction manifest, quant forecast, identification flags, kline digest and funding digest.
`scripts/reader_charter2_run.py` then runs in this order.
1. Before the claim: the manifest is checked against the registration, the records are rebuilt from the
   registered cache and must equal the record table, the features are built, the kline and funding stores are
   verified, and the whole evaluation is rehearsed on synthetic outcomes. `--preflight-only` stops here.
2. The claim (attempt 3 of 6).
3. The same preparation through the registered inputs, then the forward returns as the single outcome join.
4. Evaluation and the six outputs: `forecasts.json`, `evaluation.json`, `portfolio.json`, `books.json`,
   `reader.json`, `verdict.json`. The run makes no model call.

The verdict is the one in `verdict.json`. No re-run, no re-estimation and no change of estimator on this
window under this charter.

Block A features exist after R0 at no cost. They are not evaluated on their own before the freeze: opening
them first would condition the design of block B on an outcome of the same window.

### 4.1 Pilot result (R1)

Not run at the time of this revision.

## 5. Gates

One primary statistic and one stability condition. Charter 1b required three gates jointly, which the system
review judged close to unreachable at this sample size.

- **G1 (primary).** The encompassing regression of Charter 1b, same controls, same estimator. In every test
  week with at least 15 complete rows: OLS with intercept of the residualised return rank on the residualised
  ranks of `p_quant` and of `s_text`. A residualised rank is the within-week percentile rank minus its fit on
  the percentile ranks of `vol_ewma20`, `ret_4w` and `dvol_30d`. Statistic: Newey-West t (lag 4) of the mean
  weekly `s_text` coefficient. Rule: t at least 2.0 and mean coefficient positive.
- **G2 (stability).** The mean weekly `s_text` coefficient is positive in 2023 and in 2024 (calendar year of
  the Friday).
- **Verdict.** PASS when G1 and G2 hold. Otherwise FAIL. A statistic that cannot be computed fails its gate.

Descriptive, no gate (`evaluation.json`, `portfolio.json`, `reader.json`):
- IC of every score of §3.4 on the test weeks, and of the cross-fit scores on all 156 weeks.
- Paired weekly IC differences: `s_full − s_quant`, `g_full − g_quant`, `cf_full − cf_quant`,
  `s_full − p_quant`, `g_full − s_full`.
- The regression of G1 for other pairs. Next to `p_quant`: `s_full`, `s_block_a`, `s_block_b`,
  `s_text_class`, `g_text`, `g_full`, `cf_text`. Next to the twin: `s_text` with `s_quant`, `g_text` with
  `g_quant`.
- Ridge coefficient paths, gain shares of the boosted trees, feature coverage.
- Reader quality: validity of the readings, agreement by field, shares of agreed, adjudicated and unresolved
  records, distributions of the final fields.
- The identified-asset subsets of Charter 1b for `s_text` and `s_full`.
- The books of §3.5.
An error in a descriptive part is listed in `verdict.json` and cannot change the verdict.

What each verdict licenses:
- PASS on the development window is not a claim. It licenses building the text of Sealed-A and Sealed-B and
  one confirmation run there under a further charter.
- FAIL closes the reader configuration for weekly relative returns. The records stay as the input of the
  target-change charter (§9).

Power. With 104 test weeks and a weekly coefficient dispersion like that of Charter 1b, G1 has 80 % power
for a text score whose own rank correlation with returns is about 0.045. A true value of 0.02 passes in
roughly one run out of five. Pooling the two sealed windows later adds about 100 weeks.

Pass rate on noise. On synthetic panels of the registered shape in which the outcome is independent of the
text features, the two gates pass together in 88 of 2,700 draws (95 % interval 2.6 % to 3.9 %,
Appendix B). The nominal one-sided rate of t ≥ 2.0 is 2.3 %. The excess comes from the Newey-West t on 104
weeks, whose 97.5 % quantile under noise is 2.13 and not 1.96. G2 removes almost nothing once G1
holds. The threshold stays at 2.0 for comparability with Charter 1b, and a PASS is read with a false-pass
rate of about 3.3 % in mind. This is one more reason why a PASS only licenses the sealed run.

## 6. Leakage and exposure

- 66 of the 104 test weeks (2023-09-29 → 2024-12-27) were opened by Charter 1b for a different configuration.
  No feature, threshold or prompt in this document was chosen from those outputs, but the window is no longer
  blind in the strict sense. The remaining 38 weeks were opened only for the quant forecast.
- The reader sees a de-identified summary. Re-identification of a famous episode remains possible and could
  colour `direction` or `materiality` with hindsight. Controls: evidence must be verbatim; magnitudes come from
  the text; the class-only variant uses no reader judgement of direction; the fitted model learns signs only
  from earlier weeks.
- Persistent features. Attention and tone are persistent within an asset, so a text score can partly act as
  an asset identifier and pick up a return difference between assets that lasted through the window. The
  noise panels of Appendix B do not contain such differences. Read with a PASS: block A alone against block B
  alone, the class-only variant, the coefficient paths and the two years of G2. The sealed windows decide.
- The quant forecast and the fitted model use realised returns of earlier weeks only. The cross-fit columns
  use later weeks and are labelled descriptive.
- The pilot and the extraction read no outcome. The registered run rehearses on synthetic outcomes before
  the claim and joins the real forward returns once, after the claim.
- Sealed-B stays the arbiter for any memorisation concern. V4.1-Flash was released in September 2026, so its
  post-release part is short; this is acceptable for an extraction role and would not be for a forecasting
  role.

## 7. What is fixed and what is reused

Reused without change: text store, entity dictionary, anonymiser, typing cache (99,166 items, $12.90 already
paid), cards, quant forecast, forward returns, funding, evaluation code (`agents_v2/evaluate.py`), book code
(`agents_v2/portfolio_eval.py`), pinned client (`dossier/or_client.py`), run lifecycle
(`tradingagents.research`).

New under this charter:

| File | Content |
|---|---|
| `tradingagents/reader/items.py`, `scripts/reader_items_build.py` | reading list |
| `tradingagents/reader/reading.py` | reading sets, work list, units |
| `tradingagents/reader/schema.py` | record, JSON schema, instructions, prompt hash |
| `tradingagents/reader/extract.py` | call cache, validity, re-read |
| `tradingagents/reader/consensus.py` | agreement, adjudication, record table, quality report |
| `tradingagents/reader/features.py` | asset-week features |
| `tradingagents/reader/model.py` | ridge, boosted trees, walk-forward, cross-fit |
| `tradingagents/reader/charter2.py` | panel, gates, descriptive statistics, books, verdict |
| `scripts/reader_extract.py` | pilot and full extraction |
| `scripts/reader_charter2_register.py`, `scripts/reader_charter2_run.py` | registration and registered run |
| `scripts/reader_charter2_null_gate.py` | noise pass rate of the gates (not part of the run) |
| `tests/research/test_reader_items.py`, `test_reader_extract.py`, `test_reader_charter2.py` | tests |

Fixed by the freeze and pinned by the registration: this document, the instructions (prompt hash in
Appendix A), the model pin, the source files, the gates of §5 and every constant quoted in §3 and §4.

## 8. Budget

Decision 2 of §10: the available balance may be spent and is topped up if needed.

| Item | Basis | Estimate |
|---|---|---|
| R1 pilot | 300 documents, two readers, adjudication | $0.04 |
| R3a extraction, two readers | 48,261 documents, about 72.6 M tokens in and 8.4 M out at $0.05 / $0.20 per million | $5.3 |
| R3a extraction, adjudication | 20 %, 35 % or 50 % of documents | $0.6, $1.1 or $1.5 |
| R3a total | | $5.9 to $6.8 |
| Features, model, evaluation, registered run | local, no call | 0 |
| **Cap of this charter** | account balance | **$10.61** |

- Planned spend limit of the extraction: `--cost-cap 10.00`, cumulative with the pilot.
- Token counts are estimates (instruction of about 650 tokens per call, 4 characters per token, 70 output
  tokens per record). The pilot measures the unit cost (§4.1). A projection above $10.00 holds the freeze for
  a top-up.
- The cap of Charters 1 and 1b ($140, recorded $139.62) is closed; this charter carries its own cap.
- Confirmation on the sealed windows is outside this charter and only follows a PASS: Wayback news fetch for
  2025 and 2026 (free, about a week at the polite request rate), cards rebuilt to December 2026, typing about
  $8, extraction about $4. A top-up of about $10 would be needed at that point.
- Calendar: the last Sealed-B outcome (decision 2026-12-11) closes on 2026-12-18, three days before the
  planned results freeze of 2026-12-21.

## 9. Order of the four changes

| # | Change | Status of prior evidence | Planned as |
|---|---|---|---|
| 1 | Language model reads, fitted model forecasts | Never tested for forecast value | This charter |
| 2 | Different target (next-week volatility or tail risk from the same records) | Untried | Charter 3. No new LLM cost. Literature support is stronger for volatility than for returns. |
| 3 | Fresher information (decision close to the news, not once a week) | Earlier no-go at minute scale | Charter 4. Needs an audit of capture times first: the median gap between publication and capture is 0.5 days and prices are daily bars. Feasible at a daily horizon only. |
| 4 | Agents compare assets directly | Tested on numeric cards (t 1.01 on 222 weeks) | Last. Only the text-based variant is new. |

Four attempts remain in the family and each change consumes one.

## 10. Decisions and changes since the first draft

Decisions on the five open points of the first draft (2026-11-12):

| # | Point | Decision |
|---|---|---|
| 1 | Order of the pipeline. The assignment text reads "prediction model → multi-agent debate → consensus decisions". Here the agents debate what the text says and the fitted model decides. | Accepted. The thesis presents Charter 1b as the literal configuration and this one as the corrected one. |
| 2 | Budget | The available balance ($10.61) may be spent; a top-up follows if needed (§8). |
| 3 | Attempt accounting | Attempt 3 of 6 in the family `llm-multiagent-v2`. |
| 4 | Forecaster class | Ridge stays the gate model. Boosted trees are added as descriptive columns with no gate (§3.4). |
| 5 | Community text in block B | The 25-newest rule is kept. Typing every primary community post (192,848 further posts, about $25) is not done. |

Changes since the first draft, none of them made with an outcome in view:
- The agreement rule includes relevance, and a missing reading is a disagreement (§3.2).
- Only records with relevance `subject` enter block B, and unresolved records enter nothing (§3.3).
- The windows, the duplicate rule and the own-history rule of `attn_abn` are stated exactly (§3.3).
- The instruction carries one-line class definitions and the rule for `not_about` (Appendix A).
- R3 is split into the extraction (R3a) and the call-free registered run (R3b), with this document frozen
  before the extraction (§4).
- The descriptive list follows the code (§5), with the boosted-tree and class-only columns.
- The work-list figures are those of the registered universe (§3.1), and the cost estimate follows the final
  instruction length (§8).
- The pass rate of the gates on noise is measured and stated (§5, Appendix B).
- The family line named Charter 0 by mistake; the two attempts used are Charter 1 and Charter 1b.

## Appendix A. Instructions (fixed at the freeze)

Prompt hash (`schema.prompt_sha256()`, over the instruction, the two role paragraphs, the re-read line, the
JSON schema and the labels): `7cf96c2fa147208c2e22e9efb7439caa3e216ba066f382e161c26de26721a07f`.

System prompt of reader A:

```
You read one de-identified summary of a crypto-market news item or community post and record what it states.
Names are replaced by role tokens (Asset_K, Exchange_1, Person_2, Regulator_1, Network_3) or by [entity], and dates are relative. Never guess a real name. Never predict a price. Record only what the text states.

Return exactly one record for every asset listed under "Assets", with "asset" set to the listed token:
- relevance: subject (the item is mainly about this asset), side_mention (the asset appears, the item is mainly about something else), or not_about (the item states nothing about this asset).
- event_class: the one class that fits best.
  security_incident: hack, exploit, theft, vulnerability.
  legal_regulatory: lawsuit, enforcement, ruling, licence, regulation.
  exchange_listing: a venue lists the asset or adds a market for it.
  exchange_delisting: a venue delists the asset or suspends its trading.
  token_supply_increase: unlock, emission, mint, sale by insiders or by a treasury.
  token_supply_reduction: burn, buyback, lock-up.
  protocol_upgrade_or_launch: upgrade, fork, mainnet or product release by the project itself.
  partnership_or_integration: a named cooperation or a technical integration.
  adoption_or_product: usage, users, institutional adoption, a product of others built on the asset.
  distress_or_outage: insolvency, halt, outage, loss of a peg, withdrawal freeze.
  governance_or_team: vote, proposal, change of leadership or team.
  funding_or_treasury: fund raise, grant, treasury decision.
  market_wide_or_macro: a fact about the whole market or the economy, not about this asset in particular.
  opinion_or_forecast: a view, outlook or price forecast without a new fact.
  other: none of the above.
- status: occurred, scheduled (announced with a date or a firm plan), or proposed_or_rumoured.
- direction: what the stated fact means for a holder of this asset: favourable, unfavourable, mixed or neutral. For an opinion item: the stance of the author on the asset. A reported price move alone is neutral.
- materiality: 1 routine; 2 notable, the text states a magnitude that matters for this asset; 3 major, the text states a loss of a large share of funds, an enforcement action against the issuer, a listing or delisting on a leading venue, or a supply change above one tenth.
- evidence: at most 12 consecutive words copied exactly from the summary that support class and direction.

When relevance is not_about, set event_class other, status occurred, direction neutral, materiality 1 and an empty evidence.
```

Reader B receives the same text followed by this paragraph:

```
You are the reviewer. Start from direction neutral and materiality 1. Leave that default only where the text states a concrete fact that requires it.
```

The adjudicator receives the instruction followed by this paragraph:

```
You are the adjudicator. Two readers recorded the assets below and their records differ. Both records are shown. Issue the final record for every listed asset from the text alone. A reader may be right, or neither.
```

Line added to the user prompt on the single re-read:

```
The evidence of the earlier answer was not found in the summary. Copy the evidence word for word from the summary.
```

User prompt of a reader (the adjudicator sees, under each asset, the two readings as JSON or "no valid
record"):

```
Item type: event | opinion or analysis
Source: news | community post
Summary: <de-identified summary>
Assets:
- Asset_K
- Filed_asset (the item is filed under this asset; the summary describes it without a token)
```

## Appendix B. Pass rate of the gates on noise

`scripts/reader_charter2_null_gate.py`. Each draw builds a synthetic panel of the registered shape (156 weeks,
50 assets, the 8 text features as noise that is zero in half of the asset-weeks, an outcome that is
independent of the text features), fits `s_text` by the registered walk-forward ridge and applies the
registered gates on the 104 test weeks. No real outcome is involved. Draws:
`research/multiagent-v2/charter2_null_gate.jsonl` and
`research/multiagent-v2/charter2_null_gate_persistent.jsonl`.

| Variant | Seeds | Draws | Both gates pass | Pass rate (95 % interval) | G1 alone | t mean | t sd | t 95 % | t 97.5 % | t 99 % |
|---|---|---|---|---|---|---|---|---|---|---|
| Independent features | 0–399, 1000–1399, 2000–2399, 3000–4499 | 2,700 | 88 | 3.26 % (2.6 to 3.9) | 89 | 0.019 | 1.052 | 1.78 | 2.13 | 2.56 |
| Persistent features (0.9) | 5000–5899 | 900 | 29 | 3.22 % (2.1 to 4.4) | 30 | −0.040 | 1.077 | 1.81 | 2.19 | 2.82 |

Passes by block of seeds, independent features: 15 of 400, 4 of 400, 19 of 400, 22 of 500, 14 of 500, 14 of 500. The first check of this rate used 400 draws and gave 1.0 %, which was a favourable sample.

The persistent variant redraws the text features as stationary AR(1) series within each asset
(coefficient 0.9 from week to week, no zero mass) and keeps the outcome independent. It shows whether persistence of the
features alone changes the pass rate. It does not contain lasting return differences between assets (§6).
