# Original bulk capture closure

The source-only run `eth-remaining-graph-capture-20260916` is terminal from fixed
source `771dfeb54a90ca0724e345ddd183754e5ca80e2b`. It closed normally at
2026-09-17 08:55:58.489244 UTC, before the observed system boot at 13:17:25 UTC.
It was not interrupted by that reboot and must not be restarted under its old
identity. Lifecycle completion does not mean that the historical panel is complete.

The 1,084 scheduled source dates contain 563 complete dates with retained
independent raw-check receipts and 521 unavailable dates. Six individual
transport failures preceded 515 DNS failures. The first DNS failure was for
July 31, 2023, requested at 07:28:59 UTC on September 17. The old implementation
continued to later dates after transport errors, producing many additional
unavailable cells. The last successfully captured date was July 29, 2023.

The immutable new raw bodies total 55,201,092,056 bytes (51.41 GiB). Original
budget accounting including its conservative prior baseline is 57,348,575,704
raw bytes and 519,823,360 metadata bytes. Guard exit was 0 with no resource-limit
reason; duration 52,432.08 seconds and sampled peak RSS 447,430,656 bytes
(426.7 MiB), under the existing 8 GiB/two-CPU/no-duration-kill guard.

Independent lifecycle verification reconciled 1,085 cells, 521 unavailable cells
and 1,086 exact hashed outputs. Every per-day manifest hash was independently
matched to its dated output. The complete historical 51 GiB raw store was not
rehashed during this bounded closure; the original per-day raw checks remain the
retained evidence. Numerical graph canonicality, overlap boundaries, motifs,
historical availability and prediction performance remain unadmitted.

The coordinator preserves the complete lifecycle and per-day manifest metadata
under `research_runs/eth-remaining-graph-capture-20260916/` and `bulk-closure/`.
The copy manifest lists 2,173 objects totalling 17,224,936 bytes, including
already present byte-identical claim/first-day metadata. Actual source bodies
remain in the original Data checkout. This is not an off-device raw backup.

The user's recovery instruction is routed through the explicit single source-only
amendment, `RECOVERY_CHARTER.md` and `recovery-gates.json`. Its exact 521-date
cohort excludes all 563 successful original dates and reuses six valid response
prefixes. Original failed/truncated receipts remain unchanged. The original
family allowance remains consumed at 8/8; recovery's reviewed exception imports
all eight predecessors and adds one cumulative allowance, with no financial
sample reset or prediction outcome.
