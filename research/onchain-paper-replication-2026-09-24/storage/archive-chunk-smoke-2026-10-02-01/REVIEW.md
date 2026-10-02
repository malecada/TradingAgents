# Independent bounded release review

AT1 and AT2 are closed. The single prebound external synthetic smoke attempt is accepted **conditional on committing the exact reviewed source/contract/binding inventory unchanged and satisfying the fresh guard/unused-attempt launch checks**. This is permission within the existing authorized storage test scope, not proof the external round trip has succeeded. REVIEW_INITIAL.md and all failed evidence remain preserved. No tests, SSH requests or uploads were rerun by the reviewer.

AT1: Transport requires a live callback. Every actual subprocess now reaches it: inherited mkdir calls the overridden run, upload calls run after preparing its snapshot, and download calls the callback immediately before its bounded receiver. The local revoked-after-mkdir regression proves the upload child is not started. Archive post-callback content checks remain in place.

AT2: Upload reads at most the admitted 8 MiB maximum through the existing bounded regular-file reader, copies those captured bytes into a Linux memfd, applies WRITE/GROW/SHRINK/SEAL seals, verifies them, and only then reserves that exact length. SCP receives a `/proc/<parent PID>/fd/<descriptor>` path while the sealed descriptor remains open. Later mutation/replacement of the original pathname cannot expand or replace that captured upload. The local real-child regression changes the original file inside the budget callback and reads only the original eight bytes from the actual sealed descriptor path. This establishes the reservation boundary locally; actual SCP compatibility remains an intended observation of the smoke run.

Linux memfd flags 0x0001/0x0002 and seal bits 0x0001/0x0002/0x0004/0x0008 match the installed Linux headers. The implementation uses libc and Linux fcntl ABI constants because this pinned Python lacks the exposed memfd/seal names. Source inspection and the passing real-child test support this host-specific implementation; portability beyond this Linux host is not claimed.

The meaningful retained red test reports **2 failed, 3 deselected in 0.29 seconds**, reproducing both missing boundaries. The earlier missing-keyword red is not counted as behavioral reproduction. check03 retains **1 failed, 35 passed in 0.58 seconds** from the unavailable Python memfd interface. Corrected check04 reports **36 passed in 0.57 seconds**, combining archive cases and all five network-free adapter tests. None of those results establishes remote durability, remote authentication independently of SSH configuration, real throughput or an actual kernel-guard execution.

All **120 binding entries** were independently rehashed and matched. Binding inventory SHA-256 is `1f106a225ec98245f43c4fab47388a0773300687112dc401cdc4b1d5688f01d6`. It includes the runner, contract, inherited transfer implementation, research sources and transport test. The launcher requires byte equality to the committed HEAD inventory, then hashes each mapped file and passes the inventory hash in the actual guarded worker argv. Every worker lease rechecks that hash, mapped bytes and actual guard identity/containment. Final commitment is a release condition, not claimed completed in this review.

Scope is one deterministic 1 MiB member, one upload and two readbacks with a fresh transport for the second. Normal reserved payload is 3,211,264 bytes within the shared 4 MiB budget. Network framing/handshake and bounded diagnostic stderr are outside decoded member accounting. The guard settings remain 512 MiB maximum, 384 MiB high, zero swap, two CPUs, 180 seconds and 10 GiB local floor; commands have 30-second execution deadlines with bounded cleanup. Existing strict known-host checking, batch authentication and the prebound public host/user/path are retained. Credentials were not inspected.

A failed attempt must retain local/remote evidence and must not be retried under this identity. Success must be judged from actual archive receipts/content, guard terminal status, child exit and cleanup evidence after execution. Copying into sealed memory does not delete the original source; temporary download-name removal preserves the linked bytes. This review admits no eviction, migration of existing artifacts, archive-backed compact reader substitution, bulk storage/performance conclusion, new paid resource or empirical experiment.

Direct reviewed SHA-256 bindings:

- run.py: `f9183edb36d8ccfcfae743814ab3fe48ddb7142d1ef707220e2e942ff56e0885`
- CONTRACT.md: `9516437e4729ed207335fa94abb21fda51665d8ba07c5e35840360618e6c0742`
- test_archive_transport.py: `0ddec88975a8371d808a6107ba98b4255361ff967071e31913812978a266e437`
- check04.log: `eb7ec5cb6a13f4d81e6a8de060030930575646b89b8ae7296243f9928d1238ae`
- lease-red02.log: `2421b264fefe816431197a4338e359ac8f28c0a71d6f1c3291c83f1fbebbadd3`
- check03.log: `95d0a827eb6f5ee72e7b3210e6472844a1ae88b1de347c2b8fd170e647dc4901`
