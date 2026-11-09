# Hybrid Multi-Agent LLM Trading System, Second Attempt: Analysis and Plan

**Date:** 2026-11-08
**Status:** ANALYSIS AND PLAN ONLY. Nothing here is registered. No gate, ledger row, holdout or LLM spend is touched by this document. Execution requires a charter under `RESEARCH_LOOP_GUIDE.md` and the house rails.
**Decision log (2026-11-08, user):** primary model stack = DeepSeek via OpenRouter (7.5); Claude Opus 5.5 kept as the frontier ablation only. **Submission deadline 2027-01-08** (8.5 weeks); plan re-timed in section 10. Universe top-50 perps weekly plus the BTC/ETH daily arm. Reddit (Arctic Shift) and Common Crawl News admitted with survivorship disclosure. Forward run on this devbox; a VPS later.
**Scope:** the assignment's hybrid system (prediction model feeding a multi-agent LLM debate that reaches trading decisions), rebuilt on the knowledge, data, models and methodology accumulated since the first attempt. The document explains why the first attempt could not have worked as built, what has changed, how context retrieval and anonymization should be done, and lays out a phased, pre-registrable plan.

---

## 1. What the assignment asks for, and where the project stands

The assignment (`topic/thesis_assignment.md`) requires five things:

| # | Assignment requirement | Current state (Nov 2026) |
|---|---|---|
| A | Hybrid architecture: a prediction model produces price forecasts that enter a structured multi-agent LLM debate | Built once (TradingAgents fork, 4 crypto analysts, bull/bear/skeptic debate, risk debate, PM). Evaluated on BTC/ETH daily. Every positive number was voided by the same-bar audit (§33, §48.1). The causal re-test found the LLM layer harmful on honest legs (§48). |
| B | Integration of blockchain-specific data | Strong. PIT on-chain store (CoinMetrics, DefiLlama, Coinglass, DVOL, basis), 799-symbol survivorship-safe daily store, 217-symbol hourly store, DEX swap store, exchange-flow panel (B4). Not yet fed to LLM agents in a usable form. |
| C | Evaluation against baselines | Methodology is the project's strongest asset: pre-registration, causal harness, placebos, DSR accounting, convention swap, leakage canary. No LLM configuration has yet cleared a gate. |
| D | Analysis of individual agent contributions | Done once (§23.11 leave-one-out), but on the same-bar engine, so void. Needs redoing on a correct harness. |
| E | A functioning application able to trade autonomously | Live executor, monitor UI, systemd cycles exist and ran on testnet; decommissioned Aug-2026. Reusable. |

The thesis as it stands (checkpoint 2026-10-22) is a well-documented negative result with an audit story. The gap to the assignment is (A), (D) and (E) done properly, at a power level that can actually detect an effect, with leakage controlled. That is what this plan targets.

A note on the calendar: the assignment lists September 2026 as the planned defence month. The actual submission deadline is 8 January 2027, which leaves eight and a half weeks from the date of this document. Section 10 fits the work to that window; section 10.1 lists what was cut to make it fit.

---

## 2. Why the first attempt failed: diagnosis

The failures are documented in THESIS_FINDINGS §23, §48, §62–§65 and the memory ledger. Grouping them by cause, rather than by experiment, gives seven root causes. The first three concern context retrieval and confirm the user's intuition; the remaining four are design and evaluation problems that would have sunk the attempt even with perfect retrieval.

### 2.1 Retrieval was agent-driven, not pipeline-driven

The analysts were ReAct-style tool callers (`crypto_sentiment_analyst.py` binds `get_news`, `get_global_news`, `get_reddit_posts`, `get_crypto_google_news` and asks the LLM to "gather data from ALL four sources"). Consequences visible in the record:

- Which sources were actually fetched varied per bar with the model's whims; the system prompt even says "If you are unable to fully answer, that's OK".
- Tool failures (Reddit 403s, gtrends rate limits, GDELT gaps) silently produced thinner context on some days than others, so context quality was itself a random variable correlated with nothing useful.
- Three of the four live tools were today-relative. In PIT mode they were replaced by stubs that return "not available in PIT mode" (`news_data_pit.py`), so in backtests the sentiment analyst effectively had one source (Alpaca) plus GDELT titles and Fear & Greed. The thesis itself records that the deployed agent and the offline PIT pipeline "were never unified" (chapter 2, multi-agent component).
- Retrieval and judgment were tangled in one LLM call, so neither could be evaluated separately. Retrieval quality was never measured.

### 2.2 The retrieved text was the wrong text

`crypto_sentiment_pit.get_crypto_news_pit` returns up to 50 rows per source, newest first, with content truncated to 600 characters, no deduplication, no relevance ranking, no entity disambiguation beyond a substring match on `BTCUSD`, and no filtering of article type. Benzinga's crypto feed is dominated by price-recap items ("Bitcoin falls 3% as…"). Feeding those to the model hands it a verbal description of lagged price, which is exactly the "price-following sentiment" mechanism (Liu–Tsyvinski) that §23.12 found to be noise or harm. GDELT provided titles only. Altcoins had 10–15 articles a month. Reddit was never PIT-ingested. There was no story continuity across days, no scheduled-event calendar, no typed events.

### 2.3 Anonymization was partial

`anonymizer.py` replaces the coin name with `Asset_X` in the instrument context and in four agents' prompts. Everything else leaked identity: article headlines and bodies named the asset in every sentence; the system prompt stated "the current date is {current_date}"; prices were given in USD levels (a $60,000 asset is Bitcoin); on-chain metric names were chain-specific (hash rate, Puell multiple). The alias protected against nothing. C1's text-level `anonymize()` in `scripts/llm_event_xs_extract.py` was the first real masking, and it was used only as a probe, not in the agent system.

### 2.4 Scalar opinions at daily frequency on two assets

Every falsified design asked a cheap LLM for a directional opinion (sentiment polarity, confidence, multiplier) once a day for BTC and ETH. §40 established that purged directional accuracy on these bars is 50–53% for every model class; Grinold's law says breadth is the only unexploited axis. Two assets at a daily horizon cannot produce a detectable edge in 90–126 bars whatever the model. The Aug-2026 proposal's conclusion stands: the LLM should emit facts, orderings, probabilities and rare flags, with harvesting left to a quant layer that can be placebo-tested.

