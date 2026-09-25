# Independent successor prelaunch review

September 25, 2026. **No blocking finding for this exact one-shot 32 MiB
diagnostic successor**, subject to committing these objects and releasing their
exact contract before launch. The failed probe01 identity remains terminal; this
review does not authorize its relaunch, alteration or deletion.

| Object | SHA-256 |
| --- | --- |
| probe.py | 332382290567fd104bcd618cf0d98bb3aeeadc43e21fb0ea88d6538020ba5581 |
| contract.json | 65640889af02ca795882073f97617c126132a97e3eb9596d0acf65a34a01724d |
| CHARTER.md | 0dc08d2997dbc1b082599fa94a7b4e1e7aa3198ce1099342343d8b2664857748 |

## Parent closure and preserved exposure

The supplied parent artifacts were independently read and their six contract-bound
hashes checked: prior contract/release, worker failure, guard terminal, verified
single-before measurement and read-only remote-closure receipt. All matched.
The parent guard records phase `failed`, child exit 1, cleanup verified, a stopped
unit with empty ControlGroup, elapsed 402.89181412700054 seconds and zero kernel
OOM events. Five memory-high events and the 402,284,544-byte sampled peak remain
qualifications. The worker failure identifies the 180-second timeout during the
parallel upload of generated payload0.

The sole completed measurement is the 128 MiB single-before roundtrip:
165.454438806 seconds upload and 52.693029891 seconds download, with a matching
download hash recorded by the worker. The remote listing retains single-before
134,217,728 bytes, parallel1 134,217,728 bytes, and partial parallel0 131,727,360
bytes. Remote length alone does not verify the full parallel1 object. There is
no completed parallel roundtrip or bracketed comparison, and the timeout must
not be presented as a measured parallel throughput ratio.

This review relied on preserved guard and remote-listing evidence; it did not
perform a fresh remote hash check or inspect the large payload bytes. Partial
objects and all prior allowances remain preserved. The smaller successor is a
new diagnostic allocation informed by a failed transport attempt, not a fresh
financial trial or erased attempt.

## Changed contract and unchanged control path

The probe source hash is byte-identical to the independently reviewed final01
source. The contract now selects 33,554,432-byte files, a distinct remote directory
ending `throughput-probe-20260925-02`, and a 402,653,184-byte (0.375 GiB) payload
allowance. It binds the failed parent evidence as additional immutable inputs.
The charter explains the payload-size change and connection-setup qualification.

Independent budget arithmetic gives four uploads plus four download reservations:
`4 × [33,554,432 + (33,554,432 / 32,768 + 1) × 32,768]`
= **268,566,528 bytes**, below the new cap. Two generated source files and two
simultaneous downloads occupy at most **134,217,728 bytes** of file payload,
plus small receipts/logs. The unchanged finite schedule cannot create additional
transport stages or retries. The application-payload allowance excludes protocol
framing and must not be described as a measured total network-byte count.

The cumulative charter retains the complete previous 1.25 GiB allocation and
adds 0.375 GiB: 249 + 1.25 + 0.375 = **250.625 GiB** against the parent task's
preservation allowance. The declared 402.891814 seconds spent plus 900 seconds
prospective equals **1302.891814 seconds**, rounded to six decimal places.
This is a diagnostic time allocation alongside the backup, not elapsed backup
time or a modification to its deadline. The original 249 GiB base is inherited
from the parent accounting; its entire historical ledger was not re-audited here.

The retained source still checks source/charter hashes, reserves an exclusive
local run directory, disables SSH multiplexing/compression for probe instances,
uses strict host-key checking, and enforces the reviewed 512/384 MiB guard,
zero swap, 4/4.5 GiB runtime/startup reserves, 20 GiB disk floor and 900-second
limit. It still allows at most two probe connections, with the existing backup
separately active. It selects only its own generated paths for verified cleanup.
No production backup source, rate, identity, resource limit or remote path is
changed by this successor.

## Interpretation and completion checks

The earlier review's nonblocking completion caveat remains: measurement
completion precedes cleanup. Report success only after reconciling guard status,
child exit, cleanup and any failure receipt together. Preserve partials and stop
on another failure; this review grants no automatic further successor.

Compare the complete 32 MiB single-before/parallel/single-after sequence on its
own terms. Its greater relative connection-setup overhead and concurrent backup
traffic preclude treating it as an isolated ISP bandwidth measurement or directly
pooling it with the 128 MiB first stage. Individual stage timings and before/after
drift are observations, not a statistical variance estimate. No preservation
concurrency change follows automatically from a measured speedup.

No tests, network operations, large payload reads, credential-content access or
financial execution were performed by this review. The only written file is
this review. Host admission and actual throughput remain runtime questions.
