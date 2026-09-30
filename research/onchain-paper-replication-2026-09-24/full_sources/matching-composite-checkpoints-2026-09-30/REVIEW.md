# Independent composite matching checkpoint review

September 30, 2026. **Accepted for further isolated synthetic engineering, with no blocking defect identified.** This is not production integration, empirical execution or a capacity override. Review used source and saved compact evidence only; no tests, numerical jobs, empirical bodies or network operations were run. Neither component source was changed.

## Composition and numerical identity

`combined.py` transitions from annealing only after the inner state reaches done. It hashes the complete C-order float64 M directly through a memory view, creates a hardening state bound to that digest, and marks M read-only. Hardening retains the separately reviewed ascending row-major chunk scan and strict-greater winner update; ties retain the first eligible flat entry. Final assignment is built from the selected pairs, then evaluated with the unchanged scalar objective and convergence convention. It does not call the old atomic hardener.

The wrapper verifies the inner annealer identity, completed phase, hardening shape/dtype, policy and matrix ownership flag. The phase join requires composite done exactly when hardening is done. A mutation exception poisons the composite; an exception inside an active component also poisons that component. Valid prior checkpoints remain usable. Transition hashing and final scoring are still atomic, and a call may finish annealing without spending remaining allowance on hardening. No per-call wall-time guarantee follows.

M's read-only flag prevents accidental direct writes, not hostile alias writes or a caller resetting flags. In-process progress compares its cached identity rather than hashing the full matrix each chunk. Acceptance therefore requires the stated exclusive ownership of issued, unmodified states and inputs. This is not authentication of arbitrary caller-created state. Restore materially strengthens the boundary: after nested array restoration, it recomputes M's body hash and checks it against the hardening input identity before accepting the composite.

## Durable boundaries and allowances

Publication creates an exclusive directory, saves the nested annealing checkpoint and optional hardening JSON, then publishes and fsyncs an outer manifest binding both component digests, phase, M identity and all three execution-policy fields. Existing directories and partial identities are not overwritten. Load verifies the outer digest and exact caller policy, then the hardening JSON digest before numeric array loading. The nested annealer verifies all three array hashes/headers and graph/configuration identity. Restored M is marked read-only before the final state check. Schema 1 for the wrapper and schema 2 for its annealer are explicitly distinct.

The conservative publication admission is the three dense matrices plus three 64 KiB allowances. The nested allowance, hardening JSON cap and outer manifest cap partition that total. This bounds logical saved bytes only. Hardening metadata is limited to 64 KiB regardless of a larger caller checkpoint allowance; sufficiently many selected pairs can therefore make a later save refuse. This retained, explicit limitation must be addressed by a separate design if larger complete hardening checkpoints are needed; these tiny tests do not establish that capacity.

Retained annealing numeric state is 24×n×m bytes. Hardening's separate numeric policy covers its reviewed scan scratch, not Python pairs/JSON or total simultaneous process memory. Graphs, old caller-held states, validation/hash scans, SciPy temporaries, publication buffers, final dense int8 assignment and copied M remain outside these component allowances. Whole-hub RAM, disk-allocation and elapsed-time feasibility are not demonstrated.

## Saved verification and limits

`red01.log` records four pre-implementation interface errors, not four numerical counterexamples. The final saved `green02.log` records **five tests passed in 6.335 seconds**. All 13 entries in source-bindings.json independently rehashed correctly.

The parity test saves and reloads after every advance return for three graph-pair shapes, including a wider singleton tail, tied zero-edge inputs and a single column. It compares final soft-assignment bytes, hard assignments, score, iterations and convergence against the unchanged scalar oracle over two iterations. Patching the old hardener to fail during result construction confirms that result uses checkpointed pairs. The policy/tamper test prevents numeric loading on an outer-policy mismatch or corrupted hardening JSON. The new restoration test modifies M and updates both nested and outer hashes; it still receives the specific M-versus-hardening-identity refusal. This is a meaningful cross-component identity regression.

The hardening interrupt test raises at argmax and verifies that the composite cannot be saved afterward and that the prior checkpoint resumes to the oracle assignment. It is not a post-write interruption of the pair list/cursor; safety for those locations is supported by static exception structure and the separately reviewed component, not a new direct test here. Tests also retain original pair-capacity refusal, early buffer-policy refusal, checkpoint allowance and exclusive directory behavior.

Not tested here: filesystem crashes/fsync failures, concurrent aliases or path replacement, arbitrary reachable-state validation, metadata-cap exhaustion, large graph performance, resource peaks, all shapes/library versions, accelerated/Torch parity, scoring checkpoints or registered ancestry/ownership. No financial result, sampling change or production release follows from these checks.

Reviewed source/evidence identities:

- combined.py: `df493fa09a6d9a22c7d170128d6446b5d39a2a9cf57f0a08d57df3bb3f5786e6`
- test_combined.py: `646f6f87eacf36527fe53d75c79d0855b6848a561217ab1b26f9ae5cf836d668`
- IMPLEMENTATION.md: `eaadf8ce9cf04acb08928889cc80d2159fd46711d1ca830c9cce69983dcdce27`
- green02.log: `7157887723770d2e2316826e1177ee805ce69d55dda1007433b8b92cfbf93992`
- source-bindings.json: `3028a62dc188132414b588b3ecab51faaa6978c9360b21cb6695f12f1dbb1e46`

Observed HEAD remained `62c5b6ea66e95cc67a404d1f13898619a88237fc`. The earlier source/evidence remains intact. Only this review was written for this candidate.
