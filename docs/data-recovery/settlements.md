# Binance perpetual settlement evidence — 2026-09-10

**Readiness: terminal cashflows remain unestablished for BZRXUSDT, BNXUSDT and LUNAUSDT.** Official notices recover the scheduled forced closures and distinguish them from spot token swaps. No final settlement-price record was recovered. A material historical rule change was identified; the current FAQ must not be projected backward. No settlement value, successor splice, new portfolio result or accounting extension was produced.

Recovery is governed by commit `78b4fe9` and `audit_data_recovery_2026_09_10`. Original raw files and September 9 results remain unchanged. The outcome is an evidence-readiness assessment, not a strategy rejection.

## Preserved receipts

Twenty HTTP responses, all status 200, were preserved under `data/recovery/2026-09-10/settlements/`. The request-start interval was **2026-09-10 07:08:28.821784–07:08:38.668309 UTC**; downloads totaled **1,852,514 bytes**. `manifest.json` records each exact URL, parameters, retrieval time, provider, status, byte count and SHA256. Its SHA256 is `3fd6497f747b4c15d574a2befa769c8ddc80df6529d26fe29370b547d3dd7926`.

The archive contains five Binance public-CMS responses, three quarterly-delivery queries, six one-minute mark/index queries, three bounded funding queries, current exchange metadata, and two Internet Archive copies of Binance's historical FAQ. The latter are explicitly mirror-hosted official-page evidence, not a second market-data venue. Their embedded article-body strings were also extracted without alteration; the extraction is described in the manifest. No credentials or authenticated account endpoints were used.

All quoted excerpts below total no more than 25 words per source. Public CMS publication timestamps are recorded with millisecond precision, but do not certify the historical immutability of the current body. The individual notices return `lastUpdateTime=0` even where their text discloses amendments; zero cannot be interpreted as no revision.

## Scheduled contract closures

| Contract | Official CMS publication, UTC | Announced forced settlement / removal, UTC | Entry restriction directly established |
|---|---|---|---|
| BZRXUSDT | 2021-12-16 13:30:18.874 | 2021-12-19 02:00 | Notice specifies cancellation of pending futures orders at closure; no separate earlier entry cutoff stated |
| BNXUSDT | 2025-02-26 02:00:01.827 | 2025-03-17 09:00 | New positions prohibited from 08:30 that day |
| LUNAUSDT | 2022-05-12 14:59:01.271 | 2022-05-12 15:30 | No separate earlier cutoff stated in this final notice |

These are the announced schedule, not independently recovered timestamps of the final trade or completed settlement transaction. Positive-volume hourly tails documented in the September 9 review corroborate approximate cessation but cannot identify the final execution timestamp or settlement price. LUNA's closure is **May 12 at 15:30**, earlier than the May 13 first missing daily mark. An event-aware book would have to terminate the contract at the supported event time rather than waiting for a missing row.

### BZRXUSDT

