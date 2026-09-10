# Independent review of the conditional recovered replay

Scope: committed registration `4df421b`, `docs/data-recovery/2026-09-10-replay-charter.md`, explicit experiment-key support in `scripts/audit_reeval_common.py`, the exact input overlay in `scripts/audit_recovered_liq_2026_09_10.py`, optional hooks in the original accounting wrapper, and `tradingagents/xsect/lifecycle.py`. The review uses source, registered/saved metadata, hashes and synthetic tests. No financial replay, original/recovered price-value inspection, strategy outcome or code edit is performed by this reviewer.

## Frozen experiment and statistical interpretation

The registered family object is exactly equal to the original September 9 liquidation-fade family: all six ordered cells, original thresholds, cost assumptions, warmup, development end, probe rules, placebo policy, and original DSR count 100 are preserved. The 221 original input hashes agree with the preserved original result; the 47 replacements agree with those original identities and total 5,568 inserted hours. The five lifecycle events equal the prior verified exposure registration. All **272 original, snapshot and auxiliary file hashes** independently matched the new registration before creating any run context or output.

The cumulative DSR policy count is frozen at 156 = 126 original rebuild identities + 24 September 9 accounting cells + six registered correction cells. Exposure-only forensic rows remain outside financial counts. All six configurations must remain recorded, including unavailable inputs or probes. This is a diagnostic correction of a previously observed development window, with preserved funding exclusion and spent holdout restrictions; it cannot validate or promote a strategy. Neither statistical independence nor complete venue lifecycle history is established by the policy count.

The original existential P1/P2 logic remains unchanged: a known qualifying event/day or wholly scoreable qualifying P2 cell can establish its respective positive probe; an unavailable cell cannot pass from its scoreable subset. An unresolved P2 family stops the full six-cell family before portfolio metrics, with explicit statuses. Original SR or original-denominator DSR failure controls downstream early stopping; the more conservative current denominator does not hide a possible historical gate reversal.

## Lifecycle and execution boundary review

Every primary book, zero/double-fee diagnostic, invalid-log diagnostic and actual placebo book calls the same schedule guard before the portfolio function. The guard uses complete hourly target schedules reconstructed from the recovered inputs, rather than hardcoded exclusions from prior exposure results. It rejects a nonzero target during a bar containing closure, a final valuation becoming available exactly at closure, an incoming position when the target becomes flat exactly at closure, and any requested post-closure position. It does not synthesize an exit, settlement price, successor position, fee or funding payment.

A nonzero target decision during an announced restriction-to-closure period is unavailable even if the target fraction is unchanged: NAV/price drift can require an unknown quantity increase. Zero-target exits before termination remain possible under the original timing. The guard does not infer order fills or actual quantities.

P2 is distinct: compounded simple returns telescope to a fixed-quantity entry-to-exit price diagnostic. A trigger at bar `t` enters when the prior close is available at `t+1`, and its H-bar horizon is valued at `t+H+1`. Entry at/after a new-position restriction, or valuation at/after closure, is unavailable. An intermediate restriction alone does not imply an order for a fixed-quantity holding. This distinction was discussed during review and is explicit in the helper docstring. No extra intermediate maintenance rule was introduced into P2.

P2 retains all triggered windows, with disjoint endpoint-censored, ordinary-missing and lifecycle-unavailable counts plus an explicit missing/lifecycle overlap count. Scoreable-subset means remain descriptive; a cell with an unresolved required window has no gate value. Known event scope remains the five registered closures, with ordinary held-return errors continuing to fail closed elsewhere. This is not certification of every historical contract incarnation.

## Actionable finding and resolved fix

The initial overlay constructor called the general market-source `track` function for every pinned auxiliary file. The preserved September 9 result lives outside the registered market roots, so the real registration would reject that file after creating the exclusive output directory. The exact rejected path was confirmed from registration metadata before execution.

The parent fixed this narrowly: only exact registered auxiliary paths are separately verified and added to the final hash manifest. Market tracking and reads retain their original root restrictions. The regression fixture now places its auxiliary receipt outside every market root; no gate/root broadening occurred. Original and replacement bytes are both recorded and checked again at completion, while market reads use only the registered replacement mapping and filter dates before materialization.

Explicit experiment-key support is consistently propagated through registration lookup, preflight, start marker, output directory, completed result and ledger calls. Legacy callers retain the original default key. Existing output or incomplete start state remains non-overwritable, and all declared cell identities remain required at finalization.

## Verification

Commands use `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.` and `../TradingAgents-predlab/.venv/bin/python`; no network or empirical execution occurs.

