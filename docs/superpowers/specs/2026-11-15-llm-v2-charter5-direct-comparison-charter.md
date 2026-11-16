# Charter 5 — Direct comparison of assets on text, with a news archive (`llm-v2-charter5`) — DRAFT, NOT FROZEN

**Status:** draft of 2026-11-16 for the last attempt of the family. Option A of the source audit was chosen on
2026-11-15: a weekly direct comparison of assets on text, with the public news archive added in the small
scope. Stage D0 (code, tests, pass rate and power of the gate on synthetic returns) and stage D1 (a paid
pilot of typing, reading, comparison and identification probe on three seeded test weeks, no outcome) are
complete. Nothing is registered, no attempt is claimed and no dossier, comparison result or comparison score
has been joined with a return or any other price quantity dated at or after its decision. The decisions of
§10 are open. The full run needs the freeze approval and a top-up of the account (§8).
**Family:** `llm-multiagent-v2`, attempts used 5 of 6 (Charter 1 interrupted with a failed receipt, Charters
1b, 2, 3 and 4 FAIL). This charter is attempt 6, the last.
**Predecessor:** `docs/superpowers/specs/2026-11-14-llm-v2-charter4-fresh-news-charter.md`, run
`llm-v2c4-fresh-news-dev-run-20261114`, verdict FAIL.

## 1. Why a direct comparison

The assignment asks for a framework in which a prediction model and a debate of language-model agents reach a
decision together. Four changes to the first design were set out after Charter 1b and taken in order (§9).
Three have failed. In Charter 2 the agents read and a fitted model forecast: the text score reached t 1.39
against 2.0, and the relation that existed sat in the number of linked items, not in the judgements of the
reader agents. In Charter 3 the target changed to next-week volatility: t −0.72 for the reader block beyond
price history and attention. In Charter 4 the decision moved to the news, daily at 00:00 UTC: t −2.49 for the
reader tone beyond price history and attention.

In all three the agents judged one document at a time against a fixed scale, and code summed the judgements.
The fourth change gives the agents the task that a cross-sectional decision actually poses: of two assets,
which has the better outlook for the next week relative to the other? Agents see the reports of the last
seven days on both assets side by side and choose. The question is relative, as the target is, and the agents
weigh the reports of an asset against those of another, which a fixed scale cannot do. Code turns the choices
of a week into one strength per asset and the gate asks whether that strength carries information beyond the
existing quant forecast, the price controls and the attention counts.

The pairwise form was tested once before on numeric cards (`llm-c3p-pairwise`, THESIS §65) and gave an IC of
+0.0079, t 1.01, over 222 weeks. What is new here is the material: text dossiers, de-identified, with the
same alias space for both assets of a comparison.

The material audit and the source audit of 2026-11-14 found the present text thin for the small assets of the
cross-section: three outlets and three general forums. The public news archive of the CoinDesk Data feed adds
the other outlets of the feed. It raises the share of asset-days with a linked news item over seven days from
66.9 % to 76.5 %, and for the median asset other than BTC and ETH from 25.7 % to 50.0 %. The archive is added
so that a negative result cannot be put down to thin material.

The prior is negative (table below). Three charters on the same records found no information in the reader
judgements, the archive adds outlets of a lower tier with more price commentary, and the comparison model
judges a window that lies before its training cutoff, which can only raise the statistic (§6). A FAIL is the
expected outcome, and a FAIL closes the family.

### Earlier programmes that bear on this (closed-programmes ledger)

| Programme | What was tested | Outcome | Bearing here |
|---|---|---|---|
| Charter 1b, `llm-v2c1b-dev-run-20261112` | Debate of analyst agents and a judge on de-identified dossiers of numeric cards and text | FAIL, encompassing t −0.02 over 66 weeks | The debate form with a judge failed on mixed dossiers. Here the dossiers hold text only and the agents compare two assets instead of forecasting one. |
| Charter 2, `llm-v2c2-reader-dev-run-20261112` | Reader records as features of a fitted model for the weekly relative return | FAIL, t 1.39. Attention counts carried the weak relation, reader judgements none. | Same universe, test weeks, quant forecast and target. The records of the present store are reused to select the dossier lines. Attention is a control. |
| Charter 3, `llm-v2c3-volatility-dev-run-20261113` | Unsigned reader features for next-week relative volatility | FAIL, t −0.72 | The volatility target is not repeated. |
| Charter 4, `llm-v2c4-fresh-news-dev-run-20261114` | Reader tone of the last day for the next-day relative return | FAIL, t −2.49, both years negative | Fresher information did not help. The weekly decision returns. |
| `llm-c3p-pairwise` (THESIS §65) | Agents compare assets pairwise on numeric cards | IC +0.0079, t 1.01 over 222 weeks | The pairwise form itself showed no information on numeric cards. This charter changes the material to text. |
| `llm-c1-event-xs` (THESIS §63) | Typed-event extraction as cross-sectional features | Stopped before any outcome: extraction precision 0.75 below 0.80 | Extraction quality limits any text feature. The comparison sees the summaries, not the extracted fields. |
| Sentiment index as quant feature (THESIS §33) | Daily sentiment features for BTC and ETH | All 6 registered gates failed | A text signal on the two largest assets failed. BTC and ETH are a descriptive split here. |
| Material and source audits (2026-11-14) | What the agents read and what could be added | Present material thin for small assets; the archive is the best free addition; a daily comparison has too little to compare | The archive is added in the small scope; the comparison is weekly. |

