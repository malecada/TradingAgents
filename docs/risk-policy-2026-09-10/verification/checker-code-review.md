# Independent review of the saved-output checker

Scope: `check_results.py` and `test_check_results.py` in this directory. Review was independent of the evaluator and used source inspection plus deterministic synthetic corruption probes only. No empirical output, historical price observation or policy result was consumed. The reviewer wrote this note and the final regression-test additions. Executable fixes were sent to the root owner rather than applied to the checker.

Initial reviewed checker SHA-256: `5e0656e6a2973587d737f7d0511d45bf586ddceb0a85b670ec3b54bd5b291d95`. Initial test SHA-256: `94cf1c902b474cb683baeeb6d38583e8707c5c6d1ff7807ec9a1dd99acca583b`.

## Findings sent before source freeze

1. **Required exits were not enforced in both directions.** Initial lines122–128 checked that a reported exit had a registered cause, but did not require an exit when a price stop or pre-exit portfolio halt held a nonzero marked position. The block state was updated only from the reported exit flag. A synthetic false-exit trace was accepted as a waiting-policy arm even though it remained exposed throughout the stopped raw episode.

   Reproduction:1241 constant100 price observations, zero costs/funding, raw target zero through index19 then one. Set Low[20]=95 so the registered price stop marks97. Start from a synthetic immediate-policy trace, then alter return-row19 to `exit_executed=False`, `closing_notional=9700`, zero exit notional/turnover and opening-only total turnover10000. Set the following row's opening/total turnover to zero. NAV is unchanged under zero costs. `check_trace(..., arm='A01', ...)` accepted the fabricated no-exit book. Required fix: assert exact executed-exit status from the independently derived stop/halt cause and nonzero marked holdings under the frozen inactive equity-stop channel.

2. **Policy trace metadata and reported waiting counts could be fabricated.** On that synthetic book, setting `raw_target`, `requested_target`, `sizing_sigma`, `blocked_before` and `blocked_after` to999 and `decision_blocked=True` on every row still passed `check_trace`. The main checker then compared summary waiting counts with the unverified trace flag, allowing mutually consistent false metadata. Required fix: independently validate the full agreed raw/requested target, sigma, block-before/after-decision/after-stop, release, reason and stopped-direction fields, including their null/boolean semantics.

3. **Required period metrics could be omitted.** `check_periods({'periods': []}, ...)` returned successfully. It iterated only the supplied periods and did not verify the fixed three ordered bounds or complete period calendars. Required fix: require the exact registered periods and then verify every corresponding metric.

4. **Contrast verification was count-only.** Initial lines273–274 required54 direct and54 factorial rows but did not check identities, orientations, null propagation or numerical formulas. Required fix: reconstruct the registered direct differences and sizing/waiting/interaction contrasts from their already checked primary source records; preserve undefined metrics rather than inserting zero.

Two related evidence checks were also recommended: compare each result cell's configuration and arm with its corresponding gate cell, not only its id; and require every consumed output file to be present in the result hash manifest. Otherwise mislabeled cell bodies or unmanifested constructed-path reads could escape those parts of the review.

## Checks that were sound in the initial version

The independent once-lagged volatility formula matches the original twenty-return estimator. Entry/exit turnover, signed funding, one-way linear charges, quadratic impact using each leg's NAV, initial-NAV continuity, price-anchor persistence, threshold marks, pre/post-exit peaks and absorbing halt arithmetic are reconstructed directly. Original-field control comparisons preserve flags and the intended numerical tolerances. Complete return calendars, separate-sleeve index arithmetic and frozen-gross log shadows are checked without invoking a strategy on empirical data.

The initial three synthetic checker tests covered causal volatility, original flag/weight corruption and a funding-dollar corruption, but did not exercise the false-accept cases above. Their existence did not establish complete checker coverage.

## Disposition

**PASS for the reviewed scope after correction.** The root-owned checker now requires the independently derived executed-exit flag in both directions, reconstructs the agreed policy decisions and metadata, enforces the three exact ordered period calendars, and checks every supplied direct/factorial identity, source-field coverage, coefficient and undefined-value propagation. Result identities include configuration and arm, every saved output must be hashed, and the central ledger must contain the unchanged registered prefix followed by the exact prepared72-row receipt with matching result cell ids and metrics. No unresolved instance of the reported false accepts remains in the final synthetic probes.

The reviewer added39 regression cases to the original3. The zero-cost balanced missing-exit corruption is rejected specifically by `required executed exit`. Relabeling an immediate-policy book as a waiting arm fails, and twelve individual policy-field corruptions fail their corresponding independently reconstructed check. A synthetic exit-fee-induced halt is accepted with the pre-exit flag false and the post-exit flag true; changing the latter is rejected. Missing, duplicated and reordered period records/calendars fail. Each of the six direct/factorial scalar formulas is perturbed independently, alongside null/status/identity/metric-coverage mutations. Temporary-file evidence fixtures prove that wrong cell bodies, unmanifested outputs, a changed historical ledger prefix, extra central rows and even consistently rehashed but mismatched receipt rows are rejected.

Verification command, run before any empirical execution:

```text
PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B -m pytest -p no:cacheprovider -q docs/risk-policy-2026-09-10/verification/test_check_results.py
```

Result: **42 passed in6.06s**. Exact output is preserved in `checker-regressions.txt`. All paths were deterministic synthetic arrays or temporary evidence fixtures. The main-checker fixture deliberately stops before creating `result-review.json`; no registered data, results, ledger or policy was written. This review establishes the specified verification behavior, not empirical policy performance. The root owner must execute the checker on the once-produced registered outputs after the source freeze.

Final SHA-256 identities:


- `check_results.py`: `4cad694d76fccfa5012f939eff3de5de96220ab61399999c51dd21497a98b91c`
- `test_check_results.py`: `0d89610ff971189fd2c9c7cc62fc3018372b4d47ded930a405efc21c8aa40157`
- `checker-regressions.txt`: `9c9748f487dfc530781933af3fa2b00a6ea17c3046a2c270438152e5af0727ca`
