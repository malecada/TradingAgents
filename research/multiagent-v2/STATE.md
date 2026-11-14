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

## 2026-11-12 — Charter 2 stage R2: charter FROZEN with approval (byte-final from this commit)

The freeze was approved on 2026-11-12 after the pilot report (provider order changed after the pilot, noise pass
rate of the gates about 3.3 %, expected extraction cost $6.3 under a spend limit of $10.00 were stated in the
request). The draft mark is removed from the title and the status line is changed; nothing else in the charter
changed. 102 offline tests pass on the frozen text. From this commit the charter is not edited: results of the
extraction and of the registered run are recorded here.

Next, in this order: full extraction `scripts/reader_extract.py --cost-cap 10.00` (about 3 hours, no outcome),
registration, pre-flight, registered run with the single outcome join (attempt 3 of 6).

## 2026-11-12 — Charter 2 stage R3a: full extraction COMPLETE ($5.75 spent in total, no outcome read)

Run at commit `6f8b6213b` under the frozen charter (sha256 `0d575313…a537d7`), 13:38 to 15:43 UTC, 124 minutes
with 16 workers, one pass, no stop and no failed unit. Manifest copy:
`research/multiagent-v2/charter2_extraction_manifest.json`.

| Quantity | Value |
|---|---|
| Units (documents) and records | 48,261 and 53,330 |
| Units without a cached call | 0 |
| Calls in the cache, pilot included | 104,254 (A 45,567, B 45,490, J 13,197) |
| Cost, pilot included | $5.749 (limit $10.00) |
| Providers | DeepInfra 104,111, Baidu 143 (all in the pilot) |
| Latency per call | median 1.05 s, 90th percentile 1.53 s |
| Valid reading after the re-read | A 99.89 %, B 99.90 % |
| Evidence grounding, first reads of A and B | 0.988 (A 0.987, B 0.989) |
| Agreement on relevance, class, status | 0.947, 0.941, 0.976 |
| Agreement on direction | 0.799 (48,329 records both about the asset) |
| Materiality equal, within one | 0.727, 0.999 |
| Records agreed, adjudicated, unresolved | 72.50 %, 27.46 %, 0.03 % (18 records) |
| Documents with an adjudication | 28.6 % |
| Final relevance | subject 40,274, side mention 9,378, not about 3,660 |
| Final direction of the subject records | favourable 14,975, neutral 12,432, unfavourable 8,725, mixed 4,142 |
| Final materiality of the subject records | 1: 23,693, 2: 15,300, 3: 1,281 |

- The offline rebuild from the cache equals the stored record table (`reader_extract.py --offline`).
- Hashes: cache `c6bf4c59…55ee87`, record table `dffc450a…a78040`.
- Agreement on direction is lower than in the pilot (0.844) and above the pilot minimum (0.70); the stop rule
  applied to the pilot only and nothing is changed.
- Balance after the extraction about $4.86 of $10.61.

Next: registration, pre-flight, registered run with the single outcome join (attempt 3 of 6).

## 2026-11-12 — Charter 2 stage R3b: registered run COMPLETE, verdict FAIL (family attempt 3 of 6 used)

Registration `research/llm-v2-charter2-20261112/gates.json` (commit `7804af8cc`), pre-flight passed, run
`llm-v2c2-reader-dev-run-20261112` claimed 15:50 UTC and completed 15:55 UTC at source `7804af8cc`, five cells
complete, no fit error, no descriptive error, no missing forward return in the test weeks (5,200 rows, 104
weeks). The forward returns were joined once. Run log: `research/multiagent-v2/charter2_run_log.txt`. Outputs:
`research_runs/llm-v2c2-reader-dev-run-20261112/outputs/`.

| Gate | Value | Rule | Result |
|---|---|---|---|
| G1 text score next to the quant forecast | t 1.39, mean coefficient +0.026 (104 weeks) | t at least 2.0 and coefficient above 0 | fail |
| G2 mean coefficient by year | 2023 +0.011, 2024 +0.042 | above 0 in both years | pass |
| Verdict | | G1 and G2 | **FAIL** |