## 2. Question, target, universe

**Question.** Do pairwise comparisons of the de-identified seven-day text dossiers of two assets of the same
week, made by two analyst agents and, where they disagree, an adjudicator, carry information on the
next-week return rank beyond the existing quant forecast, the price controls and the attention counts?

**Universe.** The weekly top 50 of the perpetual contracts by the card ranking of the family
(`charter2.universe`), unchanged since Charter 1. 203 assets appear in the test weeks.

**Test weeks.** The 104 Fridays from 2023-01-06 to 2024-12-27, the test weeks of Charter 2, 5,200 asset-weeks.
The decision is on Saturday 00:00 UTC after the Friday card. The store starts on 2022-01-01; the year 2022
serves only as the history of the attention counts. The archive feed went live in July 2022, and everything
published earlier is backfill (§3.1), which the test weeks do not need.

**Target.** The simple return from the Friday close to the next Friday close (`forward_returns` of the family,
the target of Charter 2), as a percentile rank within the week. A contract delisted inside the week
books its last close.

**Prediction model.** The existing quant forecast `p_quant` (`pred_rank_pct` of
`data/dossier/quant_forecasts.parquet`, the registered input of Charters 1, 1b and 2). It is not refitted.

## 3. Design

The pipeline runs from the text stores to one score per asset and week. Every step is code except the three
model calls: typing (archive documents), reading (archive documents) and comparing (dossiers). The model is
`deepseek/deepseek-v4.1-flash` through OpenRouter, routed to DeepInfra or Baidu at fp8, without reasoning,
at temperature 0, as in the reading stage of Charter 2. Every answer is cached, and every table of the run is
rebuilt from the caches by the registered runner and compared with the stored table before the claim (§4).

### 3.1 Material

**Present store** (`data/reader`). News of three outlets (CoinDesk, Cointelegraph, The Block) through the page
archive and posts of three general forums, typed and read under Charter 2: 53,330 reader records. Unchanged.

**Archive store** (`data/compare/text`). The public dump of the CoinDesk Data news feed on Hugging Face
(`maryamfakhari/crypto-news-coindesk-2020-2025`, CC-BY-NC-4.0, attribution to the dataset and the feed). One
row is an article of one outlet with a feed id, a publication time in Iran local time, a title and a short
excerpt (median 329 characters). The rows from 2022-01-01 to 2024-12-31 of the outlets that the present store
does not hold are stored as a second source `ccnews`: 184,022 documents of 67 outlets (23,533 in 2022,
42,542 in 2023, 117,947 in 2024). Left out: 14,125 rows of the three present outlets, 147 duplicate links,
14 rows without a time.

- **Time.** The publication time is converted from Iran local time (`Asia/Tehran` rules, +03:30, +04:30 in
  daylight time until 2022). For the articles also in the present store, the first percentile of the time
  from publication to the first capture is 0.00 to 0.05 hours in 24 of 36 months; in the other months the
  lowest 1 % are republished items, which err to the late side (source audit).
- **Availability.** The archive has no capture time. The feed id follows the order of ingestion, which gives
  a clock: the running maximum of the median publication time of the 50 articles ingested before an
  article. An article published at most one hour before the clock was ingested live and is observable one
  hour after its publication. Any other article was ingested late and is observable 24 hours after the clock.
  The feed went live in July 2022; everything published earlier is backfill. In the test window 3.3 % of the
  archive articles count as late (99th percentile of the delay 28.8 hours).
- **Linking.** The alias dictionary and the linking rule of the present store (`reader.items.month_rows`):
  308,502 links of archive documents to universe assets. "Primary" means the asset is named in the title or
  at least twice in the body.
- **Typing scope (small scope).** Typed and read are the archive documents with a primary link to a universe
  asset other than BTC and ETH inside the seven-day window before the decision of a test week in which that
  asset is in the universe: 32,369 documents, covering 3,049 of the 4,992 asset-weeks of the other assets.
  The largest assets of the scope are XRP (9,580), SOL (7,973), SHIB (5,961), DOGE (3,374) and ADA (3,329).
  Documents whose main subject is BTC or ETH (130,851) are not typed: they are four times the rest, and the
  present store already fills the dossiers of the two. A typed document yields reader records for every
  linked asset whose token is in its summary, so a BTC or ETH dossier can gain an archive line through a
  mention.
- **Typing and reading.** The frozen typing call of the dossier build and the frozen reader of Charter 2
  (instruction, schema, two reader agents, adjudicator, consensus by code), into caches of their own
  (`data/compare/typing_cache.jsonl`, `data/compare/calls.jsonl`). The registered caches and tables of the
  present store stay byte-identical.
