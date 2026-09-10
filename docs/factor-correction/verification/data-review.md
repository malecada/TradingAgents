# Independent factor-correction data and failure review

The review covered `scripts/audit_factor_floor_2026_09_10.py` against the correction charter: bounded input dates, pinned provenance, exclusive output creation, preservation of eighteen configurations and five nested variants, and reporting qualifications. No empirical strategy run, network request, holdout price inspection or runtime source edit was performed.

The input snapshots retain exact original CSV lines and all available prior history. Both development calendars contain the required 1,241 dates; the XS prior-history join starts at the later source start. The saved-cache proxy limitation, initial valuation date, 1,240-return clock, benchmark-index interpretation and lack of strategy validation remain explicit. Registry preflight and pinned-file checks precede computation and are repeated before finalization; the results directory refuses reuse. This review does not certify the unavailable July input lineage.

## Finding and disposition

The original shared exception handler covered all variants and the invalid-log shadow. Pre-fix synthetic caller probes demonstrated:

- A shadow-only `ValueError` retained five successful variants in each cell but replaced every primary summary with `unavailable` and omitted an explicit shadow status.
- A zero-execution-only `ValueError` retained only the primary variant in each cell. The remaining variants were neither attempted nor represented. Both probes retained eighteen cell records, which concealed the reduced nested denominator.

The repaired wrapper isolates variant failures through `guarded_variants` and handles invalid shadow arithmetic separately. The persisted caller regressions in `tests/test_factor_correction_failures.py` repeat those two probes using the real `main` orchestration with temporary synthetic CSVs, archived-function/engine fixtures and intercepted registry calls. They verify eighteen distinct cells, all ninety nested variant statuses, successful primary summaries, explicit diagnostic failures, continuation of later variants, saved complete return clocks and matching ledger payloads. No historical input or result supplies a test value.

The two caller regressions pass. The zero-execution failure remains unavailable while the other four variants and shadow complete. The shadow-only failure leaves all five measured variants and the primary summary intact. The finding is resolved for the demonstrated failures; no further material issue was identified in this bounded review. Engine arithmetic and production registry authority are separate checks, not claims established by the mocked orchestration fixtures.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/test_factor_correction.py tests/test_factor_correction_failures.py
```

Result: **14 passed in 1.67s**. The pre-fix evidence is the caller-probe output recorded before the root repair; no runtime source was reverted to reproduce it.

Reviewed runner SHA256: `c2cd3be3c8f7096e6f1311bd031d4253d720c1f329e8e80d497a6b8d33552861`.

New regression file SHA256: `7c23896ee58a0c5bddf08b02270f0edd38d9e3a66b1f694168deb10a8e10b92c`.
