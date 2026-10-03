# Producer03 — exact TP3 hash correction

This uninstalled candidate adds one call: `hashed(ref['sha256'])` in `registered(role)`, before path resolution and the optional metadata reader. Registered roles must carry an exact non-null lowercase 64-hex SHA256. Local unpinned intent/row metadata handling is unchanged. No placeholder pin is adopted into the candidate or genuine claim.

The complete source byte/AST inverse restores producer02 exactly. Job.py and treatment_contract.py remain byte-identical; every other inherited preparation02 file and the independent review02 are preserved. T1/T2 recovery, actual resolved claim['inputs'] late bindings, complete denominator and finalization behavior are unchanged.

The actual-source controls reproduce producer02 accepting null on execution_job and plan. Successor controls refuse null, empty, short/long, nonhex/uppercase, integer/bool/dict/list/bytes and well-formed-but-wrong hashes; exact actual file hashes preserve the same opaque complete row. Invalid pins fail before path lookup or reading. TP3_CHECKS02 records 194 checks including 48 previous/successor role/pin cases and exact preservation joins. Check01 is retained but superseded: its prior-review existence-only assertion contained a dead conditional; check02 replaces it with exact byte verification of every preserved independent review body. Check01 is not counted as extra verification.

No ResearchRun, Owner, claim, numerical library/array, native process, registration, storage policy, gate, budget or Git/network action was invoked. Opaque metadata is utility evidence only. The candidate awaits different-author review and Root's separate exact integration/admission. All existing source-only and fund-cohort limitations remain.