- **Every link counts for attention.** The attention control counts the links of all 184,022 archive
  documents, typed or not, together with the present store (§3.5).

Known limits of the archive. The dump holds only the articles that the feed tagged BTC or ETH; an article
about a small asset alone is missing. The new outlets carry more price commentary (36.5 % of titles by a
keyword rule, against 28.8 % for the present outlets); the typing call labels such items as price recaps and
the reading rule leaves them out of the dossiers. The volume grows over the window (2024 holds 2.8 times as
many articles as 2023), so the weeks of 2024 have fuller dossiers.

### 3.2 Dossiers

One dossier per asset and week from the reports of the seven days before the decision
(`tradingagents/compare/dossier.py`):

- The reading set of a week is that of Charter 2 (`reading.reading_set`): every news row linked to a universe
  asset and every primary forum post, the newest posts up to the cap, with the event inside the window and
  observable at the decision. Present and archive rows are one table.
- A row enters the dossier of an asset when its reader record names the asset as the subject. A document
  whose summary still carries a name after de-identification is never shown.
- Reports with the same event class, status and direction count as one matter. A matter is shown once, by
  its most material and then most recent report, with the number of reports. Matters are ordered by
  materiality, number of reports and recency, at most 10 lines per dossier.
- A line reads `- [<age>; <news | community post>; <n> reports] <summary>`. The age is counted in days before
  the decision ("today", "1 day ago", "n days ago"). The reader's class, direction and materiality select and
  order the lines and are not shown: the agents compare on the text.
- All dossiers of a week share one alias space (`Asset_K`, `Exchange_1`, `Person_2`, ...), seeded by the
  week, so an entity carries the same token in both dossiers of a comparison. A dossier whose rendered text
  still carries a dictionary name is dropped and its asset counts as an asset without a dossier.
- Assets without a subject record in the week have no dossier and take no part in the comparisons.

### 3.3 Comparisons

- **Pairs.** The first 10 rounds of a round robin (circle method) on an order of the week's dossier assets
  drawn with the seed of the week: every asset meets 10 distinct opponents (9 in a week with an odd number of
  assets for those that rest once), no pair twice. A week with n dossiers gives about 5n comparisons.
- **Analyst A** sees the two dossiers in an order drawn per pair and week and answers the instruction of
  Appendix A: `first`, `second` or `no_basis`, and a reason of at most 25 words that names the deciding
  reports by token.
- **Analyst B (reviewer)** sees the opposite order and the same instruction with one added paragraph: start
  from `no_basis` and leave it only for a concrete fact that clearly favours one asset.
- **Consensus by code.** Both name the same asset: that asset wins. Both answer `no_basis`: no result.
  Otherwise the adjudicator sees the two dossiers in an order drawn per pair, the two answers with their
  reasons in a drawn order (the token of the named asset, never "first" or "second"), and decides; `no_basis`
  from the adjudicator is no result. An answer without the registered form leaves the comparison unresolved.
- **Settings.** Structured output with the schema of Appendix A, at most 200 output tokens. The reason is cut
  to 60 words before it is shown to the adjudicator.

### 3.4 Comparison score

`cmp_score` is the Bradley-Terry log strength of the asset over the decided comparisons of its week, fitted by
the minorisation-maximisation iteration of `tradingagents/xsect/pair_xs.py` with a prior of 0.5 pseudo-wins
and 0.5 pseudo-losses against a virtual opponent of unit strength. The log strengths of a week have mean
zero over the dossier assets. An asset with a dossier but no decided comparison sits near zero. An asset
without a dossier takes the neutral score 0 and the control `has_dossier` = 0.

Descriptive alternatives computed by code: `cmp_net` (wins minus losses) and `tone_code` (direction sign
times materiality of the reader records, summed over the dossier lines: what code makes of the same lines
without a comparison).

### 3.5 Gate statistic

For every test week, on the rows with a quant forecast and a forward return:

1. Percentile ranks within the week of the return, of `cmp_score` and of the seven controls
   `p_quant`, `vol_ewma20`, `ret_4w`, `dvol_30d`, `attn_7d`, `n_lines`, `has_dossier`. A missing control takes
   the rank 0.5.
   - `attn_7d`: log(1 + distinct linked documents with the event in the last seven days and observable at the
     decision), over the present store and the whole linked archive.
   - `n_lines`: lines of the asset's dossier (0 without one). `has_dossier`: 1 with a dossier, else 0.
2. The weekly coefficient is the coefficient of the rank of `cmp_score` in the OLS of the return rank on an
   intercept, that rank and the seven control ranks (computed from the two residuals, which gives the same
   number; a test checks the equality).
3. A week enters the statistic with at least 15 complete rows, at least 10 of them with a dossier, and a
   rank of the score that varies beyond the controls.

The coefficient equals the encompassing coefficient of Charter 2 when the attention controls are left
out (a test checks this to 1e-10). There is no fitted model and no burn-in: every test week counts.

