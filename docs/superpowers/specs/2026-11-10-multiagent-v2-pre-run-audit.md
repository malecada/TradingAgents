# Pre-run audit of the multi-agent v2 pipeline (before Charter 1 registration)

**Date:** 2026-11-09/10. **Status:** mechanics audit (A–F) and design review (H) applied and tested; the v2.8
rebuild, the full identification probe and a one-week live check of agents v2.4 remain before registration. Two sources: a checklist review by the author of the code and an independent reviewer (fresh
agent, read-only, no API access) briefed on the same files and questions. Nothing is registered until every
critical finding is fixed and re-tested.

Scope: `tradingagents/dossier/*`, `tradingagents/agents_v2/*`, `scripts/dossier_*`, `scripts/llm_v2c1_*`,
`scripts/dossier_reid_probe.py`, the card panel and kline stores, the Charter 1 draft.

## A. Point-in-time correctness

| # | Item | Finding | Severity | Action |
|---|---|---|---|---|
| A1 | Decision time vs kline bars | Daily bars are stamped at open (00:00 UTC); the Friday bar closes at Saturday 00:00 = decision time. Cards use data through the Friday bar (`llm_rank_xs_cards.py` header, verified). Forward return = Friday close → next Friday close. Consistent. | ok | none |
| A2 | Text admissibility | `store.query` requires `as_of_ts <= decision_ts`; Wayback as_of = first capture, Reddit as_of = created. Articles published earlier but captured later are excluded (conservative). | ok | none |
| A3 | Quant forecast training set | `fit_predict` uses Fridays < decision Friday whose 7-day target is realized at or before the decision Friday's close; calibration record excludes the current week. | ok | none |
| A4 | **Reddit post selection by comment count** | `retrieve_text` keeps the 25 most-commented posts per dossier. Comment counts are retrieval-time (2026), so posts about assets that later attracted attention are preferred: a look-ahead channel in *which* posts are shown, even though post text is PIT. | **critical** | select by recency (latest 25 primary posts), drop engagement fields from selection entirely; rebuild |
| A5 | Universe membership | Top-50 by trailing 30-day dollar volume from the Friday card; PIT. | ok | none |
| A6 | Delisted assets | Forward return missing when a symbol delists within the week → excluded from IC. Mild survivorship on the target side. | minor | disclose; count excluded rows in evaluation.json |

## B. Anonymization channels

| # | Item | Finding | Severity | Action |
|---|---|---|---|---|
| B1 | Universe size in the numeric block | "Universe: 128 assets this week" grows over time (128 → 200) and dates the dossier. | major | drop the count; keep the rank percentile only |
| B2 | Scheduled-events block | "next rate decision in N days" dates within a 6-week cycle only; acceptable. | minor | none |
| B3 | Residual content identification | 51% of assets identified from content on the H1-2022 set (65% top-20); measured per dossier, used as covariate (charter §4). | known | none beyond measurement |
| B4 | Non-thinking typing vs thinking | 60-article comparison: type agreement 0.97, novelty 0.92, affected-alias set 0.80; two disagreements event↔analysis. | ok | note the 0.80 alias agreement in the charter |

## C. Evaluation and runner

| # | Item | Finding | Severity | Action |
|---|---|---|---|---|
| C1 | Mixed probability sources | Debated assets carry a judge probability, others the analysts' mean; the two have different dispersion, which reshuffles ranks within a week. | major | report a uniform secondary metric (analyst-mean IC on all assets) alongside the primary system IC; consider a no-debate judge for non-debated assets if budget allows |
| C2 | Costs in the rule-twin book | Taker 5 bp per side; funding and slippage omitted. | minor | disclose; add funding from the card's 30-day funding as a sensitivity |
| C3 | Cached failed results | Fixed 2026-11-09: failed assets are never reused from cache. | fixed | — |
| C4 | PM constraint violations | Both pilot weeks; rule twin is primary. | fixed by design | — |

## D. Reproducibility and freeze

| # | Item | Finding | Severity | Action |
|---|---|---|---|---|
| D1 | Alias seed | `hash(sym)` was process-randomized → rebuilt dossiers differed byte-wise. Fixed with sha256 (commit d5881ff). | fixed | — |
| D2 | Config sha coverage | Prompts, schemas, reasoning map and token budgets enter `config_sha`; model pins live in `or_client.PINS` and are recorded per call but not in the sha. | major | include PINS in config_sha |
| D3 | Mixed builder versions | Dossier dir mixes v2.4/v2.5 outputs; manifest script rejects mixed versions. Final dev set is a fresh rebuild. | ok | rebuild into a fresh directory |

## E. Independent reviewer findings (fresh agent, read-only, same files)

