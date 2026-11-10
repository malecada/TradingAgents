# Charter 1 — Multi-agent v2 development run (`llm-v2-charter1`) — FROZEN 2026-11-11

**Status:** drafted 2026-11-08; frozen 2026-11-11 after the pre-run audit (mechanics A–F, design review H,
`docs/superpowers/specs/2026-11-10-multiagent-v2-pre-run-audit.md`), the v2.8 rebuild of all 156 weeks and
the agents v2.4 live check. Dev-window exposure before the freeze is limited to the disclosed pilot, smoke
and preview weeks listed in §6a; their per-asset calls are cached and reused by the run, and no prompt, schema,
weight or gate was changed on the basis of them.
**Parent plan:** `docs/superpowers/specs/2026-11-08-multiagent-v2-analysis-and-plan.md`.
**Prior cycle:** Charter 0 (`llm-v2-charter0-2026-11-09`) FAIL → dossier carries summaries and numeric cards,
no typed-event store.

## 1. Question
Does the dossier-fed, anonymized, order-debiased multi-agent system (DeepSeek V4-Pro in every judgment role)
produce weekly cross-sectional forecasts with detectable skill, and does it add forecast skill over the
quant-only cross-sectional model fed identical cards?

## 2. Target and universe
- Universe: weekly top-50 Binance USDT perpetuals by trailing 30-day dollar volume from the card panel
  (PIT: cards computed from trailing data; universe membership chosen on the Friday itself).
