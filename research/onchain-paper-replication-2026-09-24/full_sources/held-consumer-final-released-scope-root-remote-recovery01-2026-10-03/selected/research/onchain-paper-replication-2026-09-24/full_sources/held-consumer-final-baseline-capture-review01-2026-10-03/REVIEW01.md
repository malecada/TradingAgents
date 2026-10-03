# Actual sealed baseline capture review

Decision: **accepted local baseline capture only**. The exact capture preserves the approved immutable capsule and external-parent baseline. This review does not establish remote origin, fresh recovered Git, or permission to execute a numerical/native job.

Request `3d5481584c69034d696276431465064d01788e0fd651bdc8fe7df203bc52bf71` and capture `b9f1d20bedb3e9eff6ca7390684c439de29f5eaab062663e8419f2a3b7a40227` were independently joined. Both embedded manifests exactly equal the previously accepted local composition manifests: capsule `0ed39e3bb1f374f5eb3df1ff2053e0533804cc18df152dc8179b26598d94169e`, external parent `6c0aff0a360001e865f9678749ef96c1725396f0f86c6eb3a6b137f6ef5626cd`. The five captured output bodies, their modes, bounds and hashes match the actual receipt. Root records tool a9e19a exit0; the archive/body checks provide independent evidence beyond that transcription.

The independent raw decoder checks gzip/TAR framing before reading member or extension bodies: reads at most64 KiB, per-file4 MiB, path-only PAX up to8192 bytes, inflated192 MiB and65538 header bounds. It rejects nonselected types, links, path traversal, duplicate names, nonzero padding and trailing data. Every original member’s type, mode, name, length and opaque body hash was checked, along with complete current root membership and root modes. Numeric arrays and Git object contents were not semantically decoded. No extraction or original capture rerun occurred.

| Archive | Files | Nonroot directories | Logical file bytes | Compressed bytes |
|---|---:|---:|---:|---:|
| Capsule | 663 | 262 | 6,782,177 | 2,894,600 |
| External parent | 10 | 2 | 271,900 | 75,209 |

All925 capsule and12 external members matched. Capsule inflated framing was7,464,960 bytes with24 bounded path-only PAX records; external inflated framing was286,720 bytes. Re-encoding every verified member using the declared canonical TAR/gzip settings reproduced both entire compressed archives byte-for-byte. Capsule SHA256 is `bcbc44160e09beba8b50e28188393cce6a3e9f90af9062fd90e4026f2ce74dbd`; external SHA256 is `67e1db759678c8fe36627d6af1d313a624737ed66b4afc1f83fb63fa7faa1189`.

The root modes are preserved as manifest metadata (0775 capsule,0700 parent), not synthetic TAR directory entries. All files and both compressed archives fit4 MiB; combined logical baselines are below128 MiB. The actual capture receipt records free disk19,029,041,152 bytes against the10 GiB floor. This historical observation is not a future floor guarantee or a kernel aggregate quota.

Complete original-body equality preserves the previously independently authenticated205 current/Git source-registration bodies,199 implementation/148package,246 tracked and288 non-Git files,33 registered opaque inputs and four FAILED histories. The full original `.git` byte tree is present in the capsule archive. This is byte preservation only: a separate fresh reconstructed Git object-store/current/design/anchor/history check is still required. The selected source remains d443208795f59292c156c5b81b687594efacea4d. No parent attempt, either fresh case’s claim/outer/artifact namespace, or selected controller/job process was observed.

The first reviewer decoder refused normal canonical TAR directory headers ending with a slash. `check01.py` and its failure log are retained; `check02.py` removes exactly one terminal directory slash before manifest comparison, without relaxing exact compressed canonical equality. The corrected check passed. This was an independent harness correction, not a change to author data or a repeated capture.

The archives contain the current unreleased caller/envelope/request and source-review baseline. Later proof/release/request bodies are not recovered merely by preserving this baseline. They require separately pinned real external recovery and an explicit complete-union final review. Installed runtime binaries, outside empirical stores, remote origin, native controls, genuine Owner/outcome, numerical capacity and financial readiness are outside this acceptance. No original source, capsule, registration, Git store, budget or claim was changed.
