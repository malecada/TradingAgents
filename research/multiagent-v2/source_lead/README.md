# Sources that precede the news articles: exploration (2026-11-20)

Exploratory. No outcome column or price is read, no model call is made, nothing is registered and no attempt
is claimed. The event-time study of the same day (`../STATE.md`, last run) showed that the direction of a
reader record agrees with the price move of the day before its article and with nothing after it. This
exploration asks which sources appear before the articles, whether they can be obtained for 2023 to 2024
with exact time stamps, and what they cost.

Two parts: an availability audit by web research and endpoint probes (§1 to §3), and a measurement on time
stamps of the sources that could be obtained at once (§4).

## 1. X (Twitter)

| Route | Coverage of 2023 to 2024 | Time stamp | Cost | Terms | Verdict |
|---|---|---|---|---|---|
| Official X API, full-archive search (`/2/tweets/search/all`, `from:` and cashtag operators) | complete according to the documentation; not tested (needs an account) | second | pay per use, $0.005 per post returned, at most 3 million posts per month; day or hour counts at $0.01 per request | developer agreement; only IDs may be redistributed | usable, bound by cost |
| Public cashtag ID set (`twitterapi-io/x-cashtag-mentions-2024-2026`, Hugging Face) | measured: 2024-01-01 onwards, every day present, 14.8 million IDs in 2024; nothing for 2023 | millisecond, decoded from the ID | free; text needs hydration | CC BY 4.0 on the IDs; published on 2026-11-16 by a reseller not affiliated with X; collection method not documented | attention counts for 2024 only (§4) |
| Public tweets of 153 trader accounts (`StephanAkkerman/financial-tweets-crypto`) | measured earlier: 270 of 731 days without a tweet | second | free, MIT | | chart commentary with gaps (§4) |
| Wayback Machine captures of tweet pages | measured for ten fast news accounts: 20 to 70 % of the posts as IDs; text in 2 of 12 sampled captures | from the ID | free | | IDs and times only |
| Other public tweet datasets (thirteen inspected) | end by early 2023, or carry no time stamp, or cover weeks only | | | | not usable |
| Resellers of X data | history depth not stated | second | $0.15 to $0.20 per 1,000 posts (posted prices) | not affiliated with X; X prohibits access outside its interface | not recommended |
| Access for researchers under the EU Digital Services Act | | | free when granted | limited to research on systemic risks in the EU; six months for X to implement its plan from 2026-07-16 | does not fit the topic or the time |

What the official price buys: $100 is 20,000 posts and $300 is 60,000. The fast news accounts (Watcher Guru,
Wu Blockchain, Lookonchain, Whale Alert, Binance, Cointelegraph and two wire relays) are estimated at 40,000
to 100,000 posts over the two years; the exact number can be measured first with the counts endpoint for a
few dollars. The official accounts of all 200 assets (about 440,000 posts, $2,200) and broad cashtag
searches are out of reach. An earlier note in this file's parent ("no free archive; closed or enterprise
tiers") is corrected: the full archive is on the pay-per-use tier since 2026-02-06.

## 2. Truth Social and official sources

