# Remaining direction-prediction work

Primary reference: [Çelik and Sefer, publisher article](https://link.springer.com/article/10.1007/s10614-025-10940-1) and [published PDF](https://link.springer.com/content/pdf/10.1007/s10614-025-10940-1.pdf), inspected September 16, 2026. This note is a design assessment, not authorization or registration of a financial experiment.

The reported whole-chain direction accuracies are 76.5% BTC and 80.4% ETH (Table 2). The 88.2% result is the fund-account subset; its price-only GRU reaches 87.0% (Table 6). The method learns a motif dictionary and attributed-graph representations through MCM/GAT, then uses prices and an attention-based LSTM. It uses weekly address graphs and daily prices for 2016–2024, with stated two-year training and subsequent one-year testing. The article makes data available upon request. These paper-specific claims do not establish reproducibility or attainable future accuracy.

The current prototype counts fixed three-event temporal motifs. It is an engineering foundation and a distinct candidate feature family; it does not implement that learned spatial-motif architecture. Entity classification is a separate proposed track, not a demonstrated prerequisite for the paper's address-level whole-chain experiment. Reproducing the selected-fund result would require the exact account list and historically appropriate membership.

Remaining work:

1. Admit a multi-year, gap-checked graph/price panel with a retention and backup plan. Three years gives only one two-year training/one-year testing fold. A week establishes computational behavior, not forecast power.
2. Freeze forecast horizon, direction label, UTC close, zero-return treatment, class balance and publication/computation lag. Resolve the weekly-graph/daily-price alignment: a completed week's graph cannot be used for a forecast earlier in that week. This is a potential failure mode to test, not a finding of leakage.
3. Resolve exact node/edge attributes, filtering, graph pooling, motif dictionary construction, model dimensions, optimizer, lookback, seeds and fold dates. A paper-faithful implementation needs these choices; unresolved choices make the work an independent replication attempt rather than an exact reproduction. Fit all learned dictionaries, normalizers and selectors inside training folds.
4. First compare identical dates/targets/models using M0 market features, M1 ordinary on-chain activity, and M2 graph features. Include majority-class/persistence baselines, balanced accuracy, log loss, calibration, uncertainty that respects serial dependence and per-year results. Freeze model/trial budgets and keep a final untouched holdout.
5. Test feature value with timestamp/label placebos, activity and graph ablations, concentration and ordering sensitivity. These diagnostics can reject artifacts without implementing an expensive neural architecture first.
6. Only after the incremental feature question is supported, build and benchmark MCM/GAT/attention-LSTM for a closer architectural replication. The 8 GiB counting allowance does not establish its memory or training requirements. Costs and executable trading evaluation are later, distinct questions.

The paper's accuracy is a claim to investigate, not a target to attain by changing splits or searching configurations until the number matches. The original specification remains byte-preserved; this note qualifies its claim that entity-resolution work is necessarily the dominant prerequisite for direct price-direction research.
