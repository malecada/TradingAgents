# Compact historical metadata adapter

`metadata.py` is a pure validation function. It accepts prepared bindings and
31 raw compact JSON buffers, graph-configuration bytes and the original root
path. It verifies buffer hashes/extents and original claim, failed terminal,
guard, supervisor, observer and retained closure joins. All109 historical cells
remain represented (7complete/102unavailable). Two individually complete graph
phases are joined to their original intents, results and saved manifests, then
to seven contiguous indexed source days, the external reconstructed coverage
and raw/canonical graph configuration. Declared ten-array extents and names are
checked without reading array bodies.

`metadata-red01.log` contains ten failures before implementation;
`metadata-green01.log` records ten passing checks. These are compact historical
metadata consistency checks with in-memory invalid variants, not invented graph
data tests. They neither repeat empirical jobs nor create new outcome evidence.
The original array checker retains its separate twelve tiny synthetic tests.

The function deliberately does not read files, create claims or start workers.
Its caller must bind preparation bytes (original inputs.json SHA256
`a070b530842873b78fe144402405f613fe8a2e6625bf97600b5512b8dc0eb62e`),
this module, reviewed array checker, graph configuration, exact runtime and
finite wrapper before empirical-array reading. It must enforce bounded regular
immutable reads, preserve absolute historical paths or declare a relocation,
reject changed sources and duplicate/terminal identities, and retain exclusive
start/partial/failure/completion receipts. Pure validation success does not
provide these execution guarantees.

No source-body uniqueness, transaction-value correctness or exclusion semantics
is independently re-audited. The historical FAILED claim remains FAILED even
if both independently saved-array checks later pass. Prospective registered
reuse remains separate from verification of existing outputs.
