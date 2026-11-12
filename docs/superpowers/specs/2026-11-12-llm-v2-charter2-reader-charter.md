# Charter 2 — Reader configuration (`llm-v2-charter2`) — DRAFT, NOT FROZEN

**Status:** DRAFT 2026-11-12. Nothing is registered, no call has been paid for and no outcome has been joined
under this document. The open decisions are listed in §10.
**Family:** `llm-multiagent-v2`, attempts used 2 of 6 (Charter 0 FAIL, Charter 1b FAIL). This would be attempt 3.
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
within the universe. Windows: development 2022-01-07 → 2024-12-27 (156 weeks), Sealed-A 2025-01 → 2026-04,
Sealed-B 2026-05 → 2026-12-11. Both sealed windows are untouched and their text is not built.

Question: do facts read from anonymised news and community text by language-model agents carry information
about next-week relative returns beyond the quant forecast, when a fitted model and not the language model
maps them to a forecast?

## 3. Design

```
text store ──► typing (done, cached) ──► reading list ──► reader agents ──► consensus records
                                                                                   │
numeric card ──► quant features ───────────────────────────────┐                  ▼
                                                                └──► fitted model ◄── asset-week text features
                                                                          │
                                                                          ▼
                                                              ranks ──► rule-based book
```

### 3.1 Reading list (built, no cost)

`tradingagents/reader/items.py`, `scripts/reader_items_build.py`. One row per (document, linked asset) for
every row of the text store from 2021-12 to 2024-12, joined to the cached typing. The dossier of Charter 1b
showed at most 25 items per asset-week and that cap was binding in 26 % of asset-weeks (nearly every week for
the largest assets). The reading list has no cap. An item is admissible for a decision when its `as_of_ts` is
not later than the decision time.

Facts of the built table (`scripts/reader_coverage_preview.py`, no outcome involved). "Readable" means a typed
event or opinion item that yields a record for the asset under §3.2.

| Quantity | Value |
|---|---|
| Item rows (document × linked asset), 2021-12 → 2024-12 | 520,434 over 353,739 documents (news 54,258, community 299,481) |
| Typed documents | 101,099 (event 37,486, opinion 30,554, other types 33,059); name leaks after de-identification: 0 |
| Asset-weeks (7,800) with any linked item in the last 7 days | 78.2 % (median 6 items, 90th percentile 61) |
| Asset-weeks with a readable item in the last 7 days | 55.4 % (median 1, mean 7.1, 90th percentile 16) |
| Asset-weeks with a readable item in the last 30 days | 76.8 % (median 5) |
| Assets per week with a readable item in the last 7 days | 16 to 39 of 50, median 28 |
| Reader work list | 50,362 documents (news 26,476, community 23,886), 58,958 (document, asset) records |
| Records read for the filed asset (summary without an asset token) | 10,117 |
| Consistency with the dossier build | 96,431 of 96,433 community posts selected by the 25-newest rule are typed |

Text is sparse. In 45 % of asset-weeks block B has nothing from the last 7 days and the asset sits at the
neutral rank. This limits power and is part of the power statement in §5.

### 3.2 Reader agents and consensus

Unit: one typed document of type `event` or `analysis_opinion`, in its de-identified summary of at most two
sentences (role tokens, rounded magnitudes, relative dates, no names). Price recaps, promotional and unrelated
items are excluded upstream. The agents see no price series, no return, no date and no quant forecast.

Reading set of an asset at a decision (the rule under which the typing was bought, so every member is typed):
all news items of the last 30 days linked to the asset, and the 25 most recent community posts of the last 30
days in which the asset is the primary subject.

Two readers work independently on every unit and fill one record per asset: for each asset token that occurs
in the summary and, when the summary names no asset token, for the single asset the item is filed under as
primary subject (the reader is told that the summary describes this asset without its token).

| Field | Values | Rule |
|---|---|---|
| `relevance` | subject, side_mention, not_about | whether the item is about this asset |
| `event_class` | security_incident, legal_regulatory, exchange_listing, exchange_delisting, token_supply_increase, token_supply_reduction, protocol_upgrade_or_launch, partnership_or_integration, adoption_or_product, distress_or_outage, governance_or_team, funding_or_treasury, market_wide_or_macro, opinion_or_forecast, other | one class |
| `status` | occurred, scheduled, proposed_or_rumoured | from the wording |
| `direction` | favourable, unfavourable, mixed, neutral | for a holder of the asset, from what the item states. For an opinion item: the author's stance. Never inferred from a price move. |
| `materiality` | 1, 2, 3 | from stated magnitudes only (amounts, shares of supply, number of users, legal severity) |
| `evidence` | verbatim phrase | must occur in the summary; checked by code |

- Reader A is instructed as an event analyst. Reader B is instructed as a reviewer who defaults to neutral
  and materiality 1 unless the text states otherwise.
- Code compares the two records. They agree when class, status and direction are equal and materiality differs
  by at most one (the lower value is kept).
