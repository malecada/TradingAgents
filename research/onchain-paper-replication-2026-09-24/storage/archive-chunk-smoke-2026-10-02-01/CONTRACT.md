# External synthetic archive chunk check01

Fresh engineering storage check; no financial data, graph transform, matching,
fit, empirical sample exposure or cumulative experiment allowance is consumed.
One deterministic 1 MiB synthetic member is uploaded once to the prebound fresh
Storage Box directory paper-replication-chunk-smoke-20261002-01. An immediate
readback and a fresh-transport retrieval must both match its trusted bytes/hash.
The real guard enforces 512 MiB max/384 MiB high RAM, zero swap, two CPUs,
180 seconds, 10 GiB local free-space floor and child cleanup. Transport commands
have 30-second deadlines; decoded payload reservations total at most 4 MiB
(SSH framing/handshake overhead is excluded), transfer rate at most 32 Mbit/s.
Every identity is exclusive and terminal attempts are never replayed.

Only the existing public host/user/port/key-path configuration is used. No
credential contents are read or printed. Existing strict known-host checking is
required. All synthetic source, local attempts, receipts, transport diagnostics
and remote member are retained. No existing file is moved, evicted or deleted.
The uploader copies at most 8 MiB into a kernel-sealed memory file before
reserving its exact extent; scp opens that sealed descriptor through /proc.
Growing or replacing the original path cannot increase transmitted member bytes.
Every subprocess requires a fresh source/guard lease.

The scratch download is hard-linked exclusively into its new final path then
its temporary name is removed; the bytes remain retained. Interrupted dual links
fail the member's single-link validation and remain evidence.

Execution requires reviewed committed code/bindings and no active predecessor.
A source/contract pin and actual guard check run before every external action.
Success is only a bounded external copy/recovery result. It does not validate
bulk throughput, archive availability guarantees, compact owner/terminal reader
integration, local eviction or feasibility of the full paper experiment.
