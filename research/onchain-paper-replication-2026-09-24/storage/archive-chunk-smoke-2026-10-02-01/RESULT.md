# External synthetic archive result

external01 CLOSED: session40021 exit0. Gate
6bbcc0a9a006b9e22b0df8127d96bf3ca3f83ff2 was committed, pushed and exact remote
HEAD verified before execution. No bound source changed during the run.

A1MiB synthetic member was uploaded to the exclusively created Storage Box
directory paper-replication-chunk-smoke-20261002-01, retrieved immediately, then
retrieved through a fresh Transport instance using the saved receipt. The original,
upload snapshot and both downloaded files independently hash to
fbbab289f7f94b25736c58be46a994c441fd02552cc6022352e3d86d2fab7c83.
Archive receipt SHA-256:
d5037cb5db11393e89963af58b160961ee864ae5537cc2c67f847c471a526d02.

Actual guard final.json reports phase complete, child exit0 and cleanup_verified
true, with no limit reason. Kernel readback:536870912B max,402653184B high,
zero swap, CPUs0/1,180s wall ceiling and10737418240B local free-space floor.
Recorded elapsed2.999160738s; this tiny test does not establish bulk throughput.
Terminal OOM/oom_kill counters are0 and the former cgroup path is absent.
All four transport diagnostics report complete/exit0; both downloads received
exactly1048576B. Decoded member reservations total3211264B, below4MiB; SSH
handshake/framing overhead is excluded. No failed marker exists.

All local synthetic source/snapshot/download bytes and remote member are retained.
No historical source or result was moved or evicted. This verifies bounded actual
external copy/recovery and the new sealed-memory SCP input on this host. It does
not prove archive availability guarantees, bulk performance, current compact
owner/stage/terminal compatibility, full raw backup or empirical admission.

Next implementation follows full_sources/archive-chunks-2026-10-02/
NEXT_INTEGRATION.md: archive-backed sealed-chunk reading and bounded scratch,
then exact scientific joins/current-owner terminal admission. Whole-workflow
resource accounting and budget amendments remain required.

Independent REVIEW_RESULT accepted, SHA-256
2410e76d0fce640d61ba997328628c2709a988199d9c488670196f3f78e3ef2a. Fresh Transport recovery occurs within
the same guarded worker, not a new-process restore. Guard sampled peak
37412864B is not an exact instantaneous maximum. Cleanup stop rc5 is retained
with independently checked inactive/dead/empty ControlGroup and absent process
evidence; cleanup is accepted on those combined observations.