The [Binance BZRX migration notice](https://www.binance.com/en/support/announcement/detail/dff27dc6bcbb432c902bcbea5e24ddfa) states that Binance Futures will “close all BZRX futures positions” at December 19 02:00, perform automatic settlement, cancel orders and delist. It links the general delisting procedure. The page discloses a December 17 clarification, still before the scheduled closure.

The same notice separately describes a **1 BZRX to 10 OOKI token-balance conversion** and later OOKI spot trading. Futures closure is explicit; conversion of outstanding BZRX perpetual positions into OOKI perpetual positions is not granted. Last-price protection or changes to index constituents could be applied under extreme conditions. No final cash-settlement price or numeric settlement fee appears in the notice.

### BNXUSDT

The [Binance BNX-to-FORM notice](https://www.binance.com/en/support/announcement/detail/2f963977c7274e0583f16f2e26987b61) specifies “close all positions and conduct an automatic settlement” for BNXUSDT at March 17 09:00. Removal follows settlement; entries stop at 08:30. Current exchange metadata independently retains BNXUSDT as USDT-margined `PERPETUAL`, status `SETTLING`, with `deliveryDate=1742202000000`, matching that scheduled time. A current status field is not proof that a particular historical settlement completed or a position remained open afterward.

The notice's **1 BNX to 1 FORM conversion concerns token balances**. Futures relisting is to be separately announced. It gives no right to transfer the old perpetual exposure into FORM. Amendments on March 18–19 concern subsequent FORM spot/deposit scheduling; the currently retrieved notice is therefore a revised body. No final futures settlement price appears.

### LUNAUSDT

The [final LUNA USDT-margined closure notice](https://www.binance.com/en/support/announcement/detail/ef3ce76d5c2d45ee9b6dc3f281cde744) says “delist this contract at 2022-05-12 15:30 (UTC)” following automatic settlement. Publication was about 31 minutes earlier. No final price or fee is specified.

A [separate precautionary notice](https://www.binance.com/en/support/announcement/detail/d6b1ee2e3e724125acf0e2678fe2ec8c), published at 13:48:40.568, discusses the USDT contract's tick-size constraint and a delisting trigger below 0.005 USDT. It separately launches **LUNABUSD** at 15:00 with BUSD collateral and a finer tick. That is not a continuation of LUNAUSDT; multi-asset collateral capability does not establish transfer of positions. Neither notice justifies substituting LUNABUSD, a later LUNA contract, or a renamed token.

## Historical settlement rule differs from today's rule

The Binance FAQ is [currently available here](https://www.binance.com/en/support/faq/detail/dd60dfbf654d4055aa6b217ea6d5ddba). It was originally published October 2, 2020, but its current CMS body was updated **February 11, 2026, 17:43 UTC**. It now specifies a 30-minute average of 1,800 one-second index observations and settlement fees equal to taker fees.

The [December 24, 2021 archived Binance page](https://web.archive.org/web/20211224102630id_/https://www.binance.com/en/support/faq/dd60dfbf654d4055aa6b217ea6d5ddba) and [May 25, 2022 copy](https://web.archive.org/web/20220525030936id_/https://www.binance.com/en/support/faq/dd60dfbf654d4055aa6b217ea6d5ddba) have **identical decoded article bodies**. They specify mark-price calculation “over the last hour before cessation”: 3,600 index observations, a ten-minute reduce-only period and trading fees on automatic settlement. They do not identify a numeric or explicitly taker settlement fee.

The December snapshot is five days after BZRX closure; it does not prove the exact rule applied then. The two copies bracket LUNA's date but do not exclude an intervening rule or emergency exception. Neither establishes BNX's March 2025 rule. Historical applicability and the actual settlement print still require evidence.

| Archived object | SHA256 |
|---|---|
| December 2021 HTML | `f4ea3c31788cea217d07bddf5f1e441c2746b29100efa0c1f3f09f2d23fb354b` |
| May 2022 HTML | `0af7da68384912b061b2048f66e157421ecfa62debfc8d3d8119ca585e935fc9` |
| Identical historical article-body strings | `9aacdea97d52866685b27ea7976d3b6a5ac43782cf1bfbad951b8340c5fd04de` |
| Current FAQ article-body string | `cf80e0afa64303011fc848277aca61565d013dfc8af617efc8ededed2fc5a6a0` |

## Public price and funding probes

Binance's [public USDT-M market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) identifies `/futures/data/delivery-price` as a quarterly contract settlement endpoint. Queries with `pair=BZRXUSDT`, `BNXUSDT` and `LUNAUSDT` each returned `[]`. These empty responses do not show that settlement did not occur; they simply yielded no record for these perpetuals.

The six one-minute queries use `markPriceKlines` with `symbol`, or `indexPriceKlines` with `pair`; `interval=1m`, `limit=3`, and a range from one minute before the announced closure through one minute afterward. All yielded three bars. These are OHLC prices, not an actual settlement-price field. Both price series continue changing after the announced time. A minute OHLC candle cannot reproduce a 1,800- or 3,600-observation second-level average.

| Contract | Last pre-closure minute's mark close | Same minute's index close | Previously preserved trade-tail close |
|---|---:|---:|---:|
| BZRXUSDT | 0.22835017 | 0.22821707 | 0.2301 |
| BNXUSDT | 1.81044042 | 1.93985637 | 2.0 |
| LUNAUSDT | 0.00682760 | 0.00697000 | 0.008 |

**None of these columns is admitted as the settlement price.** Their differences directly reject the assumption that a frozen trade tail is an adequate substitute. The mark at the opening of the next minute is also not promoted to a settlement record.

Each funding request uses the contract symbol, `limit=30`, and a 48-hour interval centered on the announced closure. The last returned observations preceding it are:

| Contract | Funding timestamp, UTC | Rate as returned | Associated mark price |
|---|---|---:|---:|
| BZRXUSDT | 2021-12-19 00:00:00.031 | 0.00010000 | Missing string |
| BNXUSDT | 2025-03-17 08:00:00 | 0.00427083 | 1.81798982 |
| LUNAUSDT | 2022-05-12 08:00:00 | -0.00750000 | Missing string |

All responses also contain later rates. They are public history records, not proof of charges to positions already closed. No post-closure exposure can be justified by continued rate publication. Exact funding cashflows require the supported position lifetime, quantity and applicable funding valuation; BZRX/LUNA responses omit the associated mark. None of the individual closure notices supplies a special final funding adjustment or a numeric settlement fee. No adjustment was inferred.

## Remaining evidence required

1. **Actual final settlement price**, or an applicable historical rule plus the complete required observations and precise averaging/rounding convention. An announced closure time, minute candles and a matching current `deliveryDate` do not supply this.
2. **Historical settlement-fee treatment**, including the applicable basis/rate or an explicit permitted conservative model. Today's FAQ does not establish the old fee. The historical archived page confirms a charge but leaves the exact treatment unresolved.
3. **Final funding treatment and valuation**, stopping exposure at the supported closure event, with no post-event accrual inferred from a continuing public series.
4. **Event-accounting design and synthetic validation**, then a separately committed replay registration, only after evidence admission. The present recovery gate authorizes neither a strategy replay nor altered trading rules.

The bounded search is complete. Closure discovery materially improves lifecycle provenance, but **none of the three terminal cashflows is ready for an exact replay**. The missing-evidence status is retained; no cashflow is fabricated and no strategy FAIL is inferred from this limitation.

## Scope addendum: BNX's February 2023 contract incarnation

Under the `6f84e4b` scope addendum, four additional official CMS responses were archived at `settlements/bnx-2023/`, with their own immutable `manifest.json`. They were requested at 07:12:54.240114–07:12:55.676477 UTC on September 10, all returned status 200, and totaled 89,403 bytes. That manifest's SHA256 is `bd03b474cd8d421d7ec98f225d0b36ce4b4dc4bcd314c021bf065d24670aa372`. No price request or portfolio computation was made for this extension.

The [February 10 token-split notice](https://www.binance.com/en/support/announcement/detail/4d23ada51a2e4fa182835c77d51ba1a9), published at **2023-02-10 04:30:03.357 UTC**, establishes:

- New trading was suspended at February 10 14:00 UTC, with closing existing positions still allowed.
- All old USDT-margined BNX perpetual positions were to be settled and pending orders cancelled at **February 11 04:00 UTC**, followed by delisting.
- Token balances were to convert at **1 old BNX to 100 new BNX**. This does not transfer old perpetual positions; their closure is separately specified.

The [perpetual relaunch notice](https://www.binance.com/en/support/announcement/detail/940d0e48493e4627889c3f46371df70b), published at **February 22 10:15:04.236 UTC**, specifies a new **BNXUSDT** perpetual launch at **February 22 14:45 UTC**, settled in USDT. Crucially, the old settled contract is explicitly renamed **BNXUSDTSETTLED**. Its historical candles are said to remain accessible through `GET /fapi/v1/klines` for that old identifier, while old continuous-candle access was removed from `GET /fapi/v1/continuousKlines` at February 22 06:30 UTC. This is direct official instrument-identity evidence, not an inferred ticker mapping. Availability of that old endpoint has not been tested in this extension.

The [token-swap completion notice](https://www.binance.com/en/support/announcement/detail/a29c5916cc9f460dbf00ccefa28e19e5), published at **February 22 09:30:04.442 UTC**, separately identifies old spot tokens as **BNXOLD** and confirms **1 BNXOLD to 100 BNX** distribution. `BNXOLD` is a token/spot identity and must not be confused with the perpetual history identifier `BNXUSDTSETTLED`. The spot-chart scheduling notice `fb6c6a1c6a9947b0bd30d58314ab862c` is also retained as context; it is not futures execution evidence.

The already archived current `exchangeInfo` reports `onboardDate=1677049200000`, which converts to **February 22 07:00 UTC**. This is earlier than the announced 14:45 trading launch. It must not replace the launch time. A first complete hourly bar at 15:00 would be yet another clock concept, not proof that trading launched then.

**Readiness implication:** the reported February 1–22 hourly hole cannot be admitted as one ordinary missing-price block. It includes missing observations belonging to an old contract before February 11, a genuine interval after that contract's closure, and the later new-contract launch. Old and new returns, eligibility age, momentum history, funding and positions require separate identities. The token conversion ratio is insufficient to rescale and concatenate perpetual price histories or carry a position across the settlement.

The preserved daily manifest previously inspected starts BNXUSDT on February 22, 2023, whereas the hourly history extends into 2022. This review therefore does not assert that the present daily price file already splices both incarnations. It establishes a specific risk for joining independently sourced histories or repairing the hourly hole under a reused ticker. Any admissible old-contract recovery must preserve `BNXUSDTSETTLED` provenance and terminate its book separately. Its final settlement cashflow was not recovered or fabricated in this identity-only extension.
