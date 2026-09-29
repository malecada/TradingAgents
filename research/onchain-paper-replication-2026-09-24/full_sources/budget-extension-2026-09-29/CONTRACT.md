# Explicit cumulative extension contract

Engineering continuation from f199dddf; no empirical release. Preserve each
historical family object, claim, terminal and exposure. An optional experiment
cumulative_budget_extension reference supplies committed extension and independent-review
metadata, both also included in source_files for historical claim verification.
The extension binds the unchanged base family, program, reviewed cumulative
ceiling, consumed count, exact closed claim/terminal snapshot, initial adopter,
allocation document and reason. The review must accept that exact extension hash.

The first adopter must match its frozen identity and the full then-current family
claim snapshot. Subsequent claims carry the accepted extension, retain all spent
attempts and use its cumulative ceiling. A stale/lower ceiling cannot supersede
an already adopted higher ceiling. A later extension includes all prior claims,
including earlier extension claims. No family renaming, history editing, terminal
identity retry, active-owner omission or spent-attempt refund is permitted.

Admission checks occur under the existing start lock as well as preflight.
Extension metadata are bound at source/design freeze; empirical input bodies are
not opened by admission. Claims record effective_attempt_budget explicitly while
retaining the unchanged family object. Independent structural verification checks
the bound extension/review and recorded effective ceiling. A budget review alone
never admits data, resources, fits or a deployment.

Synthetic regression coverage must show an exhausted family can spend exactly
its reviewed extra allowance; failures still consume attempts; incomplete or stale
snapshots, active parents, changed history, missing/rejected review, changed
metadata, wrong adopter and uncarried/downgraded extensions fail before claiming.
All existing ordinary admission behavior remains covered by lifecycle tests.

Historical `budget_extension` metadata remains opaque to this generic mechanism;
it was already used by a separate dated-mark certificate implementation. The
new field is deliberately distinct and historical receipt bytes remain intact.