The verdict is the one in `verdict.json`. No re-run, no re-estimation and no change of estimator on this
window under this charter. FAIL closes the reader configuration for weekly relative returns (charter §5); the
records stay as the input of the target-change charter (§9).

Descriptive results (no gate, no claim):

| Score | Weekly IC on the 104 test weeks | Newey-West t | 2023, 2024 |
|---|---|---|---|
| `p_quant` (registered quant forecast) | 0.021 | 1.07 | 0.021, 0.021 |
| `s_text` (ridge on the 8 text features, the gate score) | 0.028 | 1.78 | 0.016, 0.040 |
| `s_block_a` (attention counts only) | 0.031 | 2.09 | 0.016, 0.045 |
| `s_block_b` (reader judgements only) | 0.012 | 0.93 | 0.012, 0.013 |
| `s_text_class` (no reader judgement of direction) | 0.031 | 2.13 | 0.020, 0.042 |
| `s_quant` (ridge on the card features) | 0.045 | 2.06 | 0.045, 0.045 |
| `s_full` (ridge on card and text features) | 0.043 | 2.14 | 0.039, 0.046 |
| `g_text`, `g_quant`, `g_full` (boosted trees) | 0.035, 0.055, 0.049 | 2.36, 3.39, 3.24 | |

| Comparison | Value |
|---|---|
| Paired IC `s_full − s_quant` | −0.002 (t −0.19) |
| Paired IC `g_full − g_quant` | −0.005 (t −0.44) |
| Paired IC `s_full − p_quant` | +0.022 (t 1.38) |
| Encompassing next to `p_quant`: `s_block_a`, `s_block_b`, `s_text_class` | t 1.55, 0.79, 1.68 |
| Encompassing next to `p_quant`: `s_full`, `g_text`, `g_full` | t 1.57, 1.76, 2.56 |
| Encompassing next to the fitted twin: `s_text` with `s_quant`, `g_text` with `g_quant` | t 1.21, 1.61 |
| Cross-fit text score next to `p_quant` (156 weeks, uses later weeks) | t 3.04 |
| Book of `s_text`, after costs and funding | Sharpe 0.79 (2023 −0.58, 2024 +1.86), asset-shuffle p 0.058 |
| Books of `s_quant`, `s_full`, `g_full`, `p_quant` | Sharpe 0.17, 0.21, 0.13, 0.01 |
| Identified against not identified assets, `s_text` IC | 0.013 against 0.029, gap p 0.81 |

Reading of the result, as far as the registered outputs carry it:
- The text score has a positive coefficient in both years and an IC of 0.028, which is in the range where the
  charter states a pass rate of about one run in five (§5, power). The gate is not met and nothing is claimed.
- What relation there is sits in the attention counts (block A: number of items, built by code from the
  reading list), not in the judgements of the reader agents (block B: IC 0.012, t 0.93). The class-only
  variant, which drops the readers' direction, does no worse than the full text score.
- The mean ridge coefficient of `unfav_7d` is positive in every test week (+0.048 in `s_text`, +0.114 in
  block B alone), the same sign as `attn_7d` (+0.085) and `tone_7d` (+0.008). The fitted model uses favourable
  and unfavourable counts alike as more attention; the direction read by the agents does not separate winners
  from losers.
- Next to a model fitted on the card features the text adds nothing: `s_full − s_quant` is −0.002 and
  `g_full − g_quant` is −0.005 in weekly IC.
- A side result outside the question of this charter: the ridge and the boosted trees fitted on the card
  features have twice the IC of the registered `p_quant` (0.045 and 0.055 against 0.021). The window is
  exposed and these fits were not gated, so this is a lead for the quant side and no finding.

