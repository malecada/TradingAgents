# Preservation and admission verification

Baseline: `3202d7982c47bb1472a8f3eb43a0851fd37b1480`. Registration: `67eb720305ccddff266df396e61d03dc2fa1985e`.

The new verifier covers every original tracked blob, the exact archived engine, semantic preservation of all prior gate objects, append-only findings/corrections, and the original financial-ledger prefix. Before execution, the ledger must remain byte-identical; final verification requires exactly 72 ordered registered identities with explicit availability for all 288 indices, 576 sleeves and 72 shadows. A missing identity, unknown status, unexplained unavailable object or incomplete child promoted to complete is rejected. Numerical metric correctness remains a separate result review.

Synthetic regression sequence, observed in tool output:

- Initial preservation tests: 9 failures because the verifier did not exist; after implementation, 9 passed.
- Nested ledger extension: the four new test methods failed because `check_ledger_cells` did not exist; after implementation, all 13 passed.
- Admission tests: 3 failures because the admission checker did not exist; after implementation, all 16 combined tests passed in 0.226 seconds.

The final test command was:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -B -m unittest discover -s docs/risk-policy-2026-09-10/verification -p 'test_*.py'
```

The tests use synthetic temporary files. Cases cover exact append boundaries/counts, changed old files, conflicting external receipts, path escapes/secrets/symlinks, immutable report writes, nested identity omissions, wrong cell order/configuration, duplicate/gapped/reversed/out-of-window clocks and a mocked Parquet reader that permits only the timestamp column.

Metadata-only baseline capture and admission commands, each completed with PASS:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -B docs/risk-policy-2026-09-10/verification/verify_preservation.py --registration-commit 67eb720305ccddff266df396e61d03dc2fa1985e --output docs/risk-policy-2026-09-10/verification/baseline-input-manifest.json
PYTHONDONTWRITEBYTECODE=1 /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -B docs/risk-policy-2026-09-10/verification/verify_registered_inputs.py --output docs/risk-policy-2026-09-10/verification/registered-input-admission.json
```

Observed coverage: 7,379 old tracked files, including 7,374 byte-identical files and five explicitly governed exceptions; 64 old gate objects unchanged; 270 external original receipts unchanged. The central ledger remained 748 rows and 569,325 bytes with SHA-256 `4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601`. The exact original engine archive matched both the baseline and original factor execution source.

All 264 registered pins matched. Timestamp-only reads admitted all 36 target files on the 1,241-date calendar and all 144 trace plus 72 return files on the 1,240-date calendar. All saved data hashes reconciled to the original factor result receipt. Source provenance distinguishes the original execution `27640882822d812c6d0478340495e033a11d3915` from the later diagnostic helper at baseline `3202d7982c47bb1472a8f3eb43a0851fd37b1480`.

Output SHA-256:

- `baseline-input-manifest.json`: `ab1db0d40b578d80cf38c9ba3e510acb2f160e6e35c33b87483e84ef2d1f3db8`
- `registered-input-admission.json`: `597dd78b4882f7c07be8b247102dbb4d409685f477414b3d6f4bf95e4de22fc4`

No financial values were analyzed, no financial statistics or simulations were computed, and no network requests or original-evidence writes occurred. These reports authenticate local evidence at capture time; they do not authorize execution or establish economic validity. A separately named final report must be produced after the registered run, without replacing either report above.