### 2.5 Cheap models for every role

All production runs used gpt-4o-mini or gpt-5.4-mini/nano in every slot, including the debate and the portfolio manager, because full-graph runs cost $15–25 per 126-bar pass and the replay cache did not amortize across variants (memory-induced cache cascade). The question "does a frontier model do better" was never asked.

### 2.6 Free-text outputs and brittle parsing

Decisions were extracted from prose ("FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**", a confidence rubric inferred from "conviction strength"). The §10 rescoring showed a parser bug inflated the headline Sharpe from +0.22 to +0.79. Position-order sensitivity in C3 (shuffle rho 0.63–0.88) showed the models' outputs depended on prompt layout.

### 2.7 Evaluation could not have passed

Windows were bounded below by the LLM cutoff (post-2026-01 for gpt-5.4-mini), so every honest test had ≤126 bars. The pre-registered gates were correct; they simply had no power. Sharpe differences of ±0.5 on 126 daily bars have confidence intervals a full Sharpe unit wide (§48: CI [−1.04, +0.07]).

**Summary.** The attempt failed for reasons that are now identifiable and, individually, addressable: deterministic PIT retrieval; text selection by type and novelty; full anonymization; structured outputs; cross-sectional breadth; frontier models in the roles that need them; and an evaluation design whose power is computed before, not after, the run. None of this guarantees a positive result. It guarantees a result that means something.

---

## 3. What has changed since the first attempt

| Area | Then (Q1–Q3 2026) | Now (Nov 2026) |
|---|---|---|
| Models | gpt-4o-mini, gpt-5.4-mini/nano; Claude 4.x in catalog but unused | **Chosen: DeepSeek via OpenRouter** (live prices 2026-11-08): V4-Pro $0.40/$0.81 per MTok (fp8, 1M context), V4.1-Flash $0.05/$0.20 on-demand and $0.011/$0.20 batch, V3.2 $0.26/$0.38 (164K context). All expose `response_format` JSON schema, `seed` and `temperature`. DeepSeek publishes no knowledge cutoffs; release dates are used as conservative cutoff bounds (V3.2 2025-12, V4-Pro 2026-04, V4.1-Flash 2026-09). Reference frontier for the optional ablation: Claude Opus 5.5 $4/$20, Sonnet 5.5 $2/$10 (batch halves), cutoff June 2026. |
| Text corpora | Alpaca BTC/ETH 2023-10→2026-04 (13.5K) | Alpaca 2021-01→2026-04 across 797 perp bases (~57K rows incl. backfills); GDELT 2021-01→2025-03 (~405K title rows); HF bitcoin_news 2011→2025-06; 400 human-adjudicated event labels (C1 P0, reusable truth set); News_fulltext archive (~20 GB, Storage Box, provenance to be admitted) |
| Numeric PIT data | BTC/ETH on-chain + indicators | 799-symbol daily klines + funding with PIT universe; 217-symbol hourly; 47.5K-card panel (287 Fridays × top-200 × 15 PIT fields, `data/llm_rank_xs/cards.parquet`); Coinglass OI/liq/long-short 2020+; DVOL; DefiLlama multi-chain; unlock CSVs; DEX 15.3M-swap store; funding/premium-index/book-depth stores in `crypto-research-loop/data` |
| Forecasts with verified skill | none | realized-vol HARQ (G1.1 PASS), funding persistence/forecast (G1.2), exchange-flow vol (B4 2/3 holdout PASS). Direction forecasts: none (all ≈ 50%) |
| Methodology | pre-registration, but same-bar engine | causal harness, convention swap, leakage canary, placebo families, DSR accounting, honest-denominator forensics, order-swap and anonymization probes (C3/C3-P) |
| Validity findings | — | pairwise-by-construction removes position bias (C3-P P0 PASS); anonymized ≈ named performance on numeric cards (C3-P P1); LLM beat a GBDT twin on identical cards (IC 0.0174 vs 0.0073, both insignificant) |

The last row matters: the one LLM construction that reached its effect-size test showed a small positive, insignificant signal from fifteen numeric fields. The open question is whether rich, well-retrieved text and a frontier model move that from 0.008 to something detectable.

---

## 4. The binding constraint: knowledge cutoff versus evaluation window

Any LLM evaluated on a period inside its training window may recall outcomes. DeepSeek does not publish cutoffs, so the model's release date is taken as the cutoff bound. For V4-Pro (released 2026-04-24) the clean window today is 2026-05 → 2026-11, six months; for V4.1-Flash (released 2026-09) it is two months, which is why Flash is confined to classification roles where recall of outcomes is irrelevant. By a mid-2027 defence it is about eleven months. Daily BTC/ETH on eleven months is again unpowered; cross-sectional weekly on 100 assets over 45 weeks is borderline. Three complementary evaluation layers resolve this; the plan uses all three.

**Layer 1: anonymized pre-cutoff development window.** Dev 2022-01 → 2024-12 (156 weeks), anonymized as in section 5, used for all design iteration. Anonymization reduces memorization leakage but cannot eliminate it for famous episodes, so Layer 1 results are never the headline. They are the engineering signal.

**Layer 2: sealed windows, one shot each.**
- Sealed-A: 2025-01 → 2026-04, anonymized, before the V4-Pro release (2026-04-24, the conservative cutoff bound). Spent once, after the design is frozen.
- Sealed-B: 2026-05 → 2026-12-11 (last decision Friday whose 5-day outcome is known before the results freeze on 2026-12-21), after the V4-Pro release. About 32 weeks. This is the Profit-Mirage test (Li et al. 2025): if anonymized pre-cutoff skill is real, it should persist here. A collapse from Layer 1/Sealed-A to Sealed-B is itself a thesis result about memorization.

**Layer 3: forward paper trading.** The application runs from the end of Phase 2 onward on this devbox against Binance testnet or paper fills, journaling decisions. It is the assignment's deliverable (E) and the only evaluation nobody can dispute.

**Layer 4: chronological control model.** DeepSeek V3.2 (released 2025-12-01; its V3.2-Exp sibling lists a 2025-07-31 cutoff) run through the identical pipeline on 2025-12 → defence gives an eleven-month window that is clean for V3.2 and overlaps Sealed-A for V4-Pro, at about $120. Because it is the same model family and the same API route, the comparison isolates the cutoff rather than the provider. It triangulates leakage: if the frontier model's anonymized pre-cutoff performance far exceeds both its own post-cutoff performance and the chrono-control, memorization is the likely explanation. Cost is small; include it if the budget tier allows.

