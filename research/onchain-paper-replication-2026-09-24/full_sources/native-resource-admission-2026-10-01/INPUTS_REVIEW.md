# Independent retained-resource input review

Accepted as a compact metadata inventory and arithmetic preparation only.
`execution_admitted: false` is appropriate. No resource job, financial fit,
array reread, budget adoption or coverage update follows from this review.

Independent reconstruction verified all **43** compact input pins against their
current byte sizes and SHA-256 values. The nine distinct weeks and graph hashes
join the exact manifest hashes in saved complete verification results. Each
manifest has the expected five array members; their declared file-byte sum
equals the verifier's total. All saved node-feature error fields are zero.
These are checks of existing verification evidence, not repeated numerical
verification or a fresh assertion about raw transaction semantics.

The two legacy results match their exact week-labelled entries in the accepted
legacy closure, including manifest identity, node/edge counts, array bytes and
closed-mapping flags. The corrected builder compares complete entries instead
of deleting the payload's `week` field. The original FAILED pilot disposition
remains seven completed and 102 unavailable cells; the later array verification
does not convert that producer into a successful run.

All 109 original requirement IDs remain unique. The 32 pending records are
identical to coverage05, including original reasons/statuses, and occur exactly
once across the nine graph rows. Counts remain 77 supported and 32 pending:
seven neighborhood, seven matching, nine MCM and nine neural-checkpoint
requirements. The first two graph weeks each retain MCM and neural requirements;
the other seven each retain all four stages. No pending cell has been dropped
or marked complete by preparing this inventory.

Independently recomputed aggregate values:

| Quantity | Value |
|---|---:|
| Nodes | 18,046,816 |
| Directed edges | 24,381,697 |
| Saved five-array file bytes | 4,779,690,416 |
| Dense 32-motif float32 payload bytes | 2,309,992,448 |
| Dense 32-motif float64 payload bytes | 4,619,984,896 |
| Node-by-motif pair evaluations | 577,498,112 |

The MCM figures are respectively `nodes × 32 × 4`, `nodes × 32 × 8` and
`nodes × 32`. They exclude headers, retained graphs, neighborhood/pair workspace,
dictionary construction, model/autograd state, publication/checkpoint copies,
leases and I/O costs. They do not select a dtype, estimate runtime/RSS, require
all graphs to be resident together, or establish feasible whole-workflow limits.

The pinned dictionary/matching settings retain 512 samples, 32 motifs,
10,000 maximum neighborhood nodes and 4,000,000 maximum pair entries. Seed 11
is an explicit builder literal, not derived from these 43 pins. Independent
source inspection confirms the original neighborhood sampling and neural stress
phase use seed 11 in `pilot_successor_02/phase.py` (SHA-256
`0bc95f7e33d97485cd9e2fba6802dde168c26aa162b987ef762f9e28ee3a1522`).
A prospective job must bind its actual seed and complete configuration through
its own committed registration rather than treat this report as admission.

`inputs01.log` retains the legacy week-field comparison failure. The corrected
`inputs02.log` reports nine graphs, 32 pending requirements and the totals above.
The reviewer inspected the source/logs and reconstructed the compact joins
without executing `build_inventory.py`, tests or any historical job.

Independently calculated SHA-256 values:

- `build_inventory.py`: `54151f9a582790d060c3cc8c74e88aa10e5ae1df8fb34df78918f39cb6ce17a5`
- Preserved `build_inventory.inputs01.py`: `6879b5f6eea6562427b967cce13ae4a72a3a3caa1965137fbed00e27c3ac4355`
- `inputs01.log`: `168adb9bfb69e57e09e31980f66d5bb2d20ff2c5e9aae8c4ef74acae7273e700`
- `inputs02.log`: `3f4c9fe2ecea1637c157e7107a9ec92262423f804dd0756c4573e16c79ded4bd`
- `inputs02.json`: `dc4c267c1cd8ce98ec14b49bc5b5c3253598f0380e3d23efdbc6a4286d3d322b`

This review does not promote the builder into a concurrent guarded input reader:
its compact-file size check and subsequent read are ordinary preparation I/O,
not an atomic or adversarial filesystem admission protocol. Array availability
and unchanged members, source/runtime closure, exact resource cells, outer
limits, physical/checkpoint growth, attempt budget and fresh guard admission
remain mandatory for a concrete future job. The adjacent budget draft is not
adopted or released by this acceptance.
