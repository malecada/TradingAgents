# Refusal inventory and timing resource investigation

The closed failed02 inventory fits the current refusal02 encoding, but the declared entry/page/aggregate limits do not guarantee that a final index fits its8KiB writer. A concrete metadata-only counterexample fails at71 pages well below those limits. The native1800-second and sampled outer1840-second controls also do not enforce the separately stated60-second whole closure or51,300-second suite ceiling. These findings leave the accepted narrow R1 late-failure correction intact; they concern prospective release feasibility and truthful resource claims.

The investigated source is immutable refusal worker preparation02 `refusal_outer01.py`, SHA `eed4786a2383cb99f426facdd00431d1bae85b1f1e5ad63f2fd3c1922eff2535`. Only the original CLOSED failed02 capsule in `original-import-native-successor-preparation04-2026-10-03/capsule02` was read. Its retention manifest is `2d1972192c89d7db31308aa97edfa596690c9bcb44d9eabfdb6b26b1ff1cbd9a`. Active CAP03 was not inspected or changed.

## Exact baseline measurement

The actual source `inventory()` function was extracted and invoked read-only using its pinned original raw-body reader against the closed tree. Its816 descendant rows, body hashes and allocated counts match the original817-member retention inventory including root. The actual final paging statements and actual nested `save`8KiB assertion were then extracted and executed with an in-memory receipt sink. No file was published into the old tree, and no job, claim or real output authority was constructed.

For that specific closed root and inventory:

| Quantity | Measured extent |
|---|---:|
| Inventory descendant rows |816|
| Inventory pages |23|
| Largest actual serialized page |6,538B|
| Final index |2,960B|
| Compact row-size aggregate used by loop |134,187B|
| Actual page plus index serialization |145,155B|

The serializer distinction matters: the paging estimator uses compact JSON plus one byte per row, but `save` and `_native_receipt` use default spaced JSON plus newline. The4MiB aggregate check therefore bounds its compact row estimate, not the complete emitted inventory byte total. Page wrappers, spaces, index references and tail receipts remain additional output that must be included in whole-tree/headroom accounting. The existing whole-tree watch remains separate; this measurement does not claim a missing kernel quota.

This is a baseline measurement of a different, already closed imported-primary attempt. It is not the final refusal capsule, any of the27 real refusal outcomes, or a proof that their cumulative retained inventory fits.

## RRI1 — reference index exceeds8KiB before the declared page ceiling

In `refusal_outer01.py:215–228`, rows are partitioned using a6,144-byte compact estimate and pages are written before the root `inventory.json`. The page count is allowed up to768. Every page contributes a filename and64-character SHA reference; that complete reference list is then passed to the same8KiB `save` at lines175–176.

For the exact closed-root envelope, canonical actual writer sizes are:

- Zero references:432B.
-70 references:8,130B, accepted.
-71 references:8,240B, refused.
-768 references:84,910B, refused.

For positive page counts the exact measured formula for this envelope is `430 + 110 * pages`. Its constant depends on the actual root/envelope, so70 is not a universal fixed cap for all future root paths.

A deterministic synthetic metadata counterexample uses ordinary ASCII paths, singly linked regular-file metadata, one logical byte and4,096 allocated bytes per record. At2,310 rows it emits70 simulated pages and an8,130-byte index. At2,311 rows it emits71 simulated pages, then the actual `save` assertion raises `ValueError: new refusal metadata exceeds8KiB` for the8,240-byte index. The loop's compact aggregate is only425,224B, far below4MiB;71 is below768;2,311 is below32,768. The scalar file allocation is9,465,856B, below1GiB. These are synthetic metadata records only: no2,311-file filesystem or future suite outcome was created or asserted. The simulation's log key `pages_published` means accepted writes into the in-memory sink, not actual filesystem publications.

In a real corresponding outcome, existing pages would remain immutable when the final index refuses. The outer must stay failed, preserve the partial pages and additive failure evidence, and retain actual exit/cleanup records. It must not drop rows/pages, overwrite an index, or rerun that identity to obtain a cleaner result.

## RRI2 — other declared limits are intersections, not admitted full capacity

The32,768-entry scanner bound does not imply32,768 entries can be encoded within4MiB. A second synthetic short-ASCII-path case reaches the actual aggregate refusal at4,194,327 compact bytes while processing a32,768-row input, before publication. This is correct fail-closed behavior but defeats a claim that the scanner's maximum is also guaranteed output capacity.

A path character-count limit is not an encoded-byte limit. A single synthetic path containing escaped non-BMP characters has901 Python characters,3,493 UTF8 bytes,28 components and maximum component128 UTF8 bytes, all within the corresponding declared path/depth-style limits. Its compact JSON row grows to10,534B under default ASCII escaping; because an oversized first row is still appended to an empty page, the actual8KiB `save` refuses that page. No such path was observed in the closed baseline or created on disk. This demonstrates only that permitted scalar character lengths do not prove page serialization fits; it is not a predicted failure of the fixed ASCII namespace recipe.

