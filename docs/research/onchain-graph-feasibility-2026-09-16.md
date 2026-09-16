# On-chain transaction graphs: feasibility review

Reviewed September 16, 2026. Documentary and design review; no financial experiment, model training, paid query, provider contact or operational launch was performed. Zero strategies are validated.

Subsequent authorized engineering evidence is preserved in the [one-day Ethereum graph result](../../research/onchain-graph-2026-09-16/forensic/RESULT.md). It demonstrates bounded column extraction and a conditional static graph reconstruction; the original strict graph gate remains unavailable. The documentary assessment below is retained as the pre-experiment review.

The subsequent [local temporal-motif benchmark](../../research/onchain-graph-2026-09-16/motifs/RESULT.md) exceeded its initial 2 GiB memory cap. The user-authorized [8 GiB successor](../../research/onchain-graph-2026-09-16/motifs8gib/RESULT.md) completed the same computation: 2.47 GiB sampled peak RSS, 10.805 seconds for the counting phase including receipt checks, and all 44 outputs retained. Independent verification reconciled raw/order identities, exports and every full-day two-node vector; whole-day star/triangle counts were not independently recounted. This establishes bounded one-day computational feasibility. Full-history scalability and predictive value remain untested.

The subsequent [multi-day readiness audit](../../research/onchain-graph-2026-09-16/panel_readiness/RESULT.md) found all 1,096 dates across 2022–2024 in both block and transaction inventories, with all 24 quarterly sampled schemas matching. A synthetic-tested completion-day adapter handles cross-midnight motifs. Full-history storage is now a practical constraint: quarterly samples imply about 130.75 GiB for selected compressed columns, versus 73.71 GiB observed free; this is an extrapolation, not a measured complete panel. Historical publication timing and every-day row integrity remain unverified. No prices or forecasting outcomes were opened.

**Verdict: a bounded graph-feature study is technically plausible. The supplied 13-week specification is not ready for implementation, and its claimed connection to successful price prediction is insufficient.** Entity classification, graph-based forecasting and a profitable strategy with little crypto-price exposure are separate claims. The cheapest useful test should isolate the incremental information in graph features before building an entity-classification platform.

The reviewed input is `/home/malecada/master_thesis/onchain-transaction-graph-spec.md`, SHA-256 `cf6904afb1d4dc60817d48237c4a8b9073450809fc6d710230849eafb071324e`. The active checkout was clean at `06c7a82ed2a0041e94b86329bfc799bb6b1b9f19`, on `research/strategy-search-2026-09-11`, before adding this review. The original spec and active research state are unchanged.

**What the cited evidence establishes**