The leakage-related probes in section 5.4 are run in every layer.

---

## 5. Anonymization, elaborated

### 5.1 Why anonymize at all

Three distinct reasons, each with a different success criterion:

1. **Leakage control.** The model should not be able to map the dossier to (asset, date) and recall what happened next. Criterion: a re-identification probe (5.4) fails at or near chance.
2. **Prior removal.** Pretrained models carry name-specific priors ("Bitcoin" evokes crashes and regulation; a meme coin evokes "scam"). Anonymization forces judgment from the evidence in the dossier. Criterion: named-versus-anonymized paired runs show no systematic bias shift.
3. **Cross-sectional fairness.** In a ranking across 100 assets, name recognition would otherwise dominate (large caps get "safer" by default). Anonymization makes the comparison about the data.

The user's intuition that all context should be anonymized is correct, with one qualification: anonymization must not destroy point-in-time-legitimate knowledge (5.3).

### 5.2 Threat model: what leaks identity and time

A dossier leaks identity through many channels beyond the ticker. All must be masked or transformed:

| Channel | Example | Treatment |
|---|---|---|
| Asset names, tickers, symbols | Bitcoin, BTC, ₿, "the world's largest cryptocurrency" | Dictionary + alias map per asset (names, tickers, common nicknames, native-unit names); replace with `Asset_K` per asset, stable within a decision, re-drawn across decisions |
| Ecosystem and protocol names | Ethereum, Solana, Uniswap, Lido, Arbitrum | Same dictionary; map to `Network_X`, `Protocol_Y` roles |
| Exchanges, companies, funds | Binance, Coinbase, FTX, BlackRock, MicroStrategy | `Exchange_A`, `Company_B`, `Fund_C` |
| People | CZ, SBF, Saylor, Gensler, Powell | `Person_1`; regulators as `Regulator_R` with jurisdiction kept generic ("a major regulator") |
| Dates and times | "on March 12", "Q4 2022", "since the 2021 peak" | Convert to relative time: "12 days ago", "about two years ago"; strip absolute years; never state the current date |
| Price levels and market cap in USD | "$60,000", "$1.2 trillion market cap" | Normalize: index the decision-day price to 100 and quote changes; market cap as rank bucket and log-size z-score |
| Chain-specific metric names | hash rate, Puell multiple, staking ratio, gas fees | Generic labels: "network security spend", "miner revenue vs trailing", "fee revenue", with the same transformation for every asset where applicable |
| Famous episodes in narrative | "the collapse of a major exchange", "algorithmic stablecoin depeg" | Not fully maskable. Handled by measurement (5.4) and by an episode-exclusion sensitivity analysis (score with and without weeks flagged as globally famous) |
| Numbers that are themselves identifiers | 21 million supply cap, 32-unit validator stake | Round and relativize supply figures; express as percent of total |
| URLs, authors, outlet names | coindesk.com, Benzinga | Drop URLs and authors; keep outlet tier (major/minor) only |
| Macro context | "Fed hikes 75bp", "SVB" | Keep macro facts but relativize dates; macro events date the dossier, so report macro as regime descriptors ("rates rising, risk assets weak") rather than named events |

Implementation: a deterministic pass (dictionary, regex for dates/prices/tickers, NER for persons and organizations) followed by a Haiku 5.5 redaction pass instructed to replace any remaining proper noun or absolute date with a role token, followed by a verification pass that rejects any dossier containing a term from the dictionary or a four-digit year. All three passes are logged; the dossier hash includes the anonymizer version.

### 5.3 What must not be anonymized away

Point-in-time legitimate knowledge is part of what a real analyst uses. Anonymization should remove identity, not information that was knowable at decision time. Keep, in anonymized form:

- Scheduled supply events: "a token unlock equal to 3.1% of circulating supply occurs in 9 days" (from the unlock calendar, PIT-knowable).
- Scheduled protocol events: "a major network upgrade is scheduled in 23 days" (from PIT news or announcement dates).
- Scheduled macro: "a central-bank rate decision falls in 2 days" (FOMC/CPI calendars are published years ahead).
- Derivative expiries: "a quarterly futures/options expiry in 4 days".
- Asset class descriptors: "layer-1 smart-contract network", "centralized-exchange token", "stablecoin-adjacent", "meme asset", market-cap rank bucket, age in years. These are properties, not identities, and 100 assets share each label.

### 5.4 Measuring residual leakage

Anonymization without measurement is a claim. Four probes, all pre-registered:

1. **Re-identification probe.** A separate model instance (same tier) receives the anonymized dossier and is asked to name the asset (from the universe list) and the date (month). Target: asset accuracy ≤ 2× chance on the universe; month accuracy within ±6 months ≤ 25%. Run on 300 dossiers per anonymizer version. Fail → anonymizer revision before any trading-side run.
2. **Named-versus-anonymized pair.** On a 10% subsample, run the full system with real names and with aliases. Compare IC and calibration. Named materially better → memorization or prior effect; the anonymized arm remains the registered one, and the gap is reported.
3. **Pre-cutoff versus post-cutoff drop.** Layer-1/Sealed-A skill versus Sealed-B skill (section 4). Pre-registered expectation: no significant drop. A drop is reported as the memorization estimate.
4. **Famous-episode exclusion.** Rescore with weeks flagged as globally famous (defined mechanically: top-decile GDELT crypto-article volume) removed. Skill concentrated in famous weeks is suspect.

The combination of (2) and (3) is the design recommended by Glasserman & Lin (2023) and Lopez-Lira & Tang (2023); C3-P P1 already applied (2) once and found no gap on numeric cards.

### 5.5 Costs of anonymization

- Loses genuine model knowledge about assets (tokenomics, team quality, past exploits). Mitigation: put the PIT-knowable version of that knowledge into the dossier explicitly (5.3) and let the ablation "named vs anonymized" quantify what is lost.
- Macro relativization weakens the model's regime understanding. Mitigation: a regime descriptor block computed from data (rates trend, DXY trend, BTC 90-day drawdown bucket).
- Engineering cost: dictionary curation for 100+ assets and their ecosystems, roughly two days, plus the verification harness.

