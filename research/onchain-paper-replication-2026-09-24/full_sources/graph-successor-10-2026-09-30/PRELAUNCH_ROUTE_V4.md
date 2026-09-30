# RAM-capacity amendment for unused Graph10

The original full December23–30,2024 graph and all eight cells remain fixed.
No graph launch or claim exists. Gate-v3/temp02/preflight03 failure are retained.
The fresh route uses temp03, preflight04 and dispatch04 exclusively.

Worker maximum changes6→5.5GiB; startup reserve9→8.5GiB. The5GiB throttle point,
3GiB host reserve, zero worker swap, two CPUs,10GiB free-disk floor and28,800s
wall limit remain fixed. Dispatch adds the same128MiB headroom:8.625GiB total
available RAM, or9,261,023,232 bytes. Disk planning requires22,103,159,134 bytes.
This changes resource allocation, not the graph algorithm or scientific scope.
Six retained complete graph guard receipts support plausibility, not a guarantee
for the December input or a proven minimum memory requirement. No closed job is
rerun to justify this amendment. Any hard-limit failure remains a spent attempt.

Gate-v4 changes only Graph10's charter and execution_job input, and appends new
source/compact evidence pins. Eleven inherited experiments and all family/budget,
window, output, cell and other scientific objects remain unchanged. Proposed60
is still unadopted;32/59 accounting persists until actual claim. All1420fits remain.
The old gate, charter and job bytes are retained as pinned history.

After independent review and commit/push, perform checked sequential fresh
ownership/RAM/disk/HEAD tests BEFORE temp03, then temp03→preflight04→immediate
checks→one launch. Both preflight and outer checks cover active AND activating
replication units; the outer check additionally rejects pending monitors.
Temp03 must be fresh within300s and fully cleaned before preflight04. Preserve
refusals and never restart a reserved identity. Source/HEAD freeze after launch.
No candidate matching owner/journal/extent consumer is enabled by this route.