### 3.6 Identification probe

Every dossier goes once to the comparison model with the instruction of Appendix A: name the real asset
from the list of the 203 tickers of the test universe and the calendar month of the reports. The flag
`identified` (the ticker is right) splits a descriptive panel; `month_within_6` (the month within six months)
is reported. The flag changes no score and no gate.

## 4. Stages

| Stage | Content | Model calls | Outcome |
|---|---|---|---|
| D0 | Archive store, linking, typing scope, dossiers, comparison, score, gate, drivers, registration and runner, tests; pass rate and power of the gate on synthetic returns (Appendix B) | none | none |
| D1 | Pilot on three seeded test weeks under a stop rule fixed before it ran (§4.1) | $0.20 | none |
| D2 | Freeze: this document loses the draft mark, the decisions of §10 are recorded, the code is committed | none | none |
| D3a | Full typing, linking, reading, dossiers, comparisons and probe on the 104 test weeks | about $7.6 (§8) | none |
| D3b | Digest of the archive store, registration, pre-flight with rehearsal, claim, the single outcome join, verdict | none | once |

- Every driver refuses a run on all test weeks while this document carries the draft mark; before the freeze
  only the pilot weeks run.
- Every paid driver has a spend cap over its whole cache, resumes from the cache after an interruption and
  writes its full table only when nothing is missing. A failing provider stops a driver after 50 failures in
  a row.
- D3a commands, in order: `cmp_type.py --cap 4.00`, `cmp_items_build.py`, `cmp_read.py --cap 3.00`,
  `cmp_dossiers.py`, `cmp_duels.py --cap 3.00`, `cmp_probe.py --cap 0.30`. No outcome is read in D3a.
- D3b: `cmp_charter5_register.py --check`, the commit of the tables' digest and of the registration
  (`research/llm-v2-charter5-<date>/gates.json`, parent `llm-v2c4-fresh-news-dev-run-20261114`), then
  `cmp_charter5_run.py --preflight-only` and the run. Before the claim the runner checks the bytes of every
  registered input, rebuilds the present records from the Charter 2 cache, the archive link tables from the
  store and the typing cache, the archive records, the dossiers, the comparison results and scores and the
  identification flags from their caches, compares each with its registered table, and runs the whole
  evaluation on synthetic returns. A defect found there stops the process without consuming the attempt.
  A test runs the whole runner on a synthetic checkout, including these refusals, the claim and the join.
  After the claim the forward returns are joined once and the verdict is written by code.
- From the freeze commit the document stays byte-identical. Results go into `research/multiagent-v2/STATE.md`.

### 4.1 Pilot (D1)

The pilot ran on 2026-11-16 under the grant "spend what is available and I will top up if needed" given for
Charter 2, within a cap of $0.50 for all four steps. The weeks were drawn with seed 20261115 from the test
weeks: 2023-01-27, 2023-09-29 and 2024-03-01. No return was read. The stop rule was fixed in the code before
the pilot: the comparison stage passes when the share of analyst A's asset answers that name the asset shown
first lies in 0.40 to 0.60, when both analysts name the same asset in at least 70 % of the comparisons in
which both name one, and when at least 30 % of the comparisons are decided; the dossiers must carry no name;
the projected cost of the full run must fit the budget. At most one revision of the comparison instruction
with a rerun on other weeks was allowed. None was needed.

| Step | Measured |
|---|---|
| Typing | 790 scope documents, 6 too short, 784 typed, no failure. $0.075, $0.096 per 1,000 documents. |
| Reading | 327 documents read for 559 asset rows, 776 calls, none missing. Agreement of the two readers: relevance 0.97, event class 0.94, direction 0.83. 24 % of the rows adjudicated, 0.2 % unresolved. Evidence quoted verbatim in 98 % of the readings. $0.055. |
| Dossiers | 93 of 150 universe rows have a dossier, against 83 from the present store alone. 55 dossiers carry an archive line. 28 to 36 dossiers per week. Median 3 lines, median 741 characters. No dossier dropped for a name, no leaky row. |
| Comparisons | 460 comparisons, 1,066 calls, none invalid. Agreed 314, adjudicated 146. Decided 68.5 %. Analyst A answered `no_basis` in 18.0 %, the reviewer in 34.6 %. Same asset in 90 % of the 280 comparisons in which both named one. $0.076, $0.00016 per comparison. |
| Position | Analyst A named the asset shown first in 44.8 % of its asset answers, the reviewer in 43.5 %. Inside the band. |
| Probe | 93 dossiers. Asset named right in 35.5 % (chance 0.49 % among 203 tickers), month within six months in 23.7 %. $0.005. |
| Total | $0.20 by the account balance ($4.8594 before, $4.6596 after). |

The stop rule passed in every check. The identification share is lower than on the dossiers of Charters 1
and 1b (51 % and 48 % in two probes with the larger model of the family, month within six months 89 % in the
first), and the month is rarely recognised. Identification concentrates on dossiers with many lines: 5.9 lines on average where the asset was
named, 2.8 where it was not. The large assets are named most often, but 22 different assets were named at
least once.