---

## 6. Context retrieval, redesigned: the dossier builder

The central engineering change: retrieval becomes a deterministic, PIT-enforced, versioned pipeline that produces one **dossier** per (asset, decision time). Agents receive the dossier; they do not fetch. Retrieval quality is then measurable independently of trading performance.

### 6.1 Sources

Admitted now (exist, PIT-timestamped):
- Alpaca/Benzinga news with `created_at` (full text for most rows), 797 bases, 2021→2026-04; extend forward to present.
- GDELT DOC 2.0 titles + URLs, 2021→2025-03; extend forward (free, 15-minute update granularity).
- Fear & Greed daily; numeric PIT stores listed in section 3.
- 400 adjudicated event labels for extraction gates.

To admit (free, PIT-correct, not yet used):
- **Common Crawl News (CC-NEWS)**: full-text WARC archives since 2016 with crawl timestamps. Filter by crypto outlets (CoinDesk, Cointelegraph, The Block, Decrypt, Blockworks, DL News, Protos) and by GDELT URL lists. Crawl time is a usable as-of bound; publication time comes from page metadata. This fixes GDELT's title-only limitation without link-rot refetching.
- **Reddit via Arctic Shift / Pushshift dumps**: created_utc is reliable; deleted-post survivorship is a bias to disclose. Subreddits: r/CryptoCurrency, r/Bitcoin, r/ethereum, asset subreddits for the universe.
- **Protocol communications**: governance forums (Snapshot, Discourse instances), project blogs via CC-NEWS/Common Crawl main index. High value for altcoins where news is thin.
- **Unlock and emission calendars** (Tokenomist CSV path exists), **macro calendars** (FOMC, CPI), **exchange listing announcements** (Binance announcement archive has publication timestamps).
- **News_fulltext archive** on the Storage Box: provenance must be admitted before use (AGENTS.md rule); inspect manifest first.

Not admitted: X/Twitter (no access), retro-scraped Google News (survivorship), any today-relative API in backtests.

### 6.2 Pipeline stages

1. **Ingest and normalize** to the bitemporal schema `(event_ts, as_of_ts, source, url, title, body, lang)`; dedupe by URL and by near-duplicate text (MinHash on body).
2. **Entity linking**: dictionary match on names/tickers/contracts → candidate assets; Haiku 5.5 verification call for ambiguous cases (short tickers like `OP`, `ARB`, `LINK` collide with English). Store `(article_id, asset, salience ∈ {primary, mentioned})`. Gate: ≥0.95 asset-link accuracy on a 200-article audit (C1 reached 0.97–1.00).
3. **Article typing** (Haiku 5.5, batch): `{price_recap, event, analysis_opinion, promotional, unrelated}`. Price recaps are counted, not included. Promotional and unrelated are dropped. This removes the price-following contamination at the source.
4. **Typed event extraction** (Sonnet 5.5 or Opus 5.5, batch, no keyword prefilter): article → list of `(asset, class, severity 1–3, scheduled_date?, evidence_span)` with the six C1 classes plus `funding_raise`, `major_holder_move`, `product_launch`. Gate: the frozen C1 P0 floors (precision ≥0.8, recall ≥0.6, asset-link ≥0.9, anonymization agreement ≥0.8) on the committed 400-article truth set. This is the cheapest and most informative first probe of the whole plan (~400 articles, under $10): C1 died here with gpt-5.4-mini plus a keyword gate; if a frontier model without the gate passes, the text layer is viable; if not, the plan falls back to typed numeric cards plus article summaries and the thesis records a second extraction negative.
5. **Story threading**: cluster events and articles per asset across a 30-day trailing window (embedding similarity + shared entities) so the dossier shows development ("exploit reported 6 days ago; funds partially recovered 2 days ago") rather than isolated headlines.
6. **Selection and budgeting**: per dossier, rank items by (salience, novelty vs prior 7 days, outlet tier, recency decay); include up to N items within a token budget (target 8–15K tokens of text). Record what was excluded.
7. **Numeric card**: the 15 PIT fields of `cards.parquet` plus derivatives (funding z, OI change, long/short skew, liquidation asymmetry), on-chain (active-address and fee z-scores where available), relative strength vs the universe, realized-vol forecast (HARQ) and its percentile, all as z-scores/percentiles/returns, never levels.
8. **Quant forecast block**: the prediction component's output for this asset and horizon, with its own trailing calibration record ("over the last 26 weeks this model's directional hit rate on this asset bucket was 51%, Brier 0.251"). This is deliberate: a real test of whether agents discount an uninformative input.
9. **Scheduled-event calendar**: next 30 days of PIT-knowable events (5.3).
10. **Historical analogs** (ablation arm, off by default): k nearest past situations by numeric similarity, drawn only from data before the decision time, with realized outcomes. Because this is a kNN forecaster in disguise, it is evaluated as a separate arm.
11. **Anonymize** (section 5), **verify**, **hash**, **store**. Dossiers are immutable artifacts keyed by (asset, decision_ts, builder_version, anonymizer_version); the same dossier feeds every ablation, which also makes prompt caching effective (stable prefix: system prompt, schemas, dossier; variable suffix: the role-specific question).

### 6.3 Measuring retrieval quality on its own

Before any trading-side evaluation, the dossier is graded as a product:

- **Coverage audit**: for 60 (asset, week) pairs chosen by stratified sampling, a human (or a blind Opus pass with the un-anonymized web as reference, then human check) lists the material facts an analyst should have known at that time; the dossier is scored on recall of those facts. Floor: ≥0.7.
- **Noise audit**: fraction of dossier tokens spent on price recaps, duplicates, promotional content. Ceiling: ≤0.15.
- **Timestamp fidelity probe**: for Alpaca and CC-NEWS, compare `as_of_ts` to independent publication timestamps on a sample; report the lag distribution and set the decision-time buffer accordingly (daily decisions at 00:05 UTC use items with as_of ≤ previous day 23:59; weekly use Friday close).
- **Anonymization probes** (5.4).

Passing these converts "context retrieval was not good enough" from an impression into a measured property, and gives the thesis a chapter section on its own.

---

