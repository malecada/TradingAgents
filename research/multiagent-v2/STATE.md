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