Checks on the negative result: the planted-signal test of the gate code passes (test
`test_planted_signal_passes_and_a_noise_draw_fails`), the pre-flight rehearsed the whole evaluation on synthetic outcomes before the
claim, the record table equals the rebuild from the registered cache, and a record about the asset as subject exists within 7 days
for 48 % of the test asset-weeks and within 30 days for 72 % (the preview counted any readable item: 55 % and
77 %).

Budget: $5.75 spent under Charter 2, balance about $4.86. Family `llm-multiagent-v2`: 3 of 6 attempts used.
Sealed-A and Sealed-B untouched. No run active.

## Charter 3 (target change: next-week volatility): draft, not frozen (2026-11-13)

Charter draft: `docs/superpowers/specs/2026-11-13-llm-v2-charter3-volatility-charter.md`. Attempt 4 of 6 when
registered. Nothing is registered, no attempt is claimed, and no feature built from the reader records has been
joined with a volatility outcome of the window. The freeze needs the user's approval; the open decisions are in
§10 of the draft.

Design in short:
- Same 53,330 records, no model call, cap $0.
- Target: realised variance of the next seven days, ranked within the week. Tail measures are descriptive.
- Question: do the six reader features (block V) carry information beyond 12 price-history controls and 2
  attention counts? Attention counts need no reader agent and carried the return relation of Charter 2.
- Gate: weekly partial correlation of a walk-forward ridge score with the target residual on 104 test weeks.
  G1: Newey-West t at least 2.0 and mean above 0. G2: mean above 0 in 2023 and in 2024. A pass is read as
  "visible" at a mean of at least 0.07 and as "thin" below (no gate).

Stage V0 is complete (code, 79 offline tests, synthetic dry run, pass rate and power on synthetic targets). It
changed the gate before any outcome was opened:
- The first design removed the controls by a linear regression within the week. On synthetic targets without
  reader information, built on the real decision-time regressors, it passed in 4.8 % to 14.7 % of 2,000 draws
  per cell. About 3 % is expected of an unbiased gate of this form.
- Two channels: the reader features and the target can both be curved functions of the controls, and an
  unseen persistent part of an asset's volatility lets the score learn the asset.
- Registered design: controls removed in two steps on both sides. First a flexible fit on earlier weeks only
  (boosted trees for the features, a quadratic surface for the target), then the linear step within the week.

| Synthetic target, 2,000 draws per cell | First design | Registered design |
|---|---|---|
| linear, no persistence | 4.80 % | 2.60 % |
| curved, no persistence | 11.00 % | 2.75 % |
| linear, persistence 0.3 | 6.70 % | 4.30 % |
| curved, persistence 0.3 | 12.20 % | 4.95 % |
| curved, persistence 0.6 | 14.65 % | 7.50 % |

- Persistence is not removed. The run reports the autocorrelation of the target residual, which states the row
  that applies. Bars of 2021 (before the window, price only) show neither persistence nor curvature.
- Power of the registered design (1,000 draws per cell): 20 % at a mean weekly partial correlation of 0.017,
  48 % at 0.031, 78 % at 0.045, 99 % at 0.074. A FAIL excludes a visible relation and not a thin one.
- The first design stays in the outputs as the descriptive score `s_reader_lin` with no weight in the verdict.

Evidence: draws in `research/multiagent-v2/charter3_null_gate*.jsonl`, design checks in
`research/multiagent-v2/charter3_design/` (README there). Check of the registration builder
(`scripts/reader_charter3_register.py --check --date 20261113`): 41 source files, 7 inputs, nothing written.

Next: freeze approval by the user, then freeze (status line), commit, registration, pre-flight, one registered
run. Family `llm-multiagent-v2` stays at 3 of 6 attempts until the claim. Sealed-A and Sealed-B untouched. No
run active.

## Charter 3: frozen (2026-11-13, V1)

Freeze approved by the user on the draft ("Go ahead"), with the implemented option on all six points of §10:
gate on the reader block beyond price history and attention counts, two-step removal of the controls,
threshold t at least 2.0, size as a reading rule at 0.07, realised variance as the gate target, attempt 4 of 6.

