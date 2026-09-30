# Independent bounded hardening prototype review

September 30, 2026. Source and saved synthetic evidence review only. No tests, empirical arrays, jobs or remote calls were executed; no frozen production file was changed. The registered-census offline verification remains a separate active owner.

## Initial assessment

No blocking correctness finding was identified in the inspected prototype. For supported finite real ndarray inputs, chunk flattening follows C/row-major order and conversion to float64 matches the legacy `harden` work matrix. Already selected rows and columns are excluded together. Each chunk's first argmax and the strictly-greater update across ascending chunks retain the earliest row-major feasible maximizer, including negative and tied values. Sorted selected endpoint arrays supply exact membership without a full dense mask. Empty dimensions return an empty int64 pair array. The sparse output lists choices in selection order; the legacy function returns a dense binary assignment, so these are different interfaces with equivalent chosen pairs, not byte-identical return objects.

The numeric reservation is conservative for visible NumPy arrays: output pairs occupy 16*k bytes and the two selected endpoint arrays another 16*k, where k=min(n,m). The 48*k component leaves room for bounded overlapping insertion work. At most a chunk of c entries is gathered/cast; values, flat indices, row and column indices, search positions, endpoint gathers and boolean comparison temporaries fit within the 64*c allowance. The initial finite scan retains only bounded chunks, and rejects nonfinite input before allocating the output/endpoints. Chunk arrays are released before each next scan. The allowance check occurs before these allocations and uses `c=min(chunk_entries,n*m)`.

This is a numeric-array envelope, not a measured allocator/RSS bound. It excludes input residency, Python/runtime/library bookkeeping, caller copies and any concurrent caller state. It does not bound disk backing or mapped page-cache residency. Source-matrix stability for the duration of the function remains a caller ownership requirement. Runtime still scales with approximately `min(n,m)*n*m` scan work plus membership searches; scratch reduction supplies no performance or checkpoint guarantee.

Saved green01 reports **five tests passing in 0.931 seconds**. Tests compare reconstructed dense assignments with the existing legacy implementation over rectangular, tied, negative, empty, random, dtype and strided cases, verify input preservation, and exercise a synthetic mapped 2 by 2,000,001 matrix with a 65,536-byte new-buffer allowance. That fixture has k=2 and c=256, yielding a declared 16,480-byte requirement; it does not test a large square matching problem. The allocation sentinel excludes direct full-shape `empty`/`zeros` calls but is not a general allocation profiler. Red01 is an import-time missing-module failure, not five separate executed failing assertions.

Literal choice-order and exact allowance-boundary/preallocation tests are pending the author's stated additions. High-magnitude int64/uint64 rounding ties and signed zero are useful additions because selection must match float64 conversion before argmax, not ordering in the original integer dtype. Current random integer values are small.

## Scope and identities

This isolated file is not imported by the matching kernel or registered feature pipeline. Existing matching capacity, dense iterative state, CPU/device transfers and dense hard-assignment scoring remain unchanged. Sparse-pair consumption requires separately reviewed integration and exact score/feasibility parity. No empirical admission, capacity override, financial result or full-neighborhood feasibility is established.

Initial reviewed SHA-256 identities:

- `bounded_hardening.py`: `258b3df38e93b65427da8242f5b25da23df6d41691ab6b64be162b2550e4fe6b`
- `test_bounded_hardening.py`: `b3fff6b80a1708318351344e0cd1a6fb9baf83ff09fc33dd0aaca3a3a33656c3`
- `green01.log`: `0b42c26eaefe2813e788c81373d4da5e17c19d8eec4242fedaf84c6b5318f5ba`
- Observed HEAD: `f762b47d3b10b514fec5e7b8122210751b62a61f`.

## Expanded hardening evidence

The unchanged hardening source now has saved green02 evidence of **eight tests passing in 0.946 seconds**. Added cases cover int64/uint64 values that collapse to float64 ties, signed zero, a literal non-row-sorted choice sequence, acceptance at the declared exact numeric allowance and refusal one byte below it before an output allocation sentinel. These close the initial requested focused coverage additions. Test SHA: `424ddbdc7f58e983074e8de17b7e0624ee502571c5863c7aba2560b17715fabc`; green02 SHA: `085198def8a56a7537bff1c44c67f0c819ce42d90e6d3160a6242032922c139a`. Focused acceptance remains for the isolated bounded hardening component, with the initial scope limitations unchanged.

## Sparse scalar objective: initial finding

