# Full-schedule directed-chain resource probe

One new isolated synthetic identity extends the reviewed ranked matcher to a
complete nonzero-edge schedule. Generate fresh identical2000-node directed chains,
1999edges0→1→...→1999, constantzero node features and unit edge features. Use the
unchanged matching-stable.json with4Mpaircap and48iterations. No raw graph, labels,
prices, old checkpoint body or closed experiment is read or rerun. The earlier
closed two-iteration edge probe and zero-edge profiles remain distinct evidence.

Expected annealing work:4,000,000initial node operations plus48iterations of
3,996,001edge-pair updates and251outer/normalization operations =195,820,096,
with191,808,048edge-pair updates. At4Moperations/call this takes49calls. Every fourth
call while still annealing saves and restores a fresh exclusive checkpoint
(04,08,...,48), explicitly closing old state first. Maximum12intermediate snapshots.
The interval is an operation bound, not a promised wall-clock interval. The finite
outer guard still applies to individual atomic calls and checkpoint operations.

After annealing, columns must sum to1within1e-12. Stable ranking may yield any
injective assignment; neither diagonal assignment nor a target score is imposed.
Advance at most65,536rankedentries, save/restore checkpoint01 whether hardening
is incomplete or done, complete remaining hardening once, then score. Save/restore
checkpoint02 and compare only the restored score/identity, without rerunning any
completed annealing or hardening. All restored mappings are explicitly closed.

Independent objective oracle: a complete bijection gives node term1. Let h be
the number of source-chain edges mapped to a target-chain edge. Constant edge
features give edge term h/[2*(1999)], hence score=(h/[2*(1999)]+alpha)/(1+alpha).
Compare within1e-12. The standalone oracle imports no matcher or graph validator;
two tiny tests cover identity/reversal/rotation and nonbijection refusal. This
checks objective arithmetic for this fixture, not assignment optimality or paper
numerical agreement. Result pairs remain in checkpoint metadata for review.

Retainednumericstate128MiB, rankedexplicitworkspace80MiB, scorebuffer8MiB,
normalization/rankedentrychunks65,536 and logicalcheckpointcap128MiB each. Up to
14snapshots reserve1.75GiB; enforce total logicalcheckpointallowance2GiB, require
10GiB+2GiBdisk at launch and10GiB+144MiBbefore each snapshot. Preserve all partials,
failures and checkpoint bodies. No automatic retry, deletion or identity reuse.
Trusted source/config/body hashes and exclusive checkpoint lifetimes remain.

One guard:1GiBmemorymax/768MiBhigh/zero swap/twoCPUs/3GiBhostreserve/4GiBstartup/
10GiBdiskfloor/1800seconds. The earlier edge-prefix timings motivate this finite
measurement but do not guarantee completion. Any timeout/failure remains evidence;
no limit is raised after seeing outcomes. Peak includes diagnostic/native/runtime
and checkpoint filecache costs, not just explicit numeric arrays.

Before execution require independent exactsource/protocol review, committed/pushed
bindings, pinnedruntime, absent newidentities, allownercleanup and no active
replicationunit. Graph10 has priority if its fresh9GiB+128MiB RAM and required
22,103,159,134diskbytes are available. Otherwise this lower-memory independent
profile may launch after its own checks; graph10 must wait until it closes.
FreezeHEADandbindings while active. Inspect actual progress/guard receipts; never
duplicate its process or relaunch an exclusive started or terminal identity.

Successful completion establishes this structured synthetic fixture only, not
worstcase real-hub, full dictionary/MCM/neural feasibility, GPUprecision, financial
results, controlled speedup or production/cache/backend integration. All paper
scope,109originalresource requirements and1,420fits remain required.