- On disagreement an adjudicator receives the item and both records with their evidence and issues the final
  record. This is the debate and the consensus of the configuration: it is about what the text says, not about
  what the price will do.
- A record whose evidence phrase is absent from the summary is rejected and the unit is re-read once.

Model: DeepSeek V4.1-Flash, fp8, reasoning disabled, temperature 0, strict JSON schema, pinned providers, the
route used for the typing. It was released in September 2026. The role is extraction, so recall of later
prices has a narrow path into the output (§6).

### 3.3 Asset-week features (code, no model call)

Block A counts every linked item admissible at the decision time, typed or not, with no cap. Block B uses
the consensus records of the reading set of §3.2. Each feature is turned into a cross-sectional rank minus 0.5
within the week; an asset without items gets the rank of zero activity.

| Block | Feature | Definition |
|---|---|---|
| A (typing only) | `attn_7d` | log(1 + linked documents in the last 7 days) |
| A | `attn_abn` | `attn_7d` minus the asset's own mean of `attn_7d` over the previous 8 weeks |
| B (reader) | `tone_7d` | sum of sign(direction) × materiality over subject events of the last 7 days, near-duplicates removed |
| B | `tone_30d` | the same over days 8 to 30 |
| B | `unfav_7d` | sum of materiality over unfavourable subject events of the last 7 days |
| B | `sched_fwd` | sum of sign × materiality over subject events with status scheduled, last 30 days |
| B | `stance_7d` | favourable minus unfavourable opinion items of the last 7 days |
| B | `supply_30d` | materiality of supply increases minus supply reductions, last 30 days |

Eight features. The list is fixed here and is not revised after any outcome is opened.

### 3.4 Forecaster

The same model family as the existing quant forecast (`tradingagents/dossier/quant_forecast.py`): ridge
regression of the next-week return rank on cross-sectionally ranked features, refitted every Friday on all
earlier Fridays whose 7-day outcome is realised before the decision.

- `s_text`: ridge on the eight text features alone.
- `s_full`: ridge on the twelve quant features and the eight text features together.
- `s_quant`: ridge on the twelve quant features on the same training weeks (the twin).
- Ridge penalty 10 and the 52-week burn-in are the constants of the quant forecast. Text features start on
  2022-01-07, so the first forecast is for 2023-01-06 and the test window is 104 weeks.

Why ridge and not a larger model: the panel is 50 assets by at most 156 weeks, and realistic effects are a
rank correlation of a few hundredths. At that signal level every extra free parameter costs more in
estimation noise than it can return. Tree ensembles were retired in the honest rebuild of July 2026 and
time-series foundation models were null in the prediction-lab programme (§56). A richer forecaster is a
separate question from whether the text carries information and would be chartered separately.

### 3.5 Decision

The rule-based long-short book of Charter 1b (`rule_weights`) applied to the ranks of `s_full`, with the same
cost and funding accounting. The book is descriptive (§5).

## 4. Stages before any outcome is opened

| Stage | Content | Cost | Opens outcomes |
|---|---|---|---|
| R0 | Reading list, feature code, model code, evaluation code, tests, synthetic dry run | 0 | no |
| R1 | Extraction pilot on 300 units: schema validity, evidence grounding, reader agreement by field, adjudication rate, cost per unit. Stop rule: evidence grounding below 0.95 or agreement on direction below 0.70 sends the prompt back once; a second failure stops the charter before the freeze. | about $0.05 | no |
| R2 | Freeze and registration (prompts, schema, feature code, model code, gates, hashes) | 0 | no |
| R3 | Full extraction, then feature build, then the outcome join and the verdict in one registered run | §8 | yes, once |

Block A features exist after R0 at no cost. They are not evaluated on their own before the freeze: opening
them first would condition the design of block B on an outcome of the same window.

## 5. Gates

One primary statistic and one stability condition. Charter 1b required three gates jointly, which the system
review judged close to unreachable at this sample size.

- **G1 (primary).** Weekly cross-sectional regression of the residualised return rank on the residualised
  ranks of the existing quant forecast and of `s_text` (the encompassing regression of Charter 1b, same
  controls, same code). Newey-West t (lag 4) of the mean `s_text` coefficient at least 2.0, coefficient
  positive.
- **G2 (stability).** The mean weekly `s_text` coefficient is positive in 2023 and in 2024.
- **Verdict.** PASS when G1 and G2 hold. Otherwise FAIL.

Descriptive, no gate: IC of `s_full` minus IC of `s_quant` (paired weekly difference); IC of `s_text`; block A
only and block B only; a class-only variant of block B in which direction comes from a fixed sign per event
class and not from the reader (§6); coefficient paths; reader agreement; the book of §3.5 against the same
book on `s_quant`; a blocked cross-fit over all 156 weeks; the identified-asset subsets of Charter 1b.

What each verdict licenses:
- PASS on the development window is not a claim. It licenses building the text of Sealed-A and Sealed-B and
  one confirmation run there under a further charter.
