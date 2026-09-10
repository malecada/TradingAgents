# Final preservation and artifact metadata verification

Status: **PASS**. The committed verifier completed on September10,2026 at15:21:33UTC. This check used file hashes, recorded identities and availability statuses; no strategy replay, return calculation or new data request occurred.

Machine-readable report: `preservation-final.json`, SHA-256 `bf3cee7c603b24ae131de7ad704cbbcb0986d651a513a3327cee84346847e1f3`.

```bash
PYTHONDONTWRITEBYTECODE=1 /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -B docs/risk-policy-2026-09-10/verification/verify_preservation.py --phase final --registration-commit 67eb720305ccddff266df396e61d03dc2fa1985e --output docs/risk-policy-2026-09-10/verification/preservation-final.json
```

All7,379 original tracked files remain covered:7,374 byte-identical files plus the five explicitly governed paths. All64 prior gate objects are unchanged, the sole new risk-policy gate matches its committed registration, and all270 external original inputs remain byte-identical. The original engine archive is exact. Findings and correction notes had no suffix yet at this capture; any subsequently authorized completion append requires its own prefix check.

The old748-row ledger prefix remains exactly569,325 bytes, SHA-256 `4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601`. Its72 appended rows have72 unique trial IDs and exactly match the prepared ledger receipt and the result's ordered cell metrics. All72 cells,288 indices,576 sleeves and72 shadows are explicitly complete. The final ledger has820 rows and5,844,626 bytes, SHA-256 `4459ddc70d41d9a99db06ab53d9ad4c8f42b6f4d282abd93b4857b4474041927`. The append SHA-256 is `4ec925c82b6b114a86c10fa639781d8b7ae6019e15f8d7a4aec257adbdb98e5f`.

Independent artifact metadata checks confirmed:

- Execution source `2dfb047d5c2f2ff821706736eb9f5508a14e7304`; no current differences under scripts, tradingagents, tests or risk-policy verification Python files relative to that source.
- Result SHA-256 `245ad6a30022a4ab7f115b1acb52d33dc5537ce43d8c0b6850e5ec25391d1006`, size10,893,498 bytes. The embedded registered gate and264 input pins match the committed registration.
- Every2,092 output hash recorded by the result matched its local file. The exact output tree contains those2,092 files plus `result.json`, with no missing or extra file:2,093 files and209,140,604 bytes total.
- Artifact identities comprise576 traces,576 daily diagnostics,576 stop-event files,288 return frames,72 invalid-log shadows, and four start/admission/control-parity/prepared-ledger receipts. All54 direct and54 factorial contrast identities are present.
- The SHA-256 of the sorted inventory serialized as compact, key-sorted JSON records `{path,bytes,sha256}` with repository-relative paths is `809761f3c56c59fc5914f2795438ce2a9e17379b59744f9e0311880bdbfdd9b0`.

These checks cover artifacts available locally at verification time. Numerical correctness is the separate independent result check; Git staging, commit and remote retention have not been certified by this note. Original artifacts and the new empirical result were not edited.