## 7. The multi-agent system, version 2

### 7.1 Design principles

- Agents judge; they do not retrieve. Input is the dossier; output is a JSON object validated against a schema (`output_config.format`, strict). No free-text parsing anywhere in the decision path.
- Every opinion is a probability or an ordering with cited dossier item IDs, never a bare label. Calibration is scored.
- Presentation effects are controlled by construction: every debate runs twice with roles and item order swapped; outputs are averaged (the C3-P lesson).
- Breadth over depth: the system decides over a cross-section (top-50 or top-100 perps by PIT volume), weekly, with a secondary daily BTC/ETH arm for continuity with the first attempt.
- DeepSeek V4-Pro in every judgment role (analysts, debate, judge, PM); V4.1-Flash batch in classification roles (article typing, entity verification, redaction pass); V3.2 as the chronological control. A frontier model (Claude Opus 5.5) appears only in the model-tier ablation on the 10% subsample, so the thesis can still say whether capability changes the verdict.
- Memory (FinMem-style episodic memory) is a tested ablation, PIT-safe: episodes become visible only after their outcome's as_of time, and are anonymized like everything else. It is not in the baseline configuration because it makes every prompt unique and defeats replay caching.

### 7.2 Roles

| Role | Model | Input | Output (schema) |
|---|---|---|---|
| Market-structure analyst | DeepSeek V4-Pro | numeric card, vol forecast, derivatives block | `P_up_{h}`, regime label, key risks, cited fields |
| On-chain / fundamentals analyst | DeepSeek V4-Pro | on-chain block, supply calendar, asset descriptors | `P_up_{h}`, fundamental drift flag, cited fields |
| News and events analyst | DeepSeek V4-Pro | threaded events and articles | event summary, `P_up_{h}`, severity-weighted shock score, novelty flag |
| Forecast interpreter | DeepSeek V4-Pro | quant forecast block with calibration record | recommended weight on the quant forecast ∈ [0,1], rationale |
| Bull / Bear researchers | DeepSeek V4-Pro | all four analyst outputs + dossier | steelman cases with cited evidence (one round each, then one rebuttal each) |
| Judge (research manager) | DeepSeek V4-Pro | debate transcript | calibrated `P_up_{h}`, confidence, invalidation conditions, abstain flag |
| Risk / portfolio manager | DeepSeek V4-Pro, weekly, portfolio-level | judges' outputs for all candidates, vol forecasts, current book, cost model | target weights (long tilt or long-short), per-asset size ∈ [0,1], abstentions |