- The draft mark is removed and the status line changed. The document is byte-final from this commit:
  sha256 `ffdfeda7bc61bd4d0a98e8dd0555fc4b0d46401844db13f15228859460c330e4`.
- Results of the run go into this file, never into the charter.
- At the freeze nothing is registered, no attempt is claimed and no text feature has been joined with a
  volatility outcome. 79 offline tests pass on the frozen text.

## Charter 3 run: complete, verdict FAIL (2026-11-13)

Registration `research/llm-v2-charter3-20261113/gates.json` (commit c8746c15c), experiment
`llm-v2c3-volatility-dev-run-20261113`, attempt 4 of 6. Pre-flight passed at 07:07 UTC (inputs verified,
records rebuilt from the cache, rehearsal on synthetic targets). Run started 07:09 UTC, claim 07:11 UTC,
complete 07:15 UTC. One outcome join, no model call. Outputs in
`research_runs/llm-v2c3-volatility-dev-run-20261113/outputs/`, log in `charter3_run_log.txt`.

| Gate | Value | Rule | Result |
|---|---|---|---|
| G1 weekly partial correlation of `s_reader` with `e_reader` | mean −0.009, t −0.72 (104 weeks) | t at least 2.0 and mean above 0 | fail |
| G2 mean by year | 2023 −0.030, 2024 +0.012 | above 0 in both years | fail |
| Verdict | | G1 and G2 | **FAIL** |

The verdict is the one in `verdict.json`. No re-run, no re-estimation and no change of estimator on this
window under this charter. FAIL closes weekly relative volatility from the reader records (charter §5). The
records stay as an input of the two remaining changes (§9).

Descriptive results (no gate, no claim):

| Partial score | Mean weekly partial correlation | Newey-West t, lag 4 and lag 12 | 2023, 2024 |
|---|---|---|---|
| `s_reader` (reader block beyond history and attention, the gate score) | −0.009 | −0.72, −0.73 | −0.030, +0.012 |
| `s_reader_lin` (same, first design: within-week step only) | +0.016 | 1.13, 1.09 | −0.005, +0.037 |
| `s_reader_sq` (same, squares of the bar history in the within-week step) | −0.014 | −0.92, −0.99 | −0.029, +0.001 |
| `s_reader_hist` (reader block beyond history, attention not controlled) | +0.041 | 3.24, 3.94 | +0.057, +0.026 |
| `s_attn` (attention counts beyond history) | +0.056 | 3.00, 2.65 | +0.106, +0.007 |
| `s_text` (attention counts and reader block beyond history) | +0.050 | 3.24, 3.13 | +0.083, +0.016 |

| Panel | Value |
|---|---|
| Forecast of the variance rank from history alone (`v_hist`) | rank IC 0.813 |
| Loss of `v_hist` minus loss of `v_full` (all text added) | 0.52 % of the loss, t 2.04 |
| Loss of `v_hist` minus loss of `v_hist_attn` (attention added) | 0.40 %, t 1.68 |
| Loss of `v_hist_attn` minus loss of `v_full` (reader block added) | 0.12 %, t 1.00 |
| Boosted trees: loss of `g_hist_attn` minus loss of `g_full` (reader block added) | −0.15 %, t −1.24 |
| Gate statistic with another target: log variance, `fwd_absret`, `fwd_drawdown`, `fwd_maxday` | −0.008 (t −0.61), +0.030 (t 1.95), +0.010 (t 0.64), −0.013 (t −0.76) |
| Permutation placebo, 500 draws | t mean −0.05, sd 1.01, 97.5 % quantile 1.89; 75.6 % of the draws at or above the observed t |
| Shift placebo, features from 13, 26, 52 weeks earlier | t −0.41, +2.14, −0.01 |
| Shift placebo, features from 13, 26, 52 weeks later | t +0.99, −0.94, +0.22 |
| Autocorrelation of the target residual within an asset at 1, 2, 4, 8 weeks | −0.009, +0.006, −0.023, +0.002 |
| Share of the target rank variance the controls leave on the test weeks | 0.200 after the within-week step alone, 0.199 after both steps |
| Target coverage on the test weeks | 0 of 5,200 rows missing, 3 rows with a short forward week |
| Share of test asset-weeks with a non-zero reader feature | `evt_7d` 37 %, `evt_30d` 56 %, `unfav_7d` 17 %, `sched_30d` 32 %, `rumour_30d` 14 %, `split_7d` 8 % |