## 5. Gates

The verdict is PASS when both gates pass, otherwise FAIL. It is written by code from the registered
statistic.

| Gate | Condition |
|---|---|
| G1 | Newey-West t (lag 4) of the mean weekly coefficient of §3.5 at least 2.0, the mean positive, at least 78 weeks in the statistic |
| G2 | The mean weekly coefficient positive in 2023 and in 2024, with at least 78 weeks in the statistic |

**Pass rate on noise.** 400 draws per scenario on the real panel structure (universe, controls, quant
forecast, attention counts, dossier pattern), with synthetic scores and returns (Appendix B). Two dossier
structures bracket the coverage of the full run: the present store alone (48.4 % of the asset-weeks with a
dossier) and a denser one (58.2 %) in which an asset-week with at least three scope documents of the archive
also has a dossier. All 104 weeks enter the statistic in both. On pure noise G1 passes in 3.0 % and 3.5 % of
the draws, G1 and G2 together likewise. A one-sided test at t 2.0 has a nominal rate of 2.3 %; the
Newey-West t over 104 weeks has slightly heavier tails than the normal.

**Confounders.** Scores and returns that both load on the four-week return, or both persist over the weeks,
pass in 1.75 % to 4.0 %. Scores and returns that both load on attention pass in 2.5 % to 3.5 % at the
attention effect measured under Charter 2 and in 7.5 % to 10.25 % when that effect is ten times as large and
loads on the standardised log count, whose long right tail the rank control does not remove. At the measured
size the attention controls hold. The stress cell is a limit of the design and is stated with the verdict.

**Power.** With a planted correlation ρ between the score and the return among the dossier assets, G1 passes
in 13 % to 16 % at ρ 0.02, 22 % to 28 % at ρ 0.03, 35 % to 39 % at ρ 0.04, 62 % to 74 % at ρ 0.06 and 88 % to
95 % at ρ 0.08. For scale: the attention counts carried a rank correlation of 0.031 with the weekly return in
Charter 2. The gate detects an effect about twice that size with good probability and misses an effect of
that size more often than not.

**Reading of the verdict.**

- A FAIL means that the comparisons carry no information on the next-week return rank beyond the quant
  forecast, price controls and attention that this window and this design can detect. It closes the family
  `llm-multiagent-v2`: no attempt remains.
- A PASS licenses one registered run on a sealed window and nothing else. The comparison model was trained on
  text written after this window (§6).
- Neither verdict is changed by a descriptive panel.

**Descriptive panels** (computed after the gate; an error in one is recorded and changes nothing):

| Panel | Content |
|---|---|
| `score_without_attention_controls` | The score beyond the quant forecast and price controls only |
| `score_without_quant` | The score beyond price controls and attention only |
| `net_wins`, `code_tone` | The alternatives of §3.4 under the gate controls |
| `score_beyond_code_tone`, `code_tone_beyond_score` | Whether the comparison adds to what code makes of the same lines, and the reverse |
| `attention`, `quant` | The two controls beyond everything else |
| `score_outside_most_covered` | The gate statistic without BTC and ETH |
| `score_within_asset` | The score less the asset's mean score over its dossier weeks: a weekly reading rather than a standing preference for an asset |
| `spread_score`, `spread_code_tone` | Mean simple return of the top third minus the bottom third of the dossier assets by the score, per week (no cost, no book) |
| `identified_split` | The weekly coefficient on identified and on other dossiers, with a bootstrap interval of the difference (500 draws, seed 20261115) |
| `coverage` | Dossier share, dossiers per week, lines and decided comparisons per dossier, rows without return or quant forecast |

The outputs also carry the quality shares of the comparison stage, the call statistics, the prompt hashes,
the dossier report, the archive counts, the probe shares and the facts of the present extraction
(`comparison.json`).

## 6. Leakage and exposure

- **The window is exposed.** The 104 test weeks are those of Charter 2, whose run joined the forward returns
  of these weeks with reader features. Charters 3 and 4 joined next-week variance and next-day returns of the
  same period. The registration states the reuse as exploratory.
- **What was known when the design was fixed.** The outputs of Charters 2 to 4: the reader judgements carried
  nothing, the attention counts a weak positive relation with the weekly return. The decision to control for
  attention and to leave the quant forecast unchanged follows from them. No output of those runs relates a
  comparison of two assets to a return.
- **What was not looked at.** Before the registered run no dossier, comparison result, comparison score or
  probe flag is joined with a return or any other price quantity dated at or after its decision. The pilot
  read answers and dossier texts of three weeks to check the mechanics (§4.1). The pass rate and power of
  Appendix B use synthetic scores and returns on the real panel structure. The instruction of the comparison
  was written before the pilot and not revised.
