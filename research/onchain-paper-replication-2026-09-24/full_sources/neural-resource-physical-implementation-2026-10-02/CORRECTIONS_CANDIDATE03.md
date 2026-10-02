# Candidate03 — original ordinary cause and first fatal preservation

Candidate02 and all historical evidence remain unchanged. The selected guard now retains the original ordinary body exception so that a later fatal cleanup exception explicitly chains that exact object. Ordinary body failure alone still returns the failed guard state. A failure during finalization still raises; the first fatal (including MemoryError) is preserved and subsequent errors become notes. The omitted-policy legacy branch is unchanged.

Red15 reproduced missing ordinary cause: 1 failed, 1 passed. Check18 passed 9 targeted tests. Red16 then reproduced an existing MemoryError being replaced by a later physical cleanup fatal: 1 failed, 3 passed. Check19 passed 10 affected tests. Check21 repeated those 10 after retaining explicit finalization-failure propagation (39 deselected, 2.30s; consult raw log for exact duration). These are synthetic mocked-unit checks, not actual OS containment or full-graph feasibility.

Check20 passed 42 tests: 39 unchanged default resource regressions and 3 pure tests of the separately frozen smoke candidate02 draft. The smoke draft preserves fatal priority across independent terminal publication errors and still attempts observer/finish after unavailable claim observation. No OS smoke was executed, no identity was reserved, and its spec remains NONEXECUTABLE_DRAFT with unresolved source bindings. The original smoke draft/spec/manifest remain preserved.

No numerical or resource caps changed. No heavy/model rerun was performed. Candidate03 source snapshots retain the same seven files as candidate02; only resources.py and test_neural_physical.py differ. New smoke test is frozen separately with the smoke preparation artifacts.