- Decision time: Saturday 00:00 UTC after each Friday card; text admissible iff `as_of_ts <= decision time`.
- Target: y = 1[asset's return Friday close → next Friday close exceeds the universe median return].
  Forecast: `p_outperform` ∈ [0,1] per asset-week.
- Dev window: Fridays 2022-01-07 → 2024-12-27 (156 weeks, 7,800 asset-weeks). Sealed-A 2025-01 → 2026-04,
  Sealed-B 2026-05 → 2026-12-11: untouched by this charter.

## 3. Frozen inputs (hashes recorded at freeze)
- Dossier builder `dossier-v2.8`; dossier files (one hash per file, `data/agents_v2/charter1/dossier_manifest.json`).
- Agent config `agents-v2.4`, sha a97972476be6f5b1… (`tradingagents/agents_v2/graph.py::config_sha`: prompts, schemas,
  reasoning map, token budgets, model pins, debate count and selection rule, analyst input partition, temperature).
- Re-identification flags: V4-Pro non-thinking probe on a 20 % stratified-per-week sample of the dossiers
  (`data/dossier/reid_flags_v26.parquet`); the identified-subset analysis runs on that sample.
- Model pins: `deepseek/deepseek-v4-pro` fp8, ordered providers Baidu then StreamLake (same weights; echoed provider recorded per call), temperature 0. Reasoning: non-thinking mode for analysts, forecast interpreter and debaters (providers did not honour effort or token caps; pilot latency 45 s and ~2,000 reasoning tokens per call otherwise), medium reasoning for judge and portfolio manager. Flash (non-thinking) for article typing.
- Text sources admitted: Wayback captures of CoinDesk, Cointelegraph, The Block (as_of = first capture);
  Arctic Shift Reddit posts for r/CryptoCurrency, r/Bitcoin, r/ethereum (as_of = created; scores are
  retrieval-time and used for nothing; posts selected by recency only). No Alpaca/Benzinga store (not synced).
- Forward returns from the 799-symbol daily kline store.

## 4. Pre-run validity probes (pilot, two dev weeks, STOP on fail)
| Probe | Floor |
|---|---|
| Schema-valid answers | ≥ 0.99 of calls |
| Order-swap consistency: Spearman between judge p in bull-first vs bear-first across debated assets | ≥ 0.75 |
| Repeat agreement: Spearman of p across two identical runs on 50 assets | ≥ 0.85 |
| Re-identification (measured on EVERY dev dossier, non-thinking V4-Pro): asset accuracy | reported, not gated (pilot: 81% before hardening, 52% after; residual identification stems from asset-intrinsic content) |
| Re-identification: month within ±6 months | reported (pilot 69%) |
| Identified-subset analysis | forecast gates (§5) computed separately for identified and non-identified dossiers; a gap is reported as the memorization estimate |
| Dossier noise share (price recaps + promotional + unrelated among retrieved) | reported; ≤ 0.6 of retrieved |
| Measured cost per asset-week | $0.041 (pilot, 2 weeks); budget set at 1.2× projection |

## 5. Gates (dev window, forecast quality before any portfolio claim)
Panels (all recorded for every asset-week): `p_quant` = ridge rank percentile; `p_judge` = LLM-only probability
(judge who never sees the quant section; debate where the asset was in the random debate subset, judge without
debate otherwise); `p_hybrid` = deployed probability, sigmoid(w·logit(q) + (1−w)·logit(p_judge)) with w the
forecast interpreter's weight; `p_judge_nd` / `p_hybrid_nd` = the uniform judge-without-debate panels;
`p_analyst_mean` = secondary. The gates apply to the deployed `p_hybrid` panel; the hybrid question is answered
by the encompassing test on `p_judge`.

| Gate | Floor |
|---|---|
| Residualized weekly rank IC of `p_hybrid` (controls: vol_ewma20, ret_4w, dvol_30d), Newey-West lag 4 | t ≥ 2.0 |
| Brier skill of `p_hybrid` after walk-forward logistic recalibration (training weeks < t, first 52 weeks training only) | > 0 |
| Forecast encompassing: Fama–MacBeth weekly regression of the residualized return rank on residualized `p_quant` rank and `p_judge` rank; NW-t of the mean `p_judge` coefficient | t ≥ 2.0 |
| Sub-periods (2022, 2023, 2024) | same sign of mean IC in ≥ 2 of 3 |

Reported, not gated (design review finding 3: with probability sd ≈ 0.05 a slope near 1 would require an IC
far above the detection floor, so the slope measures dispersion, not skill): raw Brier skill, weekly-centered
Brier skill, Cox calibration intercept and slope (logistic regression of the outcome on logit p), quintile
slope, `p_judge` and `p_quant` IC side by side, mean and sd of the interpreter's weight.

Portfolio gates (only if all forecast gates pass): the rule-twin book keyed by symbol is primary
(score (p−0.5)/vol demeaned to net 0, gross 1, |w| ≤ 0.10; abstentions flat), taker costs 5 bp per side plus
realized funding, net SR ≥ 0.8, dual-family placebo (shuffled dates, shuffled assets) p ≤ 0.05, DSR at the
declared trial count (1 configuration; ablations are descriptive). Books with `p_judge` (LLM-only), `p_judge_nd`
and the confidence-weighted variant are reported alongside.

Paired debate contrast (reported): for the 12 randomly debated assets per week, Δ rank IC and the mean absolute
shift between `p_judge_debate` and `p_judge_nd` (≈ 1,870 pairs over 156 weeks).

Mechanical validity (reported, computed from outputs at no cost): cited-item existence rate per role (≥ 0.98
expected), number-grounding rate of evidence bullets, abstention rate, schema-valid rate.

## 6. Ablations (10% stratified subsample, descriptive, no gate)
Single-call baseline (judge on the dossier, no analysts, no debate; ≈ $16); leave-one-analyst-out (3; analysts
now receive disjoint dossier slices, so this is informative); quant section hidden from the interpreter too
(pure LLM arm; ≈ $25); thinking enabled for analysts and debaters (≈ $50; paired ΔIC, citation validity, share of
changed decisions); contested instead of random debate selection; named vs anonymized dossiers; text-free
(numeric only); Flash in all roles; LLM portfolio manager as an overlay with week-unique ids (violation rate
reported); Claude Opus 5.5 in judgment roles (optional, ≤ $120); V3.2 chronological control on 2025-12 → 2026-12.
The former "no debate" ablation is replaced by the paired contrast in §5.

## 6a. Execution order and budget truncation (declared before the freeze)
- Exposed before the freeze (disclosed, cached, not gate-computed): pilot weeks 2022-01-07 and 2022-01-14 and the
  smoke week 2022-09-30 on earlier builder/agent versions; the agents v2.4 live check 2024-12-27 and the descriptive
  preview weeks 2022-05-13, 2022-11-11, 2024-06-28 on v2.8 (research/multiagent-v2/preview_4weeks.json).
- Weeks are processed newest-first (2024-12-27 backwards to 2022-01-07). The run stops only when the registered
  spend cap is reached or the window is complete; no interim gate value is computed or inspected before the stop.
- If the cap stops the run early, all gates in §5 are evaluated on the completed contiguous window and the number
  of completed weeks is disclosed; the sub-period gate then applies to the years present. Detectable IC at t ≥ 2
  is about 0.036 for 52 weeks, 0.026 for 104, 0.021 for 156.

## 7. Stop rules, budget, attribution
- One configuration; prompts, schemas, builder version and model pins frozen at registration; any change after
  the first dev call is a new charter.
- Spend cap: **$140** for the dev run (funded credit at the freeze; agents v2.4 measured $2.22–2.45 per week on four
  weeks). Under the newest-first rule of §6a this covers about 57 new weeks plus the 4 cached preview weeks, i.e. all
  52 weeks of 2024 and roughly the last 9 weeks of 2023; the older weeks of the manifest stay frozen and unexposed and
  may be run under a separately registered continuation if funded later. Flash typing and the probe sample are
  separate (≈ $10); ablations (§6, ≈ $130) are deferred until funded. Realized funding (Binance public history) is
  charged to the rule-twin book.
- Family: `llm-multiagent-v2` (new mechanism: dossier-fed debate on anonymized cross-section), attempt budget 6,
  prior attempts 0. The legacy multi-agent cells (THESIS §23, §48) are a different mechanism (tool-fetching
  agents on named daily BTC/ETH) and are cited as history.
- Disclosures: Wayback capture survivorship (only archived pages are retrievable; coverage differs by outlet and
  year); Reddit deletions; DefiLlama and CoinMetrics daily series carry publication slack (values dated day D may
  have been revised after D; treated as available at D+1); delisting weeks booked at the last traded close and
  flagged; market-cap rank covers only 24–48 % of the universe (CoinMetrics community; none after mid-2025), so
  the size control is 30-day dollar volume and the card shows a market-cap bucket only where available; asset
  categories come from present-day CoinGecko labels (stable attribute, not point-in-time); cards end 2026-06-26;
  model cutoff unknown
  (release-date bound 2026-04-24); dev window is pre-release. Anonymization removes names, dates and exact
  figures but does not prevent content-based recognition of well-known assets (pilot 52%); leakage is
  therefore MEASURED, not assumed absent: identified-vs-non-identified subsets, named-vs-anonymized ablation,
  and the Sealed-B post-release comparison together bound it.
