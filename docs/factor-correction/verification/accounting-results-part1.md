# Accounting result audit — first two completed configurations

Reviewed 2026-09-10T12:32:18.294708+00:00 while the registered main process continued. Scope is exclusively completed files for `tsmom_k7_ls` and `tsmom_k14_ls`, produced under frozen source `27640882822d812c6d0478340495e033a11d3915`. No other case output was read, no strategy was rerun, and no source, policy, registration, raw input or financial ledger was changed. This audit recomputed identities from saved traces/returns only; it did not construct a new strategy book. The two completed cases are not evidence of completion of the full18-case run.

## Disposition

**All checks passed; no material discrepancy found in these completed files.** The32 Parquet artifacts retained identical SHA-256 hashes before and after inspection. Both cases contain five complete return-index variants, eight complete corrected sleeve traces, two1241-row target schedules, and one1240-row invalid-log diagnostic. Each saved return/trace clock equals every midnight November8,2021–March31,2025 (1240 rows). Each target clock equals November7,2021–March31,2025 (1241 rows). All saved return values are finite.

## Accounting identities checked

For all16 corrected sleeve traces (19840 rows): NAV continuity and initial10000 anchor; NAV change equals gross plus signed funding minus fee and impact; gross equals opening desired exposure times effective price return; signed funding matches the registered assumed daily rate; entry turnover equals desired pretrade notional minus the previous marked holding; each entry/exit fee uses the one-way rate; quadratic impact uses the correct leg NAV; entry/exit subdivisions sum to totals; saved returns agree with NAV ratios; traced requested weights equal the saved target schedule until the permanent halt; final and exit notionals match the effective mark; halt latches are monotone and all later holdings/cashflows/returns are exactly zero with unchanged NAV. Zero-execution and zero-funding variants have exactly zero corresponding charges. Gap-stop flags match the saved OHLC envelope.

All ten saved aggregate streams exactly equal the mean of their BTC/ETH sleeve streams, including legacy streams. For each of the two shadows, replacing only the primary gross term with frozen exposure times log1p(effective mark return) reconstructs the saved diagnostic within5e-16. Primary funding, entry/exit charges and stop schedule remain unchanged in this identity. The diagnostic remains invalid as executable PnL.

| Case | Corrected variant | Sleeve | First halt row | Exact-zero post-halt rows | Assumed stop fills outside OHLC |
| --- | --- | --- | --- | ---: | ---: |
| tsmom_k7_ls | primary | bitcoin | 2022-10-21T00:00:00 | 892 | 0 |
| tsmom_k7_ls | primary | ethereum | 2022-10-24T00:00:00 | 889 | 0 |
| tsmom_k7_ls | zero_execution | bitcoin | 2022-10-24T00:00:00 | 889 | 0 |
| tsmom_k7_ls | zero_execution | ethereum | 2023-08-16T00:00:00 | 593 | 0 |
| tsmom_k7_ls | double_execution | bitcoin | 2022-08-09T00:00:00 | 965 | 0 |
| tsmom_k7_ls | double_execution | ethereum | 2022-10-22T00:00:00 | 891 | 0 |
| tsmom_k7_ls | zero_funding | bitcoin | 2022-10-21T00:00:00 | 892 | 0 |
| tsmom_k7_ls | zero_funding | ethereum | 2022-10-24T00:00:00 | 889 | 0 |
| tsmom_k14_ls | primary | bitcoin | 2022-11-08T00:00:00 | 874 | 0 |
| tsmom_k14_ls | primary | ethereum | 2023-06-20T00:00:00 | 650 | 0 |
| tsmom_k14_ls | zero_execution | bitcoin | 2022-11-08T00:00:00 | 874 | 0 |
| tsmom_k14_ls | zero_execution | ethereum | 2023-06-28T00:00:00 | 642 | 0 |
| tsmom_k14_ls | double_execution | bitcoin | 2022-10-24T00:00:00 | 889 | 0 |
| tsmom_k14_ls | double_execution | ethereum | 2023-06-06T00:00:00 | 664 | 0 |
| tsmom_k14_ls | zero_funding | bitcoin | 2022-10-24T00:00:00 | 889 | 0 |
| tsmom_k14_ls | zero_funding | ethereum | 2023-06-20T00:00:00 | 650 | 0 |

