# Independent scalar annealing checkpoint prototype review

September 30, 2026. Read-only source and saved synthetic evidence review; no tests, empirical arrays or jobs were executed. The active registered-hub offline02 freeze is untouched. This isolated prototype is not a registered or accelerated matching replacement.

## Initial findings

**A1 — accepted metadata includes unreachable/unsafe states (`annealing.py:40–52,85–89,97–113`).** The state check constrains cursor ranges but not their relation to phase and stopping conditions. In nodes phase cursor==n*m is accepted, although advance then indexes row n. A newly created state changed to phase done with cursor zero is accepted and result hardens the uninitialized zero M despite beta/iterations still permitting annealing. Normalize with an exhausted schedule is also accepted. save performs no state validation, so such states can be durably written and accepted on load under their caller-provided manifest SHA. Enforce reachable phase/cursor/iteration/beta conditions before saving, loading or returning a result. Strict cursor bounds and a valid done stopping condition are required; tests should cover false completion and terminal-boundary metadata, not only corrupt file bytes.

**A2 — an exception during mutation can leave a resumable-looking but inconsistent state (`annealing.py:63–81`).** Edge accumulation updates Q before incrementing the edge cursor. An interruption after the in-place addition and before the cursor update leaves the same contribution eligible for a second addition on resume. Normalization likewise updates M, beta, iterations and phase in separate mutations; interruption after iteration advance but before phase advance can repeat normalization at the wrong beta. A caller catching the interruption can currently save the partial state without rejection. Either supply transactional safe-point updates or conservatively poison any state whose advance call exits with an exception and refuse save/result/resume from it. Existing successful returned operation boundaries are not evidence of asynchronous interruption safety. Preserve the last completed checkpoint and failed in-memory state evidence rather than treating arbitrary interrupted state as a new valid checkpoint.

## Supported arithmetic and storage behavior

For reachable states saved after a successful advance return, node agreement traversal is row-major; edge contributions retain the exact original left-edge/right-edge nesting and addition order. Q initialization, row then column logsumexp normalization, exponentiation, multiplicative beta update and scalar hardening/scoring match the existing reference. Zero-edge transitions avoid division by zero. Config/graph identities are bound, and original pair-capacity validation remains active. There is no proof of parity with accelerated Torch batching/reduction/device arithmetic.

The stated retained numeric state is three n*m float64 arrays, **24*n*m bytes**. Create/load enforce that allowance before allocating those matrices, and load preflights every file hash, NPY header, C order, dtype, shape and exact extent before the first np.load. Input validation, repeated graph identity hashing, normalization/Q temporaries, hardening/scoring and caller-retained prior states are correctly excluded. max_operations counts state-machine work units, not CPU time, hashing, graph validation or bounded-duration normalization. This remains a dense-state checkpoint prototype, not a dense-memory reduction or finite wall-time proof.

Checkpoint save reserves an exclusive directory, writes/fsyncs three arrays, checks exact encoded manifest plus file logical bytes, publishes the manifest last, and fsyncs the directory before returning its digest. Failed partial directories remain and same-directory retry is refused. The caller-provided expected digest is essential: no manifest means no completed checkpoint, and a partial/mismatched manifest is not a valid continuation. Physical allocation, path containment, whole-process ownership, concurrent mutation exclusion, external preservation and orchestration of checkpoint generations remain future integration responsibilities.

Saved green02 reports **five tests passing in 1.901 seconds**. Exact comparisons include soft and hard arrays, score, iteration count and convergence across successful node/edge/normalization/iteration boundaries, rectangular zero-edge ties, iteration caps, input/config identity drift, corrupt-array refusal before any load, allowances and existing-directory refusal. The original green01 fixture attempted to mutate an immutable input; the corrected fixture constructs a replacement graph. Red01 is missing-module evidence. These checks do not address A1 or interruption between in-place mutation and cursor/phase commit, and do not establish real-workload checkpoint duration or integrated recovery admission.

Initial identities:

- `annealing.py`: `f2ab9f7746632dae39958160395fff8124796e543942101bad3381e640cb6262`
- `test_annealing.py`: `3b54fbe0e32d26953be1346afb10c0daaea0e1ef225f337d9de5956fc2b97830`

Verdict: correct A1/A2 before accepting restart-state safety. Ordinary successful safe-boundary arithmetic parity is supported by the saved synthetic checks; empirical use, accelerated substitution and full checkpoint/resource release remain unapproved.

## A1/A2 correction and focused acceptance

A1's reported invalid metadata paths are rejected. Check now requires a true safe flag, strict schema integer, finite positive schedule-consistent beta, a strictly unfinished node cursor with zero iterations, eligible edge/normalization phases and a genuine stopping condition for done. Save receives the bound graph/configuration arguments and calls the full state check before directory creation. Load and result retain that check. These are structural/reachability constraints, not an independent proof of every numerical operation that produced arbitrary caller-mutated matrices; external state mutation and concurrent ownership remain outside the component contract.

A2 is resolved conservatively. Advance marks state unsafe before mutation, restores safety only after a successfully completed work budget, and leaves it unsafe on any escaping BaseException. Save, advance and result reject an unsafe state. An interrupted partial state is therefore not a continuation point; recovery must use the last fully published prior checkpoint. The exact synthetic counterexample subclasses Q to raise KeyboardInterrupt immediately after an in-place matrix write and before cursor advancement, then verifies both save and continuation refusal. This directly addresses duplicate contribution risk without claiming transactional individual arithmetic updates or same-state recovery after interruption.

Retained red02 has **two failing assertions** for the original A1/A2 paths. Corrected green04 reports **seven tests passing in 1.423 seconds**, retaining exact scalar parity across successful checkpoint boundaries and adding unreachable-state and post-write interrupt rejection. Green03 is retained as a `ModuleNotFoundError: No module named tests` invocation/setup failure, not evidence against or in favor of the numerical correction. No reviewer tests were executed.

**Verdict: accept the isolated checkpoint prototype for continued synthetic engineering on the stated safe-boundary contract.** Dense retained state remains 24*n*m bytes, with the original validation/hash/temporary/hardening/scoring/caller-state exclusions. Atomic normalization, durable publication duration, total RSS, disk allocation, external preservation/owner orchestration and real-workload wall bounds remain unproven. The original pair capacity remains; there is no accelerated Torch substitution, registered producer integration or empirical continuation admission. The separate registered-hub full-suite release does not cover this isolated prototype.

Corrected identities:

- `annealing.py`: `e08bce459cb203f773f6029ec1d12577f948ac69301e6e78cc5016d0282ba0b6`
- `test_annealing.py`: `a19a49cb551467ace204004af17315698301974f48b50ad898c9b2855317d241`
- `green04.log`: `47793ecfa5bbee4978bf7829cc5355d6dc2150b0615401d9c874aa0acb591c60`
- `red02.log`: `41da0ab68dcf06dac986e21522537ccc7d89bdc9c07d9b99aa703cb9421f5854`