- **Memory of the model.** The comparison model was trained on text written after the test window. It may
  recognise an episode in a de-identified dossier and recall what followed. The probe measures how often it
  names the asset (35.5 % in the pilot) and the month (23.7 %). A recalled outcome can only raise the
  statistic, so the bias runs towards a PASS. A FAIL is robust to it; a PASS licenses only a sealed window
  after the model's training data, and the identified split is reported with the verdict.
- **De-identification.** Asset and entity names are replaced by tokens of one alias space per week, dates by
  ages in days, and a dossier that still carries a dictionary name after rendering is dropped. What an asset
  is and does can remain recognisable (a layer-2 network, a meme coin); the probe measures this.
- **Order effects.** The two analysts see the two orders, the adjudicator a drawn order, and the share of
  first-shown picks is reported. A position preference adds noise to the score and cannot create a relation
  with the return, because the shown order is drawn independently of the assets.
- **Timing of the material.** A present-store row enters a dossier when it was captured before the decision.
  An archive row enters when it is observable by the feed clock (§3.1). No row of either store dated after
  the decision is read.
- **Coverage depends on attention.** An asset with more reports has a dossier more often and longer dossiers.
  `attn_7d`, `n_lines` and `has_dossier` are controls of the gate. Appendix B shows that the controls hold at
  the measured attention effect and leak at ten times that effect.
- **Price commentary.** News follows price: a report about a move is written after the move. The typing call
  labels price recaps and the reading rule leaves them out; the controls include the four-week return; an
  opinion on a past move can still enter a dossier. A continuation or reversal of last week's move would be
  partly absorbed by `ret_4w` and `p_quant`.
- **Concentration.** BTC and ETH have a dossier in every week. The gate is reported without them.
- **Delisted contracts.** A contract delisted inside the week books its last close; a row without a forward
  return leaves the week's statistic.
- The registered run rehearses on synthetic returns before the claim and joins the real forward returns once,
  after the claim.

## 7. What is fixed and what is reused

Reused without change: everything of Charter 2 up to the record table of the present store (text store,
typing, reading rule, reader agents, adjudicator, call cache, 53,330 records), the typing and reader
instructions for the archive documents, the cards and the universe, the quant forecast, the forward returns,
the Bradley-Terry fit of `tradingagents/xsect/pair_xs.py`, the de-identification of the dossier build and the
run lifecycle (`tradingagents.research`). The registered files of Charters 2 to 4 are not modified.

New under this charter:

| File | Content |
|---|---|
| `tradingagents/compare/archive.py` | rows of the archive: time conversion, cleaning, feed clock and availability |
| `tradingagents/compare/scope.py` | typing scope and pilot weeks |
| `tradingagents/compare/dossier.py` | weekly reading sets, dossier lines, rendering in one alias space per week |
| `tradingagents/compare/duel.py` | schedule, prompts, calls, consensus, rebuild from the cache, scores, quality shares |
| `tradingagents/compare/charter5.py` | panel, gate statistic, gates, descriptive panels, verdict |
| `scripts/cmp_archive_ingest.py`, `cmp_items_build.py`, `cmp_type.py`, `cmp_read.py`, `cmp_dossiers.py`, `cmp_duels.py`, `cmp_probe.py`, `cmp_common.py` | drivers of the stages |
| `scripts/cmp_null_gate.py` | pass rate and power on synthetic returns (not part of the run) |
| `scripts/cmp_charter5_register.py`, `scripts/cmp_charter5_run.py` | registration and registered run |
| `tests/research/test_compare.py` | tests |

Fixed by the freeze and pinned by the registration: this document, the source files, the instructions of
Appendix A with their hashes, the gates of §5 and every constant quoted in §3 to §5.

Data under `data/compare/` stays out of version control (the archive licence is non-commercial and the files
are large); the registration pins every table and cache by its hash and the store by a digest of its files.

## 8. Budget

Rates measured in the pilot, scaled to the full scope. The coverage of the full run is projected from the
pilot weeks (93 dossiers against 83 from the present store alone) onto the 2,514 present-store dossiers of
the test weeks.

| Item | Basis | Projected |
|---|---|---|
| Pilot (paid) | four steps on three weeks | $0.20 |
| Typing | about 31,300 remaining documents at $0.096 per 1,000 | $3.0 |
| Reading | about 13,100 documents (0.42 per typed document) at $0.17 per 1,000 | $2.2 |
| Comparisons | about 2,800 dossiers, 5 comparisons each, about 13,600 remaining at $0.16 per 1,000 | $2.2 |
| Probe | about 2,700 remaining dossiers at $0.06 per 1,000 | $0.2 |
| Registered run | local | 0 |
| **Full run** | | **about $7.6** |

- Spend caps of the drivers, each over its whole cache including the pilot: typing $4.00, reading $3.00,
  comparisons $3.00, probe $0.30, together $10.30. The caps bound the run whatever the projection misses.
- The balance is $4.66. A top-up of $10 covers every cap with a margin of about $4.
- Calendar: D3a takes about two to four hours of calls; D3b about an hour. The submission date is 2027-01-08
  and the planned results freeze 2026-12-21.