Çelik and Sefer use learned structural motifs, GAT and LSTM, with weekly address graphs and daily prices over 2016–2024. Table 2 reports BTC/ETH accuracy of 76.5%/80.4%, versus 72.8%/76.5% for GRU. Their two-year-training/one-year-testing description also says every year from 2016 is tested; that chronology needs clarification. No net trading result is established. Data are offered on request. The specification's temporal counting/classification pipeline is a different method. Its Chainalysis reproduction requirement is not supported by this paper's address-level graph description. [Paper, methods and availability](https://link.springer.com/article/10.1007/s10614-025-10940-1), [Table 2](https://link.springer.com/article/10.1007/s10614-025-10940-1/tables/2).

A relevant public repository does exist: [seferlab/gnn_price](https://github.com/seferlab/gnn_price), forked from [Peker Çelik's project](https://github.com/nebipeker/Analyzing-Transaction-Graphs-for-Price-Prediction-of-Bitcoin). Both public trees resolved to `6ba8bda1dc5f4b4eca20ba64fc3beeda9ed8d570`; the recorded last push was February 2023. They contain notebooks and sampled graph data. The README describes older Bitcoin work, not a verified implementation of the published 2016–2024 BTC/ETH experiment. This is an artifact lead, not a reproduction package. No notebook was executed, and no stored forecasts or financial outcomes were evaluated.

Arnold et al. provide useful evidence that local temporal motifs expose behavior missed by aggregate counts, and document concentration, timestamp-order and timescale issues. Their Bitcoin inputs were proprietary Chainalysis-preprocessed datasets; their NFT data were public. They report a Raphtory counting operation taking three minutes on a 16 GB MacBook where SNAP exhausted memory. That is encouraging for a bounded counting task, not a benchmark for this complete pipeline or learned graph matching. [Temporal-motif study](https://arxiv.org/html/2402.09272v2).

The survey's high classification scores concern different tasks, datasets and feature sets. Some strong results use ordinary volume features and random forests. Its description of accuracy above 50% does not quantify how close to 50%, nor establish a ceiling. Comparing those numbers with F1 and calling the difference one or two orders of magnitude in effect size is mathematically invalid. Neither number estimates expected trading profit. [Survey, Tables 1–3 and Section 5.4](https://arxiv.org/pdf/2010.01031).

**Scientific risks that decide whether results would be credible**

The following are proposed audit requirements and methodological judgments, not findings that the authors actually committed leakage.

- A graph for a completed week can forecast only decisions after that week and the required publication delay. Broadcasting its embedding back onto earlier days leaks future transactions. Fix the horizon, timestamp convention and exact as-of join before training.
- Fit motif dictionaries, scalers, feature selection and model choices inside each training fold. An unsupervised representation can still leak future structure when fitted on the whole timeline.
- All descendants of an economic entity should remain together when testing generalization to unseen entities. Random address splits can put the same exchange in both sets. Also test forward in time; neither split alone answers both questions.
- A prices-only baseline does not isolate graph topology. Hold the learning algorithm and observations fixed while adding ordinary on-chain counts/volume, then graph features. Otherwise extra data and extra model capacity are confounded.
- Millions of transactions do not create millions of independent price outcomes. A weekly forecasting problem has only about 52 outcome dates per year. Dependence and overlapping horizons further reduce information.
- Accuracy needs class prevalence, uncertainty and a comparison with majority/persistence rules. Economic relevance additionally needs the sizes of wins and losses, turnover and execution costs.
- A high price-level R-squared is not itself evidence of leakage, and beating an LSTM is not meaningless. Neither establishes incremental return predictability without suitable controls. The spec's categorical dismissals are stronger than the evidence supports.
- Strong entity identification need not forecast prices. A deposit can be custody movement, collateral, internal treasury activity or preparation for a trade. Treat inferred flows as explanatory candidates, not observed signed buy/sell orders.

The spec's unsupported practitioner comparison and its inference from a sibling paper's Forex performance should not determine the expected effect here. Different targets, datasets and procedures do not supply a transferable prior of a specific numerical size.

**Data and infrastructure feasibility**

| Dependency | Assessment | Consequence |
|---|---|---|
| Raw chain history | Public indexed sources exist. | Plausible to obtain a bounded graph without operating a full node. Exact tables, intervals and completeness still require admission. |
| Historical labels | The central unresolved dependency for Track A/B. | Current attribution cannot establish what was knowable at an old forecast date. |
| Graph computation | Temporal counts have an existing implementation. | Benchmark the exact version, representation and worst window; do not assume full-chain scalability. |
| Existing local integration | LightGBM is declared in the active checkout. Targeted searches found no BigQuery/Raphtory/PySpark/Delta/PyG integration in its scripts, package code or project declaration. | The spec's “already in your stack” assertion is unverified. This was a scoped search, not an exhaustive workspace audit. |
| Trading deployment | No strategy or deployment is validated. | A forecast study cannot inherit permission or readiness from another research family. |

Google provides indexed chain history through BigQuery, including transactions, logs and traces. Its newer Ethereum Blockchain Analytics dataset is distinct from the legacy `crypto_ethereum` dataset named in the spec. The newer product documents approximately 12–15 minutes of finality-related delay. That delay must not be assigned to the legacy tables without verification, or treated as a historical ingestion-time guarantee. [Overview](https://docs.cloud.google.com/blockchain-analytics/docs/overview), [known issues](https://docs.cloud.google.com/blockchain-analytics/docs/known-issues).

Public data does not mean unlimited free processing. Blockchain Analytics uses BigQuery pricing; the pricing page advertises the first 1 TB of monthly query processing free. Estimate scanned bytes and enforce maximum bytes billed before extraction. Partition and column selection matter; repeated full scans and exporting to another cloud are avoidable costs. No account access or cost estimate was measured in this review. [Pricing](https://cloud.google.com/blockchain-analytics/pricing), [query cost controls](https://docs.cloud.google.com/bigquery/docs/best-practices-costs).

Etherscan's address metadata endpoint is explicitly Pro Plus, throttled to two calls per second. Its example returns `lastupdatedtimestamp`, not a complete history of when each attribution became knowable. Therefore the spec's “rate-limited; cache aggressively” note omits an access dependency, and `valid_from` alone cannot repair historical labels. [Etherscan endpoint](https://docs.etherscan.io/api-reference/endpoint/getaddresstag).

GraphSense publishes [TagPacks](https://github.com/graphsense/graphsense-tagpacks). They are a candidate source to audit for provenance and historical snapshots, not proof of representative coverage or independent ground truth. No historical label coverage percentage has been established here.

The required attribution model should distinguish at least the period in which a label is believed true, the earliest supported public availability, the actual retrieval date, source/version and confidence. Historical clustering must also be incremental: a link first observed in 2024 cannot silently merge wallets in a 2019 feature vector. A tag learned later may be suitable as retrospective evaluation truth while remaining unavailable as a historical trading feature.

**Changes needed in the specification**

| Current design | Problem | Recommended correction |
|---|---|---|
| One mutually exclusive entity-class list | An automated market maker may also be a whale; hot/deposit describe address roles. `UNKNOWN` is lack of knowledge. | Separate organization/type, address role, automation and size; permit abstention. |
| Merge precision from category tags | Two addresses tagged “exchange” need not share an owner. A few bad unions can contaminate a huge component. | Require independent same-owner/different-owner evidence; report component contamination and coverage, not only pair precision. |
| Ethereum forwarding and factory heuristics | A common destination or common software creator is not common beneficial ownership. | Keep service custody and customer identities separate; preserve address-level evidence. |
| `eth_getCode` as EOA/contract binary | EOAs can have delegated code under EIP-7702. | Use historical block state and delegation-aware account types. [EIP-7702](https://eips.ethereum.org/EIPS/eip-7702). |
| Bitcoin address-to-address transfers | A multi-input/multi-output transaction does not identify a unique allocation from each input to each output. | Declare the projection or use a bipartite transaction/address representation. Never duplicate the transferred amount across every projected edge. |
| Generic Ethereum edges | External calls, internal value transfers and token events are different observations. | Specify asset, units, failed/reverted treatment, trace/log identifiers and deduplication. Keep transfer and call graphs distinct. |
| Ratio-only motif features | Zero or tiny null means make ratios unstable; normalization can discard useful activity information. | Retain raw counts, activity controls, null mean/dispersion and a predefined zero-denominator policy. |
| Graph adjacency ablation with fixed graph-derived features | Those features already contain topology. Removing message-passing edges tests only the extra value of message passing. | Separately remove/recompute motif features and test graph versus ordinary activity features. |
| A1 required before every flow test | A broad classifier may fail while a narrow set of known exchange addresses is useful. | Allow a separate, explicitly scoped known-label flow experiment with coverage limitations. |
| Macro-F1 0.85 / merge precision 0.90 | Neither threshold measures downstream flow error; one mislabelled large wallet can dominate value. | Add per-class precision, abstention/coverage and value-weighted error; justify thresholds by the consuming task. |
| PR-AUC increment of 0.005 as universal kill criterion | A small gain can be real but uneconomic; an uncertain estimate can miss a useful gain. | Predefine a minimum relevant effect and uncertainty rule. Distinguish failure from insufficient power. |
| Weekly/monthly isolated graph partitions | Motifs crossing a boundary disappear. | Specify a lookback overlap and assign each motif once, such as by completion time. |

Several guard details also need refinement. Concentration shares make sense for nonnegative counts or explicitly defined absolute contributions, not arbitrary signed features. A 20% top-node threshold is a proposed diagnostic choice, not a universally validated stop rule. A timestamp null should be constrained to information available at the decision; a full-history shuffle is inappropriate for historical online features. Preserve ordering dependencies when testing Bitcoin reordering. Ethereum execution order and within-transaction log order carry semantics, so arbitrary reshuffling tests robustness rather than representing an equally valid chain history. A small time delta is not interchangeable with same-block membership.

Raphtory's documented local function returns 40 motif counts per node; its multiple-delta function is documented for **global** counts. The spec should not promise an efficient local per-class sweep from that API without verification. Pin the version, timestamp units and treatment of simultaneous events, then check a few hand-countable graphs. [Raphtory motif API](https://raphtory.readthedocs.io/en/v0.12.0/reference/algorithms/motifs.html). A global delta sweep can still be useful; splitting a graph by class changes which motifs are present.

**Smallest useful next study — proposed, not launched**

First choose the claim. Reproducing the published MCM needs its exact artifact/data mapping and clarification of the evaluation protocol. Testing whether graph information improves the local trading baseline is a different experiment and can proceed with a simpler method. Entity classification could independently make a thesis contribution, even if no trading edge survives, but would redirect effort away from the current economic objective.

For the trading question, the recommended development sequence is:

1. Use one chain, preferably Ethereum for the initial address-level representation, with an explicit transfer scope. Start with native ETH; adding tokens or traces is a declared expansion. Set one decision frequency and horizon. Limit initial engineering data to a fixed interval without inspecting price relationships.
2. Audit source schema, coverage, latency, event semantics and resource costs. Build immutable local Parquet partitions and a small feature table. Spark, Delta, S3, a node and PyG are not prerequisites unless measured constraints justify them. Use the pinned repository runtime or a separately declared compatible component environment.
3. Freeze a small nested comparison: existing causal market features; the same model plus ordinary on-chain activity; then the same model plus a small fixed motif family. An optional known-exchange flow arm is conditional on historical label admission. Keep every comparison on matched observations with the same optimization budget.
4. Use chronological development folds and untouched forward confirmation. Freeze all transformations before each test. Purging follows actual target overlap and execution timing; CPCV can supplement robustness analysis but does not by itself recreate training only on the past. Null tests must preserve relevant temporal dependence and cover the entire selection procedure.
5. Advance only if graph information adds a stable improvement over activity controls, with uncertainty quantified. Then test an explicit executable policy with fees, spread, slippage, turnover, funding/borrow when applicable and signed-cashflow accounting. Keep all attempted, failed and unavailable configurations.

For the stated objective of limited crypto-price exposure, raw BTC/ETH direction accuracy is incomplete. Register exposure limits and either test a causal hedge/relative-return construction or measure the resulting market exposure explicitly. Hedge costs and changing beta remain part of feasibility. No directional classifier should be described as market-neutral by construction.

An engineering planning allowance of roughly one to two working weeks for source admission and a bounded prototype is reasonable **only if access is already available**. This is judgment, not a measured estimate. It does not include historical label reconstruction, exact paper reproduction, adequate statistical power or prospective confirmation. The spec's 13-week estimate cannot be justified until those dependencies are resolved. At $1,000 capital, even an illustrative $20 monthly recurring data/compute charge consumes 2% of capital monthly before trading costs; research infrastructure expenditure and deployable strategy economics should be reported separately.

The recommended decision is to defer the full platform and GNN, retain the graph-information hypothesis, and make data availability plus incremental value over simple activity the first gates. Failure to establish historical labels blocks historical entity-flow claims; it does not automatically block an unlabeled graph experiment. No local financial sample was opened, no empirical gate was changed and no new run was registered by this review.