Reading of the result, as far as the registered outputs carry it:
- The judgements of the reader agents carry no information on next week's relative volatility beyond price
  history and attention counts. The mean is negative, and negative in 2023.
- The hardening of stage V0 did not decide the verdict. The first design (`s_reader_lin`) reaches t 1.13 with
  a negative 2023 and fails both gates as well.
- Without the attention control the reader block looks strong (`s_reader_hist`: t 3.24). With the two
  attention counts among the controls nothing is left. The reader features stand in for the number of items.
  This is the pattern of Charter 2 on a second target.
- The attention counts relate to next week's volatility beyond price history (`s_attn`: +0.056, t 3.00). The
  ridge coefficient of `attn_7d` is negative in every test week (mean −0.058): assets with more items in the
  last seven days had a lower variance in the following week than their price history implied. The relation
  sits in 2023 (+0.106) and is absent in 2024 (+0.007). It needs no language model, the row was not gated and
  the window is exposed, so nothing is claimed from it.
- Price history forecasts the rank of next week's variance with a rank IC of 0.813. All text together lowers
  the loss of that forecast by half a percent, most of it through the attention counts.
- The autocorrelation of the target residual is zero at every lag, so the rows of the noise table without
  persistence apply (pass rate on noise 2.60 % and 2.75 %, charter Appendix B).
- One of six shift placebos reaches t 2.14 (features of the same asset from 26 weeks earlier). The other five
  lie between −0.94 and +0.99. A placebo carries no claim; the value shows the scatter of the statistic.

Checks on the negative result:
- The gate code passes a planted effect and fails a noise draw
  (`test_planted_signal_passes_and_a_noise_draw_fails`), and the placebos break a planted link
  (`test_placebos_break_the_planted_link`).
- The pre-flight rehearsed the whole evaluation on synthetic targets before the claim, and the record table
  equals the rebuild from the registered cache.
- Power (charter §5): the gates pass in 99 % of the draws at a mean weekly partial correlation of 0.074 and in
  78 % at 0.045. The observed mean is −0.009 with a Newey-West standard error of 0.013. A relation of the
  visible size is excluded. A thin positive relation below about 0.02 is not.
- No descriptive error and no fit error is listed in `verdict.json` and `evaluation.json`.

Budget: $0 spent under Charter 3, balance about $4.86. Family `llm-multiagent-v2`: 4 of 6 attempts used.
Sealed-A and Sealed-B untouched. No run active.

## Charter 4 (fresher information: daily decision, next-day return): draft, not frozen (2026-11-14)

Charter draft: `docs/superpowers/specs/2026-11-14-llm-v2-charter4-fresh-news-charter.md`. Attempt 5 of 6 when
registered. Nothing is registered, no attempt is claimed, and no feature built from the reader records has been
joined with a return or price quantity dated at or after its decision. The freeze needs the user's approval;
the ten open decisions are in §10 of the draft, each with the implemented and recommended option.

Design in short:
- Same 53,330 records, no model call, cap $0.
- One decision per day at 00:00 UTC, 2022-01-08 to 2024-12-28 (1,086 days, 54,300 rows, 222 contracts). The
  members of a day are the top 50 of the last Friday before it.
- Target: return of the next day relative to the other assets of the day (`fwd_ret_1d`). The size of the
  move, the daily variance and the three-day return are descriptive variants.