- Common context tests: **12 passed in 0.46s**.
- Combined `tests/predlab/test_recovered_liq_context.py`, `test_audit_reeval_common.py`, `test_lifecycle_replay_guards.py`, and `test_audit_reevaluate_accounting.py`: **61 passed in 1.27s**.
- Registration coherence assertions: passed (unchanged original family, 221 original hashes, 47 overrides/5,568 hours, five events).
- Exact registered file-hash verification: **272 passed**; no run context or replay output created.

Final combined command:

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest tests/predlab/test_recovered_liq_context.py tests/predlab/test_audit_reeval_common.py tests/predlab/test_lifecycle_replay_guards.py tests/predlab/test_audit_reevaluate_accounting.py -q -p no:cacheprovider`

**63 passed in 1.34s.** The added integration fixture invokes the actual prepared placebo callback with synthetic inputs, makes its first draw require an unverified closure, verifies `LifecycleUnavailable`, and confirms the remaining shift/random draws advance the same seeded RNG with `materialize=False`, without a redraw or additional portfolio. The fixed-quantity P2 test separately confirms that entry before an intermediate restriction and valuation before closure remains scoreable. Legacy no-policy behavior remains covered. `git diff --check` passed.

**Disposition: the startup finding is resolved; no remaining implementation or registration blocker was identified for the frozen conditional six-cell replay.** Source must be committed before empirical execution, and lifecycle or probe unavailability must remain a reported outcome rather than triggering relaxed criteria or a substitute settlement. This review does not certify profitability, complete lifecycle history or live execution.

## Reviewed source identities

Final SHA-256 values at synthetic verification:

| File | SHA-256 |
|---|---|
| `scripts/audit_reeval_common.py` | `019eb044e9637d6080c486ad962d18fc30e1daf535c5de9611ad48ed2efff966` |
| `scripts/audit_recovered_liq_2026_09_10.py` | `1dc06d25f287dab47a7dbe1d31f35c94a39e53620876b364bf17a767830a67f3` |
| `scripts/audit_reevaluate_accounting_2026_09_09.py` | `ff4b0a1acd7f52826bab3152ceb2d7c62f285a0985a03429341d06564229da75` |
| `tradingagents/xsect/lifecycle.py` | `00f89c05f4b87e337030cc28d41372a913170d09951fc6bfe8fe270c76f9c8e3` |
| `tests/predlab/test_recovered_liq_context.py` | `d5e85f0d673830a7026e0f764fd9b8f9642e810d4d99b0e979b4eb6892003169` |
| `tests/predlab/test_lifecycle_replay_guards.py` | `71e88d2501307edadb63c1ab5406940eeae2e2af15e8b781f3a244f85c6dbb4e` |

## Independent verification of the completed replay

The single registered run completed under frozen source `a87b67b97cd88ed3bbe83e2dd03eca99a5082d33`, from `2026-09-10T07:40:04.781710Z` to `2026-09-10T07:41:15.481352Z`. The saved result is `data/predlab/audit_recovered_liq_2026_09_10/liq_fade/result.json`. This follow-up reads saved results/return streams and hashes their references; no signals, allocations, market observations or strategy are reconstructed.

**Full artifact verification passed.** Eight relevant executable/accounting/statistical source files match historical commit `a87b67b`; the result's family, canonical full-gate hash and correction-policy hash match that historical registration/policy. All 272 recorded input hashes equal the exact registered original/snapshot/auxiliary map, and all three recorded output hashes match. The start marker and result agree on experiment, source, gate, policy, runtime and start time. The output directory contains only the result, start marker and two declared return archives.

All six ordered original cell configurations remain present. Original DSR n=100 and current accounting-policy n=156 are consistent throughout every available stream. The prior central ledger's **411,461 bytes** remain an exact prefix, matching historical `a87b67b` and SHA-256 `0b9ab125e64e9c808ccd398d703092e344b6f8772de9e6ec6e223a1e2b9f9a09`. Exactly six unique new identities follow, one per declared cell; their configurations, metrics, window and source/gate/policy provenance match the result. No earlier row is replaced and no previous row used this new experiment key.

| Object | SHA-256 |
|---|---|
| Completed replay `result.json` | `2a210cb47723857e2b6b8e318f174e3becd010a91bbcf9405b47fec26d7ebd66` |
| `thr2.5_H6.parquet` | `7ef3535f27d7fcc08641be91c3828b10bf4d39314ad2b06c557c7c14abe33f2f` |
| `thr3.5_H6.parquet` | `d65d98397a69429012bd7acad1076cb1d00a130b47099da13b28d93aa6b3b888` |
| Central ledger after six appends | `710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791` |

### Recorded probes and denominator reconciliation

P0 records correlation `0.9999999999999998` across 1,550 paired daily returns, meeting the unchanged 0.99 requirement. P1 records five known hit days against the required four, no unknown days, and zero unavailable observations among its 960 required symbol-hours. These summary counts and matched-day lists reconcile.

P2 retains all six cells. Its disjoint reason counts reconcile exactly as events = scoreable + endpoint-censored + ordinary-missing + lifecycle-unavailable. Endpoint-censored and ordinary-missing counts are zero in this run. The missing/lifecycle overlap is separately disclosed and must not be counted twice:

| Cell | All triggers | Scoreable | Lifecycle unavailable | Missing/lifecycle overlap | Eligible P2 mean (bp) |
|---|---:|---:|---:|---:|---:|
| `thr2.5_H6` | 5,069 | 5,069 | 0 | 0 | 64.8364 |
| `thr2.5_H24` | 5,069 | 5,065 | 4 | 0 | Unavailable |
| `thr2.5_H48` | 5,069 | 5,050 | 19 | 9 | Unavailable |
| `thr3.5_H6` | 709 | 709 | 0 | 0 | 107.8974 |
| `thr3.5_H24` | 709 | 708 | 1 | 0 | Unavailable |
| `thr3.5_H48` | 709 | 698 | 11 | 6 | Unavailable |

The two wholly scoreable H6 cells exceed the original 25bp threshold, so the existential family P2 pass is correct despite four unavailable cells. The four subset means have null gate values and do not establish a P2 pass. The saved September 9 trigger counts were 5,064/710 versus recovered 5,069/709, confirming that availability was reevaluated rather than inherited from old cell labels.

Probe verification here establishes consistency of saved summaries and the frozen family rule. Per-trigger panels are not archived, so this review does not independently regenerate individual P2 classifications or means from market inputs. Source logic and boundary fixtures were reviewed before execution.

### Saved-return arithmetic and cell findings

All **seven saved streams** (three in the lower-threshold H6 archive and four in the higher-threshold archive) contain the exact 1,551-day UTC development clock and finite values. Using direct arithmetic on those streams, annualized calendar SR, drawdown including initial NAV=1, compounded total return, mean return, and DSR at both n=100 and n=156 independently reproduce the recorded metrics within numerical tolerance. The recomputation implements the frozen skew/kurtosis and expected-maximum-SR formulas directly; it does not call the replay or summary helper.

| Cell | Primary SR | DSR n=100 | DSR n=156 | Maximum drawdown | Total return | Original gate |
|---|---:|---:|---:|---:|---:|---|
| `thr2.5_H6` | 0.159713 | 0.013861 | 0.009289 | 71.2139% | 0.5126% | FAIL |
| `thr3.5_H6` | 0.815672 | 0.306207 | 0.254849 | 16.5905% | 49.2217% | FAIL |

Both SRs are below 1 and both original-denominator DSRs are below 0.9, independently sufficient to fail the original conjunction. Consequently, the expensive remaining placebo gates are explicitly not run. No RNG-advancement error is recorded. Compared with the saved September 9 corrected SRs, the changes are approximately −0.006002 and +0.000243; recovery does not reverse either measured verdict.

The zero-fee diagnostics yield SRs **0.612935 / 1.017149** and original-denominator DSRs **0.103181 / 0.546471** respectively. Thus fee removal alone still does not satisfy the original DSR criterion. Double-fee SRs are **−0.295272 / 0.609170**. Each computed diagnostic is explicitly ineligible. The lower-threshold invalid-log counterfactual is unavailable because a log observation is below the supported simple-return floor at `2022-05-12T09:00Z`; this is a diagnostic limitation, not failure of the real simple-return stream. The higher-threshold invalid-log diagnostic is saved and independently reconciles to SR **−0.129306**, total return **−14.1998%**, and drawdown **40.7460%**.

All four H24/H48 cells remain **unavailable**, with null gate verdicts and no saved return archive. Primary, zero/double-cost and invalid-log paths all reject unresolved LUNA exposure in the `2022-05-12T15:00Z` bar containing the 15:30 UTC forced closure. Their downstream statuses distinguish unavailable primary data from a negative primary gate. In particular, `thr3.5_H24` is unavailable under the lifecycle-aware contract even though September 9 had produced a numerical stream; that old stream cannot supply the missing terminal cashflow.

**Final disposition: no integrity, arithmetic, denominator or recorded gate-logic defect was found.** The full six-cell result is two measured original-gate failures and four lifecycle-unavailable cells, with zero passes. Funding exclusion, the five-event lifecycle scope, unresolved BNX/ICP identity periods and spent holdouts remain explicit qualifications. No strategy is validated by this replay, and the unavailable cells remain contingent on authentic settlement evidence.
