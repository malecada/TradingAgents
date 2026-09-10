# Original factor-floor archival provenance

This archive preserves existing source and recorded outputs for a prospectively registered accounting correction. No signal, fit, strategy return, ranking, performance metric, or holdout result was computed to create it. The copied historical metrics are legacy measurements, not validated strategy evidence. Original files and Git refs were not changed.

## Registration and executed-source limits

The broad model-free factor-floor charter was committed as `4ba5dd7ee76b293d00c9f9946435be8359f4bf36` on July 8, 2026 at 17:35:54 UTC. Its language specifies approximately 15–20 trend/momentum configurations and treats the best survivor as a benchmark floor. The broad gates were committed as `7c65b32b212d72d5fac1e9f33d4316a6f260b024` at 18:03:15 UTC. The ML-survival and eventual one-shot holdout requirements do not create a separate factor-floor development adoption gate.

The exact 18-configuration script and first result artifacts first appear together in `34bbe30c7d50c69478992902aaaeb668ff7ed17a`, July 9 at 06:17:09 UTC. The first 18 recorded evaluations occurred at 06:12:35–06:12:38 UTC and report HEAD `3b425da944cb8191e430868fa3e7b9bad8933fe0`, which has no factor-baseline script. The second 18 evaluations and halt note occurred at 06:29:50–06:29:53 UTC and report HEAD `34bbe30`; their added halt-transparency source was committed in `f359050c16521aa5fdd9bb10c0e25af9f37ff57f` at 06:33:36 UTC. The recorded HEAD field does not certify a clean tree or identify the executed uncommitted file bytes. Consequently exact-grid pre-result registration and clean executed-source identity cannot be established from these records.

The ledger itself first appears in Git at `e53737f34aa5beec8e9d73eccbba9e37534586c2` at 08:44:40 UTC on July 9, after both evaluations. This archive extracts its original lines 8–44 byte-for-byte. Those 37 lines exactly match the currently preserved ledger selection: 18 initial evaluations, the same 18 configurations repeated for halt transparency, and one note. There are 18 distinct strategy configurations, not 37 independent trials. All four common metrics in the two runs agree exactly. Timestamp fields are preserved recorded assertions, not independent acquisition attestations.

## Preserved source and original behavior

`factor_baselines_f359050.py` is the post-transparency wrapper and is byte-identical to the current wrapper at archival time. The initial wrapper at `34bbe30` differs in reporting and return packaging, without changing signal, sizing or engine calculations. The old V2 engine is identical at `3b425da`, `34bbe30` and `f359050`. The archived sizing and cost modules are also byte-identical across those revisions and current checkout at archival time. The old `run_coin_backtest` can be extracted as a single AST function with NumPy supplied, without invoking its CLI or data-loader imports. Archival `.py` files are evidence and must not be executed as historical application entrypoints.

Original fixed grid: TSMOM LS lookbacks 7/14/30/90/180; TSMOM LO 7/14/30/90; MA crossover LS and LO for (10,50)/(20,100)/(50,200); Donchian LS 20/55; BTC-versus-ETH XS momentum 30. BTC and ETH are the only instruments; no BZRX/LUNA/BNX closure records are needed.

Freeze signal history and sizing separately. Signals use all available pre-window cache history through the previous close; Donchian is stateful, so arbitrary 200-day truncation is not established as equivalent. The November 7, 2021–March 31, 2025 window is applied before sizing. Sizing resets inside that window; lagged prices use `px_sizing[1:] = px[:-1]`, with the first element copied from the first window close. The 20-bar volatility warmup, expanding prior volatility percentile mask, and original sqrt(252) volatility scaling remain part of the frozen quantity-generation contract. Reporting annualization can be corrected separately without changing those quantities. The first saved return is November 8; 1,240 daily return rows are preserved for the historical selected configuration.

Shared constants: target volatility 0.10, Kelly fraction 0.5, maximum leverage 3.0, minimum hold 7 bars, early exit loss 0.015 after at least 3 bars on a changed signal, volatility lookback 20, cap percentile 0.95, price stop 0.03, and initial capital 10,000 per coin. Positions are generated in advance by the sizing state machine; the engine's stop/halts do not feed back into that state machine. Same-sign requested weights are held constant until a sizing entry/flip; the accounting engine interprets them as daily target fractions. The circuit breaker is a permanent per-coin 15% drawdown latch, and subsequent cash-tail rows remain on the calendar. Ordinary equity stop is overridden to 1.0 and take-profit is 0.0.