- Capture-time audit (`charter4_design/capture_time_audit.json`): a news item has a publication date without
  a time of day and a capture time. It enters a feature at the first midnight after its capture, and only when
  it was captured on its publication date or on the day after. The median time from capture to decision is 9.9
  hours.
  The charter therefore tests a continuation over the day after the news day, not the reaction to the news.
  Community posts enter the counts only.
- Question: does the reader tone (`tone_1d`, `tone_prev6`) carry information beyond 11 price-history controls
  and 4 attention counts?
- Gate: daily partial correlation of a walk-forward ridge score with the target residual on 722 test days
  (2023-01-07 to 2024-12-28). Controls removed in two steps on both sides, as in Charter 3. G1: Newey-West t
  (lag 7) at least 2.0 and mean above 0. G2: mean above 0 in 2023 and in 2024. With a PASS the net return of a
  score book after 5 bp per side is read as "above cost" or "below cost" (no gate).

Stage V0 is complete (code, 85 offline tests, synthetic dry run, pass rate and power on synthetic targets,
calibration on bars of 2021). Two choices were made by rules written before their draws:
- Rule 1, form of the daily statistic: correlation and covariance are within 10 passes of 800. The
  correlation form of Charters 2 and 3 stays.
- Rule 2, features of the gate score: the two tone features pass 421 of 800 planted draws, the six reader
  features 325, the four features of the last day 197. The gate score uses the two tone features. Both planted
  effects are defined on the tone, so the rule favours them by construction; the six-feature score stays in
  the run as the descriptive `s_block_r`.

| Synthetic target, registered score | size per directed asset-day | PASS |
|---|---|---|
| no reader information, six cells (400 draws each) | none | 1.5 % to 2.5 % (51 of 2,400) |
| effect of the last day (200 draws) | about 18 bp | 22 % |
| effect of the last day | about 37 bp | 77 % |
| effect of the last day | about 55 bp | 98.5 % |
| effect over the week (200 draws) | about 13 bp | 29.5 % |
| effect over the week | about 27 bp | 87 % |
| effect over the week | about 45 bp | 100 % |

- These sizes are large for a liquid market one day after public news. A FAIL is the expected outcome. It
  would speak against a drift or reversal of about 40 bp and more per directed asset-day and would not exclude
  a smaller one.
- Turnover of the score book on the test days is 1.6 to 2.8 per day, which costs about 8 to 14 bp per day.
- A `stress` cell was added after the comparison with the bars of 2021 and before any outcome was opened. Its
  pass rate is 2.5 %.

Evidence: draws and design checks in `research/multiagent-v2/charter4_design/` (README there). Check of the
registration builder (`scripts/reader_charter4_register.py --date 20261114 --check`): 45 source files, 7
inputs, nothing written. The builder refuses to write while the draft mark is in the charter.

Next: freeze approval by the user, then freeze (draft mark removed, sha256 recorded), commit, registration,
pre-flight, one registered run. Family `llm-multiagent-v2` stays at 4 of 6 attempts until the claim. Sealed-A
and Sealed-B untouched. No run active.

## Charter 4: frozen (2026-11-14, V1)

Freeze approved by the user on the draft ("Approved"), with the implemented option on all ten points of §10:
next-day relative return as the gate target, gate on the reader tone beyond price history and attention
counts, fitted sign, threshold t at least 2.0, correlation form, size as a reading rule on the net return of
the score book, items without a judgement as no record, community posts in counts only, daily decision at
00:00 UTC, attempt 5 of 6.

- The draft mark is removed and the status line changed. The document is byte-final from this commit:
  sha256 `e90b8f866215585dc09b38cdd4b447ef1f8fc3eb1cad4c5353abcf1d2b0e00b0`.
- Results of the run go into this file, never into the charter.
- At the freeze nothing is registered, no attempt is claimed and no reader feature has been joined with a
  return or price quantity dated at or after its decision. 85 offline tests pass on the frozen text.
