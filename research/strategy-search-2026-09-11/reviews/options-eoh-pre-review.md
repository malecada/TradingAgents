# EOHSummary lexical probe: independent pre-result review

Initial disposition: one avoidable normalization-resource blocker remains before
freeze; final lifecycle preflight and gate review are pending. No actual ZIP,
checksum, quote, market row or endpoint was read. The reviewer owns only this
document and did not modify implementation or registration.

## Material finding

`options_eoh_schema.py:59-65` expands per-column empty counters for each record
but checks normalization size only every 1,024 records. At the end, it allocates
one missingness dictionary per observed column before checking the final 2 MiB
serialized limit. A tiny candidate header followed by one very wide comma-only
record can therefore allocate far more memory than its allowed output before
cooperatively becoming unavailable.

An independent invented example used `header` then a row with 50,000 commas:
approximately 50 KB of CSV allocated 26,493,106 traced Python bytes before the
final `actual encoded schema output bound exceeded` rejection. A much wider
record is permitted by the 5 MiB compressed/16 MiB expanded source limits and
the 1 MiB individual-field limit (each field can be empty). Such a record risks
external termination instead of the intended known-overflow unavailable closure.
Both raw receipts are already durable, but avoidable allocation failure would
still consume the source-investigation allowance.

Before populating counters or result dictionaries, enforce a cheap per-record
width/column-output lower bound and bounded ragged/column bookkeeping. Apply the
same bound to the candidate first record. Retain raw bytes and report known
normalization overflow as unavailable without truncating counts. Add a wide
second-row regression; the full lifecycle preflight must exercise this path and
its actual encoded output/resource envelope. No unknown column should be dropped
or reinterpreted to make the object pass.

## Checks already supported

The canonical request-spec hash freezes exactly the ZIP and its checksum in
that order. Each raw receipt is published before the next request and both are
published before checksum or CSV parsing. Complete HTTP 200/source receipt,
checksum syntax, paired integrity and lexical interpretation remain separate.
A syntactically valid checksum paired with the wrong ZIP does not become verified
integrity; a bad CSV can retain a passing byte-integrity result independently.
Same-host denial suppresses the second request while preserving both identities.
Uncatchable failure retains the claim/partial evidence under the disclosed
contract and is not automatically retried.

Checksum parsing requires one UTF-8 hexadecimal SHA256 record, two spaces and the
exact basename. ZIP parsing checks that digest, one exact member, directory/path
identity, encryption, positive compressed size, expanded size and ratio before
reading. Bounded member reading and the standard library enforce CRC/deflate and
length checks; no member is extracted to disk. UTF-8 is strict and BOM presence is
preserved. CSV uses the declared delimiter/quotes and strict reader, restores
the process field limit, and refuses an empty object.

The candidate first record is literal, preserving duplicate/empty tokens and
unverified header-versus-data meaning. Subsequent empty strings, absent columns,
blank records, ragged record identities and width frequencies are distinguished.
Whitespace and numerical-looking tokens do not gain semantic meaning. There is
no bid/ask/time substring classifier, price calculation, inferred timestamp,
chain completion, symbol selection or execution claim. All thirteen current
focused synthetic tests passed independently, including injected CRC/deflate,
decode/member/field errors and receipt-before-parse preservation.

## Pending admission and untested claims

The final source/charter/spec, reused transport and JSON/serialization helpers,
resource launcher, lifecycle runtime, observation marker and gate must be pinned
and independently checked before the two requests. Full disposable lifecycle
tests should exercise actual receipt/result serialization and source-check Git
helpers under the exact 512 MiB/two-CPU/120-second wrapper, including normalization
overflow. All ancestor objects, options/RVIV spending and the two intended cases
remain unchanged; this probe uses the second of three new options investigations.

The first-row meanings, clock semantics, execution quotes/sizes, lifecycle
completeness, historical fee/lot/account applicability, economic returns and
actual post-capture integrity have not been tested. These remain unavailable
regardless of lexical success. The specific unresolved question is allocation
amplification from one wide row; broader economic review is not justified here.