Cost inputs are fee 0.0004, slippage 0.0005, spread 0.0001, impact coefficient 0.00005, and assumed funding 0.0003 per day. Historical accounting doubles fees/spread, applies funding side-blind to absolute target exposure, omits drifted maintenance turnover, and has different risk-exit charging. The price stop fills at its threshold after an intrabar high/low crossing; gap execution, funding timing within a stopped day and venue settlement are not established by this approximation. Replacing assumed funding or proxy prices would be a separate declared measurement change. The aggregate is the equal-weight mean of the two independent coin return streams; interpreting it as a fully executable combined account would additionally require explicit allocation/rebalancing accounting.

## Inputs and parity qualification

The two current original-worktree cache files exist and are untracked. Their headers are `Date,Open,High,Low,Close,Volume`; their first dates are April 14 and April 15, 2019 respectively. Only headers/first prior-window dates and raw-byte hashes were inspected for this archival task; no new strategy calculation or holdout market-row evaluation occurred. No historical July input hash manifest was located. Current file hashes therefore identify candidate preserved inputs, not proven July acquisition identity. The original loader uses Binance spot `/api/v3` data with a CoinGecko fallback, and can skip malformed rows, read the full cache and fetch/update it. It must not be called by the correction runner.

| Candidate input | Bytes | Current SHA-256 |
| --- | ---: | --- |
| `bitcoin-crypto-ohlcv.csv` | 154226 | `95b99d9be1631138cb2b1546cdf64d77baa5a140c6b8b7879319babc30c88401` |
| `ethereum-crypto-ohlcv.csv` | 142580 | `5e1320598cd4fcc2ce2ef3c3b18c4f1f1e324000aa9fea412a940952cebfc5b9` |

A separately registered same-current-input legacy-engine run can be paired with corrected accounting while fixing its signals and quantities. Matching all 18 saved scalar summaries plus the historical selected daily stream would provide empirical reconstruction evidence only after execution is authorized. A mismatch must remain explicit and prevent an exact-July-reproduction claim; source availability alone does not resolve unknown historical inputs. No post-result tuning, replacement prices, hidden date dropping, or warmup adjustment is justified by this archive. The historical holdout remains spent.

## Artifact integrity

The selected daily stream is byte-identical at `34bbe30`, `f359050`, the current correction checkout and original TradingAgents worktree. The post-transparency table is also unchanged between `f359050` and those current worktrees. `comparison.json` copies the second run's saved metrics, including halt fields, without recalculation. Raw initial-run records remain in the 37-row JSONL. `manifest.json` records source commits/blob identifiers and hashes for every archival payload, including this note; the manifest does not hash itself.

| Archive file | Bytes | SHA-256 |
| --- | ---: | --- |
| `factor_baselines_f359050.py` | 25110 | `32ad2180512198d45e5fb76855abd84c8565d29e63019496fce0f5bb35706a69` |
| `baseline_strategy_v2_f359050.py` | 20397 | `d278c2084a39385d8985728b2c98915503995810a01344fb013fe139c0793d5a` |
| `v2_sizing_f359050.py` | 8778 | `19c7492c36a68a45a69451cb03ca0b846649692dbbe4e389f9abe77939170e9d` |
| `baseline_v5_mix_f359050.py` | 15555 | `6c0db31674041eb8cdebd164c89a0da6472fddee6f25c54dcae1ee2825a90a48` |
| `charter_4ba5dd7.md` | 12188 | `2040e018eda53b96774efb41188fbd9ff18c9fb704b59279e30553d55226e891` |
| `gates_7c65b32.json` | 899 | `332eddcd541e96c88f03e523e684058cdd06a96b3271ec3f4557acf0757531cf` |
| `floor_table_f359050.md` | 3492 | `3b7e5d242fe1df0e50189c13bce839fda7adb3aa6891fc76a3c38676c42994c9` |
| `BEST_daily_returns.csv` | 49197 | `704fc2f4b2cf375feb14f8aafab88093e44fc0611611c7d474b11f1185e52764` |
| `factor_floor_37rows.jsonl` | 17674 | `fa29f9ac65db6559a6d8427fc523a257569c5e0d5e2eaaef50ac94cde5ced704` |
| `comparison.json` | 18803 | `9712d0b4b322007d0e3bc354175332be3904d30c9a709e5e078c6225da8b88d0` |