Truth Social (archive of Donald Trump's posts published by CNN, 38,108 posts, millisecond stamps, measured):

| Year | Posts | With a crypto term | Of these with own text |
|---|---|---|---|
| 2022 | 3,889 | 0 | 0 |
| 2023 | 9,905 | 1 (a bare link) | 0 |
| 2024 | 10,587 | 19, none before 2024-05-25 | 14 |
| 2025 | 6,229 | 19 | 12 |
| 2026 to 11-20 | 7,498 | 4 | 4 |

The posts that plausibly mattered (the token launch of 2025-01-18, the reserve posts of 2025-03-02, the
stablecoin act posts of mid-2025) lie in Sealed-A, which is not opened. For 2023 to 2024 the source holds
about six informative posts, all about the market as a whole. Every archive is a third-party collection; the
platform's terms prohibit automated access. Verdict: not a source for the test window.

Official sources with exact times:

| Source | Items 2023 to 2024 | Of these crypto | Time stamp | Note |
|---|---|---|---|---|
| SEC EDGAR filings (submissions interface) | 2.4 million | about 7,500 filings of 533 filers with a crypto name; 755 current reports, 135 registration statements and amendments | second, UTC | best: free, exact, legal filing event; filings after 17:30 Eastern are disseminated on the next business day |
| SEC press releases and statements | 471 | 44 by title | minute, US Eastern (labelled as UTC on the page) | accurate to minutes in three checks |
| CFTC press releases | 380 | 39 | second | the stamp can precede publication by hours (one check: up to 3.3 hours) |
| US Department of Justice interface | | 212 by title | day; the second-level field is the draft time | day level only |
| Federal Reserve releases | 275 | 12 | scheduled minute | macro |
| Treasury, Circle, Tether | | | date only or unreliable | not usable at event time |
| Court dockets (CourtListener) | | | not verified | needs an account |

These sources concern the market as a whole or BTC (exchange-traded fund filings, enforcement against
exchanges, treasury purchases). The outcome of every design here is relative to BTC, so they do not add a
cross-sectional event set; they would serve a market-level event study, which no charter covers.

## 3. Crypto-native channels

| Source | Measured for 2023 to 2024 | Time stamp | Cost and terms | Share of the universe | Verdict |
|---|---|---|---|---|---|
| Telegram public channel previews (fast headline channels: Wu Blockchain, Watcher Guru, Tree News, unfolded, infinityhedge, BWEnews; exchange channels) | 12 channels reachable back past 2023-01-01 without login, 2 to 16 posts per day each; about 1,800 page requests for the six headline channels | second, original post time | free; no robots file; Telegram's content licensing terms prohibit scraping and aggregation (read through a summary; to be checked on the page). Edited posts keep the first time, deleted posts are gone | majors-heavy | best timing among the free sources; **not fetched: the terms question is the owner's decision** |
| KuCoin announcements (public interface) | 858 listing and delisting notices fetched; 15 name one of the 54 assets of the gate events | millisecond | free | listings only | too rare for these assets |
| Upbit notices | interface answered today (blocked on 11-14); about 110 to 120 trade notices | second, Korean time | free, undocumented | listings only | narrow |
| Coinbase exchange status history | about 110 market openings | minute | free | listings only | time of trading start, not of the announcement |
| Kraken blog | 93 listing posts | second | free | small | narrow |
| Governance forums on Discourse (Uniswap, Aave, Arbitrum probed) | full history; 984, 3,545 and 2,833 topics | millisecond | free | DeFi and layer-2 tokens, an estimated 25 to 35 % | untested by any earlier programme; proposals precede votes and articles |
| GitHub releases | exact times; 12 of 22 sampled assets list a repository | second | free, 60 requests per hour without a token | chain clients | narrow |
| Exploit lists (DefiLlama, De.Fi) | 414 exploits in the window | date; De.Fi links a tweet whose ID gives the time | free | small | narrow |
| CryptoPanic dump (GitHub, CC0) | 248 thousand aggregator items until 2025-12 claimed; window not measured | second | free | high | aggregates the same articles, not earlier |
| Paid feeds (Tree of Alpha history, Messari, Tokenomist, CoinGecko news) | | | paid or no history | | not pursued |
| Farcaster (public dump, 27 GB) | all casts | second | free | small in 2023 | low priority |
| Medium, Substack, Mirror, Discord, Binance Square | feeds hold the newest 10 to 20 items; no public history | | | | not usable |

## 4. Measurement: does a source rise before the article?

`lead_probe.py` takes the 3,316 gate events of the event-time study (an asset-specific news record at the
publication time of its article) and counts the items of a source that name the same asset in windows
around that time. The same counts at placebo times of the same asset, four whole weeks before and after,
give the level expected without the event. The statistic is the mean of log(1 + count) minus the mean of
the same quantity over the placebo weeks, with a standard error clustered by day; the plain ratio of rates
is given next to it. Only time stamps and asset tags are read.

Log excess over the placebo weeks (t in brackets):

| Source | Events | 24 to 4 h before | 4 to 1 h before | last 15 min | first 15 min after | 4 to 24 h after |
|---|---|---|---|---|---|---|
| All stored news items of the 70 outlets (own article excluded) | 3,144 | +10.9 % (9.6) | +4.5 % (4.4) | +1.3 % (2.0) | +2.9 % (4.1) | +13.5 % (10.7) |
| Reddit, three forums | 3,133 | +9.4 % (6.9) | +4.5 % (4.1) | +1.0 % (2.0) | +2.7 % (5.0) | +8.5 % (6.1) |
| X cashtag posts, 2024 only | 1,647 | +5.4 % (1.9) | +7.9 % (2.9) | +3.5 % (1.4) | +5.8 % (2.4) | +5.5 % (2.2) |
| X trader accounts | 3,316 | +5.2 % (2.2) | +2.1 % (2.2) | +0.4 % (1.4) | +0.7 % (2.6) | +3.0 % (1.4) |
| Binance announcements | 3,316 | −0.3 % (−1.4) | +0.1 % (1.3) | 0.0 % (−0.2) | 0.0 % (0.3) | 0.0 % (0.2) |

Ratio of the item rate to the placebo rate in the last 15 minutes before and the first 15 minutes after the
article: news 1.05 and 1.13, Reddit 1.13 and 1.31, X cashtag posts 1.17 and 1.20, X trader accounts 1.35
and 1.48. The ratios of the two X sets rest on few items per window and are not distinguishable from one
before the article (t of the rate excess 1.3 and 1.8).

Listing articles against Binance: of 159 gate events of the class "exchange listing", 10 have a Binance
listing announcement that names the asset within 72 hours. In all 10 the announcement comes first, by a
median of 158 minutes (10th percentile 85 minutes); one article followed within an hour.

Reading:

- Every text source is more active on the asset during the day before the article, and stays so the day
  after: the article falls inside an episode of attention that began hours earlier in all of them,
  including the other outlets. No source shows a sharp rise confined to the minutes before the article.
  Reddit and the news react in the first 15 minutes after it.
- The windows differ in width, and a short window of a sparse source holds mostly zero counts, so the
  values compare sources within a column better than windows within a row. With that caution: on the X
  cashtag posts, which are dense in every window, the excess is largest 4 to 1 hours before the article.
  This is the only sign that X runs ahead of the articles, and it is weak (t 2.9 in one of ten windows,
  one year, a dataset of undocumented collection).
- A count of posts measures attention, not the event. Attention follows the price as well as news, so the
  early rise does not show that the sources report the event earlier; it is the same ambiguity as in the
  event-time study.
- Where the primary source is known (exchange listings), it precedes the article by hours.

## 5. Options

| Option | What it tests | Cost | Blocker |
|---|---|---|---|
| A. Posts of fast news accounts through the official X API as events; reader records on them; event-time test from the post (second attempt of `llm-event-time`, own charter) | whether a direction read within minutes of the first public report carries a return | X data about $100 to $300 after a count for a few dollars; reading about $5 to $10; two to three days | budget; the contest of speed at this scale was closed as a no-go on 2026-07-14 from published studies |
| B. The same with the Telegram channels of these accounts | as A | $0 | terms prohibit scraping; needs the owner's decision or permission of the channels |
| C. Governance forum posts as events | proposals before votes, DeFi and layer-2 tokens | $0 data, reading about $5 | a third of the universe; new source needs a charter |
| D. No further run; the exploration is the stated limit in the thesis | | $0 | |

## Files

| File | Content |
|---|---|
| `lead_probe.py`, `lead_probe.json` | The measurement of §4 |
| `build_extra.py` | Asset and time tables of the two public X datasets |

Third-party data (outside version control, under `data/source_lead/raw/`):

| Dataset | Files | sha256 |
|---|---|---|
| Hugging Face `StephanAkkerman/financial-tweets-crypto` (MIT) | `train.parquet`, 20,735,701 bytes | `81b2f7563a44c1a103e9468a83d52319dfeae0fc616422b4a4df90d8d684b960` |
| Hugging Face `twitterapi-io/x-cashtag-mentions-2024-2026` (CC BY 4.0, IDs only) | `tweets_2024-01` to `tweets_2025-02`, 215 MB | `data/source_lead/raw/x_cashtag/SHA256SUMS` |
| KuCoin announcements (public interface) | 18 JSON pages | local |

The web research ran with a generic user agent, without accounts or purchases. Its downloads (the CNN
archive of Truth Social posts, EDGAR indexes, press release pages) were kept in a session directory and are
not preserved; the counts above are the record.
