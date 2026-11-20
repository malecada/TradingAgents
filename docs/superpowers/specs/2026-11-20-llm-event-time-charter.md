# Event-time study of the reader records (`llm-event-time`) — DRAFT, NOT FROZEN

**Status:** draft of 2026-11-20. Stage V0 is complete: code, 12 offline tests, the event table built from text
stores only, and the pass rate and power of the gate measured on events moved to a time at which their news
did not exist. Nothing is registered, no attempt is claimed, and no record has been joined with a price at or
around its publication time. The open decisions are in §8. The registration script refuses to write while the
title carries the draft mark.
**Family:** new family `llm-event-time`, attempt 1 of 2 (§8, decision 1).
**History:** family `llm-multiagent-v2`, six attempts, all FAIL, closed on 2026-11-17
(`research/multiagent-v2/STATE.md`). Its records are reused; its verdicts are not reopened.

## 1. Why this study

The six attempts of the closed family share one property: the agents decided long after the news. The weekly
designs decided on Saturday 00:00 UTC, the daily design at 00:00 UTC, about ten hours after a typical article.
In every run the direction judged by the agents carried no information on returns beyond price history and
the count of news items. The first explanation given for this is that the information was already in the
price when the agents decided.

That explanation has never been measured in this repository. The earlier no-go on event-driven news trading
(2026-07-14) rested on published studies. Charter 4 moved the decision to within a day of the news and stated
that it could not test the reaction itself, because the store held publication dates without a time of day
and daily bars.

Both limits are now removed without a model call:

- The news feed archive added for Charter 5 carries publication times to the second, and its URLs give the
  same for 8,645 documents of the three outlets of the page archive.
- A store of minute bars of 88 perpetual contracts covers 98 % of the events (§3.2).

The study places every fact record with a direction at the publication time of its document and measures the
return of the asset from minutes after it. It answers two questions. The gate asks whether the direction read
by the agents is still tradable five minutes after the publication. The descriptive tables show when the
price moves: before the publication, in the first minutes, or later.

A FAIL is the expected outcome. Its use is that the first explanation becomes a measurement: either the move
is over before a reader can act (then no change to the agents can help on public news), or no move follows
the direction at any time (then the reading itself carries nothing). A PASS would be the first positive
result of the programme and would license one confirmation on data after the window (§5).

## 2. Question

Does the direction that the reader agents give to an asset-specific news event (favourable or unfavourable)
separate the market-relative return of the asset's perpetual contract from 5 minutes after the publication to
4 hours later, on the lead events of 2023 and 2024?

## 3. Design

### 3.1 Events and clocks

An event is one fact record of the reader agents about one asset in one news document. The records are those
of Charter 2 (page archive: CoinDesk, Cointelegraph, The Block) and Charter 5 (news feed archive, 67 further
outlets), written under the frozen Charter 2 instructions by two readers and an adjudicator from a
de-identified summary of at most two sentences. A record carries a direction (favourable, unfavourable,
neutral, mixed), an event class, a status and a materiality. Community posts are not used. Documents typed as
price recap were never read, so no record describes a price move as its event.

Every event gets one of three clocks:

| Clock | Rows | Event time |
|---|---|---|
| publication | feed rows ingested live; page-archive rows with a publication time from the feed | publication time to the second |
| capture | page-archive rows without a feed match | first capture of the page (median 0.2 to 0.3 hours after publication) |
| late | feed rows ingested after the fact | time from which the row was observable |

Only the publication clock enters the gate. A page-archive document receives a publication time when its URL
matches exactly one feed row, the time is not later than the first capture plus five minutes, and it lies
within two days of the stored publication date. Feed times are converted from Iran local time (Charter 5,
source audit).

### 3.2 Lead events

The gate uses lead events. A lead event is a record with a direction, on the publication clock, of an
asset-specific class, with no earlier lead event of the same asset in the 4 hours 5 minutes before it. The
positions of one asset therefore never overlap, as for a trader who does not re-enter while holding. Further
events inside the window are counted, also those with the other direction.

Three classes are not asset-specific news and never lead: `opinion_or_forecast` (analyst views and price
forecasts, 56 % of all signed records of the feed outlets), `market_wide_or_macro` (the outcome is
market-relative) and `other`. They are reported descriptively.

