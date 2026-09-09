# NLST4 independent source review — September 9, 2026

**Disposition: ready for the tested-source commit.** No unresolved blocker was found in the registered cache-only NLST4 wrapper. Empirical execution remains subject to the common committed-source preflight and exclusive start marker. This review changed documentation only and evaluated temporary synthetic fixtures, not actual pool outcomes.

The reviewed scope is the original 3,981 entered pools (1,205 prior-history and 2,776 previously examined new-set pools), frozen ten features, six-feature minimum and historical T1/T2 diagnostics. Registration begins at `e3c0d63ec8981612be2e8712bf9942bb0b8f74e0`; the existing-settlement clarification is `e4e60d71b5b4eb946129880d51b0ecf32098a612`. The review base is `4fe113b0eee23db634e7ea9a4d942b8b44701650`; the final source commit is assigned after this review.

## Findings resolved

- **Prior-history undercount:** an unavailable earlier feature window formerly removed the pool from later deployer counts. A synthetic example changed a known count from three to two without qualification. Every frozen creation is now retained independently. Known deployer identities still support creation counts; unknown identities, buyers or eligible outcomes explicitly qualify the affected history features. Missing outcomes do not taint decisions before their earliest possible completion. The original strict creation-time history cutoff is preserved.
- **Creation-block identity:** a one-block mutation formerly passed pair/quarter checks. Cached pool creation blocks must now match the immutable screening record; mismatch prevents evaluation rather than substituting membership.
- **Unverified entry-clock donor:** a mismatched entry clock formerly left finite feature-availability timestamps, permitting the row to normalize later observations despite its missing return. Decision, availability and completion timestamps are now cleared. A regression confirms that the row cannot supply normalization history while independently known creation/deployer information survives.
- **Root review denominator findings:** global missing inputs now retain the single registered blocked cell with all planned cohort counts. All 1,000 bootstrap draws are retained; any unavailable draw makes primary T1 unavailable. A finite-subset quantile is explicitly diagnostic.

## Verification and boundaries

Independent command:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest tests/predlab/test_audit_reevaluate_nlst4.py -q
```

Result: **20 passed in 5.99 seconds**. `git diff --check` also passed. The implementation's saved RED evidence was inspected in `verification/nlst4-history-red.txt` (four failures) and `verification/nlst4-clock-red.txt` (one failure). Root's integration log, `verification/final-integration.log`, records **171 passed in 19.03 seconds**; that broader suite was not repeated by this review.

Source inspection and targeted tests cover exact cached entry clocks, `raw2.b24 < entry_block`, strictly prior same-quarter scaling, same-time exclusion, completion at the later of nominal seven days and the selected exit header, unknown ownership as missing, completed five-minute ETH conversion, original constant-product/gas cashflows, missing-row retention, offline RPC/HTTP fencing and the explicit execution flag. Global q80 remains retrospective and cannot trigger promotion or P1.

Reviewed SHA256 values:

| File | SHA256 |
| --- | --- |
| `scripts/audit_reevaluate_nlst4_2026_09_09.py` | `dbedbc7c631f379c6695ab24d8a1f9da807280b500ea3da0834a97a83a5db32d` |
| `tests/predlab/test_audit_reevaluate_nlst4.py` | `05491d40911cfee1ecd4f3a778ac84d7258a66444ba90f8653a90f43a745701e` |
| `docs/superpowers/specs/2026-09-09-lead-reevaluation.md` | `c34b1a742cd9721dadbbd4f38d7a12a0c56b678bcc3e77229be61c3087810956` |

## Remaining limitations

Creation timestamps remain interpolated. Prior-only scaling, unverified legacy ownership and conservative history qualification can materially reduce coverage; the actual scoreable count has not been calculated here. Original three-/seven-/fourteen-day helper cashflows require their cached headers and completed FX observations. Original gas and LP assumptions exclude MEV and are not observed live fills. The new-set sample has already been examined, and full-sample q80 does not define a causal online entry policy. These limitations prevent a validation claim regardless of the eventual diagnostic thresholds.

The common publication path refuses automatic repetition, but a low-level disk failure during ledger/result publication can require explicit recovery of the unfinished run. Synthetic tests do not establish completeness or correctness of the actual cached market observations.