- Confirmation on a sealed window follows only a PASS and is outside this charter. It would need the news
  fetch and archive rows for 2025 and 2026, cards to December 2026 and the same stages on those weeks.

## 9. Order of the four changes

| # | Change | Status |
|---|---|---|
| 1 | Language model reads, fitted model forecasts | Charter 2, FAIL (t 1.39) |
| 2 | Different target (next-week volatility) | Charter 3, FAIL (t −0.72) |
| 3 | Fresher information (daily decision, next-day return) | Charter 4, FAIL (t −2.49) |
| 4 | Agents compare assets directly, on text | This charter, attempt 6 of 6 |

After this charter no attempt remains in the family. A FAIL closes it; the thesis reports all six attempts
with their verdicts.

## 10. Decisions

Open at the draft. The column "Recommended" is what the code implements now; an alternative changes code and
this text before the freeze.

| # | Point | Recommended | Alternative |
|---|---|---|---|
| 1 | Material | Present store plus the archive in the small scope (option A, chosen 2026-11-15). | Present store alone (option B, no typing or reading cost, coverage of 48 %). Or the archive in the full scope, every linked document of the new outlets: about 145,000 more documents to type and read, about $25 more at the pilot rates. |
| 2 | Comparisons per week | 10 rounds of the round robin: every asset meets 10 opponents, about 5n comparisons. | 6 rounds: 40 % cheaper, a noisier score. Or the full round robin: n − 1 rounds, about three times the cost. |
| 3 | Agents | Analyst and reviewer in opposite orders, the reviewer with a default of `no_basis`; adjudicator on disagreement. | One analyst asked in both orders, consensus by code: about 15 % cheaper, but no second agent and no adjudication, which the assignment asks for. |
| 4 | Model | `deepseek-v4.1-flash` for all three roles, as in the reading stage. | The larger model of the family for the comparisons. On the identification probes it cost $0.0016 per dossier against $0.00006 for the smaller model here; the comparison stage would cost tens of dollars. |
| 5 | Score | Bradley-Terry log strength with a prior of 0.5. | Net wins. Reported as a descriptive panel either way. |
| 6 | Assets without a dossier | In the gate with the neutral score 0 and the control `has_dossier`. | Gate on dossier assets only: fewer rows per week, and the gate would need a lower minimum than 15 rows. |
| 7 | Attention | Three attention controls in the gate. | Gate beyond quant forecast and price controls only (descriptive panel). A pass could then rest on the counts that Charters 2 and 3 already found. |
| 8 | Threshold of G1 | t at least 2.0, as in Charters 1b to 4. Pass rate on noise 3.0 % to 3.5 %. | t at least 2.3: a lower pass rate on noise and less power (not drawn for this design). |
| 9 | Identified dossiers | Descriptive split; the gate uses every dossier. | Leave identified dossiers out of the gate: about a third of the dossiers, mostly large assets, less power. |
| 10 | Pilot | Accept the pilot: the stop rule passed and no revision was made. | Revise the comparison instruction once and rerun on other weeks (allowed by the stop rule, not needed). |
| 11 | Top-up | $10 before D3a. | About $5.50, which covers the caps with no margin. |
| 12 | Attempt accounting | Attempt 6 of 6; a FAIL closes the family. | No last attempt (option C): the thesis reports five attempts and the design of this one as not run. |

## Appendix A. Instructions

The texts below are the code (`tradingagents/compare/duel.py`, `scripts/cmp_probe.py`). The hashes identify
them in every output and in the registration.

### A.1 Comparison

Hash of the instructions, the schema and the prompt layout (`duel.prompt_sha256`): `4b1b66c1f625230f871b04c5ba078d9f474e65c13c1515ae149c107c04647e8f`.

System text of analyst A (the instruction):

> You compare two crypto assets on the reports of the last seven days. Assets and all other entities are replaced by role tokens such as Asset_K, Exchange_1, Person_2, and dates are relative. Never guess which asset a token stands for and never use knowledge about real assets, prices or dates. Judge from the reports shown and from nothing else.
>
> For each asset you see the reports in which it is the subject: the age of the report, the kind of source, the number of similar reports where there are several, and a summary. Both lists were selected by the same rule. A longer list alone is no argument, and a price move that already happened is no argument by itself.
>
> Question: given only these reports, which of the two assets has the better outlook for its price over the next seven days relative to the other?
>
> Answer with a JSON object:
> - choice: first, second or no_basis. Answer no_basis when the reports give no concrete ground to prefer one asset, for example when both lists hold only routine items or opinions without a new fact.
> - reason: at most 25 words that name the reports which decide. Refer to an asset by its token, never as first or second.

Analyst B (reviewer) receives the instruction followed by:

> You are the reviewer. Start from no_basis. Leave that default only where the reports state a concrete fact that clearly favours one asset over the other.

The adjudicator receives the instruction followed by:

> You are the adjudicator. Two analysts compared the two assets below and did not name the same asset. Both answers are shown with their reasons. Issue the final answer from the reports alone. An analyst may be right, or neither.

