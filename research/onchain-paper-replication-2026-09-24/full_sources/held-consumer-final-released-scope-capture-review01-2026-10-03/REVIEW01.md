# Independent actual final released-scope capture review

Disposition: **ACCEPTED_ACTUAL_NEW_FULL950_LOCAL_CAPTURE_ONLY**. The new local capture preserves all 925 capsule members and the original 12 Parent members, and adds the exact 13 requested regular Parent bodies. Independent bounded framing, complete opaque-body comparison, original modes and canonical gzip/TAR reconstruction passed 15,968 checks. This disposition establishes this distinct local archive scope only. Fresh external recovery of this full 950-member scope and the final independent union, request and native-eligibility gates remain required.

## Exact chain

The request is `660a715bc4da9bfd93e4076cee4d82730301024b9fa95668c8182a48d9ac2061`; the capture receipt is `122706bfcd5cf8eaaecc31b7230a0553d804606fad4db4d86a74f136dbe27408`. Both are canonical JSON and their request/source/manifest/archive joins match. Accepted Recovery04 source is `b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a`. The fixed source identity remains `d443208795f59292c156c5b81b687594efacea4d`.

The actual recorded capture terminal reports exit 0, elapsed 1.7176114450121531 seconds, 18,929,614,848 free bytes, and no genuine run or native start. The recorded command invokes capture with the exact request pin and no `--launch`; captured stdout and stderr are empty. These are retained terminal observations, not a new capture invocation by this reviewer.

| Scope | Members | Regular bodies | Logical body bytes | Root mode | Inflated bytes |
| --- | ---: | ---: | ---: | --- | ---: |
| Capsule | 925 | 663 | 6,782,177 | 0775 | 7,464,960 |
| Parent/external | 25 | 23 | 514,939 | 0700 | 542,720 |

The total excludes the two roots: 950 members, 686 regular bodies, 264 directories, and 7,297,116 logical body bytes. Capsule manifest SHA-256 is `0ed39e3bb1f374f5eb3df1ff2053e0533804cc18df152dc8179b26598d94169e`; capsule archive SHA-256 is `bcbc44160e09beba8b50e28188393cce6a3e9f90af9062fd90e4026f2ce74dbd`, 2,894,600 compressed bytes. Parent manifest SHA-256 is `1b96c4ab4cddf2c89e711b130aa46be71e2dc27604f68353162652331997e2a8`; Parent archive SHA-256 is `788ec697816f6dbb802af6546dcc5a095ab883167111518def9b7c6089e484b4`, 143,332 compressed bytes.

## Independent evidence

`check01.py` ran under the pinned `.venv/bin/python -B`. It uses the accepted Recovery04 bounded readers and pure request/path validators, but neither its capture/restore entry points nor its framed-member iterator. Its independent decoder reads raw 512-byte headers through bounded gzip reads, limits inflated content to 192 MiB, limits local path-only PAX bodies to 8,192 bytes and regular bodies to 4 MiB, checks finite header count, type, names, duplicate exclusion, padding and termination, and compares the entire ordered typed member list to the manifest. The capsule has 24 local PAX headers; the Parent has none. Directory terminal slash normalization is limited to one slash on directory records. No generic extraction is used.

Every original regular body is compared as opaque bytes to its archived body through the bounded nofollow reader. All original regular files retain single-link identity and expected modes, every directory retains its expected mode, and both complete source roots scan identically before and after this read-only examination. Canonical gzip/TAR is independently rebuilt in memory from all verified archived members, preserving names, types, modes and bodies with the specified canonical header metadata. Both complete compressed byte strings reproduce exactly. The bundle contains exactly its five declared files.

The entire capsule manifest equals the original baseline request pinned `3d5481584c69034d696276431465064d01788e0fd651bdc8fe7df203bc52bf71`. Every original Parent member remains present with exactly its original type/mode/size/hash. The added set equals all 13 precapture declarations; all are regular 0600 bodies, with no replacement or added directory. Each size/hash matches the declaration. Eleven copied proof/review bodies also equal their actual source bytes; the two final documents match their exact archived pins. The final request is `bc482b1196e691d8a0a06e3c866a11877b8cf8556ef407e5d3da72743412e4d4`; final release is `eeac08eef932caccea1346149ec8a7f7473de03e774e0285634a74ae71b8774f`.

`READBACK01.json` preserves counts, hashes, terminal observations and the continuing Root launch hold. `PINS01.json` identifies the inspected canonical documents. `CHECK01.log` records the successful check output. There was no failing witness or altered source during this review.

## Exact boundary

No original capture was rerun, no restored tree or flat store was created, and no Git helper, network operation, native parent or research computation was invoked. The new capture is a separate scope; the earlier accepted external baseline and actual selected-object Git proof do not establish external recoverability of these 13 added bodies. Their copied evidence bytes are authenticated here without widening their original dispositions. Full C6 ancestry/tree completeness, original POSIX tree restoration, runtime/raw-store recovery, independent external origin and native/research authority are not established by this local capture review.

The final documents' release wording does not waive the retained `ROOT_LAUNCH_HOLD`: actual external full950-scope fresh recovery plus independent union/request/native eligibility are still required. No numerical modules were imported, and no arrays, labels or scientific outcomes were decoded or admitted. All old baselines, failures and immutable Parent members remain preserved.
