# Independent source closure and recovery review

September 17, 2026. This review concerns raw source preservation and one proposed
missing-range recovery. Operative instructions, research lifecycle policy, the
bulk charter, original source and actual Data-checkout receipts were inspected.
No financial experiment, network acquisition, registration or ledger was run or
changed. Reviewer-owned artifacts are this report and its accompanying approval receipt.

**Decision: approve one source-only recovery allowance and the reviewed execution
contract.** No unresolved material blocker remains in the reviewed source after
the correction below. Final gate/input/source hashes must match this reviewed
tree, pass metadata admission, be committed and remotely verified before the
single finite launch. This decision is not evidence that recovery has started
or that missing inputs have become available.

## Preserved original closure

The pinned Python 3.13.13 interpreter ran the independent lifecycle verifier
against the original Data checkout's
`research_runs/eth-remaining-graph-capture-20260916`. Verification passed: exact
committed source `771dfeb54a90ca0724e345ddd183754e5ca80e2b`, 1,085 cells,
1,086 hashed outputs and 521 unavailable cells. The extra cell is the index;
the 1,084 dated outputs independently contain 563 complete and 521 unavailable
dates. All 1,084 dated manifest SHA256 bindings matched actual manifest bytes.
Every dated output retains a verified independent-check receipt; this review
did not rerun those checks over the roughly 51 GiB raw corpus.

The terminal receipt ended at `2026-09-17T08:55:58.489244+00:00`; its SHA256 is
`9eed03b230b8c09eac2508b8f0eae3df1da13da7c2fe84722def43814c02e419`.
The resource receipt records child exit 0, no limit trigger, elapsed
52,432.077 seconds and peak sampled process-tree RSS 447,430,656 bytes against
8,589,934,592 bytes. Sampling is not proof against unobserved brief peaks.

Each unavailable date's final request receipt was independently inspected.
There are 515 DNS failures, two TLS handshake timeouts, two TLS EOF failures,
one connection reset and one read timeout. The first DNS failure belongs to
July 31, 2023, request 1: requested September 17 at 07:28:59.317605 UTC and
returned at 07:29:07.336547 UTC. The final DNS receipt returned at
08:55:50.047363 UTC. The current boot time, read from `/proc/stat`, is
13:17:25 UTC. Thus the original process was already terminal before this
reboot; describing the reboot as the interruption of that acquisition would
misstate the evidence. The underlying reason for the earlier DNS outage is
not established by these receipts.

## Recovery review requirements

The original source family is exhausted at 8/8. Lifecycle policy
`docs/research/README.md:78`–`86` requires a separately reviewed engineering or
policy amendment for an extension. A new family name with prior 8/cap 9 alone
does not justify another attempt. The proposed explicit source-only amendment
can satisfy this route if it preserves the original family definition and
limit, binds the exact parent claim and terminal receipt, imports all eight
unique predecessors once, and grants exactly one named recovery identity.
The amendment and its validating wrapper must bind the new gate and exact
521-date unavailable calendar before claim. The complete 563 dates remain
references, not recovery targets. No financial sample becomes fresh.

The proposed recovery calendar independently matches all 521 unavailable dates;
the untouched set matches all 563 complete dates. The six successful cached
prefixes contain 233 receipts and 699 files totalling 449,845,693 bytes. Their
current sizes and streaming SHA256 values independently match both the proposed
reuse inventory and the original dated manifest entries. Every reused receipt
is successful and each prefix ends immediately before the original failed
request. Cached receipts retain their original clocks; newly copied storage is
charged again, and separate counters distinguish network and reused responses.

One material defect was independently reproduced and corrected during review:
the initial `recovery_graph.py` transport classifier excluded every `ValueError`,
including a short HTTP body rejected for Content-Length mismatch. A fake 200
response with immediate EOF caused two HTTP requests across two dates and no
global stop. The corrected classifier explicitly includes this case. Eight
focused recovery tests independently passed, including short EOF, DNS failure,
prefix-byte tampering, request-header tampering, failed receipt rejection,
symlink rejection, exact copied bytes/clocks and missing-request-only replay.
The final source additionally reserves copied raw and metadata storage before
publishing the prefix, while retaining inherited request reserves.

The explicit `SOURCE_RECOVERY_AMENDMENT.md` and source-specific pre-claim
validator satisfy the policy amendment route: exactly one named source identity,
prior 8/effective cap 9, old cap 8 unchanged, exact unavailable cohort and no
financial freshness. The validator binds the new experiment contract, old gate,
claim and terminal, review approval and cohort; it checks exact predecessor
identities and rejects an already claimed recovery or reuse of its certificate
or terminal parent. All eight lineage identities independently match the old
seven plus the terminal bulk parent; all sixteen claim/terminal hashes match.
An independently assembled valid policy passed. Seven mutations were rejected:
larger new cap, changed old cap, missing target date, duplicate lineage, changed
target contract, a second grant and a boolean substituted for the grant count.

The final eight recovery tests and five inherited independent-checker tests
passed together (13 tests). A separate synthetic construction exercised the
recovery wrapper through the independent checker: 20 reused responses plus one
new request reconciled, while a later stopped day retained an unavailable
manifest and verified zero HTTP. The checker retains original capture fields
when validation fails. These are invented-source checks, not financial trials.

The runner uses a fresh checkout and exclusively creates its output directory;
the original Data checkout remains the cache source. The launcher preserves the
existing 8 GiB sampled RSS guard and two-CPU affinity. The starter exclusively
creates launch intent/log evidence, refuses an existing claim, and records PID,
process start ticks and boot ID. There is no restart loop. The 54 GiB prior raw
baseline exceeds the original 57,348,575,704-byte accounting; 512 MiB prior
metadata exceeds 519,823,360 bytes, with another 128 MiB reserved for new
lifecycle/log/guard records. Source-copy and per-request reservations retain the
120 GiB raw/2 GiB metadata ceilings and 20 GiB disk floor. These serial checks do
not reserve space against unrelated disk writers or make local evidence an
off-device backup.

## Untested claims

Raw bodies across the complete corpus were not independently rehashed here;
successful cached prefixes were checked as described and must be revalidated
by the execution path before reuse. Actual future source
availability, off-device backup, numerical graph canonicality and uniqueness,
cross-day overlap, historical publication availability, graph features,
forecast performance, fees/funding and trading accounting were not tested.
This raw-source operation yields no economic verdict. No higher-effort review
is suggested absent a specific unresolved correctness question.