User text of the analysts (`duel_prompt`), with the two dossiers in the order of §3.3:

```
FIRST asset: Asset_K
Reports of the last seven days:
<dossier lines of Asset_K>

SECOND asset: Asset_C
Reports of the last seven days:
<dossier lines of Asset_C>
```

The adjudicator's user text adds the two answers in a drawn order:

```
Analyst 1 answered: Asset_K. Reason: <reason>
Analyst 2 answered: Asset_C. Reason: <reason>
```

An analyst answer of `no_basis` is shown as `no_basis. Reason: <reason>`, an invalid one as `no valid answer`.
Answer schema (structured output, at most 200 output tokens):

```json
{"type": "object", "additionalProperties": false, "required": ["choice", "reason"], "properties": {"choice": {"type": "string", "enum": ["first", "second", "no_basis"]}, "reason": {"type": "string"}}}
```

### A.2 Identification probe

Hash (`cmp_probe.prompt_sha256`): `9dc83719c68bb223a6956195374da1eaa3474da29936b24d7a0a6d0ec3a18b2c`. System text:

> The reports below are about one crypto asset. Its name and all other entities are replaced by role tokens. Name the real asset (a ticker from the list) and the calendar month (YYYY-MM) in which the reports were written. Use any clue. Always give your best guess.

User text:

```
Candidate tickers: <the 203 tickers of the test universe, sorted>

Asset token: Asset_K
Reports of the last seven days:
<dossier lines of Asset_K>
```

Answer schema (at most 100 output tokens):

```json
{"type": "object", "additionalProperties": false, "required": ["asset", "year_month", "confidence"], "properties": {"asset": {"type": "string"}, "year_month": {"type": "string"}, "confidence": {"type": "number"}}}
```

### A.3 Typing and reading of the archive documents

Unchanged from the present store. Typing: the call of `tradingagents/dossier/llm_text.py`, cache key hash
`96b5e6bb700763fdda6ca31a4ae1da59f11e2947c99455a17ab3d72933bcca65`. Reading: the instruction, schema, reviewer and adjudicator of Charter 2
(`tradingagents/reader/schema.py`), hash `7cf96c2fa147208c2e22e9efb7439caa3e216ba066f382e161c26de26721a07f`.

## Appendix B. Pass rate and power of the gate on synthetic returns

`scripts/cmp_null_gate.py`, 400 draws per cell, seed 20261115, on the real panel structure of the
104 test weeks (5,200 asset-weeks): universe, price controls, quant forecast, attention counts of the present
store and the linked archive, and a dossier pattern. Scores (zero without a dossier) and returns are drawn; no
return of the window is read. The first five draws of every cell are checked against `charter5.gate_statistics`.

- `present`: the dossiers the present records give, 48.35 % of the asset-weeks.
- `dense`: in addition an asset-week with at least three archive documents of the typing scope, 58.23 %.

Scenarios on noise. `noise`: scores and returns independent. `attention`: scores and returns both load on the
standardised `attn_7d` and the return also on having a dossier, loading 0.3 (about ten times the measured
effect); `attention_measured`: loading 0.03; `attention_compressed`: loading 0.3 on the standardised log of
`attn_7d`. `momentum`: both load on the four-week return. `persistent`: scores and a return component both
persist from week to week (AR 0.8), independently.

Cells: G1 pass rate (G1 and G2 where different), mean t, standard deviation of t.

| Scenario | present | t mean | t sd | dense | t mean | t sd |
|---|---|---|---|---|---|---|
| noise | 3 % | 0.00 | 1.02 | 3.50 % | 0.05 | 1.03 |
| attention | 7.50 % | 0.58 | 1.05 | 10.25 % (10 %) | 0.67 | 1.01 |
| attention_measured | 3.50 % | 0.12 | 1.00 | 2.50 % | 0.12 | 0.98 |
| attention_compressed | 2 % (1.75 %) | −0.25 | 1.07 | 3.25 % (3 %) | −0.14 | 1.12 |
| momentum | 1.75 % | 0.00 | 1.01 | 3.75 % | 0.05 | 1.04 |
| persistent | 3.25 % | −0.12 | 1.12 | 4 % (3.75 %) | −0.11 | 1.15 |

Power: the return of a dossier asset correlates with its score at ρ.

| ρ | present | t mean | t sd | dense | t mean | t sd |
|---|---|---|---|---|---|---|
| 0.02 | 13.25 % | 0.73 | 1.12 | 16.25 % | 0.89 | 1.16 |
| 0.03 | 22 % (21.75 %) | 1.21 | 1.07 | 28.25 % (27.75 %) | 1.37 | 1.09 |
| 0.04 | 35 % | 1.53 | 1.16 | 38.50 % | 1.74 | 1.10 |
| 0.06 | 62.50 % (62.25 %) | 2.38 | 1.12 | 73.50 % (73.25 %) | 2.71 | 1.16 |
| 0.08 | 87.50 % (87.25 %) | 3.25 | 1.11 | 95.25 % (95 %) | 3.74 | 1.13 |