A concrete release must compute bounds using the exact serialization used by the immutable writer and actual registered path alphabet/envelope. A narrow prospective remedy is an explicitly bounded hierarchical index: small fixed-size groups of page references in independently hashed index shards, then a small root reference list. That can preserve every page while retaining the8KiB per-record limit. Any such format needs new source/parser/manifest binding, no-missing/no-duplicate member checks, exact count/logical denominators, first-fatal/partial-publication tests and extra retained file/byte reservations before use. This investigation does not prescribe a global cap increase or authorize a source edit.

Alternatively, a release may prove a tighter finite bound for its exact complete capsule and maximum future namespace population, refusing before claim when the required index cannot fit. It must include original history, generated case inputs, every future guard/log/Owner/journal/stage/oracle record and every previous case's retained inventory pages. Inventories of earlier inventories remain in the shared capsule; their cumulative growth cannot be ignored. A cap inferred only from this816-row baseline is insufficient.

## RRI3 — timer labels exceed demonstrated enforcement

`refusal_outer01.py:174` starts its sampled outer timer only after source/runtime checking, cache setup, initial scan and exclusive outer birth. Line190 checks elapsed1840seconds inside the active loop, after `watch.check()` and the disk check. This is a sampled condition, not an external hard whole-controller timer. An independent extraction of that exact loop prefix with a fake clock starts at1,839.9seconds, spends five simulated seconds in the watch and refuses at1,844.9seconds. This is an illustrative timer counterexample with no actual sleep or process, not a claim about an observed native overrun. A stalled operation can delay an in-process check further.

The native unit separately has hard `RuntimeMaxSec=1800` and the existing finite memory/file controls. Those limits do not include all controller preflight, post-stop authentication, inventories, durable writes or restoration. The original `closure_seconds:60` field is written as telemetry in the intent but is never used as a shared remaining-time bound in the finalizer. The source permits independent systemd inspections/stop waits of10+10+10seconds, supervisor waits20+5seconds and a separate30-second inventory scan allowance: those allowances sum to85seconds before authentication, page writes, fsync, post-tail scans or signal restoration. This arithmetic is not a claim that all actions actually exhaust those limits; it disproves treating60seconds as an enforced sum. Inventory's own30-second check is also sampled between path operations.

The preclaim path has actual guarded native containment and post-guard validation; its subsequent final watch/write/restore sequence likewise has no hard entire-controller deadline. Thus `PROTOCOL02.json` values `per_case_closure_seconds=60` and `entire_suite_wall_bound_seconds=51300` must be qualified as prospective scheduling assumptions or replaced by a separately implemented, reviewed external deadline/cleanup protocol. A hard whole invocation claim would require independent supervision covering preflight through terminal closure, with original-owner joined stop/kill/reap and partial-evidence preservation. Killing the sole evidence writer at an arbitrary deadline does not itself prove cleanup or durable retention. No unreviewed supervisor is requested or authorized here.

## Remaining concrete admission requirements

The suite remains27 variants/16 classes, four preclaim cases, at most23 claims,17 Owners and19 journals, with1,088 prospective identity comparisons and a separate maximum129 scored pairs. None of those real cases was run here, and this investigation does not alter their denominator, original spent samples or paper budget.

Before a whole-suite resource claim or concrete release, the corrected source/parser must either provide bounded complete inventory indexing or demonstrate the exact tighter population/encoding bound; generated genuine inputs and the assembled shared capsule must be counted under the same rules; cumulative future artifacts and immutable inventory-on-inventory growth need explicit headroom; timing terminology must match actual enforcement; and fresh native/disk capacity plus original process ownership must be rechecked. A case may remain unattempted when later storage is insufficient, but that is a deferred/unavailable requirement, not suite completion. Closed identities and already retained partial outcomes must never be recycled.

## Evidence and scope

`measure02.py/.log` retains the first complete independent baseline/boundary measurements. `measure03.py/.log` adds exact emitted serialization totals; all previous logs remain unchanged. Initial `measure01.py/.log` preserves a reviewer AST-harness StopIteration from selecting the early birth-fsync try-block rather than the main finalizer; it occurred after a read-only closed-tree scan, before any synthetic paging, and created no job or authority. `timers01.py/.log` retains the exact-source sampled-timer counterexample and static closure check. Every synthetic receipt is in memory. No real refusal output, path tree or native observation was manufactured.

No numerical imports, financial experiment, array computation, activeCAP03 access, source/registration/ledger/STATE/Git mutation, network action, job, claim or OS signal was performed. Only new investigation files were written. The accepted worker02 R1 restoration/first-fatal source correction is unaffected.