Counts in the test window, built without any price (`data/eventtime/events_report.json`):

| Measure | Value |
|---|---|
| Signed news records, publication clock | 15,731 |
| Signed news records, capture clock / late | 5,477 / 236 |
| Lead events on assets other than the market contract | 3,375 |
| of these with minute bars | 3,316 (98.3 %) |
| By year | 2023: 1,529; 2024: 1,787 |
| Favourable / unfavourable | 2,262 / 1,054 |
| Page-archive outlets / feed outlets | 699 / 2,617 |
| Assets / days with an event / median events per day | 54 / 689 / 4 |
| Largest assets | ETH 1,000; XRP 402; SOL 378; SHIB 292; MATIC 155 |
| First news on the asset in 24 hours ("fresh") | 593 |
| With a further event inside the holding window / with an opposed one | 743 / 269 |

### 3.3 Returns

Prices are open prices of minute bars of the USDT perpetual contracts. The price at a time is the open of the
first bar at or after it, at most five minutes late; otherwise the return is missing. Returns are simple
returns. The market contract is BTC; the outcome of an event on another asset is the return of its contract
minus the return of the market contract over the same window. Events on BTC are reported with raw returns and
are outside the gate.

| Window | From | To |
|---|---|---|
| before, k = 1,440, 240, 60, 15 minutes | k minutes before the event time | event time |
| first minutes, d = 1, 5, 15, 60 | event time | d minutes after |
| after, d = 0, 1, 5, 15, 60 and h = 15, 60, 240, 1,440 | d minutes after the event time | h minutes later |

The registered cell is d = 5, h = 240: entry five minutes after the publication, exit four hours later.

### 3.4 Statistic

The gate statistic is the slope of the outcome on the sign of the event (+1 favourable, −1 unfavourable) with
one intercept per calendar year, over the lead events. The slope is half the difference between the mean
outcome after favourable and after unfavourable events. Its standard error is clustered by UTC day.

A plain mean of sign times outcome is not used as the gate: 68 % of the lead events are favourable, so it
would book the average drift of the assets against the market as an effect of the news. The intercept takes
that drift. The plain mean is reported descriptively.

## 4. Stages

| Stage | Content | State |
|---|---|---|
| V0 | Code (`tradingagents/eventtime/study.py`, `scripts/evt_*.py`), tests, event table, noise pass rate and power | done |
| V1 | Decisions of §8, draft mark removed, commit; from then on this text stays byte-identical | open |
| V2 | Digest of the minute bar store, registration, pre-flight with a rehearsal on synthetic returns | open |
| V3 | One registered run: the single join of events with minute bars, verdict by code | open |

Results are written to `research/multiagent-v2/STATE.md`, never into this charter.

## 5. Gates

- **G1:** slope of the registered cell positive with a clustered t of at least 2.0.
- **G2:** slope positive in 2023 and in 2024.
- **Verdict:** PASS when both hold, otherwise FAIL. No re-run, no re-estimation and no change of estimator on
  this window under this charter.
- **Size reading (no gate):** "above cost" when the slope is at least 10 basis points per event (one contract
  in and out at 5 basis points per side), otherwise "below cost". A hedge with the market contract doubles
  the cost.

A PASS does not validate a strategy. It licenses one confirmation charter on events after 2024, which needs
new reader records and its own approval. A FAIL closes the direction of the present records at the registered
cell; the descriptive tables then say which reading of the failure applies (§1).

**Noise pass rate and power** (`data/eventtime/null_gate.json`, 2,000 draws per row). The lead events keep
their asset and time of day and are moved back by 104 weeks, where their news did not exist; 2,878 of them
have bars (37 assets, 678 days). Signs are a random permutation of the real sign vector. The outcome at the
moved times has a standard deviation of 187 basis points.

| Planted effect per event | Pass rate |
|---|---|
| none | 2.2 % |
| 5 bp | 25.7 % |
| 10 bp (the cost) | 74.8 % |
| 15 bp | 96.2 % |
| 20 bp | 99.95 % |

