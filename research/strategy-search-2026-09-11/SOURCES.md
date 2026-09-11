# Source and applicability notes

Read-only independent source review completed September 11, 2026. Literature
supplies hypotheses, not executable prices, current account permissions or
evidence of profit. Publication and retrieval dates are different.

- [BIS Crypto carry](https://www.bis.org/publications/working-paper-1087-crypto-carry),
  April 4, 2023; [revised PDF](https://www.bis.org/publ/work1087.pdf), October 2025.
  Leveraged demand and limits on arbitrage capital motivate carry; margin and
  liquidation risk qualify the interpretation. Older findings do not establish
  current premiums after institutional entry.
- [Binance public data](https://github.com/binance/binance-public-data), retrieved
  September 11. Daily/monthly publication schedule, archive revisions/checksums
  and spot microsecond timestamps from January 2025 require explicit handling.
- [Binance USD-M market data](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data),
  retrieved September 11; publication date unestablished. Funding history returns
  settled event rates/times and associated marks. Funding-info is not a historical
  expected-event calendar. Basis endpoint is limited to the latest 30 days.
- [Binance funding explanation](https://www.binance.com/en/support/faq/detail/360033525031),
  retrieved September 11. Funding cashflow uses mark price times contract quantity
  times rate. Summed daily rates alone cannot value a fixed-quantity position.
- [Liu and Tsyvinski](https://www.nber.org/papers/w24877), August 2018, and
  [common risk factors](https://www.nber.org/system/files/working_papers/w25882/w25882.pdf),
  2019 working paper. Attention, momentum and factor attribution context; exchange
  prices in historical research are not present tradability evidence.
- [Makarov and Schoar](https://mitsloan.mit.edu/cfi/trading-and-arbitrage-cryptocurrency-markets),
  JFE 2020. Capital mobility/segmentation explains persistence of some cross-market
  spreads; it does not demonstrate a Binance–Bitrue opportunity.
- [Risk Premia in the Bitcoin Market v2](https://arxiv.org/abs/2410.15195v2),
  August 1, 2025 (original October 19, 2024). Variance compensation hypothesis;
  dynamic hedging, contract quotes and executable costs remain necessary.

Current liquidation documentation redirected to a generic landing page during
the independent review; present sampling semantics remain unestablished.
Bitrue dated products and account applicability remain unverified. Retained
[September 10 source receipts](../../docs/carry-feasibility-2026-09-10/SOURCES.md)
provide historical documentation evidence, not current private commissions.

## Breadth source review after Decision 01

Independent documentation review, September 11, 2026; no market requests.

| Mechanism | Official source and established field | Missing/admission boundary |
|---|---|---|
| Dated/calendar | Public-data README documents UM/CM trades/klines and checksums; futures market API has quarterly continuous series | Exact expiry archive, historical executable spread and settlement still unverified; continuous series cannot represent a held contract |
| Options | [Market API](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/market-data): exchangeInfo expiry/unit/minQty/filters/margin/nakedSell; exerciseHistory and current books | Examples are not current lot limits; no complete historical bid/ask chain archive established; exercise history insufficient for entry premiums |
| Options fees | [Fee FAQ](https://www.binance.com/en/support/faq/detail/5326e5de61c34fed98abe28d2f175a23), updated March 6, 2026, displays 0.024%; [introduction](https://www.binance.com/en-AE/support/faq/detail/374321c9317c473480243365298b8706) displays 0.02% | Documentation conflict; applicable entity/fee basis/cap must be settled before a cash book; no account permission inferred |
| Bitrue delivery | [Delivery API](https://www.bitrue.com/api_docs_includes_file/delivery/index.html): contracts multiplier/minOrderVolume/minOrderMoney; klines maximum 300 | URL label does not establish fixed-expiry products; expiry fields, retention and settlement history missing; example/prose timestamp units conflict |
| Spot triangles | [Spot filters](https://developers.binance.com/en/docs/products/spot/filters): lot/market-lot/step and notional filters per leg | Three fees, rounding/dust, asynchronous snapshots, partial fills and residual inventory; no atomic fills established |
| Convert | [Trade API](https://developers.binance.com/en/docs/catalog/core-trading-convert/api/rest-api/trade): getQuote is signed TRADE and sufficient funds required for quoteId | Authenticated empirical route outside no-credentials scope; do not transfer Convert guarantees to public spot books |
| Staking/WBETH | [ETH staking FAQ](https://www.binance.com/en-GB/earn-faq/light/eth-staking/faq) describes reward conversion ratio, quota and variable redemption; [API](https://developers.binance.com/en/docs/catalog/investment-and-services-staking/api/rest-api/eth-staking) marks rate/quota history USER_DATA | Historical public ratio and redemption waiting-time history not admitted; current APR/example redemption duration cannot be historical observation |

The [January 5, 2026 options specifications](https://bin.bnbstatic.com/static/cms/cg08ou2ak0tn7mcplvfg/file/443bcc67fde7274898ff8e3f7af23c7d89e654c5e609d250772e0ddaa96409be.pdf)
describe European USDT settlement and BTC/ETH unit 1, conditional short-selling
eligibility and margin. Exact legal/entity and clearing applicability remain
unverified. Public contract metadata and minimum-lot capital calculations are an
affordable distinct investigation; no option payoff has yet been evaluated.

## Dated archive directory discovery

Read-only official catalogue inspection on September 11, 2026, with daily XML
listings observed at 07:46:07–10 UTC. No ZIP/price bodies were opened in this
source-discovery step. XML was inspected through source tools; its raw body was
not retained as a local immutable snapshot. Registered acquisition will retain
actual ZIP/checksum bytes independently; this note is a catalogue observation.

The [official landing page](https://data.binance.vision/?prefix=data/futures/um/monthly/klines/)
identifies the S3 bucket. [BTC monthly XML](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Ffutures%2Fum%2Fmonthly%2Fklines%2FBTCUSDT_260626%2F1h%2F&max-keys=100)
and [ETH monthly XML](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Ffutures%2Fum%2Fmonthly%2Fklines%2FETHUSDT_260626%2F1h%2F&max-keys=100)
returned HTTP 200 with IsTruncated=false. Listed ZIPs:

| Contract / month | Bytes | Current object LastModified UTC |
|---|---:|---|
| BTCUSDT_260626 / May 2026 | 31,906 | 2026-06-02 10:57:54 |
| BTCUSDT_260626 / June 2026 | 26,843 | 2026-07-02 12:04:38 |
| ETHUSDT_260626 / May 2026 | 32,688 | 2026-06-02 10:58:12 |
| ETHUSDT_260626 / June 2026 | 27,378 | 2026-07-02 12:04:58 |

Each has a listed 96-byte .CHECKSUM companion. Daily listings contain 183 ZIP
filenames from December 26, 2025 through June 26, 2026. File dates and current
object timestamps do not establish exact contract launch/expiry time, original
publication, execution liquidity or settlement cashflows. Third-party snippets
returned incidentally by search were not used to infer prices/economics or choose
these contracts. The existing mechanism and last completed quarterly contract
identity determine the bounded admission question.
