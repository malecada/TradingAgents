# Coin Metrics price-data attribution

The retained BTC and ETH CSV responses originate from [Coin Metrics Community
Data](https://github.com/coinmetrics/data), commit
`f1a36afb962731c387bb03982758ab0103063da5`, distributed under
[Creative Commons Attribution–NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/).
The price definition is documented in the provider's
[PriceUSD metric](https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/market/price).

Raw response bytes are retained without alteration. Derived price panels select
the `time` and `PriceUSD` fields for 2016-01-01 through 2024-12-31 and represent
the parsed values and explicit date coverage in JSON. No interpolation, date
shift, alternate metric or provider blending was applied. Capture timestamps,
revision, source hashes and complete transformation policy are retained with
each panel. The provider did not endorse this independent academic replication.

This attribution and data license accompany the retained and derived price-data
artifacts. They do not relabel the independently written implementation software
or the publisher's separately attributed article.
