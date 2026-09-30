# Independent normalization/chunk initialization investigation

September30,2026. Read-only source and saved synthetic evidence; no probe/test execution, empirical arrays, raw/SQLite reads, source/HEAD edit or production approval.

**Naive independent column chunks are not unconditionally exact.** Reconstructing the288 saved case records gives0 row-reduction mismatches,28 column-reduction mismatches and28 final-normalization mismatches. First counterexample:17×6, seed23, scale1, chunk width1; column difference2.220446049250313e-16 and final difference4.163336342344337e-17. Maximum column difference is2.6645352591003757e-15; maximum final difference6.938893903907228e-17. Width counts are1:19,2:3,4:3,16:3. Every mismatch has a potential one-column block/tail with original width greater than one. This supports, but does not isolate/prove, the contiguous-reduction explanation.

The probe's `np.array_equal` is exact numeric-value equality, not byte identity: it does not distinguish signed zeros. Its random Q matrices include negative entries; the valid scalar matching Q is formed from nonnegative agreement terms. Thus this is a decisive counterexample to unconditional transformation equality, not yet a demonstrated reachable matching-state failure. No claim about observed predictions, assignments or scores follows. Zero row failures do not prove general equivalence.

## Pinned arithmetic and concrete next candidate

Local NumPy2.3.0/SciPy1.17.1 source was inspected. The `_logsumexp` kernel source hash equals the probe record. The public wrapper evaluates a direct exponential/log fallback, then the kernel separates every maximum, counts their multiplicity, exponentiates nonmaximum shifted values, sums them, divides by multiplicity where appropriate, and computes `log1p(s)+log(m)+max`. Replacing this with the usual `max+log(sum(exp(...)))`, different reduction trees, partial-sum combination, or compensated sums would change the reference arithmetic.

A specific next isolated implementation candidate is:

1. Finish **all edge updates** before overwriting M: every edge update reads the previous iteration's M. Then reuse M as the log-normalization workspace by bounded `np.multiply(beta,Q,out=M)` slices. Likewise use bounded `np.multiply(alpha,V,out=Q)` and copy V→M slices for initialization, avoiding full dense expression temporaries. Scalar operation order within each element must remain unchanged.
2. Apply row normalization in blocks that retain the **full original column width**. Do not split a single row's reduction or combine block log-sums. Account for SciPy's internal block-sized temporary arrays, not merely the caller's slice.
3. For C-order reference matrices with m>1, use C-contiguous column blocks of width≥2. When a block would have width1, copy its column into both columns of a two-column C-order scratch block, call the pinned logsumexp along axis0, and retain only the first answer. If original m=1, keep the actual singleton route: padding it would itself change the reference layout. This preserves the non-fast-axis character of axis0 reductions in SciPy's dense copied intermediates. It is a **candidate requiring parity evidence**, not an accepted numerical substitution. Do not assume Fortran/strided inputs have the same reduction order.
4. Make each completed block a durable state-machine boundary: separate copy/scale, row-normalization, column-normalization, exp and iteration-advance phases/cursors. Save only after the block's output and cursor are consistent; poison live state on any escaping exception. Resume must never reapply an already-subtracted normalization or advance beta twice. Column reductions must see each column's complete row-normalized values. Scratch need not be persisted if exactly reconstructible from a saved consistent boundary.

The minimum column scratch still scales with n (at least n×2 for the padded route and several SciPy intermediates); one full-row reduction scales with m. This avoids an additional full n×m normalization temporary for large shapes, but does not eliminate the three retained dense matrices or bound the maximum atomic reduction time. If even a whole-column block exceeds the allowed scratch/time, exact resumable reduction kernels would require a separate proof of the pinned reduction tree, not an arbitrary chunked sum.

For initialization, `np.empty` alone is insufficient: a checkpoint must not serialize uninitialized suffix bytes or validate arbitrary unfilled values. Either retain deterministic zero-initialized backing with explicit completed fill phases or define a reviewed partial-state format that excludes uninitialized regions. A mapped dense workspace and its ownership/durability policy remain separate work.

## Required focused evidence

Retain this counterexample. A padding follow-up should include literal byte comparison with dtype/shape equality, nonnegative finite and small agreement-derived Q, originalm=1 and singleton tails, repeated maxima, signed zero, highly separated values and C/Fortran/strided layout cases. For the intended C-only path, reject other layouts explicitly or qualify their conversion. Exercise interruption and resume at every new phase/block boundary against the uninterrupted scalar reference before any production or policy integration. Numeric allowance must cover real simultaneous SciPy temporaries; no process-RSS or wall-time feasibility claim is established by this probe.

Reviewed evidence:

- probe.py: `a156528f73c916c1eeef4c9bb00d675863ff4c4206c5483037fc3e36ed3e4a13`
- result.json: `088a068a89260f9c030a955ee0ab732a329e963e0d290ae2d4043fc51e9156da`
- probe01.log: `1f1641ad724992ad3cb6456695b2ac8491053e6f0519175607427c57b9917327`
- Pinned local SciPy kernel source: `78d3e69bdd4bb08521126d1ca1fa2c1c7cdf1eedcadf023b2027b946d3fc754b`
