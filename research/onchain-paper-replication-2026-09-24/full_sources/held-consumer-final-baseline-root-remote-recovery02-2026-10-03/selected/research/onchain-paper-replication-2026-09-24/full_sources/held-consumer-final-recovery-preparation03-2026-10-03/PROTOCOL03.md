# Recovery03: flat archival recovery, source preparation only

This successor is implemented but has not captured the actual capsule, fetched an
external archive, recovered actual source or exercised native/research authority.
Recovery01 and recovery02 remain WITHHELD. Their sources, reviews and witnesses
remain unchanged. The exact recovery02 birth witness is reproduced in the new
owned birth-fixture: a preexisting inode with mode0700 replaces the mkdir-created
inode before the first stat, is accepted, and becomes0750. BIRTH_RACE01.json and
BIRTH_RED03.log retain that concrete failure, including both inode identities.

## Explicit change in recovery protocol

Recovery03 never instantiates the archived POSIX tree. Root supplies one EXISTING,
canonical, empty, effective-user-owned directory with exact0700 permissions. The
helper opens and checks that directory and holds its descriptor. This is scoped
output ownership supplied by Root, not a mkdir birth proof. Recovery03 performs
no mkdir, pathname chmod or fchmod while recovering. A same-user actor is not
excluded by a hidden-path assumption; detected namespace changes fail closed.

For each authenticated regular archive member, a fixed flat name is opened with
O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW and0600. That creation returns the inode descriptor
atomically. Writes, fsync and actual bounded byte readback use that descriptor.
The descriptor and final namespace inode are rejoined, with link count one. A
foreign replacement cannot receive writes through its pathname. Failures retain
created or moved partials; no file or directory is deleted. The directory's
original permissions are never restored or altered. Namespace enumeration is
streaming, rejects a foreign entry immediately, and has a65540-entry ceiling.

Every original logical name, type, mode, size and body SHA256 is retained in the
authenticated typed manifest, including empty directories and root mode. Each
role's metadata JSON retains the COMPLETE original manifest, archive pins and
logical-name-to-flat-file map. File modes are archival metadata; flat file0600
permissions are not represented as recovered original modes.

All regular bodies are read back again from the created flat files, checked
against the original manifest, and fed into a canonical gzip/PAX encoder using
original names, types and modes. Exact compressed bytes are compared incrementally
against the authenticated archive, and final size/hash are also compared. This
is not a count-only proof or a digest of only selected source members. Arbitrary
TAR metadata, alternate canonical encodings and appended gzip/zero framing fail.
The archive format does not encode root mode; its separately pinned complete
manifest does, and that exact manifest is retained in metadata.

The recover CLI returns status
fresh-flat-archival-recovery-not-origin-proof. instantiated_posix_tree,
recovered_tree_git_join, runtime_package_bodies_recovered,
outside_stores_recovered and research_authority are all false. Original capture
still authenticates genuine Git/source/registration/input joins. Executing Git
against a newly instantiated recovered tree is explicitly unavailable under
this protocol. Root would need a separately qualified offline proof for that.

## Preserved original capture and bounds

The entire prefix before the removed RestoreDirectories block, the complete
put/request/authenticate_source/capture block and the CLI block are byte-identical
to frozen02. Unchanged function bodies and AST are independently recorded in
INVERSE03.json. owned_io.py, bounded_git01.py and REQUEST_TEMPLATE01.json are exact
copies. Only restore/directory helpers and recover's output protocol change.

Original capture continues to require actual fixed capsule07 and actual HEAD
 d443208795f59292c156c5b81b687594efacea4d, authentic205 committed source+registration
bodies,33 opaque input hashes,246 tracked paths,288 non-Git regular files, and the
complete typed supplied capsule manifest including actual .git/history. Existing
Git indirection refusals and source/input body authentication are unchanged.
Those counts are scope checks, not substitutes for the source/history body joins.
No synthetic receipt here is claimed as a positive capture or source proof.

The canonical actual request digest binds both complete manifest digests and
all explicit external file hashes. Actual capture binds that request and both
archives. Recovery requires the independently supplied expected capture and
request SHA256 and reads the exact fetched manifest/archive bodies. Root remains
responsible for the genuine external origin/fetch/readback chain. A configured
remote, a local manifest, or this source preparation cannot establish it.

All original finite limits remain: regular/member/compressed archive/receipt
4MiB, combined logical and allocated initial baseline128MiB, inflated TAR total
192MiB, local path PAX8192 bytes, bounded gzip reads65536 bytes, TAR header count
65538,32768 logical members per archive, and10GiB observed free-space floor in
capture/recover. No budget increase or hard quota/deadline guarantee is asserted.
Metadata that exceeds4MiB fails closed. Baseline/output roots remain disjoint;
flat recovery additionally requires separation from fetched bundle and all
request roots. First-fatal cleanup attempts owned closes independently, exactly
once per acquired handle. Recovery does not retry uncertain descriptor integers.

## Root fill and invocation

REQUEST_TEMPLATE01.json retains null absent manifests/external scope/output.
ROOT_FILL03.json separately records null absent final parent and native envelope
references. Root must fill and review the exact final caller, envelope, helper,
review and scope pins, build authentic whole baseline manifests, then compute the
canonical request hash. The schema remains unchanged; worksheet-only keys must
not be inserted into the request. No null template is admissible.

Use checkout .venv/bin/python -B recovery03.py with explicit --request,
--request-sha256 and --mode capture, only after Root review. For recovery Root
first independently fetches and authenticates the complete bundle, prepares the
existing empty private flat output, then supplies --mode recover --bundle,
--capture-sha256 and --destination. No network is performed by this helper.
Original scopes, runtime/stores exclusions and the nonrecursive baseline→request
→capture→external fetch→flat recovery→independent review chain remain explicit.

## Validation and limitations

The locked checkout Python3.13.13 runtime check passed with no mismatches.
GREEN05.log:27 final flat/security/inverse tests; IO03.log:6 preserved reader
checks adapted to retained fixture directories and existing flat output;
WRITE03.log:3 unchanged writer/request controls adapted only for retained fixtures.
All36 checks passed. GREEN03/GREEN04 preserve earlier27-pass versions before the
bounded-directory-enumeration tightening; their source snapshot is retained.
The192MiB cap is checked as an exact constant and with a reduced limit on tiny
bytes; no192MiB allocation was made. The exact67-byte PAX witness requests only
512 decompressed bytes before refusal. All fixtures are tiny opaque bytes and
are retained. No numerical modules, data arrays, labels, empirical runs, fake
Owner/Binding/native authority, credentials, deletion or network were used.

The broad repository offline target was not run by this narrowly scoped worker:
this assignment permits only stdlib tiny opaque checks. Root owns broader
integration validation and any actual full-scope operations. Independent review
is pending. Resource feasibility, actual archive compression, final scope
membership, external recoverability and native/scientific admission remain
unperformed, not inferred from synthetic success.
