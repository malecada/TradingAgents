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
