# Independent metadata component review

Accepted for the stated pure metadata denominator validation scope. No material blocker was identified in the reviewed source and saved evidence. This does not establish registered ownership, raw-data completeness, economic validity or empirical admission.

## Exact evidence

All 17 declared bindings match current bytes. Manifest SHA-256: `150f5303366cefa36d0d5bf507f9a50e392246fbd51230774c7084837b2de651`.

- `denominator.py`: `e3ffddacc03011fb6e1b5f446c6820ac491a6e7b84c8ffef01b7f507530c1bd8`.
- `test_denominator.py`: `709d4b0823bd99ba64a7950bf66f0a665934315f8a06eb127307cca984a65554`.
- `check03.log`: `bcb0ae1ec58059f2d80c397e3ebb1cd3cad2a8c666d7e62e362a48cb06bb6771`.

The saved final log reports seven methods passing in 0.026 seconds. Earlier missing-component failures and datetime/string fixture-path errors remain preserved with source/test versions. The expanded tests add missing/late graph and purge branches without changing the corrected component source. No reviewer rerun was performed.

## Assessed semantics

The validator reconstructs every daily decision slot from train start through the exclusive test end. Included train/test rows and explicit exclusions must account for every slot exactly once, with chronological included sequences and chronological exclusions. Rehashing a truncated, duplicated or reordered manifest cannot waive this independent calendar check. It verifies the complete supplied manifest hash and the manifest's train and test-mask hashes separately.

Comparison with maintained `dataset.build_examples_from_metadata` confirms the same train/test partition convention and forced exclusion precedence: training labels ending at or after test start are purged; the intervening fold gap is outside-fold; test labels cannot cross test end. The actual input-day lookback sequence and one-day label interval are exact. Each graph must belong to the expected week for that input step and be available by that step, closing the final-decision-only timing shortcut.

Weekly metadata requires Monday midnights, seven-day intervals and at least the frozen one-day publication lag. Graph hashes and week keys cannot duplicate, assets must agree, and graph source references must be contained in the supplied example source set. The supplied population and required graph lists are sorted and unique; the former must match actual metadata identities and the latter the union actually used by included examples. Missing/late graph exclusions replay the maintained first-failure order across input dates.

The tests use five literal calendar dates and two weekly graph identities. They cover complete accounting, rehashed missing/duplicate/reordered dates, per-input future graph use, wrong labels/lookbacks/partition clocks, graph population/union and calendar-cap refusals, missing/late graph exclusions and a purged training label. A recorded price exclusion still occupies its denominator slot and does not become a successful data-coverage claim.

## Explicit limitations

The expected manifest hash, actual Fold fields, lookback and CalendarGraph metadata are trusted externally supplied inputs that must later join registration. Equality with `fold.member_hash` alone does not independently recompute its binding to Fold fields or source coverage. Graph identities likewise are not recomputed from numerical graph bodies here. Required completion receipts, leases and owner/source/runtime admission remain separate.

Prices, targets, direction labels and price-based exclusions are not independently validated. The explicit `price_exclusions_revalidated: false` qualification is necessary; a passing denominator does not authorize dropping dates or assert price/history completeness. Missing/late graph exclusion checks remain conditional on the supplied graph population.

`max_calendar_days` bounds daily calendar enumeration. It is not a total input-size, lookback, graph-population, serialization-memory or process RSS bound; manifest hashing occurs over already supplied objects. The five-day/two-lookback synthetic fixture does not alter the registered 28-day scientific lookback or prove full-fold resources.

Review activity read source, compact logs and declared compact-file hashes only. No historical jobs, tests, empirical arrays, raw market data or financial trials were executed or read. No registration, ledger, scientific configuration or empirical budget was changed.
