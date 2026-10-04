# Chunked financial outcome preservation — source candidate

SOURCE ONLY, DRAFT NOT RELEASED. Root alone may freeze, independently review,
compose and invoke this candidate against actual closed outcome scopes. Existing
R4, Parent, numerical source, source registrations, 4MiB native file limit,
1GiB writable watch and10GiB disk floor remain unchanged. No larger job/cap,
retry, budget transfer or financial credit is admitted. No live outcome was read.

## Concrete APIs and format

`capture({logical_root: absolute_closed_root}, absolute_fresh_archive_directory)`
returns an exact index SHA256. `restore(archive, index_sha256, fresh_flat_directory)`
reconstructs fresh numbered body files plus complete logical member/mode/Git
metadata. `verify_flat(flat_directory, index_sha256)` independently verifies the
copied complete index, member pages, mapping pages and exact body hashes without
reading the original source or requiring the source archive to remain present.
All destinations are exclusive, direct fresh children, disjoint from sources and
each other. Existing/partial identities are never reopened or deleted.

Canonical raw chunks replace the old single compressed tar artifact. This is a
new archive format, not a modification to R4 framing or its128MiB baseline limit.
Chunks are consecutive numbered raw binary bodies of at most1MiB; each original
file has exact ordered chunk length/hash descriptors and a whole-file SHA256.
Pages hold at most128 complete typed entries. The final canonical index binds
all pages, exact sorted root/path membership and complete counts/bytes. An intent
appears before chunks; index publication occurs only after complete re-inventory.
No compression, tar/PAX extraction, external commands or child processes occur.
There are zero child outcomes to invent or discard.

R4 recovery04.py, owned_io.py and bounded_git01.py are exact unchanged copies
pinned in HELPER_PINS01. Only its stable bounded read/path/signature helpers and
first-fatal cleanup machinery are reused; no Git function is invoked, no limit
constant is patched, and R4's capture/scan/tar/restore interfaces are not called.
The new scanner and chunk/page framing are independently implemented here.
Original helper hashes provide exact copy evidence rather than a claimed inverse
of a modified historical source.

Complete logical roots include hidden directories and Git files. Worktree .git
pointer files and nonempty objects/info/alternates refuse because those references
would make a declared root incomplete. Root supplies the genuine full selected
repository/caller/outcome roots; this helper cannot infer undeclared external
roots or prove an empirical attempt denominator. All Git bytes and mode/path
metadata are preserved, including any OID text already in those bytes; Git object
validity, ancestry, ref reachability and remote recovery are explicitly unverified.
Flat recovery preserves complete directory and mode metadata without claiming
POSIX directory instantiation, executable permissions or a usable Git checkout.

## Fixed bounds and accounting

At most4 declared roots,32,768 aggregate entries,32 path components,2,048 path
bytes,4MiB source/metadata/output file extent,1MiB chunks,128 rows/page and1,800
seconds per operation. Existing protected-path refusals apply. Source symlinks,
hardlinks, redirected directories and cross-device members refuse. Root anchors
bind actual device/inode/mode. Writes open every ancestor without following
links, bind the owned destination inode before exclusive creation, fsync, and
close all acquired descriptors under the accepted first-fatal cleanup policy.
Source scans and reads check stability; capture repeats the whole inventory.

All source bodies plus archive bodies plus eventual flat bodies are conservatively
reserved under1GiB, including source allocated blocks,32MiB metadata reserve and
16KiB per-entry overhead. Every output file write also checks the current and
prospective10GiB disk floor. This removes single-archive4MiB and old128MiB-format
constraints; it does not prove that every1GiB source can coexist with two retained
copies under a1GiB watch. Such a scope explicitly refuses and needs a separately
reviewed external streaming/recovery arrangement, not a cap ladder or deletion.
The numerical Root-owned1GiB watch is unchanged. A final Root caller still needs
actual current accounting of all its watched paths, closed processes/units,
source/helper/review pins, outcome identities, complete external transport and
fresh independent recovery before using this preservation as release evidence.

## Failure preservation and checks

All completed and partial chunks remain after failure. Failure receipts are best
effort; inability to publish them never fabricates a terminal or recovery. If
index/recovery publication happened before a later error, an extra failure body
makes complete validation refuse. Original source bytes are never deleted.
First fatal errors survive secondary cleanup/publication failures; ordinary
cleanup uncertainty stops the caller through the original CleanupFailure policy.

CHECKS01 has22 passed real opaque byte controls; CHECKS02 has40 passed error/
cleanup controls. Actual source and fresh flat reconstruction included an empty
file, empty directory, binary bytes, logical Git bodies and a file spanning two
raw chunks. Corrupt/missing/duplicate/traversal/redirected/hardlinked members,
reused destinations, unexpected bodies, oversize outputs and partial captures
were exercised. A16-case primary/failure-publication matrix exercised actual
partial writes with ordinary/fatal errors; exact helper bytes/bounds remained
unchanged. No NumPy/Torch/SciPy, labels, real checkpoint, Run/Owner/claim, native
unit, network or Git mutation was used. Larger128MiB/100epoch scopes and capacity
have not been measured and are not inferred from these controls.
