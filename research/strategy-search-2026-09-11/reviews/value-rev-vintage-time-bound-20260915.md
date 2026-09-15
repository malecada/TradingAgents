# First-vintage timing provenance — September 15, 2026

## Finding

A contemporaneous committed completion statement exists. An exact hash-bound
September 4 completion time for today's retained 704 raw members has not been
established by the bounded checks. These are different evidence strengths; the
charter's September 18 earliest date must not be silently advanced or delayed
by a new interpretation of the vintage interval.

The [charter](../../../docs/superpowers/specs/2026-09-04-value-rev-charter.md)
acquired its snapshot-1 coverage paragraph in commit
`05b28ccc62e4c283e598a000c081052c8a2c576a`, whose author and committer timestamps
both equal **2026-09-04 08:18:48 UTC**. That paragraph reports 704 raw responses
and 220 token panels. The commit exists in both the consolidated checkout and
the preserved TradingAgents worktree. It is affirmative contemporary status,
not a completion time inferred from the snapshot date or a file timestamp.
The initial registration commit is
`eebf5f41820b3f322c3af29a807a98dfd5047675` at 07:56:24 UTC;
a fetcher repair followed in `4239ddb352a0f23480d8de8b2a799103c6b1ba72`
at 07:56:59 UTC. Registration and fetcher edits alone do not prove completion.

No manifest or raw members appear in `git ls-tree` at the completion-statement
commit under the exact `data/xsect/fees`, `data/xsect/fees_raw` and
`data/rebuild/value_rev` roots. The inspected status contains no first-vintage
manifest digest. Matching the currently verified member count corroborates the
statement but does not establish that every current member is byte-identical to
its September 4 counterpart. Git's local commit timestamps also are not an
independent trusted timestamp service.

## Hash-bound conservative upper bound

The completed [preservation report](value-rev-preservation-20260915-v2.json)
verified all 704 declared members, totaling 83,368,599 bytes, twice against the
anchored first-vintage manifest. Its SHA256 is
`a4ab29f13c39155d4301573a22d11296cf276b882d4a7451c3e70cc6d8c18bdf`.
The [guard report](value-rev-preservation-20260915-v2.guard.json) SHA256 is
`0ca2db40ff23281ff55b1315c005de609899b2b9cfadfeb776aa3e52d2b1c680`.
The manifest SHA256 remains
`89a9eb8ccbe073c1530047faa3bd64ca22085a79f933d782dcd2098a870d5151`.

A tool clock observation after that successful verification returned
**2026-09-15 08:58:09 UTC**. This is a conservative upper bound on the time when
all currently verified raw members had been observed to exist. It is a local
session provenance statement linked to the reports, not cryptographic
third-party timestamp attestation. Report filesystem modification times were
not used. The manifest's `fetched_utc` of September 4 07:56:59.543672 UTC is
capture start; it supplies no all-member capture-end bound.

If the proposed actual-gap rule requires independently bound current bytes at
least fourteen days before any second-vintage response, the conservative
fallback earliest instant is **2026-09-29 08:58:09 UTC**. This is conditional on
that stricter admission rule; it is not a modification of the existing gate or
a finding that the September 4 capture did not complete then.

## September 18 eligibility and remaining evidence

Accepting the September 4 committed completion statement, together with the
preserved manifest and documented continuity, would support a conservative
September 18 **08:18:48 UTC** second-capture start under a status-based elapsed
time interpretation. That acceptance must be explicit in the coordinator's
pre-outcome source-admission review. The stronger statement that the exact raw
bytes were authenticated on September 4 is presently unsupported.

For a strict exact-byte September 18 admission, the missing evidence is a
contemporaneously retained completion receipt, archival inventory, backup
receipt or committed manifest-hash reference that binds the current manifest
(or every current raw member) to an all-member existence upper bound on
September 4. A trusted acquisition transcript binding the completed inventory
to a timestamp could also suffice. Date labels, capture-start timestamps,
current filesystem times and generic statements that a job was started do not
supply that binding. No search for credentials, remote backup access or network
request was performed.

## Scope of checks

The follow-up used targeted searches in the data catalogue, current state,
evidence index, charter and findings; exact-path Git history for the charter,
fetcher and manifest; and the relevant charter diff and tree inventory. Three
candidate dated handoff/report paths were absent. No broad filesystem search,
market-response parsing, panel access or empirical revision calculation was
performed. The committed paragraph was read as already published provenance;
its reported coverage statistics were not recomputed. Only this review was
written. Earlier failed preservation preflight and successful v2 reports remain
unchanged.
