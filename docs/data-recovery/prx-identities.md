# PRX contract identity evidence — September 10, 2026

## Disposition

Official Binance notices identify termination and automatic settlement of the old **TOMOUSDT, RNDRUSDT and MATICUSDT USDⓈ-M perpetual contracts**, followed by separate successor-contract launches. The token conversions are 1:1; the notices do not provide an automatic transfer of the old perpetual positions into successor perpetuals. The six unavailable PRX outcomes therefore cannot be repaired by renaming columns, joining successor prices, carrying the last old price forward or treating settled cash as subsequent contract prices.

This is documentary identity research only. No price series, settlement cashflow, P0 statistic, model fit or backtest was produced. Original sources, gates, results and raw stores were unchanged. The six outcomes and 25-observation minimum are taken from the frozen [PRX result review](../reevaluation/prx-result-review.md); its result SHA256 remains `799662b5ec8307aa9ca4008aef0b3d219a79c40a37dddebcbb0f8606cffba3ce`.

## Official chronology

Event times below are UTC and are the **announced** restrictions, closures and launches. They are not account-level execution receipts or recovered settlement prices. Publication times are confirmed from the public CMS `publishDate` epoch-millisecond field, rounded to the minute in this table.

| Old perpetual | Closure notice publication | Restriction on new positions | Announced position closure / automatic settlement | Separate successor perpetual launch |
| --- | --- | --- | --- | --- |
| TOMOUSDT | 2023-11-06 09:30 | 2023-11-14 08:30; existing positions could still be closed | 2023-11-14 09:00; pending orders canceled and contract delisted after settlement | VICUSDT: 2025-03-12 17:00; launch notice published 2025-03-12 14:59 |
| RNDRUSDT | 2024-07-10 06:30 | 2024-07-16 08:30 | 2024-07-16 09:00; contract delisted after settlement | RENDERUSDT: 2024-07-26 10:00; launch notice published 2024-07-26 08:30 |
| MATICUSDT | 2024-08-28 09:00 | 2024-09-04 08:30 | 2024-09-04 09:00; contract delisted after settlement | POLUSDT: 2024-09-13 12:15; launch notice published 2024-09-13 09:30 |

