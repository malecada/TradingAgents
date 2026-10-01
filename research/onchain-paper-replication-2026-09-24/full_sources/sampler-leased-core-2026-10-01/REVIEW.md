# Independent leased sampler-core review

Accepted for the bounded resident core described in SCOPE.md. No material
blocker was found in the inspected source. This is not acceptance of a durable
sampler producer, resumable sampling or an empirical execution.

Source, the maintained sampler, array-neighborhood cleanup, fixtures and saved
evidence were inspected independently. All 16 declared direct-file hashes match
current bytes. bindings.json SHA256 is
`d14a4edfe4866302d8c6df318595a9efe3e577a49132fbdec1c4b12ebd01ba81`.
Only this review file was written. No tests, jobs or numerical files were opened
or executed by the reviewer.

The derived resident algorithm preserves the maintained training-time filter,
sorting and parent hashes, initial equal weights, PCG64 construction, NumPy
choice and chosen-probability capture, selected-center zeroing, overlap halving,
record order and final sample-identity formula. Deleting the probability array
after capturing its selected value changes its lifetime rather than the draw or
update semantics. Configuration is copied before callbacks can operate.

Center/direct-weight limits and a fresh lease precede weight allocation. Each
draw checks the lease, obtains a complete bounded array neighborhood, applies
the unchanged weight update, and emits a frozen record with before/after RNG
states. Index and previous-hash fields chain the events; the event hash is
computed before its sha256 field is added. A lease precedes and follows the
checkpoint callback. ExitStack closes the current index on callback/lease
exceptions and graph switches. A final lease precedes the returned manifest.

Saved check01 reports seven passing tests in 0.055 seconds. Five seeds each draw
seven centers from two training graphs while excluding a future graph. Tests
compare complete records and probabilities, source order, final RNG state,
sample identity, local graph identities and all three local array values with
the unchanged maintained sampler. The event hashes/previous links are recomputed.
Other tests cover initial lease and direct-weight refusal before np.ones,
mandatory policy/callbacks, retained-cap and nontruncating hub refusal, callback
failure with index closure and post-checkpoint lease loss preventing more draws.
These are saved synthetic results, not an independent rerun or proof for every
population/runtime. The seven missing-component failures remain preserved.

Evidence SHA256:

- core.py: `07428fc777ec7224f199d245aee10658b8f4e74520732f6c85dcc7d8d2a37bc6`
- test_core.py: `20701aa4e12e0b2c1d864fee50cf56d237869b338450b60e69ddf460ac7e8606`
- check01.log: `704bf6eb5cfa8c474d704ebeffcb132602837282689bf03c30f752c4c1fdddbe`
- SCOPE.md: `d305ef5909174c90a5fb2061ab3a23716e69a8fff149e26d94567b88a55377f2`

The retained sample cap is checked after constructing the next local graph;
that graph's scratch/output copies require the separate neighborhood allowance.
Sixteen bytes per center accounts only for weights and one probability array,
not NumPy choice scratch, offsets, parent arrays, metadata or process RSS.
No measured scaled feasibility or actual guard admission is established.

Callbacks are not durable checkpoints. Exclusive attempt reservation, terminal
dispositions, refusal to redraw partial identities, registered source/policy
and actual owner admission, pre-write artifact capacity and exact publication
proof remain required. No resume API exists. The existing sample-artifact reader
does not verify a sampler sidecar, so provenance-aware consumer admission also
remains outstanding. The direct manifest is not complete empirical source/runtime
closure. No scientific configuration, mapped-weight floor, trial allowance or
historical result is changed by this component acceptance.