## Wide-row fix re-review: resolved

The new source checks candidate-header width and every following record's width
against a conservative minimum per-column serialized profile size before
updating Counters or constructing missingness dictionaries. A running minimal
ragged-index serialization count blocks unbounded index accumulation; periodic
and final actual lifecycle-encoded limits remain. These lower bounds only reject
outputs that cannot fit; no unknown field is discarded or semantically mapped.

The original invented 50,000-comma second-row counterexample now rejects at the
immediate column-profile guard with peak traced allocation **854,107 bytes**,
compared with 26,493,106 bytes before the fix. The same width in the first record
also rejects, with peak **1,547,864 bytes**. Both checks were independent, used
invented bytes and ran without resource pressure. The added capture-level test
preserves both raw receipts and passing paired integrity while marking the ZIP's
lexical result unavailable with the explicit width-budget reason.

All **14 focused synthetic tests pass**. No remaining source-level blocker is
identified for the reviewed lexical/discovery scope. Final disposable lifecycle
resource preflight and gate/launcher/hash admission remain pending before any
real object acquisition.

Reviewed collector SHA256:
`b786a35f5beb05b64c9a6e017f384a323e99d9b4df3b23321e98a684196bd626`.
Reviewed test SHA256:
`79fc4ceba4517453127284b4312843e3173598ac88c3231fa9297da0f618853b`.

## Final lifecycle and registration review: PASS

All **16 combined synthetic tests pass**, including two disposable, source-pinned
`ResearchRun` lifecycles under the actual v2 resource guard. The valid fixture
contains a one-million-character candidate-header field and a same-size following
field; both cells complete with four actual files totaling 6,648,262 bytes. The
invalid fixture provides two complete 5 MiB bodies: both semantic cells become
unavailable, while all four outputs totaling 27,967,896 bytes are retained. The
saved guard reports show no limit failure, two-CPU affinity and sampled peaks
53,645,312 and 129,482,752 bytes respectively, below 512 MiB. These reports and
the independently repeated tests concern invented bytes only.

Final gate checks confirm every ancestor experiment/dataset object and every
family budget matches `gates-options-metadata.json` unchanged. The new experiment
names `options-metadata-20260911` as parent, keeps the options family, and contains
exactly the two request identities and four output filenames. Collector,
transport, serialization/strict-JSON helper, guard v2, lockfile, documentary marker,
request-spec, charter and all lifecycle runtime hashes match current bytes. The
request-spec canonical hash also matches the collector constant.

The marker's 08:59:38.161697–08:59:38.161767 UTC interval records local observation
of static request-definition bytes only. It does not backdate archive receipt
availability. A separately named EOH history identity conservatively preserves
the June 2022–March 2025 exposure interval, explicitly without claiming this exact
archive was previously opened. Actual future HTTP observation clocks, historical
filename date and catalogue modification date remain distinct. No financial
freshness or semantic clock availability follows from this registration.

There is no unresolved pre-result blocker for this exact source-only probe after
the coordinator's required committed/pushed freeze. Final hashes:

| Artifact | SHA256 |
|---|---|
| `gates-options-eoh.json` | `a1f63a88374a3514728a966c45744691fadfb79e51cf972bc6c4a5beb728fe5b` |
| `options-eoh-schema-charter.md` | `58367077c620dbdf7b62fdea4516dc7d0f9ec4f5fd5c492e84980b67a55c69e7` |
| `options_eoh_schema.py` | `b786a35f5beb05b64c9a6e017f384a323e99d9b4df3b23321e98a684196bd626` |
| `options-eoh-request-spec.json` | `db56b03410be7656092e39cba780d62a53cc754d994db0bf5ae668f49f73039f` |

Real response integrity, literal counts, field meanings, executable history and
remote backup have not been independently tested by this pre-review. A completed
capture still requires separate independent raw-byte/count reconstruction.