Sources for each row: [TOMO closure/rebranding](https://www.binance.com/en/support/announcement/detail/034eee2293964e26b915b1ec5c42972a) and [VIC futures launch](https://www.binance.com/en/support/announcement/detail/08e0ea0b2c534dffab50f42c3776895c); [RNDR closure/swap](https://www.binance.com/en/support/announcement/detail/d1f2ae8d99b24439a7a900caa9bb6b3b) and [RENDER futures launch](https://www.binance.com/en/support/announcement/detail/3e0b3e47a09c4e7ea6963d467c1eec28); [MATIC closure/swap](https://www.binance.com/en/support/announcement/detail/6a6de383727f4659a3050f7982e1620f) and [POL futures launch](https://www.binance.com/en/support/announcement/detail/36118ab7d3684330ac7113fe489b4827).

The TOMO notice describes a suspension at 08:30 while expressly allowing position closure afterward; it must not be interpreted as full closure at 08:30. For MATIC, the separate COIN-M closure is 09:30; that time does not apply to the USDT-margined contract.

### Token rights versus futures identity

Each rebranding/swap notice states one old token for one successor token. Those token-balance arrangements coexist with explicit futures position closure and later separate relisting. VIC spot trading was scheduled for November 24, 2023 at 08:00; that is **not** the VICUSDT perpetual launch, which the separate notice places in March 2025. RENDER spot trading was scheduled for July 26, 2024 at 08:00, two hours before its perpetual launch. POL spot trading was scheduled for September 13, 2024 10:00, before its 12:15 perpetual launch. The successor launch tables identify separate USDⓈ-M contracts settled in USDT. [TOMO/VIC](https://www.binance.com/en/support/announcement/detail/034eee2293964e26b915b1ec5c42972a), [RNDR/RENDER](https://www.binance.com/en/support/announcement/detail/d1f2ae8d99b24439a7a900caa9bb6b3b), [MATIC/POL](https://www.binance.com/en/support/announcement/detail/6a6de383727f4659a3050f7982e1620f).

**Inference:** token-level 1:1 conversion does not establish continuity of perpetual prices, funding, position rights or the old estimated hedge ratio. The cited notices authorize closure of old futures positions; no successor-perpetual position entitlement was found in them. Spot/margin token conversions and MATIC COIN-M wallet arrangements cannot be imported into USDT-margined PRX accounting.

## Consequence for the six frozen outcomes

| Persistence month | Selected pairs | Saved paired daily observations | Identity finding and permissible measurement |
| --- | --- | ---: | --- |
| November 2023 | BCHUSDT–TOMOUSDT; BTCUSDT–TOMOUSDT | 14 each | Announced old-contract termination falls on November 14, leaving fewer than 25 possible daily observations in that month. VICUSDT futures did not launch in November. The original monthly persistence outcomes remain unavailable. |
| August 2024 | OPUSDT–RNDRUSDT; BCHUSDT–RNDRUSDT; MATICUSDT–RNDRUSDT | 0 each | RNDRUSDT termination precedes August. RENDERUSDT is separately launched; its August prices cannot supply the old RNDR contract outcome. These are not ordinary internal gaps in a continuing RNDR contract. |
| September 2024 | MATICUSDT–LTCUSDT | 4 | Announced termination on September 4 precludes 25 old-contract daily observations in September. A later POLUSDT launch does not extend MATICUSDT's life. The original monthly persistence outcome remains unavailable. |

This interpretation follows from the registered minimum and the official lifecycle dates; no new stationarity statistic was calculated. Even a fully verified terminal settlement would supply a closure/cash event, not the missing post-termination daily prices needed for the original fixed-beta ADF outcome. Shortening the month, changing the observation minimum, substituting spot/successor contracts or removing the affected pairs from the denominator would change that measurement contract.

The notice chronology also matters for any separately registered eligibility correction. The TOMO notice postdates the November 1 formation decision; it cannot be used retroactively to exclude the pair on that date. RNDR termination precedes the August 1 decision, and the MATIC notice precedes September 1. An explicitly registered instrument-lifetime policy could distinguish those situations; it would not retroactively complete the six frozen outcomes. The original 50-month denominator and incomplete-panel qualification remain intact.

## Settlement evidence still absent

The individual announcements establish scheduled automatic closure but do not supply final per-contract settlement prices, account fees, funding cutoffs or execution receipts. The currently served [Binance futures-delisting FAQ](https://www.binance.com/en/support/faq/detail/dd60dfbf654d4055aa6b217ea6d5ddba) describes a final-30-minute, 1,800 one-second index-value average and a taker settlement fee. It is visibly updated February 11, 2026 and refers to legal terms effective January 5, 2026. Its current text is **not sufficient evidence of the exact rules applicable in 2023–2024**. No historic settlement formula, cash price or fee was inferred from it. BZRX/BNX/LUNA settlement research is maintained separately by the accounting task.

## Retrieval receipts and temporal limits

Official English announcement/FAQ pages were read using the web tool on September 10, 2026. Public CMS GET requests used:

```text
https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=<code>
Accept: application/json
Accept-Language: en-US
```

All seven successful responses below returned HTTP 200, API code `000000` and `success=true`; no credentials or authenticated endpoints were used. The initially tried path without `/query` returned 404 and supplied no evidence. The seven exact response bodies are archived with an immutable [request and hash manifest](../../data/recovery/2026-09-10/prx-identities/manifest.json) in the separately authorized recovery namespace. The archive totals 641,450 response bytes and was captured after recovery charter commit `78b4fe9`. No historical raw store or market-data series was changed. Earlier in-memory discovery receipts at 07:04 UTC have matching full-response and body hashes; the table records the later archived retrievals.

| Code / document | Retrieved UTC, 2026-09-10 | `publishDate` UTC from CMS |
| --- | --- | --- |
| `034eee2293964e26b915b1ec5c42972a` — TOMO | 07:10:18.926158 | 2023-11-06 09:30:14.259 |
| `08e0ea0b2c534dffab50f42c3776895c` — VIC | 07:10:19.287613 | 2025-03-12 14:59:27.497 |
| `d1f2ae8d99b24439a7a900caa9bb6b3b` — RNDR | 07:10:19.652098 | 2024-07-10 06:30:03.071 |
| `3e0b3e47a09c4e7ea6963d467c1eec28` — RENDER | 07:10:20.010491 | 2024-07-26 08:30:05.766 |
| `6a6de383727f4659a3050f7982e1620f` — MATIC | 07:10:20.365447 | 2024-08-28 09:00:07.402 |
| `36118ab7d3684330ac7113fe489b4827` — POL | 07:10:20.722837 | 2024-09-13 09:30:04.612 |
| `dd60dfbf654d4055aa6b217ea6d5ddba` — delisting FAQ | 07:10:21.048139 | 2020-10-02 02:36:38.950 |

| Document | SHA256 of exact HTTP response bytes | SHA256 of UTF-8 `data.body` string |
| --- | --- | --- |
| TOMO | `65cc9cfc645d56ca3e1e5e1150000cd044a693dce427521abbdbff29dd9d3e59` | `6d11b0ec62bd483f81bcdbe60d9be66f05b6098cb83c32792f550a22ea14b47a` |
| VIC | `9458363ca18be68c8227d6d373a66a2cb5ad960343fe6625bce93f75c6e3cb98` | `469062b14ea4582d491faba6e0a7da27fc01b373b7b31c504b15c5c2c6504677` |
| RNDR | `bd7352f9b8fb2a2ed5eff584db1e1b704e0226e038bca24926495154b4644968` | `99c562787061e9063b439df765176a5d395187c38971f6849e3e18d381e5bd15` |
| RENDER | `8463f6b329c9bd20b0fa5e828d1882d5a1c4121f24a6d74463ac5b736c6275b3` | `635f7094d028d79e3e7f17c32029cc658e9ca49403aa2509d654c0fbcd32e3f4` |
| MATIC | `66649f9211fe79e11d16ec297942d12d36561be728c3a920aed3cbbe88d6cbed` | `647c88a69cca6139e7ec7c439adb52f437ba27673305672e4a96020a4a7d8e36` |
| POL | `5bae4bd806b59360dd1d4ef7ee3dab90100d8829cf88bddf80f247aad60eeac5` | `c744087254cb133923da20cb0b002047f5c86adc045c780d8bf6167d3faffadd` |
| Delisting FAQ | `662dc6368efd28a1088daea38e45a2f6d989cf3aa7471974b135f459e8305722` | `cf80e0afa64303011fc848277aca61565d013dfc8af617efc8ededed2fc5a6a0` |

All responses report `version="1"`. The six announcements report `lastUpdateTime=0`, although the VIC page expressly discloses a March 13, 2025 amendment. Zero therefore does not prove an unchanged contemporaneous article. The FAQ reports `lastUpdateTime=1770831780000`, or 2026-02-11 17:43:00 UTC. These are present-day official documentary receipts, not immutable historical information vintages. Any future executable use of announcement availability or settlement rules needs an explicit provenance contract; this research does not silently install one.