- FAIL closes the reader configuration for weekly relative returns. The records stay as the input of the
  target-change charter (§9).

Power. With 104 test weeks and a weekly coefficient dispersion like that of Charter 1b, G1 has 80 % power
for a text score whose own rank correlation with returns is about 0.045. A true value of 0.02 passes in
roughly one run out of five. Pooling the two sealed windows later adds about 100 weeks.

## 6. Leakage and exposure

- 66 of the 104 test weeks (2023-09-29 → 2024-12-27) were opened by Charter 1b for a different configuration.
  No feature, threshold or prompt in this document was chosen from those outputs, but the window is no longer
  blind in the strict sense. The remaining 38 weeks were opened only for the quant forecast.
- The reader sees a de-identified summary. Re-identification of a famous episode remains possible and could
  colour `direction` or `materiality` with hindsight. Controls: evidence must be verbatim; magnitudes come from
  the text; the class-only variant uses no reader judgement of direction; the fitted model learns signs only
  from earlier weeks.
- The quant forecast and the fitted model use realised returns of earlier weeks only.
- Sealed-B stays the arbiter for any memorisation concern. V4.1-Flash was released in September 2026, so its
  post-release part is short; this is acceptable for an extraction role and would not be for a forecasting
  role.

## 7. What is fixed and what is reused

Reused without change: text store, entity dictionary, anonymiser, typing cache (99,166 items, $12.90 already
paid), cards, quant forecast, forward returns, funding, evaluation code (`agents_v2/evaluate.py`), book code
(`agents_v2/portfolio_eval.py`), run lifecycle (`tradingagents.research`).
New: `tradingagents/reader/` (reading list, schema and prompts, consensus, features, model, charter tail) and
its tests.

## 8. Budget

| Item | Basis | Estimate |
|---|---|---|
| R1 pilot | 300 documents, two readers, adjudication | $0.05 |
| R3 extraction | 50,362 documents. One reader pass: 26.0 M tokens in, 4.1 M out at $0.05 / $0.20 per million = $2.13. Two readers plus adjudication on 20 to 50 % of documents. | $4.9 to $6.0 |
| Features, model, evaluation | local | 0 |
| **Cap proposed for this charter** | | **$7.00** |

- Account balance $10.61. The cap of Charter 1 and 1b ($140, recorded $139.62) is closed; this charter carries
  its own cap.
- Token counts are estimates (450 instruction tokens, summary length / 4, 70 output tokens per record). The
  pilot measures the unit cost. A projection above the cap holds the freeze for a decision.
- Confirmation on the sealed windows is outside this charter and only follows a PASS: Wayback news fetch for
  2025 and 2026 (free, about a week at the polite request rate), cards rebuilt to December 2026, typing about
  $8, extraction about $4. About $3.6 would be left after the development run, so a top-up of about $10 would
  be needed at that point and not before.
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

## 10. Open decisions

1. **Order of the pipeline.** The assignment text reads "prediction model → multi-agent debate → consensus
   decisions". Here the agents debate what the text says, and the fitted model decides. The thesis would
   present Charter 1b as the literal configuration and this one as the corrected one.
2. **Budget.** A cap of $7.00 from the existing balance (§8). No top-up before a PASS.
3. **Attempt accounting.** Booked as attempt 3 of 6 in the same family.
4. **Forecaster class.** Ridge as in §3.4. A boosted-tree forecaster on the same 20 features can be added as a
   descriptive column with no gate (needs one library in the environment).
5. **Community text in block B.** The 25-newest rule covers the last hours for the largest assets and up to
   30 days for quiet ones. Kept as is (no extra typing cost). The alternative, typing every primary community
   post, means 192,848 further posts (153,345 on BTC, 35,876 on ETH), about $25 for typing before any reading,
   and is not proposed.

## Appendix A. Reader instruction (draft wording, fixed at the freeze)

```
You read one de-identified summary of a crypto-market news item or community post and record what it states.
Names are replaced by role tokens (Asset_K, Exchange_1, Person_2, Regulator_1, Network_3) and dates are
relative. Never guess a real name. Never predict a price. Record only what the text states.

Return one record for every asset listed under "Assets":
- relevance: subject (the item is mainly about this asset), side_mention, or not_about.
- event_class: one of the listed classes.
- status: occurred, scheduled, or proposed_or_rumoured.
- direction: what the stated fact means for a holder of this asset: favourable, unfavourable, mixed or
  neutral. For an opinion item: the author's stance on the asset. A reported price move alone is neutral.
- materiality: 1 routine; 2 notable, the text states a magnitude that matters for this asset; 3 major, the
  text states a loss of a large share of funds, an enforcement action against the issuer, a listing or
  delisting on a leading venue, or a supply change above one tenth.
- evidence: at most 12 consecutive words copied from the summary that support class and direction.
```

Reader B receives the same text with one more paragraph: "You are the reviewer. Start from neutral and
materiality 1. Leave that default only where the text states a concrete fact that requires it."

The adjudicator receives the summary and both records and returns one record in the same schema.
