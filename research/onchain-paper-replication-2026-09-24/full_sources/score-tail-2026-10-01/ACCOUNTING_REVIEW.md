# Independent completed-score accounting review

Accepted as the stated conditional encoded-byte arithmetic. All three maintained-source hashes and the compact input hash match current files. Independent reconstruction matches every field in all nine rows and all totals; no accounting script, test, matcher, array reader or empirical job was executed.

The proposed 65,536-cell chunk yields 5,242,880 record bytes per full tail and 524,288 float64 payload bytes per full batch, within the respective primitive limits. Chunk counts are rounded separately for each graph, correctly totaling 8,816 rather than rounding only the combined denominator. The unchanged nine-graph, 32-motif arithmetic contains 577,498,112 cells.

The actual writers support the metadata count: per chunk, tail start and terminal, batch header and stream seal link contribute four independently capped 8 KiB files. Per graph, batch start and terminal plus stream start and completion contribute four more. Record payloads retain 80 bytes per cell; batch payloads retain another eight bytes. Thus the exact conditional totals are:

| Term | Bytes |
|---|---:|
| Retained tail records | 46,199,848,960 |
| Sealed float64 batch payloads | 4,619,984,896 |
| Metadata allowance | 289,177,600 |
| Logical completed-score bound | **51,109,011,456** |

This bound describes one completed proposed stream per graph under the three pinned implementations. The metadata term is an allowance, not measured file size. This is not a physical allocation estimate, a runtime/IOPS/RSS measurement, an adopted chunk configuration or a purchase requirement. Existing per-pair journals/checkpoints remain additional storage; tails are deliberately preserved alongside chunks. Filesystem overhead, graphs/dictionaries, logs, live matching state, predecessor/failed-attempt evidence and other outputs remain outside the total. No inference is made that a real dictionary with 32 representatives or a feasible full-fold run has been produced.

Reviewed SHA-256 values are recorded below. The input and three source pins inside accounting01.json were independently checked. This direct arithmetic provenance is not a full execution dependency closure or registration amendment.

- `accounting.py`: `8565cdaf4fa7b3b45ca5b3e177a13cd9b8047b12f4e0a4fbfac5349fedf1ca56`.
- `accounting01.json`: `d3dfa6ece6acccd76c5afc9863261c0ac8fb9b40e3dc60f78cd1f5e690bac044`.
