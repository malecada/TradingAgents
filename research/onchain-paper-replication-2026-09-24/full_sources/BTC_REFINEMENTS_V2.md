# Prospective Bitcoin source and subset refinements

The completed metadata-only claim retains its original85,488-cell denominator.
The prospective full-value source grid adds BTC top-level transaction index for
observed UTXO ordering:88,776asset/date/field cells,3,288additional cells. No
original source/result/gate bytes are overwritten and no price/model outcome
has been inspected. Every body capture must bind the revised grid explicitly.

The normalized decoder admits only scalar address strings or missing addresses;
list/tuple schema variants, including singleton lists, fail rather than silently
becoming exclusions. Null/empty address means the declared whole-transaction
nonunique-script exclusion. Each source binary64 input/output value is inverted
onto the unique satoshi grid only if conversion back to binary64 is identical.
Nonfinite/off-grid values fail. This is a declared source-precision assumption,
not proof that the original provider preserved chain values. No aggregate fee
or value float is used for exact accounting. Source-naive timestamps are
interpreted as UTC, explicitly qualified by the source schema.

When all positions are supplied, a block height maps to one hash and timestamp,
positions are unique, observed creators precede spenders, observed creator output
indices/values/addresses agree, and observed coinbase maturity is at least100
blocks. All-or-none position completeness is enforced. These checks do not
certify unobserved prevouts or canonical chain membership. They do not replace
raw-to-graph independent verification.

Exact graph sidecars use hex numerator/denominator pairs, avoiding integer decimal
conversion limits and binary64 rounding. Generic subset receipts use schema2; the
BTC exact wrapper uses schema3, binds the parent exact edge/incident amounts,
retains selected isolates, and sums retained rational node values before the
sole final native-unit binary64 conversion. Known fees and raw admission counters
remain explicitly those of the parent transaction population. They are not
reinterpreted as subset transaction totals. The wrapper rejects inconsistent
parent edge/incident/node features before either whale or fund treatment.

Evidence: btc-synthetic-01.xml37cases; btc-synthetic-02.xml39cases including exact
subset integration. Independent review is recorded in IMPLEMENTATION_REVIEW.md.
Empirical BTC source admission, actual body capture, canonical-chain assurance
and the original fund cohort remain pending. These software refinements do not
consume an empirical fit or admit a data source.
