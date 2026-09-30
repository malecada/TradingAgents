# Independent hub-edge census component review

September 30, 2026. Source and saved synthetic evidence only; no tests, graph bodies, census arrays or jobs were executed by the reviewer.

No blocking component finding was identified. Membership starts with the center, then includes every opposite endpoint of every incident source column in both directions. It does not expand recursively through newly selected neighbors. After checking the exact expected cardinality, the second full scan counts each original directed edge column whose endpoints are both members. Reciprocal columns, duplicate columns and loops retain their original multiplicity; isolates and zero-edge graphs are handled. This matches full weak one-hop induced-edge semantics and introduces no scientific capacity limit or truncation.

The numeric envelope `N + 32*min(edge_chunk,E) + 16*center_count + 65,536` is conservative for one N-byte boolean mask, bounded endpoint comparison/gather temporaries, and induced-membership masks. For the prospective N=2,764,221, chunk=65,536 and 35 centers it is **4,927,469 bytes**, below the proposed 8 MiB allowance. Input/mapped residency, Python rows/dictionary/callback state and runtime/library overhead remain excluded. The positive/strict-integer policy and allowance are checked before mask allocation. There is no runtime or RSS proof, and work still requires two full edge scans per center after endpoint validation.

Saved green01 reports **five tests passing in 0.019 seconds**. The independent set oracle covers reciprocal, directed, duplicate and self-loop columns, isolates, random graphs, multiple chunk boundaries, no edges, a complete 10,002-node star, cardinality mismatch and allowance refusal. The checkpoint test establishes callback invocation for completed centers and propagation of callback failure. It does not establish durable publication, interrupted denominator recovery, same-device ownership, buffer lifetime under retained exception tracebacks, or an empirical 540-second bound. Red01 is retained missing-module evidence, not five separately executed failing assertions.

The component accepts one to 64 explicit centers in dictionary insertion order. The prospective wrapper must independently derive **all 35** centers above 10,000 from the exact bound prior cardinalities, sort them by original global index, verify the denominator and each expected count, and preserve every complete/failed/unavailable disposition. It must bind the exact graph/census identities, supply durable per-center checkpoints, account actual output allocation, and enforce outer RAM/disk/time ownership. The prototype callback alone is not a durable checkpoint system or continuation mechanism. Source/runtime/gate admission and empirical release remain separate.

Verdict: accept this isolated component for continued synthetic integration. Exact induced-edge measurements, resource feasibility, production integration, matching and financial fits remain untested.

SHA-256 identities:

- `hub_edges.py`: `e5858170437f6d9f0a994315e2b2aa30d502844cf0a1c1b8ec782a1e693887e9`
- `test_hub_edges.py`: `71a785b9df0cbf2bb2a1c0e14c02416d7a712d07fd169cc9cd3eff6ae356c63b`
- `green01.log`: `bfe10f9e06140b6d8025b852df8827f450f1d720d41f4648382bd16364593151`
- `red01.log`: `c61506d0198a5f731e31cf454967ab0971c22a7eea4c6baf28fb8e7868a220e4`
