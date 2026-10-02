# Independent initial archive review

Acceptance withheld for two material evidence-boundary findings. Review was static against the actual source and saved test results; no tests, external requests or numerical jobs were run.

## AC1 — success is published after the final live/content boundary

`archive_chunks.py:111–117` checks lease and source/snapshot/readback content before writing complete.json, then returns the write's expected-body hash immediately. `retrieve:152–158` likewise writes completion after its last lease/content checks and returns the destination. The shared writer returns the hash of its input bytes; it does not read back completion or repeat the caller lease.

A deterministic completion-write/fsync hook can revoke the lease, alter the destination, replace the attempt path or alter complete.json after those checks, yet the API returns success. This undermines the returned receipt's current verified-content claim even within the sampled, non-atomic contract. Add a post-publication live boundary followed by callback-free verification of exact completion/intent bytes, pinned roots and expected source/snapshot/download content. Preserve completed and failed evidence together when a late failure occurs. Test preserve and retrieve independently, including changed completion bytes and changed downloaded content or revoked lease during final publication. No atomic guarantee after the final read is required or implied.

## AC2 — attempt and receipt terminal membership is not checked

Neither preserve nor retrieve enforces an exact local phase inventory. In particular, retrieve reads a trusted complete.json at lines 131–155 without rejecting failed.json, even a dangling failure symlink. A failed/conflicting attempt can therefore be accepted for a fresh read if its completion hash is supplied. Extra files written during transport/lease callbacks also survive successful completion without refusal and fall outside the small attempt accounting.

Define exact phase membership for preservation and retrieval; require all expected members and reject foreign entries and regular/dangling failure markers before acceptance. Validate the preservation receipt-root terminal inventory during retrieval and repeat it after the last external callback. Enumerate incrementally against the small expected set rather than building an unbounded directory listing. New tests should cover a preexisting complete+failed receipt, a late failure marker and an extra local member. Existing exclusive attempt creation prevents retry of the same path, but does not establish terminal consistency of a different receipt consumed later.

## What the existing evidence supports

The source caps members at 8 MiB, prebinds expected source SHA/extent and scope, uses bounded nonblocking no-follow regular-file reads, rejects hard links and unsupported sparse extent accounting, limits remote object names, checks available local bytes prospectively and preserves local source/snapshot/partial remote evidence. Caller-provided transport identity and exclusive mkdir/put/get are explicit assumptions. Fresh retrieval does not require the original source file. These are useful copy/readback primitives and do not themselves authorize source disposal or replacement of existing compact readers.

check01.log reports **16 passed in 0.25 seconds**, following **16 missing-module failures in 0.17 seconds**. Tests use a filesystem-backed synthetic transport. They exercise successful round trip/fresh read, retained upload/corruption/source-change/lease failures, source type/hash/size/floor/name refusals, changed receipt/transport/remote bytes and existing remote preservation. They do not exercise AC1/AC2, real SSH/network limits, durable remote acknowledgement, fresh-process external recovery, transport identity authenticity, interrupted descriptor cleanup or actual source/owner eligibility. No external-upload or eviction admission follows from this review.

Inspected SHA-256 bindings: archive_chunks.py `72336456d40ded9823b67340855b2528816db40adc51a0ed3e54237a1b210fc7`; test_archive_chunks.py `476934b4c3321c4655cbc10ab494c3b2afb2956416a0a4a8d3dbb6fc268d6b85`; CONTRACT.md `e52700ed100d88ab3b74c909022446538569219e266b0f23c5c9e4043f50cfd4`; check01.log `dddb27592ce48ade0d0b3aeca0ac9c2d06833a6891450e4d2f238465607fa7c2`.
