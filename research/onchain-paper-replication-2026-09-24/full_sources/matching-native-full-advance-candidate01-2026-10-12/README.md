# Native whole single-pair annealing candidate

UNINSTALLED, UNCOMPILED, NUMERICALLY UNEXECUTED. Engineering prototype only.
No source admission, owned loader, runtime grant, empirical registration or launch
is supplied. The original 48 temperatures, algorithm, pair and native limits are
not changed. All files are confined to this new evidence directory.

`native_full.c` is a CPython extension with one bounded `run` function.
`wrapper.py` supplies the checked `Candidate.try_advance` interface. `None`
means unsupported before state mutation; selected failures propagate with the
inner state unsafe. The original composite caller must poison and clean up as
usual. No state is serialized by the candidate. `root_qualify.py` is an explicit
Root-only compile/comparison hook; it has not been run by the author.

## Scientific operations and arithmetic qualification

The native code calls the pinned original `matching_reference.agreement` through
CPython with ordinary float64 row views. It does not approximate or reimplement
the generator, individual Python-float subtraction/square, `math.fsum` or
`math.exp`. Nodes are visited in row-major order, and first-iteration edges in
left-edge then right-edge order. Half-agreements are lazily saved at their first
edge visit and reused for the remaining temperatures. This mirrors the existing
small-pair cache selection: full budget is greater than edgeproduct and the
graphs are immutable. Contributions use a separately rounded product and a
sequential destination update; no atomics, parallel reductions or FMA. Node V
initializes M; each iteration initializes Q=alpha*V, accumulates edges, scales by
beta, normalizes rows then columns, and exponentiates. Beta uses the original
repeated multiplication and yields48 iterations. Original hardening remains
outside this function.

The deliberately unqualified arithmetic seam is native normalization: SciPy1.17.1
max-exclusion is mirrored (all maxima excluded, count maxima, shifted exp sum,
divide by maxima count, log1p+log(count)+maximum). A NumPy-style eight-lane
reduction is used for contiguous axes up to32 terms; the noncontiguous column
axis is accumulated sequentially. When m=1, its column vector is contiguous.
The candidate does not claim this equals every NumPy build/reduction dispatch.
Native libm exp/log/log1p can differ from NumPy ufuncs, including final exp;
signed-zero details and tie-sensitive hardening may differ. The fixed existing
atol1e-8/rtol1e-6 contract is not changed. The comparison hook separately records
soft bit equality, maximum absolute difference, score bit equality, exact hard
assignment, iteration and operation/cursor history. It fails on tolerance,
assignment or history mismatch. A tolerance pass is not universal bit equivalence
or proof of real-data ties. A failing fixture must remain failed; do not relax
tolerance or hide assignment differences.

## Domain, mutation and failure limits

Fresh nodes/cursor0/iteration0/safe state, fixed original config, one full-axis
normalization operation per phase, enough budget for all48 iterations; each
side1–32 nodes, positive edgeproduct<=1024, ordinary C-contiguous aligned native
float64 features of width1–4 and magnitude<=256, immutable bytes backing,
int64 bounded endpoints, disjoint writable original V/M/Q, default NumPy error
policy and nearest rounding. Original `ann.check` still runs. Partial/restored
states, partial budgets, zero edges, other runtime/error policy or unsupported
layout return `None`; caller must make one original unsplit fallback call.

Used operations are n*m +48*(1+edgeproduct+4). An exactly equal budget ends at
outer/cursor0; extra budget performs the original zero-operation completion to
done. The original composite engine then performs matrix identity and ranked
hardening creation; the extension never owns ranking state. No new poll is
introduced or old between-call poll removed. The direct C function is an
implementation detail, not an authority API; its buffer and shape checks are
defensive, while immutable-source/runtime/currentness belongs to the wrapper
and ultimately to separately reviewed genuine integration.

Ordinary agreement exceptions preserve the computed node/edge prefix and edge
cursor; the original exception is retained if cursor publication itself fails.
The selected input domain rules out ordinary numeric overflow/domain errors.
This is NOT full asynchronous/resource-failure equivalence: C/libm loops can
defer Python signal delivery, and allocation failure during Python metadata
publication can occur at a different instant. Native phase writes may expose a
different intermediate array prefix during such fatal interruption than a NumPy
bulk operation. The caller must keep unsafe/poisoned disposition and no completed
credit on any failure. No claim of atomic rollback, checkpoint after a failed
call or per-instruction signal equivalence is made. Such behavior is a concrete
remaining review/qualification condition, not permission to remove checks.

## Explicit memory bound

No full-pair geometry vectors and no additional dense V/M/Q arrays are allocated.
Native stack weights=1024*8=8192B; normalization output vector=32*8=256B;
one logsumexp terms vector=32*8=256B; eight-lane sum scratch64B; nine buffer
headers plus bounded local scalar state. Numeric/header stack is conservatively
below16KiB on the selected64-bit ABI. Wrapper feature checks use <=256rows*4
columns: abs payload8192B plus Boolean comparison1024B, separately evaluated
finite mask<=1024B. These Python NumPy feature temporaries finish before native
entry. Per-agreement row-view/argument objects are transient, not a retained
table; tuple/state metadata remains O(1). A conservative64KiB explicit scratch
bound covers these candidate payloads/header objects, excluding existing arrays,
interpreter frames, allocator/native library/runtime and original validation
workspace. It fits the existing262144B vector/adaptive reservation only if the
future integration selects this path before allocating fallback scratch and
proves nonoverlap. The v2 cache never allocates for this <=1024 edgeproduct domain.
The current784951284B declared numeric requirement is not generic spare memory.
Native6GiB maximum/5GiB high remain unchanged. Physical fit is unmeasured.

## Root-only hook and unresolved integration

After source review, Root may run `root_qualify.py` with
`--root-reviewed-offline-qualification --output <NEW-directory> --config
<original-matching-stable.json> --config-sha256 <pinned-hash>` under its existing
bounded offline envelope. `--compile-only` stops before importing the extension
or numerical modules. The compiler command is fixed O3/C11/no-fast-math/
ffp-contract=off/no-associative-math/no-unsafe-math/frounding-math, with no shell
or inherited compiler/linker flags. Root must retain compiler/platform/runtime
identity and resulting body hash; no supplied artifact is executable authority.

The finite hook creates only synthetic graphs:1x1,3x4,8x8,16x16,32x32, tied
8x8 and zero-edge fallback; budgets below/exactly/above the complete advance need.
It runs original create/check/advance/hardening/result/close and compares final
results/history. This is a single cold timing per case, not a stable speed
estimate, and no paired current C05v2/compiled-normalizer baseline is supplied.
Such a baseline, adversarial refusals, callback/fatal injection and original
checkpoint save/load qualification remain Root/reviewer work before release.
The hook writes compile and comparison records; it never mutates Main, claims
or source pins. Its local loader hashes a body but is not the sealed native Owner.

Genuine integration remains at matching_checkpoint._advance_owned's checked
annealing branch, with unchanged session checks, PairExecutor callbacks/budgets,
hardening handoff, source/runtime pins and cleanup. This candidate supplies no
new policy fields or fake integration. Whether it approaches the11.6x conditional
numeric gap is unknown until Root measures it; Python agreement callbacks and
all nonnumeric work remain. No strategy/model/result credit follows.
