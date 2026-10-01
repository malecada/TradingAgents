# Independent final review

Accepted for registered metadata-only daily denominator admission from an actual current compact Training route. CDEN1 is resolved. `REVIEW_INITIAL.md` and all failed/intermediate evidence remain preserved. This review used source, test, diff, log and hash inspection; no checks or empirical jobs were rerun.

The adapter joins both selected plan/job policies and descriptors to actual Training authority, registered calendar and coverage inputs, a reconstructed exact Fold, the full ExampleManifest hash, and actual graph population metadata. The preserved validator is explicitly admitted by source hash. It accounts for every date in the fold span through included rows or explicit exclusions, checks chronological lookback and each graph's expected week/availability, and verifies the exact required graph union. It does not recompute price-based exclusions or prices/labels.

CDEN1's new preflight rehashes original examples/fold/graphs and requires both admitted partitions to be nonempty and every row's date/price/graph/availability lengths to equal configured lookback before calling the validator. This binds date expansion to already admitted resident rows. The actual Training implementation also requires nonempty partitions, so exclusion-only populations cannot bypass this preflight. The lookback regression supplies 500,000 registered days but traps the validator boundary: corrected admission refuses before that boundary without allocating the large tuple. No lookback truncation or historical validator edit was made.

Receipt checks retain the actual Training lease, source checks, and callback-free original example/fold/graph rehashing. The final timing regression now arms only after the source-check barrier in `Receipt._check`, replaces an immutable GraphSnapshot array through explicit attribute replacement during the following final Training callback, and requires the exact original-graph hash refusal. No mutable-array assignment protection is mistaken for this boundary check.

## Evidence and qualifications

- `check01.log`: **5 passed, 96.22 s**, original source. Its original broadly named graph-mutation case only hit immutable array protection; it did not prove mutated graph rejection.
- `red02.log`: **1 failed, 5 deselected, 21.35 s**, safely reproduced CDEN1 by trapping entry into the validator.
- `check02.log`: **1 failed, 2 passed, 4 deselected, 60.65 s**. Corrected positive admission and lookback refusal passed. The new final-callback test still attempted direct mutation of immutable array storage and failed its expected diagnostic.
- `check03.log`: **1 failed, 1 passed, 5 deselected, 40.86 s**. Attempting to enable writeability on the immutable byte backing still did not implement the intended mutation. Its one passing broad refusal is not evidence of changed graph content.
- `check04.log`: **2 passed, 5 deselected, 41.52 s**. Explicit graph attribute replacement exercises actual population drift, including the specifically armed final callback.

There was no combined final seven-case run. Implementation is unchanged since the check02 positive/lookback passes; the later changes correct test injections. The earlier truncated-denominator, coverage and calendar-cap refusals remain separately preserved evidence. Synthetic positive coverage is 20 fold dates, 2 train rows, 2 test rows and 16 explicit exclusions. Actual registered ownership is exercised with mocked guard surfaces; no fitting, array materialization or sampling occurs in the adapter.

This establishes accounting of the registered daily population, not empirical data completeness, independently validated price exclusions, reconstructed label validity or successful graph features for all required inputs. `graph_completion_validated` and `representation_admitted` remain false. Historical/cold reuse, full resource/RSS feasibility, native dispatch and empirical fitting remain outside acceptance. Calendar cap bounds represented days; lookback work is additionally constrained by admitted row sizes, not by a new universal process-memory bound.

## Final direct bindings

Final source/test/log hashes are recorded below. They are direct bindings, not a complete transitive execution manifest.

- `compact_denominator.py`: `6579c4aa57804ecfd35010beb81df0e81f722285bea9fda856d1a7f8e466b372`
- `test_compact_denominator.py`: `7e0dadcd96d28de7b0287268bdea35945d4938e3ef6adb8faccc04fa3f724caa`
- `check04.log`: `3a92f7938739087441ccd2eac83f86a0ed1d315dcbe4ced516ddf6daac966c41`
