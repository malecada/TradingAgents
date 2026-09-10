# Independent factor-risk code review

Review date: September 10, 2026. Binding registration: `38d9a67e6ff042cb1fd870877b3e0222f40fdc08`; scope: the factor-risk charter, plan, pure diagnostic module, runner, original execution source and synthetic tests. This review used source and metadata only. No saved target/trace values were consumed, no strategy or alternative policy was run, and no network request occurred. The worker's 35 passing synthetic tests were read but not rerun.

**Verdict: PASS for the reviewed implementation after the parent-requested guard and reporting corrections.** No additional material issue was identified. Final committed-source preflight, preservation verification and independent saved-output reconciliation remain required.

## Accounting and chronology

- Diagnostic volatility matches the original development reset, duplicated initial close, one-day price lag, twenty-return sample standard deviation and strictly prior volatility threshold. It does not regenerate signals or targets. Saved entry/flip sizes are reconciled to the original formula; unsupported same-sign target changes make the sleeve unavailable.
- Incoming drifted, applied, closing and latent weights remain separate. Each receives nominal volatility proxies, reference-risk ratios, finite/active/unavailable counts and threshold coverage. Unknown reference comparisons remain null. A drifted leverage crossing is not described as a breached opening-target rule.
- The signed target-change and maintenance terms add to the observed opening trade. Their absolute values retain the explicit netting term and are not presented as additive realized turnover or counterfactual savings. Opening charge classes are disjoint; stop exit charges remain separate.
- Every price stop has a dated successor classification, with same/opposite entry, flat, halted and censored cases. Next-entry charges are assigned to their single preceding stop once. Saved builder sizing dates and ages distinguish reused target sizes from fresh raw-target entries; no restart scenario is simulated.
- Staged peak accounting matches the original engine's initial, pre-exit and post-exit order. The pre-exit portfolio-stop flag remains meaningful during halted cash tails because the original engine continues calculating it. Post-exit charges can trigger the permanent halt despite a false pre-exit flag. Peak-to-halt attribution uses differences in cumulative recorded dollar components at those exact stages.
- All target and trace dates remain present, including warmup and halted cash. The module reconciles the initial NAV, continuity, target/halt exposure, opening and exit notionals, turnover/charge subdivisions, saved returns and cumulative component identities. Prior result component totals, stop counts and halt dates must agree.

## Admission and failure preservation

The production path checks the registered 18 configurations, 36 sleeves and 78 pins. The independently completed timestamp-only admission established the exact 1,241 target and 1,240 trace dates for all sleeves, so the pinned files contain only the authorized development window. Unverified target/trace bytes are never parsed; a bad sleeve input remains unavailable while other admitted sleeves can be retained. Unavailable shared provenance preserves the full denominator.

The final runner reserves `started.json` before fallible input fingerprints or admission reads. Its production admission callback checks complete registry provenance and compares the central financial ledger byte-for-byte with the registered baseline, requiring 748 rows. The same callback runs before completion. Input, source and financial-ledger fingerprints are also checked again. Global failures preserve all 36 unavailable identities and a failure receipt; no result is admitted. Per-file output creation is exclusive, and an existing namespace prevents a repeat.

The parent-requested corrections—full registry recheck, exact baseline-ledger admission, durable early failure records and all-four exposure ratio/threshold coverage—are present in the reviewed code. Their regression tests cover the relevant refusal and denominator paths. No old source, gate, ledger or empirical artifact was changed by this review.

## Reviewed source identities

| File | SHA-256 |
|---|---|
| `tradingagents/strategies/factor_risk_diagnostics.py` | `bb4fd507d00aa2ba2c543d0d237ae50e6328213054971eaab115c0c21e6fbc21` |
| `scripts/audit_factor_risk_2026_09_10.py` | `3ccad266feae547ebe8a02958039f4af6370f6f96e10adf0230d923d4ce2dab9` |
| `tests/test_factor_risk_diagnostics.py` | `63f4c0d462c006d28830b78bcc1cb887d8d7eacd88049ccce2952d5fd8a99d23` |
| `tests/test_factor_risk_runner.py` | `bf5f1346ca61ac418cc7610ad07ca69ac832ec978d1c70ac54931f3eff419574` |

The original price-cache proxy, assumed daily funding, threshold stop fills and separate sleeve accounting remain qualified. These descriptive identities do not estimate realized account volatility, prove a causal cost effect, pool the sleeves into one executable account or validate a revised strategy.
