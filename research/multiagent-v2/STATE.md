# multiagent-v2 — Phase 1 state (dossier builder)

Plan: `docs/superpowers/specs/2026-11-08-multiagent-v2-analysis-and-plan.md`. Branch `feature/multiagent-v2-dossier`.
Runtime: minimal `.venv` (pandas, pyarrow, requests, python-dotenv, trafilatura, warcio, datasketch, pytest);
run scripts with `PYTHONPATH=. .venv/bin/python scripts/<name>.py`. Key: `OPENROUTER_API_KEY` in `~/.secrets/openrouter.env`.

## Components (all unit-tested, `tests/research/test_dossier_*.py`)
- `tradingagents/dossier/universe.py` — weekly top-N by `dvol_30d` from `data/llm_rank_xs/cards.parquet` (2021-01 → 2026-06-26; top-50 over 2022-01→2024-12 = 7,800 asset-weeks, 222 symbols).
- `store.py` — bitemporal Parquet text store `data/dossier/text/<source>/<yyyy>/<mm>.parquet`; earliest capture wins; PIT query.
- `wayback.py` + `scripts/dossier_news_discover.py` / `dossier_news_fetch.py` — CoinDesk, Cointelegraph, The Block via Wayback CDX (first capture = as_of) and raw capture fetch at 1 req/3.5 s; trafilatura text + publication date. Common Crawl index found too sparse (0–668 records per crawl).
- `reddit.py` + `scripts/dossier_reddit_fetch.py` — Arctic Shift posts (r/CryptoCurrency, r/Bitcoin, r/ethereum); as_of = created; 87% of bodies empty (link posts).
- `entities.py` — dictionary from CoinGecko top-1000 + curated aliases/synonym groups; linker with salience.
- `anonymizer.py` — Masker v2: role tokens per channel, relative dates, year-less dates resolved to nearest occurrence, price levels masked, verification pass.
- `numeric_card.py` — relative-only numeric block + indexed weekly price path.
- `llm_text.py` — DeepSeek V4.1-Flash (Baidu fp8) typing {price_recap, event, analysis_opinion, promotional, unrelated} + anonymized 2-sentence summary + novelty; disk cache; smoke 3 items $0.0003.
- `quant_forecast.py` — walk-forward cross-sectional ridge (52-week burn-in) with trailing 26-week calibration record.
- `builder.py` + `scripts/dossier_build.py` — assembles dossier text (numeric → text → linking → masking → typing → selection within ~9K tokens → verify → hash) to `data/dossier/dossiers/<friday>/<symbol>.json`.
- `or_client.py` — generic pinned structured-output client (roles pro/flash/chrono); `scripts/dossier_reid_probe.py` — re-identification probe.

## Jobs
- 2026-11-08 discovery (`/tmp/dossier_discover.log`) and Reddit ingest (`/tmp/dossier_reddit.log`) started in background.
- Fetch worker to start after discovery completes: `scripts/dossier_news_fetch.py --start 2022-01 --end 2024-12` first (dev window), then later months.

## Open
- Macro calendar block (FOMC/CPI) not yet in the dossier.
- Cards end 2026-06-26: Sealed-B / forward need card rebuild from Binance public funding + klines (week 5).
- Alpaca/Benzinga store lives on the laptop; sync when available (`data/sentiment/alpaca`).

## Phase 2 scaffolding (written 2026-11-08, ahead of schedule; awaits dossiers)
- `tradingagents/agents_v2/{schemas,roles,graph,runner,evaluate}.py` + `scripts/agents_run.py`: three analysts
  (market, fundamental, news) + forecast interpreter; debate in both orders with one rebuttal each; judge per
  order, probabilities averaged; debate only for the 20 most contested/convinced aliases per week, analysts' mean
  probability for the rest; weekly PM with constraint validation and a deterministic rule twin as fallback and
  baseline; results cached per (dossier sha, config sha) in `data/agents_v2/runs/<friday>/`.
- Evaluation: residualized weekly rank IC (controls vol, 4w momentum, size), Newey-West t, Brier skill vs 0.5,
  calibration slope (`agents_v2/evaluate.py`).
- Target definition: P(asset 7-day return > universe median return), decision Saturday 00:00 UTC after the Friday card.

## 2026-11-08 evening — pilot findings on Q1-2022 dossiers (builder v2.3)
- Audit (145 dossiers): 93% with shown items, median 9 items, noise share 27%, 0 leaks by dictionary verification.
- **Re-identification probe FAIL**: DeepSeek V4-Pro (non-thinking, StreamLake route because Baidu returned 502s)
  names the asset in 81/100 anonymized dossiers (chance 1.9%) and the month within ±6 months in 81/100.
  Name masking is insufficient: content (project-specific events, partners, products, price-path shape)
  identifies the asset. Per-section probes (numeric-only, text-only) running to locate the channel.
