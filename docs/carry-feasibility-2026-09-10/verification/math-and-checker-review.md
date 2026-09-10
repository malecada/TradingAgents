# Independent calculator review and saved-evidence checker

**PASS for the registered conditional arithmetic.** The final calculator was read independently at SHA-256 `3e15bf12c3edfc765e4a6c52f2d4b8c0e7d1fe337c16dded893b7c9483e9928b`. No material accounting defect was identified. The review covers largest affordable lot selection, minimum versus maximum filter ordering, depth across price levels, contract multipliers, spot-base commission gross-up, retained excess spot, full-capital accounting, every terminal cash leg, reserve insufficiency and separately accrued cash benchmarks. It also confirms that the local Decimal context fixes precision80 and ROUND_HALF_EVEN, while one-third reserve admission uses rational cross-multiplication before division. No actual fee/rounding or liquidation-survival claim is introduced.

The independent `check_saved.py` does not import the calculator or collector. It uses exact rational arithmetic to reconstruct the reported quantities, cumulative entry-book cash amounts, maximal feasible lot, fee legs and conditional terminal results. Comparison with the calculator's saved decimal strings uses an absolute tolerance of1e-20. The checker verifies48 ordered entry identities and432 ordered scenario identities, including explicit unavailable records, the complete raw/receipt hash inventory, raw-to-normalized book agreement, source/charter and old-gate preservation, the unchanged820-row central financial ledger, measurement-ledger hash, snapshot clocks and conditional flags. It calculates no alternative policy, downloads no quote, and cannot execute an order.

The initial27 synthetic cases failed because the checker was absent; the exact output is `checker-red.txt`. After implementation,31 tests passed in0.21s (`checker-green.txt`). The four added raw-evidence cases reject altered bytes, a consistently rehashed but disagreeing receipt, an omitted file and duplicate request identities. The arithmetic cases reject individual quantity/cash/terminal/benchmark/margin-field corruptions even when other totals are left valid. A hand-derived nonzero-residual example and exact one-third reserve case pass. A smaller internally valid hedge cannot be substituted for the required maximum-budget hedge, and missing or duplicated measurement identities are rejected.

Command:

```text
PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B -m pytest -p no:cacheprovider -q docs/carry-feasibility-2026-09-10/verification/test_check_saved.py
```

Final checker SHA-256: `f9cee58229dc147849e174313cc5448efb7543d72983152382e16d1a852c4c13`. Test SHA-256: `19d8d7354108da5bd924558eabbc74976950989366926fa0ba7a75376e5c16b7`. The root separately reports127 combined tests passing:40 calculator,56 collector and31 independent-checker cases.

After the single registered capture, the root can run:

```text
PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B docs/carry-feasibility-2026-09-10/verification/check_saved.py
```

Success exclusively creates `saved-review.json` in this directory. No empirical capture was available or consumed during this review, so successful verification of real saved artifacts remains pending. Instrument-admission policy and venue documentation are reviewed separately by the root/data reviewer; this note does not upgrade assumed fees, public displayed liquidity or terminal reserve scenarios to executable investment evidence.
