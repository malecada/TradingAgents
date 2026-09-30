# Independent compact-input commit review

Accepted: the six staged additions are byte-for-byte the already reviewed
legacy graph manifest/intent/result JSON files. They are exactly the six
manifest members absent from committed HEAD
`cf9b582d73002dd4178530ed1ce3db150dcd2d63`; no additional staged files were
present at this inspection. Each staged blob equals its working-tree bytes,
the 1,870-file release manifest pin, the original preparation pin and the
retained historical closure member's hash and byte extent.

Paths below are relative to
`research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/`:

| File | Bytes | SHA256 |
|---|---:|---|
| 2022-01-03/decode_graph/graph/manifest.json | 1604 | bc3bf9a6104ffcb93b8c8b9ba7dd068f1dc0db28b0fca2a74f32cc3a0ba76c98 |
| 2022-01-03/decode_graph/intent.json | 19664 | ea4171c34f385d4c11065d9444325a204971706eba5b99aa786f0f02eeba6beb |
| 2022-01-03/decode_graph/result.json | 817 | 633568740b817889edf8cd39590ccd772066f4792725d102ff969675e860d3a7 |
| 2022-06-13/decode_graph/graph/manifest.json | 1604 | a7599cb4dce5a3d7b01614fe097026e70d48ecd63bb1c25518ccb05f41204d59 |
| 2022-06-13/decode_graph/intent.json | 19664 | 85501afe7fe78693d0da8a0cff4d0fa8264d0a2e061ca5952bfd6a48183cd836 |
| 2022-06-13/decode_graph/result.json | 817 | 8b9b85b369f9e590fcfb2f02fa4faeae34cacac091b637e57c54ea5004814e18 |

Release manifest SHA256 remains
`f5dcd478dd159f927e58a2c3798497fa669d4940636fdd7d01df0ea1e2eebd4b`.
The original retained closure SHA256 is
`dc305bbbc9b76de6eab1e6b9015ca78f5be787c70225f635c918d482a7ac7c54`.
The wrapper sources, protocol and manifest current bytes are unchanged from
HEAD. This correction changes committed availability, not the reviewed bytes
or historical outcome.

`preflight01-failed.json`, SHA256
`d77c0f6005e358f60d7ed5e52ac9b6c2a2c4844bb567143f3fcfb04fb6dafbf0`,
retains the failed preflight and exact missing-path list. The committed-source
check occurs before array reading and launcher reservation; `verification01`
remains absent. This is a failed preparation check, not a reserved/started
verification retry. Commit/push the exact additions and failure evidence, then
perform fresh preflight02 against the new source. The unchanged conditional
one-off release requirements in RELEASE_REVIEW_V2.md continue to apply.

Only this review file was written. No tests, jobs, array bodies or SQLite were
run/read; no source, staging or historical ledger was changed. Actual committed
availability after the next commit and actual execution remain untested here.