- Consequence for the plan: §5 anonymization must be hardened (generic rewriting of news summaries,
  removal of non-dictionary proper nouns, coarser numeric rendering) and re-probed; otherwise pre-release
  windows cannot be claimed leakage-controlled and Sealed-B carries the whole evidential weight.

## 2026-11-08 late — hardening result (builder v2.4) and the leakage-measurement decision
- v2.4 (de-identified generic summaries + proper-noun scrub + coarse numeric profile) cut re-identification
  from 81% to 52% (text-only 75% → 50%); month within ±6 months 81% → 69%. Numeric-only stays ~7%.
- Residual identification comes from what the asset *is* and *does* (governance-reward mechanics, "NFT creature
  battling game", ecosystem relations), i.e. the information the agents need. Further masking would remove the
  signal itself. Conclusion for the thesis: anonymization removes name priors and dates but cannot prevent a
  knowledgeable model from recognizing well-known assets from content.
- Decision: keep v2.4; treat re-identification as a MEASURED covariate, not a solved problem. The probe runs on
  every dev dossier (`dossier_reid_probe.py --all`, ≈ $1 per 7,800) and writes `data/dossier/reid_flags.parquet`;
  forecast skill is then reported for identified vs non-identified dossiers (and named vs anonymized, and
  Sealed-B post-release). A skill gap concentrated in identified dossiers is the memorization signature.

## 2026-11-09 01:30 UTC — pilot result and credit stop
- Pilot week 2022-01-07 (config v2.2, 20 debates via CLI default, now 12): 0 failed, order-swap Spearman 0.906,
  mean |Δp| 0.017, abstain 4%, p mean 0.46 sd 0.045, $2.27/week (6.6 calls per asset-week), 11 min/week.
  Repeat-agreement probe not run (credits). Week 2 discarded (402 errors mid-run).
- OpenRouter account credit ($10) exhausted; dossier build stopped at 178 clean dossiers (22 degraded ones removed).
  Fetch and Reddit ingests continue (no LLM). Resume steps in memory/plan; Charter 1 freeze waits for the repeat
  probe and the completed dev dossiers.

## 2026-11-09 06:30 UTC — pilot complete (config v2.2, weeks 2022-01-07 and 2022-01-14 + repeat of week 1)
| Probe | Result | Floor |
|---|---|---|
| Schema/call failures | 0 of 100 asset-weeks | ≤ 1% |
| Order-swap consistency (Spearman, judges) | 0.89 (mean abs gap 0.016) | ≥ 0.75 |
| Repeat agreement (50 assets, identical run) | 0.91 (mean abs gap 0.015) | ≥ 0.85 |
| Abstain share | 2% | reported |
| Cost | $0.041 per asset-week; $0.10 per debated asset; $2.07 per week | — |
| Wall time | ~12 min per week with 12 workers | — |
- Judge probabilities are tight (mean 0.47, sd 0.05, range 0.35–0.58): cautious, bearish lean in a falling market.
- PM prompt violated its constraints in both weeks (weights above cap, gross > 1, net −0.75/−0.55, weights on
  abstentions) → fallback to the rule twin. **Decision:** the deterministic rule twin is the primary portfolio
  constructor; the PM call is kept as an ablation and its violation rate is a reported diagnostic.
- Dev-run budget at measured rates: 156 weeks × $2.07 ≈ $325; plus Flash typing ≈ $10, identification probe ≈ $2,
  ablations ≈ $100, sealed windows ≈ $260. Current balance $6.62 covers the H1-2022 dossier build and the probe only.

## 2026-11-09 09:30 UTC — build performance settings (builder v2.5)
- Flash typing: non-thinking, providers Morph/CoreWeave/DeepInfra selected by throughput, pooled HTTP sessions,
  16 workers; median latency 1.4 s, ≈ $0.00008 per article. Baidu rate-limits concurrent Flash calls (429).
- Masking: one combined alternation pattern per case class (≈17 ms per mask+verify); canonical masked text,
  week rows and entity links cached per document/week.
- The cache key includes the reasoning setting, so the one-time re-typing of the ~7K already-cached articles is
  in progress; dossiers built before this (250, v2.4) stay for probing only. The dev set gets a clean v2.5 rebuild
  into a fresh directory before the Charter 1 freeze.

## 2026-11-09 13:30 UTC — H1-2022 dossier set complete (1,500 dossiers, 30 weeks × top-50; typing $1.53)
Audit: 91% of dossiers have linked text, 88% show items (median 11 shown, 30 retrieved), noise share 28%,
events 36% of retrieved, community posts 37% of shown items, 0 dictionary leaks, median ~1,300 tokens of text.
Identification probe over all 1,500 dossiers running (non-thinking V4-Pro) → `data/dossier/reid_flags.parquet`.

## 2026-11-09 15:00 UTC — identification probe on all 1,500 H1-2022 dossiers (`data/dossier/reid_flags.parquet`)
- Asset identified: 51% overall (chance 1.1%); top-20-by-size assets 65%, smaller assets 40%; majors (BTC, ETH,
  DOGE, XRP, DOT, LINK, AXS, SOL) identified in nearly every week. Month within ±6 months: 89%.
- Cost $3.90 for 1,500 (non-thinking V4-Pro, full dossier text as input); per-dossier flags saved for the
  identified-subset analysis in Charter 1. Credit left ≈ $0.6: LLM steps paused again until top-up.

## 2026-11-09 17:30 UTC — Reddit ingest complete
1,118,556 posts stored (r/CryptoCurrency, r/Bitcoin, r/ethereum; 1,772 days each, 2022-01-01 → 2026-11-07;
2 zero-post days), 215 MB. Bodies are empty for ~87% (link posts/removed); titles carry the signal.
News fetch at 24,214 of ~74,000 URLs, ~1,260/h after overlapping requests; ETA ≈ 2026-11-11.

## 2026-11-10 — pre-run audit, batch 2 (agents/runner side)
- Reviewer findings C1–C2, M1–M9 all fixed (see audit doc §E). Batch 1 = 9235ce11a (dossier side, builder v2.6).
- Batch 2: SpendCapError + newest-first stop-at-cap in llm_v2c1_run.py; rule twin net-neutral (iterative demean/clip);
  uniform judge panel for non-debated assets (judge_all) + analyst-mean secondary panel; per-asset results persisted
  immediately; vol fallback = week median; runs dir per experiment; config_sha covers PINS/N_DEBATE/roles/temperature;
  kline digest verified at run time; forward_returns keeps delisting weeks (last close, flagged); optional funding cost;
  prompts allow full probability range; --dossiers flags on manifest/probe/audit. Tests: 12 agents/quant + 36 dossier pass.
- Cost: judge-all adds ≈ $0.5–0.8/week → dev run ≈ $410–450; cap $400 truncates oldest weeks per §6a.
- Wayback fetch (newest-first) at 27.5K/74K ledger rows, ~1,440/h; rebuild waits for it.
- Live smoke of the fixed runner (2022-09-30, scratch dir): cap path stops correctly; full week 50/12/38, 0 failed,
  $2.48, 15.3 min; rule twin net 0, gross 1; p compressed (0.35–0.55). 156 weeks ≈ $387.
- Realized funding fetcher + realized_funding() + book with/without funding wired into llm_v2c1_run.py.

## 2026-11-10 — v2.6 pilot build, December 2024 (data/dossier/dossiers_v26, 4 weeks)
- 200 dossiers, $0.33 Flash typing, 25 with no shown items (87.5 % with items), 0 leaked names, 0 exact duplicates,
  0 residual role tokens, 0 year literals; median 10 items shown, tokens ≈ 1.2K.
- Identification probe (60 sampled, V4-Pro non-thinking, $0.18): asset 57 %, month within 6 months 97 %.
  The late-2024 rally is recognizable from the price path alone; this is the measured covariate, not a defect.
- Coverage gaps found: market-cap rank present for only 24–48 % of the top-50 (none after mid-2025; CoinMetrics
  community panel), DefiLlama categories for ~40 %. CoinGecko historical market cap is not free beyond 365 days.
  Decisions: size control in the evaluation = 30-day dollar volume (100 % coverage) instead of the half-empty
  market-cap rank; categories filled from CoinGecko labels (stable attribute, present label used for all weeks,
  disclosed) via scripts/dossier_categories_fetch.py -> data/dossier/categories.json; unlock line reads
  "unavailable" instead of "n/a%". The Charter 1 rebuild uses these.
- Categories: CoinGecko labels for 281/345 universe symbols (64 ambiguous ids → unknown); family mapping ignores
  ecosystem/portfolio/index labels and matches by family priority (meme before network). Distribution: network 118,
  DeFi 65, unknown 64, meme 35, AI 21, gaming/NFT 19, other 11, misc 12. data/dossier/categories.json committed.

## 2026-11-09 19:30 UTC — check-in
- Wayback fetch alive, newest-first pass 11,700/47,502 (~1,400/h); ledger 38,306 rows. Fully fetched months:
  2022-01→2022-11 (earlier oldest-first pass) and 2024-07→2024-12; remaining 2022-12→2024-06 ≈ 26 h.
- Builder bumped to v2.7 (category fallback + unlock wording); the December v2.6 pilot directory was cleared so the
  Charter 1 set has one builder version. Rebuild running (log /tmp/build_v27_a.log): Fridays 2024-08-02→2024-12-27
  (30-day lookback fully fetched), then 2022-01-07→2022-11-25; est. ≈ $6 Flash typing.
- OpenRouter: $45 total credits, $23.46 used → $21.54 available.

## 2026-11-10 02:35 UTC — check-in
- Rebuild batch A complete (00:40 UTC): 3,450 v2.7 dossiers, 69 weeks (2024-08-02→12-27, 2022-01-07→11-25), $2.66;
  audit: 0 leaks / 0 duplicates / 0 role-token defects / 0 year literals; 83 % with shown items; category known 95 %.
- Fetch 21,800/47,502 (~1,416/h); 2024-02→2024-06 now fully fetched (2024-01 at 80 %, 2022-12 at 16 %).
- Batch B started detached (log /tmp/build_v27_b.log): Fridays 2024-03-01→2024-07-26 (22 weeks, ≈1,100 dossiers).
- OpenRouter $45 total, $26.12 used → $18.88 available.

## 2026-11-10 05:10 UTC — design review of the agent framework (independent reviewer, read-only) → agents v2.4
- 12 findings; design-critical: (1) dossier aliases collide across a week (50 assets, 20–22 aliases) and the
  runner/book were keyed by alias → every portfolio number of the smoke/pilot was corrupt (forecast gates were
  keyed by symbol and unaffected); (2) "system IC ≥ quant IC" gate mis-specified for a hybrid whose LLM discounts
  a 0.09-IC signal; (3) calibration-slope gate is a dispersion test under compression and ties.
- Implemented (commit 14d192547, 54 tests): symbol-keyed runner/book; analysts get physically different dossier
  slices (market n2/n3/n4/n7/n8 + calendar; fundamental n1/n5/n6 + event-typed items; news text + calendar); quant
  section only to the forecast interpreter; debaters/judges see the dossier without it → p_judge = LLM-only;
  deployed p_hybrid = sigmoid(w·logit(q) + (1−w)·logit(p_judge)); judge-without-debate for ALL assets (uniform
  panel) + seeded-random 12-asset debate with its own judges (paired within-asset contrast); symmetric two-turn
  debate (−2 calls per order); confidence out of the primary book; abstain → p 0.5, weight 0; PM dropped from the
  main run (ablation with week-unique ids C01..); citation-existence and number-grounding rates per role;
  evaluation adds encompassing (Fama–MacBeth, NW t), Cox calibration, walk-forward recalibrated Brier, centered Brier.
- Builder v2.8: percentiles rendered "pct K, higher than K% of the universe"; COMMON defines pct and states that
  half the universe beats the median; quant forecasts computed over the full card history so the trailing record
  never resets at a build-batch boundary. Batch A+B (91 weeks, 4,550 dossiers, v2.7) deleted and rebuilding as
  v2.8 detached (log /tmp/build_v28_a.log; typing cached).
- Cost per week changes: +12 paired judge calls, −4 debate calls per debated asset, −1 PM call → ≈ $2.5/week.
- Fetch 25,400/47,502 at 05:03 UTC (~15.5 h left).
- Live check agents v2.4 on v2.8 week 2024-12-27: 322 calls, $2.45, 13.8 min, 0 failed; citations exist 1.00 all roles;
  analyst triples all distinct; judge-nd mean 0.447 sd 0.056; interpreter weight mean 0.48; hybrid sd 0.229 (ridge
  dominates); paired debate shift 0.028; book 50 symbols net 0 gross 1. agents_run.py gained --dossiers.

## 2026-11-10 09:45 UTC — check-in
- v2.8 rebuild of the 91 weeks complete (4,550 dossiers; audit: 0 leaks/dups/role-token defects/year literals;
  84 % with shown items; quant record short only during the 2022-H1 burn-in, monotonic, no batch resets).
- Fetch 32,000/47,502 (~1,420/h, ≈ 11 h left); 2023-08→2024-02 now fully fetched (2023-12 at 99 %, residual = fetch
  failures ≈ 1.4 % overall, not retried).
- Batch C started detached (log /tmp/build_v28_b.log): Fridays 2023-09-01→2024-02-23 (26 weeks).
- OpenRouter $45 total, $30.09 used → $14.91 available (live check $2.45 + rebuild typing).

## 2026-11-10 ~12:30 UTC — descriptive preview, 4 weeks (NOT a gate computation; weeks chosen as regime extremes)
- Weeks 2022-05-13 (LUNA), 2022-11-11 (FTX), 2024-06-28, 2024-12-27; 200 asset-weeks; $6.83 for the three new weeks;
  cache data/agents_v2/runs/charter1-preview (agents v2.4 config sha; reused by the registered run).
- Residualized weekly IC (quant / LLM-only judge / hybrid / deployed / analyst mean): mean −0.095 / +0.118 / −0.024 /
  −0.020 / +0.055; the judge is positive in 3 of 4 weeks, the ridge negative in 3 of 4 (its trailing record is +0.09;
  these four weeks are extreme). Hybrid follows the ridge at interpreter weights 0.23–0.62 (mean 0.43).
- Paired debate shift 0.028 (48 pairs); citation existence 1.00; number grounding 0.91; 0 failures; 0 delisted rows.
- Rule-twin book (deployed hybrid) weekly net: −2.98, −0.67, +4.76, −2.91 %.
- Reading: suggestive that the LLM-only panel carries information the ridge does not (encompassing t on 4 weeks is not
  interpretable); no change to prompts or design follows from this (pre-registration discipline). File:
  research/multiagent-v2/preview_4weeks.json.
- Credit after preview: ≈ $153.9 available. Registered run cap stays $140.

## 2026-11-10 15:45 UTC — check-in
- 117 weeks built (batch C done). Fetch 40,600/47,502 (~1,420/h, ≈ 5 h left); 2023-04→2023-08 fetched (2023-05 at 98 %).
- Batch D started detached (log /tmp/build_v28_c.log): Fridays 2023-05-05→2023-08-25 (17 weeks). Remaining after the
  fetch: 2022-12-02→2023-04-28 (22 weeks).
- OpenRouter $195 total, $38.65 used → $156.35 available.

## 2026-11-11 — FREEZE of Charter 1 (llm-v2-charter1-20261111)
- All 156 weeks built with builder v2.8 (7,800 dossiers; audit 0 leaks / 0 duplicates / 0 role-token defects /
  0 year literals; 84 % with shown items; noise share of retrieved 0.26). Fetch final: 46,873/47,502 captures.
- Manifest data/agents_v2/charter1/{dossier_manifest,klines_digest,agent_config}.json; agent config agents-v2.4
  sha a97972476be6f5b1…; identification flags from a 20 % stratified probe (data/dossier/reid_flags_v26.parquet).
- Cap $140 (newest-first → ≈ 2024 + late 2023); cache data/agents_v2/runs/charter1-preview reused.
- Run: `llm_v2c1_run.py --registration research/llm-v2-charter1-20261111/gates.json --experiment
  llm-v2c1-dev-run-20261111 --cost-cap 140 --runs-dir data/agents_v2/runs/charter1-preview`, log /tmp/charter1_run.log.
  NO commits/checkouts in this checkout while the run is active.
- Probe sample: 1,560 dossiers (20 % per week), V4-Pro non-thinking, $2.46, 0 failures: asset identified 48.0 %
  (2022 52.5 %, 2023 47.7 %, 2024 43.8 %), month within ±6 months 58.1 %. Balance at freeze ≈ $151.

## 2026-11-11 12:14 UTC — Charter 1 attempt 1 INTERRUPTED (failed receipt); Charter 1b DRAFTED, NOT FROZEN
- System review during the run (`docs/superpowers/specs/2026-11-11-multiagent-v2-system-review.md`): the evaluation
  tail could not complete. `write_json` rejects NaN and the identified-subset block always yields NaN (ten flagged
  assets per week), so the attempt would have spent the cap and failed after writing `forecasts.json` (B1). Further
  evaluation defects B6, B8, B9, B10, B11, B13 and the run-loop failure path A14. Source files are hash-checked at
  every write, so nothing could be patched in the running attempt.
- Run interrupted by SIGINT at 12:14 UTC. Receipt `research_runs/llm-v2c1-dev-run-20261111/failed.json`
  (KeyboardInterrupt), log copy `research/multiagent-v2/charter1_attempt1_run_log.txt`. No output written, no
  forecast joined with a forward return. Family `llm-multiagent-v2`: 1 of 6 attempts used.
- Cache `data/agents_v2/runs/charter1-preview`: 61 complete weeks 2024-12-27 → 2023-11-03 (3,050 asset-weeks) and
  part of 2023-10-27 (50 assets without debate, 2 of 12 debates). Spend: client tally $127.49 at the last complete
  week + $1.58 cached calls of the interrupted week = $129.07 recorded. Account balance $21.16.
- Decisions 2026-11-11: stop the run; Path A (same dossiers, agents and cached calls, corrected evaluation tail);
  the three registered gate families and thresholds stay, only defects are fixed; no top-up.
- Charter 1b draft: `docs/superpowers/specs/2026-11-11-llm-v2-charter1b-dev-run-charter.md` (marked DRAFT, three
  open decisions in §9). Code: `tradingagents/agents_v2/charter1b.py` (cache admission, panel assembly, gate
  statistics, verdict by code, `json_safe`), `evaluate.py` (sub-period rule, subset-gap estimator with week-block
  bootstrap), `portfolio_eval.py` (funding window on the holding period, funded headline Sharpe, funded placebos
  with +1 correction, probabilistic Sharpe), scripts `llm_v2c1b_{manifest,register,run,dryrun}.py`.
  Manifests `data/agents_v2/charter1b/{cache_manifest,funding_digest}.json` (3,111 cached files pinned by sha256,
  347 funding files).
- Verification: 35 tests in `tests/research/test_agents_v2*.py` pass, including the lifecycle run end to end in a
  temporary repository with a stub client. Dry run on the real 61-week forecast panel with SYNTHETIC outcomes
  (`research/multiagent-v2/charter1b_dryrun.json`): noise FAIL, planted signal PASS, zero returns FAIL, three weeks
  FAIL, no descriptive block raised, tail ≈ 90 s. `llm_v2c1b_register.py --date 20261111 --check` validates
  (18 source files, 8 inputs, 6 outputs, 4 cells) and writes nothing.
- To freeze after approval: resolve §9 in the charter and remove the draft marker; commit; then
  `PYTHONPATH=. .venv/bin/python scripts/llm_v2c1b_register.py --date <date>`; commit `gates.json`; run
  `llm_v2c1b_run.py --registration research/llm-v2-charter1b-<date>/gates.json --experiment llm-v2c1b-dev-run-<date>
  --cost-cap 10.43` (or `--cost-cap 0 --no-new-weeks`) at that HEAD. The run is one-shot: it unblinds the dev
  outcomes and consumes attempt 2 of 6. NO commits/checkouts in this checkout while it is active.
- Open: stray `uv` build process PID 48318 in `TradingAgents-onchain-b` (since 2026-10-23) still alive; ending it
  needs a manual `kill 48318`.

## 2026-11-12 02:53 UTC — Charter 1b FROZEN and RUN: verdict FAIL (family attempt 2 of 6)
- Decisions before the freeze (charter §9): the remaining $10.43 under the $140 cap is spent on further weeks;
  the sub-period gate keeps its literal reading (binding with two calendar years); the rebuilt design (review
  Path B, about $94) is not planned and not funded, and the run was not held for it.
- Frozen charter `docs/superpowers/specs/2026-11-11-llm-v2-charter1b-dev-run-charter.md`, registration
  `research/llm-v2-charter1b-20261112/gates.json`, both at `6a3a25ec6`. Run `llm-v2c1b-dev-run-20261112`,
  01:50 → 02:53 UTC, exit 0, `complete.json` with 4 cells, `verify_run` status complete. Log copy
  `research/multiagent-v2/charter1b_run_log.txt`.
- Panel: 66 contiguous weeks 2024-12-27 → 2023-09-29 (61 frozen from the cache, 5 new: 2023-10-27 completed with
  60 calls, 2023-10-20 to 2023-09-29 with 322 calls each, 0 failed assets). 3,300 asset-weeks, 233 abstentions,
  4 failed, 791 debated, 2 delisted rows. Stopped by the spend cap inside week 2023-09-22 (discarded).
- Spend: $10.548 in this run (cap $10.43, overshoot $0.118 inside the declared $0.15 allowance), 1,519 calls.
  Cumulative recorded $139.616 of $140. Account balance after the run $10.61.
- VERDICT by code (`outputs/verdict.json`): FAIL. Failed gates: hybrid IC, encompassing.
  | gate | rule | value | result |
  |---|---|---|---|
  | hybrid residual rank IC, NW(4) t | ≥ 2.0 | 0.813 (mean IC 0.0230, hit rate 0.530) | fail |
  | encompassing, t of `p_judge` next to `p_quant` | ≥ 2.0 | −0.018 (beta −0.0004) | fail |
  | recalibrated Brier skill, 14 test weeks | > 0 | +0.0266 | pass |
  | sub-period sign, 2 years | same sign in 2 | 2023 +0.0451, 2024 +0.0170 | pass |
  Portfolio gates not evaluated (forecast gates failed); descriptive: rule-twin net Sharpe 0.371 (rule ≥ 0.8),
  asset-shuffle p 0.261, date-shuffle p 0.042, PSR vs 0 0.661, max drawdown −19.2 %, 2023 Sharpe −4.14 (14 weeks),
  2024 +1.29 (52 weeks), funding coverage 1.0.
- Descriptive reading (no gate, not tuned on):
  - Quant twin alone IC 0.0176 (t 0.59); LLM-only judge IC 0.0119 (t 0.75); analyst mean IC 0.0302 (t 1.96, hit
    rate 0.591), the strongest single column and below the 2.0 mark without any multiplicity allowance.
  - Debate did not help the judge: paired delta IC −0.0100 (t −0.60), mean absolute shift 0.021 on 791 pairs.
  - Calibration: raw Brier skill of the hybrid −0.055, slope 0.32; the recalibrated pass rests on 14 test weeks and
    was declared weak beforehand (P(pass | no skill) ≈ 0.39).
  - Sensitivities agree: abstentions excluded IC t 1.02, encompassing t −0.25; primary-provider rows (64 weeks) IC
    t 0.61, encompassing t +0.16.
  - Identification: on the flagged rows the judge's IC is +0.039 where the asset was identified and −0.113 where
    not (gap 0.152, week-block bootstrap p 0.044); the quant column shows no such gap (0.028, p 0.72); the
    difference-in-differences is not significant (0.123, p 0.28). Weak evidence that the LLM's ranking depends on
    recognising the asset; one of several descriptive tests.
  - `encompassing_hybrid_vs_quant` (hybrid next to quant, t 2.11) is not the registered LLM test: `p_hybrid`
    contains `p_quant` (Spearman 0.95), so the pair is near-collinear and the registered isolation is `p_judge`.
- Power statement of the charter stands: 80 % power needed IC ≈ 0.054 (encompassing) and ≈ 0.090 (hybrid IC) at
  61 weeks. The FAIL rules out a large LLM contribution; it says little about an IC between 0.02 and 0.05.
- Closed by charter §10: this configuration on this window. No re-run, no re-estimation, no change of estimator.
  Family `llm-multiagent-v2`: 2 of 6 attempts used, four remain and each needs its own charter. Sealed-A and
  Sealed-B untouched. A later rebuild evaluated on these 66 weeks counts as conditioned on these outputs.
- Open: direction after the FAIL (user). Stray `uv` build process PID 48318 still alive; needs a manual
  `kill 48318`.

## 2026-11-12 — direction after the FAIL: reader configuration (Charter 2 DRAFT, nothing frozen, nothing spent)
- Direction (user, 2026-11-12): explore four changes, first the one in which the language model is not the
  forecaster and a fitted model forecasts. The other three: different target, fresher information, direct
  comparison of assets.
- Ledger check done after the four changes were named (it belonged before): direct comparison was largely
  tested (`llm_c3_rank_xs`, `llm_c3p_pair_xs`, t 1.01 on 222 weeks, numeric cards only); the reader idea was
  started as `llm_c1_event_xs` (Aug 2026) and stopped at extraction quality, its forecast value was never
  tested; sentiment as a feature failed for BTC/ETH daily (§33); event-time trading was a no-go; news →
  volatility is untried.
- Draft charter `docs/superpowers/specs/2026-11-12-llm-v2-charter2-reader-charter.md`: two reader agents and
  an adjudicator turn each de-identified summary into a fact record (class, status, direction, materiality,
  verbatim evidence); code aggregates eight asset-week features; the walk-forward ridge of the quant model
  forecasts with and without them. Primary gate: encompassing t of the text score next to the quant forecast
  ≥ 2.0 on 104 test weeks (2023-01-06 → 2024-12-27), positive in both years. PASS only licenses the sealed
  windows. Proposed cap $7.00 from the $10.61 balance.
- Built at zero cost: `tradingagents/reader/items.py` (uncapped reading list, `FastLinker` with identical
  output to `Linker` at about 14× the speed), `scripts/reader_items_build.py`, `scripts/reader_coverage_preview.py`,
  `tests/research/test_reader_items.py` (3 tests). Outputs under `data/reader/` (git-ignored): `items.parquet`
  520,434 rows over 353,739 documents, `docs.parquet` 101,099 typed documents (0 leaks), `work_list.parquet`
  50,362 documents and 58,958 records, `coverage_panel.parquet`.
- Coverage on the 7,800 asset-weeks (no outcome joined): any linked item in 7 days 78.2 %; a readable item in
  7 days 55.4 % (median 1), in 30 days 76.8 % (median 5); 16 to 39 assets per week with a readable 7-day item.
  The 25-item dossier cap of Charter 1b was binding in 26 % of asset-weeks; the reading list has no cap for
  news. Community posts stay on the 25-newest rule (96,431 of 96,433 such posts are typed); typing the other
  192,848 primary posts (BTC 153,345, ETH 35,876) would cost about $25 and is not proposed.
- Cost estimate: one reader pass $2.13; two readers plus adjudication $4.9 to $6.0. Confirmation on the sealed
  windows (only after a PASS) about $12, top-up about $10 at that point.
- Not done and not allowed before approval: reader prompts and client code beyond the draft wording, pilot,
  registration, freeze, any paid call, any outcome join.
- Open (user): pipeline order versus the assignment wording, cap $7.00, attempt 3 of 6, forecaster class,
  community-text rule. Stray `uv` process PID 48318 still needs a manual `kill 48318`.

## 2026-11-12 — Charter 2: five decisions taken, stage R0 complete (draft revision 2, nothing frozen, nothing spent)
- Decisions (user, 2026-11-12) on the five open points of the first draft: (1) pipeline order accepted, the
  thesis presents Charter 1b as the literal configuration and the reader configuration as the corrected one;
  (2) the available balance ($10.61) may be spent and is topped up if needed; (3) attempt 3 of 6; (4) boosted
  trees are added as descriptive columns, the gate stays on the ridge; (5) the 25-newest community rule is kept.
- R0 code (no paid call, no real outcome): `tradingagents/reader/{reading,schema,extract,consensus,features,
  model,charter2}.py`, `scripts/reader_extract.py` (pilot and full extraction), `scripts/reader_charter2_register.py`,
  `scripts/reader_charter2_run.py`, `scripts/reader_charter2_null_gate.py`. Tests: 102 offline tests in
  `tests/research/test_reader_{items,extract,charter2}.py`, among them a dry run of the whole registered run on
  synthetic inputs and a test that the charter quotes the instructions, the prompt hash and the constants of
  the code. The earlier suites (dossier, agents v2) still pass (72).
- Prompt hash `7cf96c2fa147208c2e22e9efb7439caa3e216ba066f382e161c26de26721a07f`. Model pin
  `deepseek/deepseek-v4.1-flash`, Baidu and DeepInfra, fp8, reasoning disabled, temperature 0.
- Corrected figures (final reading rule on the registered weekly top 50): work list 48,261 documents and
  53,330 records (the first draft counted 50,362 and 58,958 before the universe restriction); a read item in
  the last 7 days in 55.1 % of asset-weeks, in 30 days in 76.7 %. Cost estimate of the extraction $5.9 to
  $6.8. Spend limit of the extraction `--cost-cap 10.00`, cap of the charter $10.61.
- Corrected family line: the two attempts used in `llm-multiagent-v2` are Charter 1 (interrupted, failed
  receipt) and Charter 1b (FAIL). Charter 0 belongs to the family `llm-news-event-extraction`.
- Pass rate of the gates on noise (`scripts/reader_charter2_null_gate.py`, synthetic panels, draws in
  `charter2_null_gate.jsonl` and `charter2_null_gate_persistent.jsonl`): 88 of 2,700 draws pass both gates,
  3.26 % (95 % interval 2.6 % to 3.9 %); with persistent features (AR(1) 0.9) 29 of 900, 3.22 %. The nominal
  rate of t ≥ 2.0 is 2.3 %; the 97.5 % quantile of the Newey-West t on 104 weeks under noise is 2.13. The
  threshold stays at 2.0 for comparability with Charter 1b and the rate is stated in the charter (§5,
  Appendix B). An early check on 400 draws had given 1.0 %, a favourable sample.
- Order fixed in the charter: freeze, then extraction (the manifest records the charter hash), then
  registration, pre-flight, claim and the single outcome join. The charter is not edited after the extraction.
- Next: pilot on 300 units (about $0.04), result into §4.1, then the freeze request. Not allowed before
  approval: freeze, full extraction, registration, any outcome join.
- Stray `uv` process PID 48318 still needs a manual `kill 48318`.

## 2026-11-12 — Charter 2 stage R1: pilot PASSED the stop rule ($0.055 spent, nothing frozen, no outcome read)
- `scripts/reader_extract.py --pilot 300 --cost-cap 0.25` at commit `8677b27f0`: 300 units, 339 records, 687
  calls, 1.2 minutes, $0.0546. Report copied to `research/multiagent-v2/charter2_pilot_report.json`; the calls
  are in `data/reader/calls.jsonl` (git-ignored) and are reused by the full extraction.
- Stop rule: evidence grounding 0.981 (minimum 0.95), agreement on direction 0.844 (minimum 0.70). Passed, the
  instructions stay (prompt hash unchanged).
- Other quality: valid readings A 100 %, B 99.7 %; agreement on relevance 0.953, class 0.945, status 0.971,
  materiality within one 1.000; 75.5 % of records agreed, 24.5 % adjudicated, none unresolved; no pair of
  readings with opposite signs (45 of the 48 direction disagreements are the reviewer setting neutral).
- Cost: $0.000182 per unit, 2.29 calls per unit. Per call $0.000057 at DeepInfra (544 calls) and $0.000167 at
  Baidu (143 calls). Projection for 48,261 units: $6.26 DeepInfra alone, $8.78 pilot mix, $18.27 Baidu alone.
  Evidence grounding by provider: DeepInfra 0.992, Baidu 0.930.
- Change after the pilot (cost and evidence grounding only, no outcome): the reader tries DeepInfra first and
  Baidu second (`PROVIDER_ORDER` in `scripts/reader_extract.py`). Same model, weights, quantisation and
  instructions; cache keys do not depend on the provider.
- Charter draft revision 2 now carries the pilot result (§4.1), the measured budget (§8) and the route (§3.2).
- Balance about $10.55. Waiting for the approval of the freeze (R2). After it: freeze commit, extraction with
  `--cost-cap 10.00` (about 3 hours), registration, pre-flight, registered run with the single outcome join.