**S1 — zero-term omission changes overflow/failure semantics for admitted finite attributes (`sparse_objective.py:25`, and edge filtering at lines 30–37).** The existing scalar scorer evaluates agreement before multiplying by assignment zeros. The sparse prototype never evaluates those discarded agreements. For two identical two-node graphs with node features `[[0.0], [1e200]]`, no edges and identity pairs `[[0,0], [1,1]]`, graph/pair validation admits finite attributes. Legacy scoring evaluates the off-diagonal squared difference `(0.0-1e200)**2` and raises `OverflowError`; the sparse scorer evaluates only equal-feature agreements and returns a finite result. This is an independently reconstructed source counterexample, not a reviewer-executed run. Retain a synthetic regression and either preserve the legacy failure semantics or explicitly restrict and check the representable-agreement domain before asserting parity. Exact unconditional behavior parity over all currently admitted finite attributes is not supported.

For the domain where every scalar agreement is defined, sorting chosen pairs by left node and scanning right edges in original order preserve the reference's nonzero summation sequence. Removing positive zero terms does not change the nonnegative math.fsum result. Partial and empty injective assignments are intentionally supported, and validate_pair retains original graph validation and capacity checks. Reciprocal edges, self-loops and the reference half coefficient retain their original meaning. This does not establish equivalence to the accelerated Torch reduction order or permit substituting this scalar reduction into that backend.

The visible numeric scratch bound `64*pair_count + 32*min(chunk_edges,right_edges)` appears conservative for injectivity checks, sorting/gathering endpoint arrays and chunk masks/index arrays. Graph/pair input residency and graph validation work are expressly excluded. The first budget check precedes validate_pair, but exclusions mean it is not an RSS or complete validation-allocation cap. Right-edge scanning remains potentially quadratic in edge counts; no time, capacity-extension or checkpoint guarantee is established.

Saved sparse-green01 reports **four tests passing in 0.024 seconds**, comparing exact scalar scores on literal directed/reciprocal/self-loop, zero-edge, random, full and partial cases, and checking invalid assignments, capacity and insufficient allowance. These cover ordinary finite attributes but not S1. Sparse-red01 is reported as a missing-module import failure; no functional red assertions are inferred. Sparse acceptance is pending disposition of S1.

Initial sparse identities:

- `sparse_objective.py`: `95ff2fd16fb76df102564bedaa64be5158367ba33fc113fda994afe2b706d301`
- `test_sparse_objective.py`: `a0f4ad7227733df0eeecd390a4efc4dcb0f04970f1a534efdcc8d75d7a941b8b`
- `sparse-green01.log`: `f06d1125e589d2706ba5cf9108d8b63daabf18da21c7065a7ade90edf18326ca`

## S1 correction and qualified sparse acceptance

The correction explicitly narrows admission to a checked representable-agreement envelope. For each attribute it computes the greatest cross-input extrema difference, rejects a nonfinite difference or a square beyond float64 range, and uses math.fsum over the envelope squares to reject summed-square overflow. Both node inputs are always checked; edge attributes are checked only when the edge cross-product is nonempty, matching whether the scalar objective evaluates any edge agreements. The check precedes sparse evaluation and creates no per-node or per-edge feature copy. Existing graph/capacity validation remains in force.

This resolves S1 as an **explicit domain restriction**, not restoration of identical acceptance/error behavior over every legacy input. The prototype raises a descriptive ValueError where the preserved counterexample raises OverflowError in the reference. Componentwise extrema may come from different rows, so the envelope can conservatively reject an instance whose actual pairwise agreements are all representable. That limitation is now stated in the source and must remain visible in any future policy review. It must not be silently substituted into an empirically registered scorer.

Retained sparse-red02 reproduces the original counterexample as one failed assertion that the domain refusal was missing. Corrected sparse-green02 reports **six tests passing in 0.027 seconds**, including the scalar-reference overflow demonstration, node/edge domain refusal, summed-square overflow and an empty edge cross-product that does not spuriously require edge agreement evaluation. The prior exact scalar parity cases continue to pass. Source inspection supports the envelope and bounded-array accounting on its stated domain; this review ran no tests or empirical inputs.

**Verdict: accept both isolated prototypes for continued synthetic engineering with the stated limits.** Hardening retains the legacy selection semantics for supported inputs. Sparse objective score parity is restricted to the checked representable domain and the scalar reference summation route. Production caller/policy admission, Torch reduction parity, large-pair performance, checkpointing and complete matching memory feasibility remain untested and unenabled.

Corrected identities:

- `sparse_objective.py`: `06f2d312a1527f335decc8e0c4d1283448a28e783d5e64018d70e9bf3416883e`
- `test_sparse_objective.py`: `122afbcef914c30ff18d87b027227e1defc86cc3043b223f4547e83c59b08d24`
- `sparse-green02.log`: `ac5543af9f4af779defb101bfabc824808fb9580772765c0fc75540b15869847`
- `sparse-red02.log`: `f6ab17158970b6921270ecfb3d34bd708903cbec638adf5693100276d2ff6d0b`
