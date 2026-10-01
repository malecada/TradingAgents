# Compact terminal handoff

Implemented a distinct schema2 compact terminal transition from actual publication.
Prebound seals and registered outputs are checked against original objects and
saved evidence. Original active leases stay closed. Current-run metadata leases
and full content checks are distinct. Partial output failures retain the terminal
identity and completed evidence; no retry or cold reuse is granted.

Evidence: red01 missing-module failure (1 failed, 3 deselected, 2.51s);
owner-check01 extracted finish regression (2 passed, 18 deselected, 35.18s);
check01 (1 passed, 3 fixture failures, 652.11s) refused missing selected execution
output names before sealing. Original test retained as test-check01.py.
Fixture correction explicitly registers binding/journal names in both plan and job;
no production relaxation. check02 (3 passed, 1 deselected, 745.20s) exercises
actual success and later registered outputs, old lease refusal, corruption,
final callback revocation and preservation after the second output fails.
No combined final four-case run is claimed.

This is a bounded current-resident engineering result. The original producer
objects remain held; metadata leases do not verify complete scientific content.
No financial fit, whole-workflow capacity or empirical admission is established.

Exact source/test SHA-256:

- tradingagents/research/onchain_replication/compact_terminal.py: `40a1a2f696e742b91404acf0b7b993ba8c236998bb60f7c7c89ed5614b94fdec`
- tradingagents/research/onchain_replication/compact_owner.py: `e6400728902eca6c0d72a1eab9ff6cdaf2e82f7d65bda2f2def9d8752b990df5`
- tests/research/onchain_replication/test_compact_terminal.py: `7194e9e7d737b0c7e509c77882d9700ea06e04f58e5699834223b3caa15b8920`
