# options-timing-20260915 — independent source and quiescence review

Date: 2026-11-21. Scope: source operability of the returned raw journal only. No price,
return, cash book or other financial quantity was computed or read for this review;
receipt bodies were not interpreted, only file names, `spec.json`, receipt metadata and
clocks.

The review was made in a separate session that was given the returned data, the released
package and the frozen protocol files, and was not given the closing session's
conclusion. Its counts were derived from the files and then compared with
`returned.prepare`.

## Objects reviewed

| Object | Location | Identity |
|---|---|---|
| Returned data and launch log | `/home/malecada/master_thesis/research-deployment/options-timing-20260915/return-20261119/` | 16,600 regular files, 100,953,662 bytes; manifest `reviews/options-timing-return-manifest-20261119.sha256` |
| Released package | `.../options-timing-20260915/release-22bdf6c/` | `assignment.json` 375d70df…d4a3, `claim.json` 550c7532…8a73; the five worker modules, the two policy modules and the claim are byte-identical to the claim commit |
| Protocol | policy and runbook of 2026-09-15, `tradingagents/research_options_timing/` at claim commit `dca15f51a` | runbook read at its last version `00862e27d` |

## Findings

**Inventory.** 16,599 files and 100,951,651 bytes under `data/`, plus the launch log of
2,011 bytes. No symbolic link and no non-regular member; every file has mode 0600 and
link count 1. `data/` holds `bootstrap/`, `daily/`, `final/`, `known/`, `selected/`,
`selection.json`, `supervisor-exit-000000.json`, `supervisor.lock` and `worker.lock`.
There is no `source-seal.json`, no `seal.json` in any of the five journals and no `STOP`
file.

**Journals.**

| Journal | Slots in the spec | Receipts | Range | Last receipt (UTC) |
|---|---|---|---|---|
| bootstrap | 3 | 3 | one group, 60 s before entry | 2026-09-15 10:59:01 |
| daily | 225 (45 × 5) | 75 | d00–d14 | 2026-09-29 11:01:01 |
| known | 8,456 (1,057 × 8) | 2,728 (341 × 8) | h0000–h0340, no gap | 2026-09-29 15:00:05 |
| selected | 8,456 | 2,728 (2,504 received, 224 missed) | h0000–h0340, no gap | 2026-09-29 15:00:12 |
| final | 4 (scheduled 2026-10-30 11:00:00) | 0 | — | none |

In total 5,534 receipts exist for 17,144 intended slots (5,310 received, 224 missed);
11,610 slots were never attempted. The last hour with complete HTTP-200 receipts is
h0339 (14:00 UTC on 2026-09-29); the eight known receipts of h0340 are flagged incomplete
and the eight selected receipts of h0340 are missed. `returned.prepare` gives the same
member count, byte count and per-journal states, with `source_status: incomplete` and
`evaluate_kwargs: None`; its read-only journal validation passed.

**Stop.** `data/supervisor-exit-000000.json` records `ended_ms` 1790697040531
(2026-09-29 15:50:40.531 UTC), reason `wall/monotonic discontinuity`, child exit code −9,
empty stderr and a sampled peak of 305,594,368 bytes. The launch log has one
"finite launch entered 2026-09-15T10:14:29Z" line and ends with
`RuntimeError: wall/monotonic discontinuity; preserve interrupted intents, no automatic restart`.
The supervisor samples every 100 ms and stops when wall and monotonic time diverge by
more than 0.1 s; it then kills the child, so the child's sealing code never ran. The stop
came 340 h 50 min 40 s after entry, while the child was waiting for h0341, not during a
write. Every intent has a receipt; no pending or staging file is left. The latest
modification time in the tree is the launch log (15:50:40.710); the last journal write is
`selected/recovery-000027.json` at 15:00:12.788. There is one exit record, one launch
line and no recovery record in `known/`, so the data show no second invocation.

**Lease.** Worker lease 2026-09-15T10:58:00Z → 2026-10-30T11:01:00Z; observation window
2026-09-15T11:00:00Z → 2026-10-29T11:00:05Z. On 2026-11-21 the lease has been expired for
22 days. `worker.run` and the supervisor both refuse outside the lease, so the worker
cannot be resumed and missed slots are never filled later.

**Disposition.** All eight cases are unavailable. The deciding rule is in `returned.py`:
a source without `source-seal.json` returns
`unavailable('Source is not sealed; no analysis-source admission.')` for every case, and
`control.py` refuses an analysis binding without a sealed source
(`returned sealed source required`). The runbook: "If source fails before financial
interpretation, preserve every unavailable cell and use the new timing protocol's
failure-only closure after committed external quiescence/source evidence." The failure is
a statement about source operability only (`worker.py`: "Source operability only; no
economic rejection of either asset or strategy family."). Independently of the seal,
`selection.json` puts the exit of both books at h0381 (2026-10-01 08:00 UTC), after the
last collected hour, and the policy states that an exit failure leaves cash attribution
unavailable.

## Observations beyond the simple reading

- The worker did not crash; the supervisor stopped a waiting child on its clock guard.
  The missing seal is the designed result of that path.
- The cause of the clock step cannot be determined: the exit record stores neither its
  size nor its direction. Receipt clocks show the wall-minus-monotonic offset constant
  within 1.5 ms over 15,793 samples up to 15:00:05 on 2026-09-29.
- At h0340, fifty minutes before the stop, intent writes took 1.33 s against a median of
  56 ms. A host-level event (storage stall, then a pause or time step of the virtual
  machine) is an inference, not an observation.
- Coverage before the stop was uneven: 302 of the 341 collected hours have all 16 hourly
  roles decodable; in 38 hours no selected-option receipt is usable.
- All 16 `fundingInfo` receipts (bootstrap and d00–d14) stopped at the 65,536-byte body
  cap. They are stored as received and are not decodable. The funding normaliser does not
  appear to read this role; this was not traced to the end.

## Quiescence

Mode `lease-expired`. The basis is the frozen lease end (2026-10-30T11:01:00Z, 22 days
before this review), the supervisor exit record of 2026-09-29 and the absence of any
write after it in the returned tree. The control code accepts lease expiry as quiescence
(`Episode._quiescent`), and the runbook names "reviewed lease expiry" as sufficient.

## Not verified

- The state of the remote host on 2026-11-21 (processes, terminal session, whether the
  remote data root changed after the copy). The host was inspected over read-only SSH on
  2026-11-19, when the data were copied; no transcript of that inspection is retained, so
  it is not evidence here.
- Byte fidelity of the copy: no manifest was taken on the remote side. The local manifest
  binds the copy as it is; local change times show the copy was made on 2026-11-19
  between 08:03:34 and 08:03:45 UTC.
- Whether a manual invocation failed before writing anything.

## Result

The source is an unsealed, incomplete raw journal: 5,534 receipts for 17,144 slots,
ending at hour 340 of 1,056 after the supervisor's clock guard stopped the worker on
2026-09-29 15:50:40 UTC; the lease expired on 2026-10-30. All eight cases are unavailable
on source operability alone. Nothing follows about the economics of the strategy.
