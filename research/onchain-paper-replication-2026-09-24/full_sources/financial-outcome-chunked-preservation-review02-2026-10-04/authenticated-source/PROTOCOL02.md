# Chunked preservation CA1/CA2 successor

SOURCE ONLY, NOT RELEASED. Originalfa7a9440, independent withheld reviewb54814f1,
all raw old counterexamples and the old helper remain unchanged at their actual
paths. This new directory contains the exact old source, unchanged accepted R4
helper bodies, concrete successor, new controls and all newly generated failures.
No actual financial outcome or live root was read or mutated.

## CA1 — shared complete validation

Both validate_archive and verify_flat now invoke the same _index and _members
validators. They enforce exact canonical schema/kind/version, false authority
flag, strict integer types, four-root bounds, root anchors and disjoint paths,
fixed simultaneous1GiB reservation, finite exact page/file/member/chunk counts,
opaque Git/POSIX qualification strings, sorted unique members, explicit parent
directories, mode and path rules, exact fragment length/order and complete
manifest hash. Archive verification checks chunk bodies; flat verification
checks both whole-file hashes and the exact chunk hashes reconstructed from flat
body slices. Complete copied manifests remain self-contained with empty files,
empty directories and original logical modes. No external Root hash is invented.

Exact old-source RED tests reproduce flat acceptance of newly pinned malformed
version/kind/authority/cap indexes and a wrong chunk hash. The successor refuses
all of them. A newly pinned opaque test index is not a bypass of a genuine external
Root pin. Valid old/new archive and flat artifact bytes remain identical in an
actual two-page/two-mapping-page opaque pipeline.

## CA2 — descriptor-relative fresh creation

fresh traverses absolute parent components using O_DIRECTORY/O_NOFOLLOW, binds
the actual parent fd to its original device/inode/mode before creation, and calls
os.mkdir(child, dir_fd=parent_fd). The new child fd and visible namespace are
verified, parent fsync uses that same descriptor, and every acquired fd is closed
through unchanged accepted first-fatal cleanup. No path-based target.mkdir remains.

Explicit scheduling of exact source operations on owned paths reproduces the
old redirected side effect before refusal. Substitution before successor traversal
is refused with no child created. Substitution after its verified parent fd is
acquired cannot redirect creation: only the originally owned inode receives the
child; final namespace verification refuses and preserves that child as a partial
artifact. This is not a timed race observation or a claim that a concurrent rename
can produce successful namespace closure. No substituted directory receives a child.

## Bounds and validation

All original constants remain unchanged:4MiB per file,1MiB chunks,1GiB whole
source/archive/flat conservative reservation,10GiB disk floor,32,768 entries,
128 rows/page, four roots and1,800 seconds. Original stable R4 reader and owned_io
helpers retain exact hashes and constants; no cap ladder or numerical admission.
Git remains opaque bytes and logical metadata, not verified objects or a restored
checkout. Large100epoch outcomes and near-capacity behavior remain unmeasured.

Final CORRECTION_CHECKS04 contains202 passed correction controls, with actual
malformed-index RED→GREEN, two-page full pipeline/artifact equality, canonical
member corruption refusals, owned changed-parent witnesses and exact whole source
byte/AST inverse. Original22 byte controls and40 first-fatal/failure controls pass
in this new directory. Earlier199 correction controls, sourcecheckpoint and
INVERSE02 remain preserved; they are not added again to the final264 total.
INVERSE03 is the final source inverse. No failing assertion was hidden.

No NumPy/Torch/SciPy, arrays/labels, genuine Run/Owner/claim, Git/native child or
network operation was used. Root still owns real terminal/process closure, exact
root/attempt scope, current whole writable accounting, final source/caller/review
pins, external transport and independent fresh recovery. Source corrections grant
zero financial credit, external-backup proof or execution authority.