Floating-point checks used absolute tolerance1e-9 dollars for accounting cash/holding identities, exact equality for persisted aliases/continuity/clock/target/return formulas and deterministic component sums, and5e-16 for the shadow aggregation identity. Maximum absolute residuals across reviewed rows:

| Identity | Maximum absolute residual |
| --- | ---: |
| aggregate_equals_sleeve_mean | 0 |
| nav_alias_before | 0 |
| nav_alias_after | 0 |
| nav_continuity | 0 |
| cashflow_reconciliation | 4.1211478674085811e-12 |
| gross_price_component | 5.6843418860808015e-14 |
| signed_assumed_funding | 4.4408920985006262e-16 |
| drifted_entry_turnover | 1.8189894035458565e-12 |
| entry_fee | 3.5527136788005009e-15 |
| exit_fee | 1.7763568394002505e-15 |
| fee_subdivisions | 0 |
| entry_impact | 1.1102230246251565e-15 |
| exit_impact | 5.5511151231257827e-17 |
| impact_subdivisions | 0 |
| turnover_subdivisions | 0 |
| ret_matches_trace | 0 |
| trace_net_return | 0 |
| same_registered_target_schedule | 0 |
| final_marked_notional | 0 |
| exit_notional | 0 |
| shadow_only_replaces_gross | 1.3877787807814457e-17 |

These results remain conditional proxy-price/assumed-funding benchmark measurements, not a pooled executable account or validated strategy. Historical scalar/BEST parity, all18 configuration records, all90 variants and ledger-prefix preservation remain for the final completed-run review.

## Inspected artifact hashes