| # | Finding (condensed) | Severity | Fix | Commit |
|---|---|---|---|---|
| C1 | Reddit posts selected by retrieval-time `num_comments` (82 % of comments accrue after decision time): a future-information channel that the charter declared absent. | critical | Selection by recency only (newest `event_ts` first, cap 25); scores and comment counts are never read. | 9235ce11a |
| C2 | Delisting weeks vanish: `forward_returns` requires a bar at Friday+7, so a contract that stops trading mid-week (LUNA 2022-05) leaves the target and is booked at 0 % in the book. | critical | Last available close inside the week is booked with a `delisted` flag; the week stays in the target, the median and the book; count disclosed in `evaluation.json`. | this commit |
| M1 | Stop rule not implemented: oldest-first iteration, cap trips caught per asset so the run degrades instead of stopping; incomplete week kept. | major | `SpendCapError` propagates through runner and threads; `llm_v2c1_run.py` iterates newest-first, stops at the cap, excludes the incomplete week, records completed weeks and `truncated_at`. | this commit |
| M2 | Rule twin not market-neutral (gross-scaled, never demeaned; pilot mean p 0.47 → net short, SR measures beta); funding costs absent. | major | `rule_weights` alternates demeaning and clipping until net 0, gross ≤ 1, |w| ≤ 0.10; `book_returns` accepts a funding table (longs pay, shorts receive, 7 days). | this commit |
| M3 | Mixed probability sources: 12 debated assets replaced by compressed judge probabilities, 38 others keep analyst means → extremes pulled back relative to the rest. | major | Uniform primary panel: every non-debated asset gets a judge-without-debate call (same role, same scale); analysts' mean kept as a separate secondary panel (`p_analyst_mean`, evaluated as `analyst_mean`). | this commit |
| M4 | Percentiles and "Universe: N assets" computed over the ~130-asset card panel while the target median is over the top-50. | major | Percentiles within the decision universe (`universe_symbols` passed per week); universe size no longer printed. | 9235ce11a |
| M5 | Freeze gaps: dossier sha computed before the quant section was appended; `config_sha` omits model pins, N_DEBATE, analyst roles, temperature; runs dir shared across experiments; kline digest never verified at run time. | major | Sha recomputed over the final text; `config_sha` covers PINS, N_DEBATE, ANALYST_ROLES, TEMPERATURE; runs dir `data/agents_v2/runs/<experiment>`; kline digest verified before the first call. | 9235ce11a + this commit |
| M6 | Structural time fingerprints: exact FOMC day counts (34 distinct pairs over 261 weeks) and universe size nearly identify the week. | major | FOMC bucketed to "within the next two weeks"/"no meeting"; universe size removed. | 9235ce11a |
| M7 | Numeric rendering errors: `size_rank` percentile compared to 20/100 (every asset "top-20"); log returns printed as simple; funding annualized twice. | major | Percentile-based size buckets; `expm1` on log returns; funding annualized once (×365). | 9235ce11a |
| M8 | 6.8 % exact-duplicate items plus near-duplicates across outlets inflate evidence weight. | major | Jaccard-0.8 near-duplicate removal before item selection. | 9235ce11a |
| M9 | Prompts push p toward 0.5 (pilot range 0.35–0.58) so the calibration-slope gate fails on under-confidence even with skill; PM prompt inconsistent with the validator. | major | Prompt now asks for the full range when evidence is one-sided and 0.5 only when it is not; PM prompt restated as the demeaned formula with binding constraints (net ±0.05). The rule twin remains the primary book. | this commit |
| minor | `r.json()` on a non-JSON 200 raised a bare `ValueError`; `--out` of `dossier_build.py` not honoured by manifest/probe/audit; disclosures incomplete. | minor | Non-JSON 200 is retried then raised as `ORError`; `--dossiers` (and probe `--out`) flags added; charter disclosures extended (DefiLlama/CoinMetrics daily slack, Wayback survivorship, delisting convention). | this commit |

## F. Cost consequence of M3 and the budget rule

The uniform judge panel adds one judge call for each of the ~38 non-debated assets per week. Pilot cost was
$2.07 per week with 12–20 debates and no judge for the rest; the extra judge calls are estimated at $0.5–0.8
per week, so the dev run is expected at $2.6–2.9 per week, about $410–450 for all 156 weeks. The registered
cap stays at $400; under the newest-first rule (charter §6a) this covers roughly 140–155 weeks and the
truncation is disclosed rather than hidden. The cap can be raised before registration if more credit is
available.

## F2. Live verification of the fixed runner (2026-11-10, pilot week 2022-09-30, scratch directory)

- Cap path: with a $0.40 cap the run raised the spend-cap error on the first call past the cap and stopped;
  24 finished per-asset results were on disk.
- Full week with a $4.50 cap: 50 assets, 12 debated, 38 judged without debate, 0 failures, 335 calls,
  **$2.48**, 15.3 min. All 50 probabilities come from the judge role; the analysts' mean is stored for all 50.
  Rule twin: net 0.0000, gross 1.000, max |w| 0.100. The PM output still violated the caps, confirming the
  rule twin as primary book.