The test detects an effect of the size of the cost with a power of about three quarters. This is the highest
power of the programme: the weekly and daily designs needed effects several times their cost.

**Descriptive tables** (no claim, no multiplicity allowance): the slope in every window of §3.3; the share of
the move from one day before to one day after the event that is done before the entry; splits by freshness,
materiality, status, outlet group, event class, with and without ETH; opinion records; capture-clock records;
the market contract; mean outcome by sign; the plain signed mean; a permutation of the signs within the day.

## 6. Leakage and exposure

- **Order of work.** The event table, the lead rule, the class exclusion, the form of the statistic and the
  registered cell were fixed from text stores and from bars at moved times only. The change from a plain
  signed mean to a slope was made before any real outcome, for the reason in §3.4.
- **Exposed window.** Daily and weekly returns of 2023 to 2024 were joined with features of the same records
  in Charters 2 to 5. The minute bars were used by one earlier programme on passive execution, without text.
  The registration states the window as exposed.
- **Recall.** The reader model was released after the window. It read de-identified summaries, and the model
  named the hidden asset in 35 to 50 % of dossiers in the probes of the closed family. A direction can
  therefore carry memory of what followed. This works in favour of a PASS and is the reason a PASS licenses
  only a confirmation after the window.
- **Publication times.** In the source audit 0.75 % of the joined articles carried a publication time later
  than their first capture (updated articles); the rule of §3.1 drops them. A feed time later than the true
  publication errs towards "already priced".
- **First report.** The outlets are not the first source of most events; exchanges, project accounts and
  social media precede them. The windows before the event measure this. The study speaks about news articles
  as a source, not about every public source.
- **Selection of assets.** The minute bar store was built for the earlier execution programme. 59 lead events
  (1.7 %) fall on assets without bars and are dropped; the assets are listed in the events report.
- **Latency.** The typing and reading calls took seconds per document in the extraction runs. Five minutes
  from publication to entry is taken as attainable; one minute and zero are reported as bounds.

## 7. Budget

No model call and no data purchase. Running time: about one minute for the event table, a few minutes for the
join with minute bars.

## 8. Decisions

The first option of every row is implemented and recommended. A change of rows 2 to 6 needs new draws for the
table of §5 before the freeze.

| # | Decision | Implemented | Alternative |
|---|---|---|---|
| 1 | Family | New family `llm-event-time`, 2 attempts; the closed family stays closed and is cited | No new run; shortfall 1 stays a cited explanation in the thesis |
| 2 | Registered cell | Entry 5 minutes after publication, exit 4 hours later | 1 minute and 1 hour; 15 minutes and 24 hours |
| 3 | Gate events | Asset-specific news classes; opinions, market-wide items and `other` descriptive | All signed records (6,928 lead events, 56 % opinions) |
| 4 | Statistic | Slope on the sign with an intercept per year, clustered by day | Plain signed mean (books the common drift) |
| 5 | Outcome | Return minus the market contract; BTC events descriptive | Raw returns |
| 6 | Threshold and size | t ≥ 2.0 (noise 2.2 %); size against cost as a reading | Third gate: slope ≥ 10 bp |
| 7 | Assets without minute bars | Dropped (59 events) | Download their bars from the exchange's public archive first |
| 8 | Second attempt | Reserved; its design is chosen after this run under its own charter | Budget of 1 |

## Appendix. Files

| File | Role |
|---|---|
| `tradingagents/eventtime/study.py` | Event table, lead rule, bar prices, return windows, slope, gate, descriptive tables |
| `scripts/evt_events_build.py` | Publication times by URL (once) and the event table with its counts; no price |
| `scripts/evt_null_gate.py` | Noise pass rate and power on moved events |
| `scripts/evt_register.py` | Digest of the bar store and the registration |
| `scripts/evt_run.py` | Pre-flight, rehearsal on synthetic returns, the registered run |
| `tests/research/test_eventtime.py` | 12 offline tests |
| `data/eventtime/` | `pub_times.parquet`, `events.parquet`, `events_report.json`, `null_gate.json` (not in version control) |

The raw feed dump (CC-BY-NC-4.0, attribution in the thesis) stays outside the repository.