| Completed artifact | SHA-256 before and after |
| --- | --- |
| `tsmom_k7_ls-bitcoin-targets.parquet` | `218bbdc0e3c061ee8aeba1f7aee75bebdca607e96cf6ffb8d973b38bd9e2d3cc` |
| `tsmom_k7_ls-double_execution-bitcoin-trace.parquet` | `17b57d64e6cb9def006dcc3133474827d26cf979b70eefbe455bad9e86e06e7e` |
| `tsmom_k7_ls-double_execution-ethereum-trace.parquet` | `e14af15ba9cacb52a7013445cdfc3dd3dfaf85bf9bf37ec23a200bb11782e16f` |
| `tsmom_k7_ls-double_execution-returns.parquet` | `82c33f800d3247d64b4466cd0c00600a1e478605f131c7800c429900b3f077ff` |
| `tsmom_k7_ls-ethereum-targets.parquet` | `973e33e15d77a3ea7ed7ae4f4bbea6a5e52315234fe7a0511b4ec41296c1bea2` |
| `tsmom_k7_ls-legacy-returns.parquet` | `5d796ffb3a2e12f74a6003d39ef7f5d261f177db014fdea1ef6fada24064c85d` |
| `tsmom_k7_ls-log-shadow.parquet` | `2f293272460a5e400ccc4af51989dd74deb0c102d1b2b86cf78b2f4c9966bd51` |
| `tsmom_k7_ls-primary-bitcoin-trace.parquet` | `40f80f769d94056b3d3f7c27c635e4abad821975c6f789d9a8953ed670436d0d` |
| `tsmom_k7_ls-primary-ethereum-trace.parquet` | `97e86b8ca7940acb9aaa6cb2fe053a128d2e6e1b3161dd0e28f2ad69be760640` |
| `tsmom_k7_ls-primary-returns.parquet` | `2132b06d8d1646d210a0790cae7dc6c0360fe3e984ea9a77ee6e5c6ee99b01a3` |
| `tsmom_k7_ls-zero_execution-bitcoin-trace.parquet` | `d49c5c7c77395b73ba07440340f7b7bce701c20ce17350682113a110c947d288` |
| `tsmom_k7_ls-zero_execution-ethereum-trace.parquet` | `bc3e6eb94b12219cba45fafce57f2c7180235b1e4bef893dd215252ba5ec6ad5` |
| `tsmom_k7_ls-zero_execution-returns.parquet` | `ff2dbb4b9dff8622c929cffa8aea55393d6cd3df42aabff925a3b3ba63559cec` |
| `tsmom_k7_ls-zero_funding-bitcoin-trace.parquet` | `8357c871ec54238cde0c28d38a8ffc0dea01f34ae4a93a3bfc7060f9a1377407` |
| `tsmom_k7_ls-zero_funding-ethereum-trace.parquet` | `c3b3e86f4ac90441b16b83a76632802ad5cb9d7f3c3920a4d0f551af58842b4d` |
| `tsmom_k7_ls-zero_funding-returns.parquet` | `b189e46787643786bac43c09db3c23622dafcce837ab01d1812e140ad0c0d07b` |
| `tsmom_k14_ls-bitcoin-targets.parquet` | `d313c2139a382f4187657991bf71f9967daeae44ca049d335d103fed3cabb540` |
| `tsmom_k14_ls-double_execution-bitcoin-trace.parquet` | `d10ddc7e8c98acec9cd0cb8bea3500e4717b26377f9d912357336a120b696911` |
| `tsmom_k14_ls-double_execution-ethereum-trace.parquet` | `5ec991bcbcaa454bb77ad54768e73dfdc2bf32b9f8a7dfcc148bd3b02320f1a1` |
| `tsmom_k14_ls-double_execution-returns.parquet` | `b50696d155abb14d64dc8d681f06b390e3cfc305fe096549fd51e320ef0aa470` |
| `tsmom_k14_ls-ethereum-targets.parquet` | `66d05b312d872206dcb7a2b243365269f8c8ce96c874d5a55da80f9c456497df` |
| `tsmom_k14_ls-legacy-returns.parquet` | `eff4e57370a5e59c5a4d42cd4632fbaa4c027a222d4464c0c70404dc6e2bacd3` |
| `tsmom_k14_ls-log-shadow.parquet` | `58f68667760e6afa5f10165f62dc771e42668ef6b4f94d97eb4e54e0136932da` |
| `tsmom_k14_ls-primary-bitcoin-trace.parquet` | `af6f20b670ba388f9a8777645a9cc03dc2ab65b267cbf3e56a67989835369661` |
| `tsmom_k14_ls-primary-ethereum-trace.parquet` | `c4d398a8b2faae23ddabe80c4ae38dad3e435df5653a6e96f6f0dbba4e8aa142` |
| `tsmom_k14_ls-primary-returns.parquet` | `b8426982ed24ef99af093306a9f5ca926914ed39ce67b105e0deb4ea1a29af16` |
| `tsmom_k14_ls-zero_execution-bitcoin-trace.parquet` | `bd816476960d077d1a319508221dee72a8d3015f692b63ce6f89be56d516f7b1` |
| `tsmom_k14_ls-zero_execution-ethereum-trace.parquet` | `f34669cf1560c067154fbd67438e3717b8ed3e6d265ae8dc13d16dd547fcb51b` |
| `tsmom_k14_ls-zero_execution-returns.parquet` | `6822225bcf3cef8870176ad5018f0f0365996b2015fb4e81f751e89be9f76ab1` |
| `tsmom_k14_ls-zero_funding-bitcoin-trace.parquet` | `1e59d7ffe6220f4eca5eb31b49b81fda132e1b67aca35d61efb3105efb8ced38` |
| `tsmom_k14_ls-zero_funding-ethereum-trace.parquet` | `295d58bcd7bfbd979dccd7db6f2ff71e8838a6e32af359f3d102cbef4fdf9c38` |
| `tsmom_k14_ls-zero_funding-returns.parquet` | `26a40bb11602e3eff27f68ca891d008e2b1e50730379d6c3d9d93139ee74d9dc` |