- Measured cost replaces the §F estimate: 156 weeks ≈ $387, inside the $400 cap with little headroom.
- Probability spread remains compressed (mean 0.452, sd 0.050, range 0.35–0.55; judge-only sd 0.049,
  debated sd 0.026). The calibration-slope gate will register this honestly; no further prompt tuning before
  registration (tuning on dev-window output would be a post-hoc step).
- Realized funding: `scripts/dossier_funding_fetch.py` stores Binance USDT-M funding history per symbol;
  `realized_funding` sums the settlements in (Friday, Friday+7] and the book charges longs / credits shorts.
  `portfolio.json` reports the book with and without funding and the funding coverage.

## H. Design review of the agent framework (independent reviewer, 2026-11-10) and the resulting agents v2.4

Sections A–F audited mechanics; a second independent reviewer was briefed on the DESIGN of the roles, debate,
aggregation, information flow and gates (read-only, no API access, same files plus the smoke run). Twelve
findings; all implemented in commit 14d192547 except the ablations, which are registered in charter §6.

| # | Finding (condensed) | Severity | Change |
|---|---|---|---|
| 1 | Dossier aliases are unique within a dossier but not across the week (50 assets, 20–22 aliases); runner and book were keyed by alias, so every portfolio number of the pilot and smoke was corrupt (forecast panels keyed by symbol were unaffected). | design-critical | Runner, candidates and book keyed by symbol; aliases appear only inside prompts; assertion on unique keys; the PM (ablation) sees week-unique ids C01..C50. |
| 2 | "System IC ≥ quant IC" gate mis-specified: the interpreter's weight (modal 0.15) was consumed nowhere and an LLM that discounts a 0.09-IC signal fails the gate regardless of content. | design-critical | Structural hybrid p_hybrid = sigmoid(w·logit(q) + (1−w)·logit(p_judge)); p_quant, p_judge, p_hybrid recorded; gate replaced by a forecast-encompassing test (Fama–MacBeth, NW t ≥ 2 on the p_judge coefficient). |
| 3 | Calibration-slope gate is a dispersion test under compression (sd 0.05) and ties; quintile binning on tied ranks is unstable. | design-critical | Gate = IC t ≥ 2 plus Brier skill after walk-forward logistic recalibration; Cox slope and quintile slope reported as diagnostics. |
| 4 | Debate subset chosen on conviction, not randomized; the debated/judge-only sd gap was restricted range, not a debate effect. | material | Seeded random subset per week; judge-without-debate for every asset (uniform panel) plus debate judges on the subset → paired within-asset contrast (≈ 1,870 pairs); the no-debate ablation is dropped. |
| 5 | Analysts differ by instruction only; all see the full dossier; 19/50 identical probability triples. | material | Physical input partition: market = n2/n3/n4/n7/n8 + calendar; fundamental = n1/n5/n6 + event-typed items; news = text + calendar; quant line only to the interpreter. Cuts analyst tokens ≈ 30 %. |
| 6 | Percentiles misread by non-thinking roles ("pct 5" read as extreme volatility). | material | Rendered "pct K, higher than K% of the universe"; COMMON defines the convention. Builder v2.8. |
| 7 | Mean p below 0.5 on a relative target (agents forecast market direction). | material | COMMON states that exactly half the universe beats the median; weekly-centered Brier reported. |
| 8 | LLM-only arm not separable (every role restated the quant line); the trailing calibration record shown to agents reset at build-batch boundaries. | material | Debaters and judges never see the quant section (p_judge is LLM-only); quant forecasts computed over the full card history before any build; quant-hidden ablation registered. |
| 9 | Self-reported confidence sized positions without validation and double-counted |p − 0.5|; abstain asymmetric between arms. | material | Primary book (p − 0.5)/vol; confidence-weighted book reported; abstain → p 0.5 in both arms, weight 0. |
| 10 | Debate asymmetric (opener had two turns) and inert; thinking-off cost argument sound but untested. | material | Symmetric two-turn debate (open; opponent opens and rebuts), judge sees both; thinking-on ablation registered. |
| 11 | No citation validity check; cited ids detached from claims. | material | Parse-time citation-existence and number-grounding rates per role, reported per asset-week and in the evaluation summary. |
| 12 | PM violated constraints in every run; single-call baseline missing; omissions vs the original TradingAgents not justified. | material | PM removed from the main run (ablation overlay only); single-call baseline registered; the design chapter is to justify each omission with its §2 root cause. |

Cost consequence: +12 judge calls and −4 debate calls per debated asset and −1 PM call per week → ≈ $2.5 per week,
unchanged from the §F2 measurement within noise; ablations ≈ $130 (registered, separate from the $400 cap).

## G. Remaining before registration

1. Fresh v2.6 rebuild of the dev window into a new directory (2024 first) after the Wayback fetch completes.
2. Identification probe on the rebuilt set (`dossier_reid_probe.py --all --dossiers <dir> --out <parquet>`).
3. `dossier_audit.py --dossiers <dir>` re-check: duplicates ≈ 0, no leaked names, no residual role tokens.
4. Manifest, charter freeze (remove DRAFT), registration, run with the funded cap.
