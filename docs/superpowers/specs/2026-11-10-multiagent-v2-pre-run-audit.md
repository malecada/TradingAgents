# Pre-run audit of the multi-agent v2 pipeline (before Charter 1 registration)

**Date:** 2026-11-09/10. **Status:** in progress; findings are added as they are verified, fixes are listed with
their commit. Two sources: a checklist review by the author of the code and an independent reviewer (fresh
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

(Independent reviewer findings and the fix commits are appended below when available.)
