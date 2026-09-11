# Options source feasibility — September 11, 2026

Disposition: a small registered public contract-metadata and archive-catalogue
capture can resolve a real dependency, but does not yet justify an options
performance test. Exact current minimum tradable quantities, account eligibility,
applicable fees, seller margin and historical executable chains are not jointly
established. These are missing inputs, not negative strategy results.

## Scope and request denominator

Eight distinct official source fetches were made: seven document pages and one
archive directory listing. All eight returned readable material; the directory
returned HTTP 200. Subsequent `find` operations extracted already opened web
references, without adding source URLs. Access date for all documents:
September 11, 2026; exact document request clocks are not exposed by the web
tool. The directory request began at 08:10:49.217860 UTC. No option quote,
premium, price-history body, authenticated API, purchase or financial return was
requested. The web tool manages its own retrieval/cache behavior; eight is the
explicit source denominator, not a claim about its underlying network traffic.

| ID | Exact official source | Publication/update and retained outcome |
|---|---|---|
| O1 | https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/market-data | Date unspecified; readable current schema, examples not observed contracts |
| O2 | https://www.binance.com/en/support/faq/detail/5326e5de61c34fed98abe28d2f175a23 | Published September 8, 2022 09:46; updated March 6, 2026 06:05; readable fee formulas |
| O3 | https://www.binance.com/en/support/faq/detail/374321c9317c473480243365298b8706 | Published December 23, 2020 16:20; updated January 12, 2026 05:00; introductory guidance, expressly potentially outdated |
| O4 | https://bin.bnbstatic.com/static/cms/cg08ou2ak0tn7mcplvfg/file/443bcc67fde7274898ff8e3f7af23c7d89e654c5e609d250772e0ddaa96409be.pdf | Published January 5, 2026; four-page RIE/RCH option specifications |
| O5 | https://developers.binance.com/en/docs/products/derivatives-trading-options/change-log | Readable combined derivatives chronology; relevant entries November 12, 2025 and July 9, 2026 |
| O6 | https://www.binance.com/en/fee/optionsTrading | Publication date unspecified; rendered table contains concatenated rate alternatives |
| O7 | https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/trade | Date unspecified; readable authenticated commission interface documentation |
| O8 | https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Foption%2F&delimiter=%2F&max-keys=1000 | HTTP 200, nontruncated, one child prefix `data/option/daily/`; no member/data bodies inspected |

## Contract, access and accounting evidence

The January 2026 specification identifies European-style, automatically exercised,
USDT-settled contracts. BTC and ETH contract units are one underlying coin each;
this does not imply minimum order size of one whole contract. Short-selling
eligibility is explicitly conditional. Short positions require initial and
maintenance margin, with exact formulas referred to clearing procedures.
Applicable entity/participant rules and fee tables take precedence over general
guidance. No direct account entitlement is established by this document. [O4](https://bin.bnbstatic.com/static/cms/cg08ou2ak0tn7mcplvfg/file/443bcc67fde7274898ff8e3f7af23c7d89e654c5e609d250772e0ddaa96409be.pdf)

The public market schema supplies `unit`, `minQty`, `stepSize`, expiry, margin
ratios, symbol status and `nakedSell`. Its displayed 0.01 quantity and 0.15/0.075
margin ratios are examples. Historical exercise records and option OHLC endpoints
are documented. Order books and option marks are current observations; a complete
historical bid/ask-size chain is not established by those interfaces. A current
metadata snapshot would resolve actual symbol rules, not historical rules or
account permission. The schema phrase mapping CALL/PUT to long/short is not an
economic direction rule: either option type can be bought or sold. [O1](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/market-data)

The fee FAQ displays a 0.024% trading rate, calculated from index price and
contract unit with a premium-related cap. Exercise is separately charged at
0.015% with an intrinsic-value cap. These published formulas are useful scenario
inputs only after product/entity applicability is established. [O2](https://www.binance.com/en/support/faq/detail/5326e5de61c34fed98abe28d2f175a23)
The introductory page displays 0.02% trading and warns that its content may be
outdated. [O3](https://www.binance.com/en/support/faq/detail/374321c9317c473480243365298b8706)
The current fee-table extraction concatenates 0.0240% and 0.0300% alternatives
for regular users; selecting one silently would be unsupported. [O6](https://www.binance.com/en/fee/optionsTrading)
Exact account commission is available through signed USER_DATA
`GET /eapi/v1/commission`, which is outside this no-credentials task. [O7](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/trade)

The change log records an options-system rebuild and new demo environment on
November 12, 2025. On July 9, 2026 it records new `contractType` and
`underlyingType` fields and a separate TradFi agreement endpoint. It does not,
in the inspected entries, establish the exact production migration date or
historical-chain compatibility. Thus old European option samples, newer crypto
options and TradFi products require explicit identities; none may be silently
combined. [O5](https://developers.binance.com/en/docs/products/derivatives-trading-options/change-log)

## Historical data and capital distinction

The observed option archive root has a daily child directory. Its descendants,
field schemas and period coverage were not opened within this eight-source
bound. This is positive evidence of an official archive namespace, not proof of
executable historical chains and not a negative search result. [O8](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Foption%2F&delimiter=%2F&max-keys=1000)

For long options, affordability depends on minimum quantity times actual premium,
fees and a funded hedge/reserve. Neither $1,000 nor $10,000 affordability can be
adjudicated from contract unit alone. For selling volatility, premium receipt
does not remove short-option initial/maintenance margin, tail exposure or hedge
cash needs. Symbol-level `nakedSell` is not personal seller access. Low initial
delta does not establish low stress exposure because gamma changes that delta.
These are accounting implications, not measured outcomes.

A historical delta-hedged test needs timestamped option bid/ask prices and sizes,
contract lifecycle, underlying executable hedge observations, funding or borrow
cashflows as applicable, lot constraints and a committed hedge policy. An index
or mark alone is not an executable hedge; daily option OHLC cannot certify
simultaneous entry and hedge fills. This complete input bundle remains missing.

## Ancestry and bounded next action

The saved history contains `predlab_rviv_p0`, twelve ledger rows, and
`THESIS_FINDINGS.md` Section 71 (line 5856). Its 30-day HAR versus debiased DVOL
forecast comparison on June 2022–March 2025 failed its specified gate. That is
an inherited warning against renaming HAR-based 30-day volatility timing as a
new discovery. It is not an execution test of all Binance option contracts.
The original record and exposed observations remain retained.

Recommended next registration: metadata only, no quotes, at most four requests:
one public `eapi/v1/exchangeInfo`, one `eapi/v1/time`, and two explicitly frozen
official option-directory listings. Capture actual BTC/ETH crypto-option
quantity/unit/status/expiry/filter and margin fields, preserving all other rows
in raw evidence. Catalogue descendants should identify available data types;
no ZIP or price body should be opened in that registration. Record absence,
denial and ambiguous schemas as unavailable, with a complete denominator.

This resolves whether instrument granularity and a public historical-data route
exist before a capital/volatility experiment is built. It cannot resolve account
fees/eligibility or prove $1,000/$10,000 executable feasibility. If only marks,
indices or summary snapshots exist, defer the historical executable-chain claim
pending a separately frozen prospective collection; do not invent fills from
them. If that dependency remains blocked, the next distinct affordable mechanism
is public same-venue spot triangular conversion with a separately registered
quote/fill-risk design. Binance Convert authenticated quotes are excluded.

No financial experiment, strategy rejection, public metadata API capture or
prospective collector was executed by this source review.