Horizon h: 5 trading days for the weekly cross-section (matches C3-P's residual IC horizon and the 21-day diagnostic can be reported); 1 day for the BTC/ETH arm.

The debate is capped at one round plus one rebuttal. Longer debates were not shown to help in the record and multiply cost; debate depth is itself an ablation (0, 1, 2 rounds).

### 7.3 Prediction component

Honest options, in order of preference:

1. **Keep a directional model and tell the agents its record.** The LightGBM/RF line is retired for lack of skill, but the assignment requires a prediction component, and the interesting hybrid question is whether agents weight a weak forecaster correctly. Use a simple, pre-registered cross-sectional model (ridge on the card fields, walk-forward, as in the C3-P GBDT twin) and report its skill honestly.
2. **Add the forecasts that do have skill as sizing inputs**: HARQ realized-vol forecasts (G1.1 PASS) and, for BTC/ETH, the exchange-flow vol forecast (B4). These go to the risk/PM role, not the direction debate. The thesis checkpoint (chapter 7) already proposes exactly this integration and notes it was never evaluated.
3. **Report the quant baseline as a first-class arm**: quant-only portfolio from the same forecasts with the same cost model. The hybrid must beat it or the LLM layer's contribution is zero by construction.

### 7.4 Cost model (DeepSeek via OpenRouter, live prices 2026-11-08)

Assumptions: dev window 156 weeks; universe top-50 (7,800 asset-weeks); dossier ~12K tokens; four analyst calls per asset-week (52K in, 3.2K out); 20 debated candidates per week, each debate 5 calls in both orders (150K in, 12K out); V4-Pro on-demand at $0.40/$0.81 (StreamLake or Baidu fp8); V4.1-Flash batch at $0.011/$0.20; V3.2 at $0.26/$0.38. Cache-read discounts (V4-Pro cache read $0.034/MTok on several routes) are not counted and would lower the input lines further.

| Line | Arithmetic | Pro-judgment stack | Flash-everywhere stack |
|---|---|---|---|
| Article typing + entity verification | ~450K articles × 1.5K in + 100 out, Flash batch | $17 | $17 |
| Event extraction | ~112K event-typed articles × 1.5K in + 300 out | $100 (Pro) | $10 (Flash) |
| Analysts | 7,800 × (52K in + 3.2K out) | $185 | $10 |
| Debate + judge | 3,120 debates × (150K in + 12K out) | $220 | $13 |
| Portfolio manager | 156 × (80K in + 4K out) | $6 | $1 |
| BTC/ETH daily arm | 2,200 asset-days, analysts + judge both orders | $40 | $5 |
| Ablations | 780 asset-weeks × 8 variants × per-asset-week cost | $325 | $25 |
| Probes | re-identification, named vs anonymized, seed repeats | $30 | $5 |
| Sealed-A + Sealed-B + forward | 123 weeks at dev per-week cost; forward ~$3/week live | $325 | $25 |
| Chronological control (V3.2, ~45 weeks) | same pipeline, V3.2 prices | $120 | $120 |
| Optional frontier ablation (Opus 5.5 batch, 780 asset-weeks) | | $120 | $120 |
| **Total** | | **≈ $1,500** | **≈ $350** |

The pro-judgment stack is the recommendation. Its dev run alone (typing, extraction, analysts, debate, PM) is about $530, roughly a fifth of the Claude mixed stack costed earlier, and it keeps the six-month post-release window for Sealed-B. The flash-everywhere stack is an order of magnitude cheaper but V4.1-Flash's September 2026 release leaves a two-month post-release window and its judgment quality is untested; it is run as the model-tier ablation, not as the baseline. Every number is replaced by the measured two-week pilot (~$40 at these prices) before registration.

### 7.5 OpenRouter operating rules

The client layer already supports OpenRouter (`tradingagents/llm_clients/openai_client.py`, provider `openrouter`, `OPENROUTER_API_KEY`), and the Jev probe charter established the drift rules. Registered runs follow:

- **Pin the route.** Request body `provider: {order: ["<provider>"], allow_fallbacks: false, quantizations: ["fp8"]}`. V4-Pro: StreamLake or Baidu fp8 ($0.40/$0.81; 384K–393K max output). V4.1-Flash batch: the `deepseek/deepseek-v4.1-flash:batch` variant with the same provider pin. Never use the `-latest` aliases.
- **Freeze model IDs with dates** where OpenRouter exposes them (`deepseek-v4-pro`, `deepseek-v4.1-flash-1017`, `deepseek-v3.2`), and record the `provider_name`, `quantization` and model ID echoed in every response; a mismatch fails the run (Jev rule).
- **Determinism.** `temperature: 0`, fixed `seed`; the two-seed agreement probe uses two seeds rather than two samples. Replay-cache key includes model ID, provider and seed.
- **Structured outputs.** `response_format: {type: "json_schema", strict: true}`; providers lacking `structured_outputs` are excluded from the pin list (checked from the endpoints API). Schema-valid rate ≥0.99 remains a gate.
- **Cutoff bound.** Release date is the cutoff for evaluation-window purposes until DeepSeek publishes one; this rule is recorded in the charter.
- **Spend caps.** OpenRouter per-key credit limits set to the charter cap; HTTP 402 or a cap breach fails the run; retries on 408/429/5xx with the Jev back-off table.
- **Data handling.** Dossiers are anonymized public information; no keys or account data ever enter a prompt. Provider terms are reviewed once at registration.

---

## 8. Evaluation protocol

### 8.1 Metric ladder (STOP on fail, in order)

1. **Retrieval gates** (6.3): coverage ≥0.7, noise ≤0.15, timestamp lag documented, re-identification at chance.
2. **Extraction gates**: C1 P0 floors on the frozen 400-article truth set.
3. **Validity probes on the agent system** (2-week pilot): order-swap consistency ≥0.75; two-seed agreement ≥0.85 (sampling parameters are no longer controllable on current API versions, so repeat runs measure intrinsic variance); schema-valid output rate ≥0.99; abstain rate reported.
4. **Forecast-quality gates** (dev window): weekly cross-sectional Spearman IC of the judge's `P_up` versus 5-day forward return, residualized on volatility, 4-week momentum and size (C3-P protocol), Newey–West t ≥ 2.0; Brier skill score vs the base rate > 0; calibration slope within [0.7, 1.3]. The hybrid must also beat the quant-only forecast's IC on common weeks.
5. **Portfolio gates** (dev window, then sealed): decile long-short and long-tilt books from the PM weights, taker costs plus funding, net SR floor 0.8 (house), dual-family placebo, DSR at the declared trial count, three sub-periods same sign.
6. **Sealed one-shots** (Sealed-A, Sealed-B) with gates 4–5 frozen; no retune between them.

Forecast quality is deliberately placed before PnL. On 18,000 asset-weeks an IC of 0.02 is detectable (t≈2 at weekly IC std ≈0.13); PnL on the same data has a far wider interval. The thesis can report a precise forecast-quality result even if the portfolio gate fails.

### 8.2 Baselines (assignment 4.4)

- Quant-only cross-sectional forecast and portfolio (same cards, same costs).
- Equal-weight universe and BTC buy-and-hold.
- Cross-sectional momentum and low-volatility sorts (the §43/§58 machinery, known to be at or below the floor, which makes them honest comparators).
- Single-call LLM (one Sonnet call, no analysts, no debate) with the same dossier.
- Random weights matched on turnover and gross exposure (placebo family).

### 8.3 Ablations (assignment 4.5)

Run on a fixed 10% stratified subsample of asset-weeks so each variant costs a tenth of a full pass; the same dossiers are used throughout so differences are attributable to the agent configuration.

- Leave-one-analyst-out (four variants).
- No debate (analysts → judge directly); one round; two rounds.
- Model tier swap: Haiku in analyst roles; Sonnet in judge role; Opus everywhere.
- Named versus anonymized (5.4).
- Text-free (numeric card only) versus full dossier; events-only versus full text.
- Quant forecast block hidden versus shown; calibration record hidden versus shown.
- Memory on versus off.
- Historical analogs on versus off.

Each ablation reports ΔIC with a paired bootstrap over weeks and the fraction of decisions changed. Multiplicity is declared: the ablations are descriptive, not additional strategy claims.

### 8.4 Pre-registration and rails

One charter per phase, registered under the research loop with gates, denominators and budget before any call touches dev data. Rails inherited: causal t+1 execution, simple returns only (never log returns as PnL), convention-swap kill test on any portfolio claim, honest denominators (every attempted cell retained), sealed data untouched until one-shot, replay cache on, prompts and model IDs frozen at registration, amendments logged.

---

## 9. Application and deployment (assignment 2.5, 3.5)

- A `dossier-build` job and a `decide` job run as systemd user timers on this devbox (never the production VPS): daily 00:15 UTC for the BTC/ETH arm, Friday 00:15 UTC for the cross-section.
- Decisions are journaled with the dossier hash, every agent's JSON, and the PM weights; the existing executor (`tradingagents/execution/live`) posts testnet orders or paper fills; the monitor UI shows the current book, the latest debate and the running forecast-quality scoreboard.
- Live calls go through OpenRouter Chat Completions with the pinned provider and JSON-schema outputs; batch variants are used for backtests where offered. Replay cache keyed on (model ID, provider, seed, prompt hash).
- Operational safeguards from the pipeline audit remain: kill switch, max position, hedge-mode checks. Real funds are out of scope for the thesis run unless the user decides otherwise after Sealed-B.

---

## 10. Phased plan, fitted to the 8 January 2027 submission

Eight and a half weeks at roughly twelve hours a week is about one hundred hours. The schedule below spends them on the items the assignment grades and treats everything else as optional. Results freeze on Sunday 21 December; the last two and a half weeks are writing only. Dates are Mondays unless stated.

| Week | Dates | Work | Gate or artifact |
|---|---|---|---|
| 1 | Nov 9 – 15 | **DONE EARLY (Nov 8): Charter 0 registered, run and closed — FAIL.** V4-Pro on the frozen 400 articles, no prefilter, 550 calls, $0.22; recall 0.26 on human-adjudicated rows, 135/400 rows declined as ambiguous (title-only GDELT). Verdict determined under both review bounds (`research/llm-v2-charter0-2026-11-09/p0_bounds.json`); E2 not run. Remaining week-1 work: Charter 1 registration draft | Text layer routed to summaries + numeric cards (10.2); typed events need full text, not titles |
| 2 | Nov 16 – 22 | Dossier builder core: Alpaca + GDELT extension to present, entity linking, article typing (Flash batch), selection and budgeting, numeric card from `cards.parquet` + derivatives, calendar block; anonymizer v2 with verification pass | 60-dossier coverage/noise audit; re-identification probe |
| 3 | Nov 23 – 29 | CC-NEWS ingest for the six main crypto outlets and Reddit (r/CryptoCurrency, r/Bitcoin, r/ethereum) for the top-50; story threading; event extraction over the event-typed corpus if Charter 0 passed; agent graph v2 (dossier-fed roles, JSON schemas, order-swapped debate, PM) | Pilot (2 weeks of dev data, ~$40): validity probes, measured cost |
| 4 | Nov 30 – Dec 6 | **Charter 1** registered (gates, trial count, budget); full dev run 2022-01 → 2024-12, top-50 weekly + BTC/ETH daily arm; thesis chapter 2 and 3 drafts start in parallel | Dev verdict on forecast-quality and portfolio gates |
| 5 | Dec 7 – 13 | Core ablations on the 10% subsample: leave-one-analyst-out, no-debate, named vs anonymized, text-free, Flash vs Pro, Claude Opus 5.5; V3.2 chronological control on 2025-12 → 2026-12; forward paper run starts on the devbox (Friday Dec 11 first live decision) | Ablation table; forward journal live |
| 6 | Dec 14 – 20 | **Sealed-A** (2025-01 → 2026-04) and **Sealed-B** (2026-05 → 2026-12-11) one-shots with frozen configuration; forensic verification of both verdicts; famous-episode sensitivity | Sealed verdicts; results freeze Dec 21 |
| 7 | Dec 21 – 27 | Writing: chapters 2 (design v2), 3 (implementation), 4/5 (results ladder, ablations, leakage analysis, Profit-Mirage comparison), chapter 7 extension dated at the new checkpoint; figures and tables generated from committed artifacts | Full draft |
| 8 | Dec 28 – Jan 3 | Read-through, assignment-coverage check against items A–E, reproducibility appendix, Czech abstract, bibliography | Review draft tagged |
| 8.5 | Jan 4 – 8 | Corrections, PDF build, submission; forward journal snapshot included as of Jan 5 | Submitted |

### 10.1 What was cut to fit

- Historical-analog arm, episodic memory arm, debate-depth sweep (0/1/2 rounds): dropped. Mentioned as future work.
- Reddit limited to three subreddits; CC-NEWS limited to six outlets; protocol forums and project blogs dropped.
- Ablations reduced from eight variants to six; all on the 10% subsample.
- Forward record at submission is about four weekly decisions; it is reported as a started live run, with the journal continuing to the defence.
- The daily BTC/ETH arm keeps only the analyst-plus-judge path (no full debate) to stay inside the week-4 compute window.
- No second amendment round anywhere; every charter is one shot. A gate that fails is written up, not re-tried.

### 10.2 Default if gates fail early

Charter 0 failed on 2026-11-08: the dossier carries article summaries and typed numeric cards instead of extracted events, and the thesis gains a second extraction negative, this time at a frontier-class tier with the mechanism identified (the model declines to assert events from headlines alone; gpt-5.4-mini asserted them). The lesson feeds Phase 1 directly: Common Crawl full text replaces GDELT titles wherever available, and summaries are generated only from articles with a body. If the dev run fails the forecast-quality gate, the sealed runs still execute once (the gates are frozen either way) and the thesis reports the full ladder. The retrieval-quality audit, the anonymization measurement, the ablation table and the running application are deliverables regardless of sign, and together they cover assignment items (A), (D) and (E), which the current checkpoint does not.

---

## 11. Risks and stop rules

| Risk | Mitigation / stop rule |
|---|---|
| Memorization leakage despite anonymization | Probes 5.4 registered; Sealed-B is the arbiter; report the drop rather than hide it |
| Extraction fails again at frontier tier | Phase 0 gate; proceed numeric-plus-summaries; record the negative |
| Cost overrun | Measured pilot before registration; batch API; cached dossier prefix; memory off in baseline; hard cap per charter with a STOP on 110% |
| Nondeterminism | `temperature: 0` and fixed seeds; two-seed repeat as a validity probe; average both debate orders |
| OpenRouter provider or quantization drift | Pinned provider and fp8, no fallbacks, echoed provider/model checked per call, run fails on mismatch (Jev rule) |
| Unknown DeepSeek cutoffs | Release date used as the cutoff bound; V3.2 chronological control; Profit-Mirage comparison across Sealed-A/B |
| Timestamp infidelity in news (backfilled `created_at`) | Fidelity probe; conservative decision-time buffer; disclose lag distribution |
| Survivorship in Reddit dumps and news archives | Disclose; compare Alpaca (live-collected since 2023-10) vs archive-derived periods |
| Universe survivorship | PIT universe from the 799-symbol store with listing/delisting history (LUNA lesson) |
| Sealed window reuse | Sealed-A and Sealed-B each spent once; the 2025-04→2026-07 window was spent for other families, not this one; disclose the overlap |
| Same-bar and log-return artifacts | Causal harness, simple returns, convention-swap kill test, leakage canary before any claim |
| Thesis time | Phase 5 runs in parallel from week 10; Layer-3 forward record accrues regardless of backtest verdicts |

---

## 12. Relation to the literature in the assignment

- **TradingAgents** (Chen et al. 2024): the role structure is kept; the retrieval model is inverted (dossier in, no tool calls), outputs are schema-constrained, and the debate is order-debiased.
- **FinMem** (Yu et al. 2023): layered memory becomes a PIT-safe, anonymized episodic store tested as an ablation rather than assumed beneficial.
- **AutoGen** (Wu et al. 2023): conversation orchestration is retained in LangGraph form; the contribution is the evaluation and data discipline, not the orchestration.
- **Dubey & Enke 2025** (on-chain direction prediction): the prediction component reports its honest skill and the agents' weighting of it is itself measured.
- Audit literature (Profit Mirage, StockBench, Xia et al. 2026, Glasserman & Lin, Lopez-Lira & Tang): the three-layer window design and the leakage probes implement their recommendations directly, which positions the thesis as one of the few LLM-trading studies with contamination controls built in.

---

## 13. What this plan does not do

- It does not re-run any falsified cell under its old identity. Every registration is a new item with the parent cited.
- It does not promise a positive trading result. Prior odds, given the record, are low; the plan is designed so that a negative is precise and publishable.
- It does not use paid data, production systems, or real funds.
- It does not commit the thesis to a defence date; that input is needed to finalize the phase calendar.

---

## 13a. Progress log (appended; this branch is now the canonical copy of the plan)

**2026-11-08/09 — Phase 1 pilot results (details in `research/multiagent-v2/STATE.md`).**
- Corpora: Wayback discovery complete (CoinDesk 22K, Cointelegraph 30K, The Block 26K dev-window articles after
  dedupe and pre-2022 exclusion); fetch worker running at ~1,230 articles/h; Reddit ingest running. Common Crawl
  was too sparse to use.
- Dossier builder v2.4: canonical-masking cache (one classification per article for all assets and weeks),
  de-identified generic summaries with a proper-noun scrub, coarse numeric profile. Quality audit on 145
  dossiers: 93% with shown items, noise share 27%, zero dictionary leaks.
- **Re-identification probe (plan §5.4 probe 1) FAILS as a leakage-elimination claim:** before hardening the
  model named the asset in 81% of dossiers and the month within ±6 months in 81%; after hardening 52% and 69%.
  Numeric-only profile: 2% (chance). Text-only: 50%. The residual comes from asset-intrinsic content (what the
  asset does), which is the information the agents need. **Decision:** anonymization is kept as prior removal
  and date/figure masking; leakage is MEASURED per dossier (`identified` flag from the probe run on every dev
  dossier) and used as an evaluation covariate, together with the named-vs-anonymized ablation and Sealed-B.
  §5.4 target rates are replaced by this measurement design in Charter 1.
- Agent configuration v2.2 after latency measurement: providers did not honour reasoning effort or token caps on
  DeepSeek V4-Pro (~2,000 reasoning tokens, 45–60 s per call), so analysts, forecast interpreter and debaters run
  in non-thinking mode (9–15 s, cites dossier items), judge and PM think; 12 parallel workers; 12 debated assets
  per week; ordered provider pin Baidu→StreamLake (Baidu returned 5xx twice).
- Pilot week 1 (50 assets, 20 debates): 0 failures, order-swap Spearman 0.91 (floor 0.75), mean |Δp| 0.017,
  abstain 4%, $2.27 per week with 20 debates (≈ $1.75 with 12). Dev run (156 weeks) ≈ $275 at these rates.
- Charter 0 (extraction) FAIL recorded earlier; dossier uses summaries, not typed events.
- Credit recharged to $20 on 2026-11-09; pilot completed (order-swap 0.89, repeat 0.91, 0 failures, $2.07 per week),
  the rule-twin book replaces the PM prompt as primary constructor; 1,500 dossiers built for Jan–Jul 2022 (typing $1.53).
- Identification probe on all 1,500 dossiers: 51% of assets identified (65% for top-20 assets, 40% for smaller),
  month within ±6 months 89%; flags stored per dossier for the identified-subset analysis. Credit ≈ $0.6 again.
- **Blocker:** a further top-up (≈ $400 for the dev run, ≈ $700 through the sealed windows) is needed before the dev run.

## 14. Decisions

Resolved 2026-11-08 with the user:

1. **Submission deadline:** 8 January 2027. Plan fitted in section 10.
2. **Budget:** pro-judgment DeepSeek stack, about $1,500 total, about $530 for the dev run.
3. **Universe and cadence:** top-50 perps weekly plus the BTC/ETH daily arm.
4. **Provider:** DeepSeek via OpenRouter (V4-Pro judgment roles, V4.1-Flash classification, V3.2 chronological control). Claude Opus 5.5 kept as the $120 frontier ablation.
5. **Reddit and Common Crawl News:** admitted, survivorship disclosed.
6. **Chronological control:** V3.2, included.
7. **Forward run:** this devbox now; a dedicated VPS later, outside the thesis window.

Prerequisite before Charter 0: an OpenRouter API key on the devbox (`OPENROUTER_API_KEY`) with a credit limit set to the charter cap.

---

## Appendix A. Evidence pointers

- Falsification record: THESIS_FINDINGS §23.11, §23.12, §33, §40, §48, §62, §63, §64, §65; `LLM_INTEGRATION_PROPOSAL_2026-08.md`; `SENTIMENT_EARLY_WARNING_RESEARCH_2026-07-14.md`; `crypto-research-loop/KILLED.md`.
- Retrieval code reviewed: `tradingagents/agents/analysts/crypto_sentiment_analyst.py`, `tradingagents/dataflows/crypto_sentiment_pit.py`, `tradingagents/dataflows/news_data_pit.py`, `tradingagents/agents/utils/anonymizer.py`, `tradingagents/agents/utils/agent_utils.py::build_instrument_context`, `scripts/llm_event_xs_extract.py::anonymize`.
- Reusable assets: `data/llm_rank_xs/cards.parquet` (47.5K cards); `data/llm_event_xs/` (400 adjudicated labels, gates, extractor outputs); `data/sentiment/{alpaca,gdelt,hf_btc}` (laptop / Storage Box); `tradingagents/xsect/pair_xs.py`; `scripts/llm_pair_xs_p2_score.py` (residualized IC + GBDT twin protocol); `research/llm-jev-event-2026-09-29/` (Jev probe, registered, never run); `tradingagents/llm_clients/{anthropic_client,replay_cache,multi_sample}.py`; `tradingagents/execution/live`; monitor UI.
- Thesis: `thesis-latex/chapters/02_system_design.tex` (multi-agent component), `05_post_audit.tex` (LLM re-test, other roles), `07_checkpoint.tex` (implications for the hybrid assignment).
