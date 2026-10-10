# Concrete runtime-input review

**ACCEPT_METADATA_SCOPED_RUNTIME_ENTRY_ONLY_UNEXECUTED.** No material defect found in manifest `c4b2ac89dd60d1db4a40035d47d174e2165007c7424745d1e8809bb521b69d78`. This accepts the concrete inputs within scope review9a82f6c5; it does not accept full package payload integrity, loaded NumPy/SciPy versions, native execution or financial admission.

The independent external digest chain is exact: INVENTORY01 `7f0cbd1a34389ac112c9e09241cb1bcab7b1972e77e5fe7d13dc124984266175` → runtime.runtime_inventory_sha256; RUNTIME_REFERENCE01 `247d62394372e4ef10b4e79f351e5c2aee017b846cb2fc35e29b774b2a7eb366`,382bytes → policy runtime path/hash/length; POLICY01 `cf9cbe5ca7aa1a9e1849d59ec63916f8aa288b35a82d84f8b35c432c575506be` → manifest policy reference. This independently supplies the inventory-body join that the parser itself does not perform.

Six actual bodies were streamed through SHA256: resolved interpreter binary, NumPy/SciPy METADATA and RECORD, and actual29 gate-pinned environment. Their exact byte counts, hashes, recorded mode/link counts and stable descriptor signatures match. The pinned interpreter's actual executable/resolution, Python version, platform, machine and byte order match the runtime reference. Both distribution METADATA versions match inventory/reference/environment; each RECORD entry for its METADATA independently agrees with the actual METADATA digest and size. Other files listed by RECORD were not read or verified. The two METADATA files have recorded hard links; this does not defeat the explicitly metadata-only body observation, and no writer exclusion or future currentness is asserted.

The exact accepted04 stdlib policy parser accepts the eight policy fields and nine runtime fields. Actual bounded C/library reads match its pinned hashes; library ownership and bounded regular-file requirements pass. No rebuild, library load, native/scientific import or numerical execution occurred. The inventory's package-payload, loaded-version, historical compiler/libm, writer/currentness and financial-authority exclusions are explicit and preserved. Candidate drafts and the scope review were not changed.

One CPU3/nice10 focused verification completed without fixture failures, bounded by CPU15s, alarm20s/external25s, AS256MiB/file4MiB. RESULT01 contains the actual six-body observations and all assertions. No qualification or historical numerical matrix was replayed. Main/Git/STATE and the current pilot were not changed.

After actual pilot29 terminal/outcome handling and Root's exact04 installation/source acceptance, Root can use the existing policy in this unchanged finite command. The output path was absent at review time and must still be fresh at execution:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 timeout 185 .venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-connected-qualification02-2026-10-10/qualify.py --runtime-policy /home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-runtime-input01-2026-10-10/POLICY01.json --output /home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-connected-qualification02-execution01-2026-10-10 --execute-after-terminal
```

Root alone owns installation and launching. Current frozen Main is not installed04. The command will still need genuine loaded-version/currentness checks and actual finite native/connected numerical results; failures or unavailability must be retained. This entry acceptance creates no Admission/Owner, universal equivalence, mapping/RSS/capacity or production claim.
